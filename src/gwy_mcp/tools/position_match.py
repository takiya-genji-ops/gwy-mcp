"""选岗匹配 Tool。

接收用户个人画像和公告文本，调用 LLM 结构化提取岗位信息，
然后逐岗位匹配用户条件，返回可报岗位列表和匹配分析。
"""

from __future__ import annotations

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
        匹配结果列表，包含每个岗位是否符合条件及详细分析
    """
    # --- V1 骨架实现 ---
    # 当前返回一个示意结果，后续接入 LLM 做结构化提取和条件匹配

    from gwy_mcp.models.schemas import Position, PositionRequirements

    results: list[MatchResult] = []

    # TODO: Step 1 — 调用 LLM 从 announcement_text 提取岗位列表
    # positions = await _extract_positions_via_llm(announcement_text)

    # TODO: Step 2 — 逐岗位匹配用户条件
    # for pos in positions:
    #     result = _match_single_position(user_profile, pos)
    #     results.append(result)

    # TODO: Step 3 — 按匹配度排序，附加进面分参考

    # 示意数据（开发阶段占位）
    sample_position = Position(
        unit_name="示例用人单位",
        position_name="示例岗位",
        position_code="000001",
        recruitment_count=2,
        requirements=PositionRequirements(
            education=user_profile.education,
            majors=[user_profile.major],
            is_fresh_required=user_profile.is_fresh_graduate,
        ),
        work_location="示例省市",
        source_url=announcement_url,
    )

    results.append(
        MatchResult(
            position=sample_position,
            is_match=True,
            matched_conditions=[
                f"学历匹配: {user_profile.education}",
                f"专业匹配: {user_profile.major}",
            ],
            blocked_conditions=[],
            suggestion="请核实公告原文确认所有条件。该功能开发中，当前为骨架占位结果。",
        )
    )

    return results
