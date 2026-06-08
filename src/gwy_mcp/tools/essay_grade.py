"""申论批改 MCP Tool。"""

from __future__ import annotations

from gwy_mcp.engines.essay_grader import (
    grade_essay,
    list_reference_topics,
    list_question_types,
)
from gwy_mcp.models.schemas import EssayGradingResult


async def grade_essay_answer(
    question: str,
    user_answer: str,
    essay_type: str | None = None,
) -> EssayGradingResult:
    """批改一篇申论答卷，按题型自动应用对应评分标准。

    支持题型：概括题、分析题、对策题、应用文、大作文、综合题

    Args:
        question: 申论题目原文
        user_answer: 考生的作答内容
        essay_type: 题型（不传则默认大作文）

    Returns:
        EssayGradingResult: 含总分、各维度评分、逐段/逐条批注、对比分析、改进建议
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


async def list_supported_question_types() -> list[dict]:
    """列出所有支持的申论题型及评分标准概要。

    Returns:
        [{type, total_score, word_count, dimensions}, ...]
    """
    return list_question_types()
