"""选岗匹配 Tool。

接收用户个人画像和公告文本，调用 LLM 结构化提取岗位信息，
然后逐岗位匹配用户条件，返回可报岗位列表和匹配分析。
"""

from __future__ import annotations

from gwy_mcp.engines.position_matcher import match_all_positions
from gwy_mcp.llm.client import extract_positions_from_text
from gwy_mcp.models.schemas import ExamAnnouncement, MatchResult, UserProfile


async def match_positions(
    user_profile: UserProfile,
    announcement_text: str,
    announcement_url: str | None = None,
) -> list[MatchResult]:
    """根据用户画像和招考公告筛选可报岗位。

    Args:
        user_profile: 用户个人画像（学历、专业、应届等）
        announcement_text: 招考公告全文或 PDF 提取文本
        announcement_url: 公告原始链接（可选，用于溯源）

    Returns:
        匹配结果列表，先可报岗位，后不可报岗位，每个附详细分析。
        如果公告未提取到任何岗位信息，返回空列表。

    流程：
    1. LLM 结构化提取岗位列表
    2. 规则引擎逐岗位匹配条件
    """
    # Step 1: LLM 结构化提取岗位
    announcement: ExamAnnouncement = await extract_positions_from_text(
        announcement_text=announcement_text,
        announcement_url=announcement_url or None,
    )

    if not announcement.positions:
        return []

    # Step 2: 规则引擎匹配
    return match_all_positions(user_profile, announcement.positions)
