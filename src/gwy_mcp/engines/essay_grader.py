"""申论批改引擎 — 分题型评分 + 范文锚定 + 结构化输出。

支持全部申论题型：概括题、分析题、对策题、应用文、大作文、综合题
每种题型有独立的评分维度和采分点逻辑。
"""

from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"

with open(_DATA_DIR / "essay_rubrics.json", "r", encoding="utf-8") as _f:
    _RUBRICS = json.load(_f)

with open(_DATA_DIR / "reference_essays" / "essay_bank.json", "r", encoding="utf-8") as _f:
    _ESSAY_BANK = json.load(_f)


def _get_rubric(essay_type: str) -> dict:
    """获取指定题型的评分细则。"""
    # 规范化题型名
    type_map = {
        "概括题": "概括题", "归纳概括": "概括题", "归纳概括题": "概括题",
        "分析题": "分析题", "综合分析": "分析题", "综合分析题": "分析题",
        "对策题": "对策题", "对策建议": "对策题", "对策建议题": "对策题",
        "应用文": "应用文", "应用文写作": "应用文",
        "大作文": "大作文", "议论文": "大作文", "策论文": "大作文",
        "综合题": "综合题",
    }
    canonical = type_map.get(essay_type, "大作文")
    return _RUBRICS["question_types"].get(canonical, _RUBRICS["question_types"]["大作文"])


def _find_references(topic: str, essay_type: str) -> list[dict]:
    """从范文库检索相关参考范文。"""
    matches = []
    canonical = essay_type
    # 将"概括+对策"等复合类型同时匹配两种
    search_types = {essay_type}
    if "+" in essay_type:
        for t in essay_type.split("+"):
            search_types.add(t.strip())
    
    for t in _ESSAY_BANK.get("topics", []):
        if t["type"] in search_types or t["type"] == essay_type:
            matches.append(t)
        elif any(kw in topic[:30] for kw in t["topic"][:30]):
            matches.append(t)

    refs = []
    for m in matches[:2]:
        samples = m.get("samples", {})
        for tier in ["high_score", "mid_score"]:
            if tier in samples:
                s = samples[tier]
                refs.append({
                    "title": s["title"],
                    "score": s["score"],
                    "max_score": s["max_score"],
                    "content": s["content"],
                })
        if "scoring_guide" in m:
            refs.append({"scoring_guide": m["scoring_guide"]})
    return refs


# ---------------------------------------------------------------------------
# 分题型评分 Prompt
# ---------------------------------------------------------------------------

def _build_system_prompt(essay_type: str) -> str:
    """根据题型构建评分系统 prompt。"""
    rubric = _get_rubric(essay_type)
    dims = rubric["dimensions"]
    total_score = rubric["total_score"]
    
    dim_lines = []
    for i, d in enumerate(dims, 1):
        guide = d.get("scoring_guide", d["description"])
        dim_lines.append(f"{i}. **{d['name']}**（{d['max_score']}分）：{guide}")
    
    prompt = f"""你是一位经验丰富的公务员考试申论阅卷老师。请严格按照以下标准批改这道**{essay_type}**。

## 本题评分标准（满分{total_score}分）

{chr(10).join(dim_lines)}

## 批改流程

### 第一步：采分点对照（仅概括题/对策题需要）
- 如果是概括题：逐条检查考生是否覆盖了资料中的核心要点
- 如果是对策题：逐条检查对策是否针对具体问题，是否包含'主体+手段+目标'

### 第二步：逐维评分
按照上述维度逐一打分，每个维度必须给出：
- 得分 + 扣分理由
- 具体改进建议（引用考生原文指出问题）

### 第三步：逐段/逐条批注
- 对答卷的每个要点或段落给出具体问题 + 修改建议
- 如果有参考范文，指出差距

### 第四步：综合评语 + 改进优先级
- 给出50-100字综合评语
- 列出3条最优先改进方向

## 关键原则
- **概括题**：核心是采分点覆盖度，不是文采
- **分析题**：核心是多角度分析的深度
- **对策题**：核心是对策的针对性和可行性
- **应用文**：核心是格式正确性和语言得体性
- **大作文**：核心是立意、论证和政策高度
- 严格按照 JSON Schema 输出，不要遗漏任何字段
"""
    return prompt


# ---------------------------------------------------------------------------
# 批改主函数
# ---------------------------------------------------------------------------

async def grade_essay(
    question: str,
    user_answer: str,
    essay_type: str | None = None,
) -> "EssayGradingResult":
    """批改一篇申论答卷。

    Args:
        question: 申论题目
        user_answer: 考生作答内容
        essay_type: 题型（概括题/分析题/对策题/应用文/大作文/综合题）

    Returns:
        EssayGradingResult
    """
    from gwy_mcp.llm.client import get_client
    from gwy_mcp.models.schemas import EssayGradingResult

    client = get_client()
    etype = essay_type or "大作文"
    rubric = _get_rubric(etype)
    refs = _find_references(question, etype)

    # 构建参考范文文本
    ref_text = ""
    for r in refs:
        if "scoring_guide" in r:
            continue  # scoring_guide 已在 prompt 中
        ref_text += f"\n## 参考范文（{r['score']}/{r['max_score']}分）\n{r['content']}\n"

    user_text = f"""## 题型
{etype}（满分{rubric['total_score']}分，建议字数{rubric['typical_word_count']}）

## 考生题目
{question}

## 考生作答
{user_answer}
{ref_text}
"""

    system_prompt = _build_system_prompt(etype)

    return await client.extract_structured(
        text=user_text,
        schema=EssayGradingResult,
        system_prompt=system_prompt,
        temperature=0.1,
        max_tokens=4096,
    )


def list_reference_topics() -> list[dict]:
    """列出范文库中所有题目。"""
    return [
        {"id": t["id"], "topic": t["topic"][:50], "type": t["type"]}
        for t in _ESSAY_BANK.get("topics", [])
    ]


def list_question_types() -> list[dict]:
    """列出所有支持的题型及评分标准概要。"""
    result = []
    for name, info in _RUBRICS["question_types"].items():
        result.append({
            "type": name,
            "total_score": info["total_score"],
            "word_count": info["typical_word_count"],
            "dimensions": [d["name"] for d in info["dimensions"]],
        })
    return result
