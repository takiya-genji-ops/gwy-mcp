"""申论批改 MCP Tool。"""

from __future__ import annotations

from gwy_mcp.engines.essay_grader import grade_essay, list_reference_topics
from gwy_mcp.models.schemas import EssayGradingResult


async def grade_essay_answer(
    question: str,
    user_answer: str,
    essay_type: str | None = None,
) -> EssayGradingResult:
    """批改一篇申论答卷，返回多维评分和逐段批注。

    Args:
        question: 申论题目原文
        user_answer: 考生的作答内容
        essay_type: 题型（概括题/分析题/对策题/大作文/综合题），不传则自动判断

    Returns:
        EssayGradingResult: 包含总分、六维评分、逐段批注、对比分析、改进建议
    """
    return await grade_essay(
        question=question,
        user_answer=user_answer,
        essay_type=essay_type,
    )


async def list_reference_essays() -> list[dict]:
    """列出当前范文库中所有参考题目。

    Returns:
        [{id, topic, type}, ...]
    """
    return list_reference_topics()
