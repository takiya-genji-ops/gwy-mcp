"""申论批改引擎 — 基于 DeepSeek + 范文锚定 + 多维评分细则。

核心策略：
1. 根据题目类型加载对应评分标准
2. 从范文库中检索相关参考范文（高分+中档）作为锚定
3. 调用 LLM 进行结构化评分（6 维）+ 逐段批注
4. 返回 EssayGradingResult
"""

from __future__ import annotations

import json
from pathlib import Path

from gwy_mcp.models.schemas import EssayGradingResult


# ---------------------------------------------------------------------------
# 范文库 & 评分细则加载
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

with open(_DATA_DIR / "reference_essays" / "essay_bank.json", "r", encoding="utf-8") as _f:
    _ESSAY_BANK = json.load(_f)


def _find_references(topic: str, essay_type: str) -> list[dict]:
    """从范文库中检索相关参考范文。

    Args:
        topic: 用户答卷对应的题目文本
        essay_type: 题型（大作文/概括题/分析题/对策题/综合题）

    Returns:
        匹配的参考范文列表，每项含 {title, score, max_score, content}
    """
    matches = []
    for t in _ESSAY_BANK.get("topics", []):
        # 类型匹配 + 关键词匹配
        if t["type"] == essay_type:
            matches.append(t)
        elif any(kw in topic for kw in t["topic"][:20]):
            matches.append(t)

    refs = []
    for m in matches[:2]:  # 最多取 2 个匹配主题
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
        # 附加评分指南
        if "scoring_guide" in m:
            refs.append({"scoring_guide": m["scoring_guide"]})

    return refs


# ---------------------------------------------------------------------------
# 评分 Prompt
# ---------------------------------------------------------------------------

_GRADING_SYSTEM_PROMPT = """你是一位经验丰富的公务员考试申论阅卷老师。请严格按照以下流程批改考生答卷。

## 批改流程

### 第一步：确定题型和评分标准
- 首先判断题型（概括题/分析题/对策题/大作文/综合题）
- 根据以下通用评分维度进行评分（每个维度满分为该维度的权重分）

### 第二步：六维评分

| 维度 | 概括/分析/对策题满分 | 大作文满分 | 评分标准 |
|------|---------------------|-----------|---------|
| 立意准确度 | 20 | 25 | 是否紧扣题目、抓住核心命题 |
| 结构完整性 | 15 | 20 | 是否有清晰的开头-主体-结尾结构 |
| 内容充实度 | 25 | 20 | 要点是否全面、论证是否充分 |
| 政策高度 | 10 | 15 | 是否引用政策文件、结合时政背景 |
| 语言规范性 | 15 | 10 | 是否使用规范公文语言、无口语化表达 |
| 格式规范 | 15 | 10 | 字数是否符合要求、段落是否合理 |

### 第三步：逐段批注
- 对答卷的每一段给出具体问题 + 修改建议
- 如果某段写得很好，也要明确指出

### 第四步：对比分析
- 如果提供了参考范文，将考生答卷与高分范文进行对比
- 指出差距最大的 1-2 个方面

### 第五步：综合评语 + 改进优先级
- 给出 50-100 字的综合评语
- 列出 3 条最优先的改进方向

## 输出格式
严格按照提供的 JSON Schema 输出，不要遗漏任何字段。
"""


# ---------------------------------------------------------------------------
# 批改主函数
# ---------------------------------------------------------------------------

async def grade_essay(
    question: str,
    user_answer: str,
    essay_type: str | None = None,
) -> EssayGradingResult:
    """批改一篇申论答卷。

    Args:
        question: 申论题目
        user_answer: 考生作答内容
        essay_type: 题型（可选，不传则 AI 自动判断）

    Returns:
        EssayGradingResult 包含总分、各维度评分、逐段批注、改进建议
    """
    from gwy_mcp.llm.client import get_client

    client = get_client()

    # 检索参考范文
    refs = _find_references(question, essay_type or "大作文")

    # 构建 prompt
    ref_text = ""
    for r in refs:
        if "scoring_guide" in r:
            guide = r["scoring_guide"]
            ref_text += "\n## 本题评分标准\n"
            for k, v in guide.items():
                ref_text += f"- {k}: {v}\n"
        else:
            ref_text += f"\n## 参考范文（{r['score']}/{r['max_score']}分）\n{r['content']}\n"

    user_text = f"""## 考生题目
{question}

## 考生作答
{user_answer}

## 题型提示
{essay_type or "请根据题目自动判断题型"}

{ref_text}
"""

    return await client.extract_structured(
        text=user_text,
        schema=EssayGradingResult,
        system_prompt=_GRADING_SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=4096,
    )


# ---------------------------------------------------------------------------
# 范文库查询
# ---------------------------------------------------------------------------

def list_reference_topics() -> list[dict]:
    """列出范文库中所有题目。"""
    return [
        {"id": t["id"], "topic": t["topic"][:50], "type": t["type"]}
        for t in _ESSAY_BANK.get("topics", [])
    ]
