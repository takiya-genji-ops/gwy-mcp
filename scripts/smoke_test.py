#!/usr/bin/env python3
"""gwy-mcp 冒烟测试 — 验证所有核心功能。

用法:
  1. 在项目根目录创建 .env 文件，填入 ANTHROPIC_API_KEY
  2. python scripts/smoke_test.py

测试内容:
  - 用户画像保存/加载
  - 岗位规则匹配引擎
  - LLM 公告解析（需要 API key）
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gwy_mcp.models.schemas import UserProfile, Position, PositionRequirements
from gwy_mcp.engines.position_matcher import match_all_positions
from gwy_mcp.tools.user_profile import save_user_profile, load_user_profile
from gwy_mcp.config import config


# 示例公告文本（模拟江苏省考岗位表）
SAMPLE_ANNOUNCEMENT = """
江苏省2026年度考试录用公务员公告

一、招录计划
2026年全省各级机关计划招录公务员9504名。

二、岗位表
| 单位名称 | 职位代码 | 招录人数 | 专业要求 | 学历要求 | 其他条件 |
|----------|---------|---------|---------|---------|---------|
| 省大数据管理中心 | 010010 | 2 | 计算机类 | 本科及以上 | 不限 |
| 南京市发改委 | 010020 | 1 | 经济学、金融学 | 硕士研究生 | 中共党员 |
| 苏州市审计局 | 010030 | 1 | 审计学、会计学、财务管理 | 本科 | 中共党员，2年以上基层工作经历 |
| 盐城市公安局 | 010040 | 3 | 计算机科学与技术、软件工程、网络工程 | 本科 | 限2026年应届毕业生，男性 |
"""


async def test_user_profile():
    """测试 1: 用户画像保存/加载"""
    print("=" * 50)
    print("Test 1: 用户画像持久化")
    print("=" * 50)

    profile = await save_user_profile(
        education="本科",
        major="计算机科学与技术",
        is_fresh_graduate=False,
        political_status="群众",
        household_registration="江苏省南京市",
    )
    print(f"  保存: {profile.education} / {profile.major} / {profile.household_registration}")

    loaded = await load_user_profile()
    assert loaded is not None
    assert loaded.major == "计算机科学与技术"
    print(f"  加载: {loaded.education} / {loaded.major}")
    print("  PASS")
    print()
    return loaded


async def test_matcher(profile: UserProfile):
    """测试 2: 岗位匹配引擎"""
    print("=" * 50)
    print("Test 2: 岗位规则匹配引擎")
    print("=" * 50)

    positions = [
        Position(
            unit_name="省大数据管理中心",
            position_name="信息技术岗",
            recruitment_count=2,
            requirements=PositionRequirements(
                education="本科",
                majors=["计算机类"],
            ),
        ),
        Position(
            unit_name="苏州市审计局",
            position_name="审计岗",
            recruitment_count=1,
            requirements=PositionRequirements(
                education="本科",
                majors=["审计学", "会计学", "财务管理"],
                is_fresh_required=True,
                political_status="中共党员",
                grassroots_years=2,
            ),
        ),
        Position(
            unit_name="盐城市公安局",
            position_name="网安技术",
            recruitment_count=3,
            requirements=PositionRequirements(
                education="本科",
                majors=["计算机科学与技术", "软件工程", "网络工程"],
            ),
        ),
    ]

    results = match_all_positions(profile, positions)

    for r in results:
        status = "可报" if r.is_match else "不可报"
        print(f"  [{status}] {r.position.unit_name} - {r.position.position_name}")
        if not r.is_match:
            for b in r.blocked_conditions:
                print(f"         {b}")

    matchable = sum(1 for r in results if r.is_match)
    print(f"  结果: {matchable}/{len(results)} 个岗位可报")
    assert matchable >= 2, f"Expected at least 2 matchable, got {matchable}"
    print("  PASS")
    print()


async def test_llm_extraction():
    """测试 3: LLM 公告解析"""
    print("=" * 50)
    print("Test 3: LLM 公告解析")
    print("=" * 50)

    if not config.anthropic_api_key:
        print("  SKIP - 未配置 ANTHROPIC_API_KEY")
        print("  在 .env 文件中设置 ANTHROPIC_API_KEY 后重试")
        print()
        return

    from gwy_mcp.llm.client import extract_positions_from_text

    print("  发送解析请求...")
    announcement = await extract_positions_from_text(SAMPLE_ANNOUNCEMENT)

    print(f"  公告标题: {announcement.title}")
    print(f"  考试类型: {announcement.exam_type.value}")
    print(f"  省份: {announcement.province}")
    print(f"  提取岗位数: {len(announcement.positions)}")

    for pos in announcement.positions:
        print(f"    - {pos.unit_name} | {pos.position_name} | {pos.requirements.education} | {pos.requirements.majors}")

    print("  PASS")
    print()
    return announcement


async def test_full_pipeline():
    """测试 4: 完整选岗流程（LLM 提取 + 匹配）"""
    print("=" * 50)
    print("Test 4: 完整选岗流程")
    print("=" * 50)

    if not config.anthropic_api_key:
        print("  SKIP - 未配置 ANTHROPIC_API_KEY")
        print()
        return

    from gwy_mcp.tools.position_match import match_positions

    profile = await load_user_profile()
    if profile is None:
        profile = UserProfile(
            education="本科",
            major="计算机科学与技术",
            is_fresh_graduate=False,
            political_status="群众",
        )

    print("  执行完整选岗流程...")
    results = await match_positions(profile, SAMPLE_ANNOUNCEMENT)

    if not results:
        print("  LLM 未提取到岗位信息，请检查 API key 或公告文本")
        return

    for r in results:
        status = "可报" if r.is_match else "不可报"
        print(f"  [{status}] {r.position.unit_name}")

    matchable = sum(1 for r in results if r.is_match)
    print(f"  结果: {matchable}/{len(results)} 个岗位可报")
    print("  PASS")


async def main():
    profile = await test_user_profile()
    await test_matcher(profile)
    await test_llm_extraction()
    await test_full_pipeline()

    print("=" * 50)
    print("冒烟测试完成!")
    print(f"  API key 已配置: {bool(config.anthropic_api_key)}")
    if not config.anthropic_api_key:
        print("  [提示] 在 .env 中设置 ANTHROPIC_API_KEY 后重新运行以测试 LLM 功能")


if __name__ == "__main__":
    asyncio.run(main())
