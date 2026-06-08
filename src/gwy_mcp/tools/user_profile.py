"""用户画像管理 MCP Tool。

提供用户画像的本地持久化存储和加载功能。
数据存储在 ~/.gwy-mcp/user_profile.json。
"""

from __future__ import annotations

import json
from pathlib import Path

from gwy_mcp.models.schemas import UserProfile


def _profile_path() -> Path:
    """用户画像文件路径。"""
    base = Path.home() / ".gwy-mcp"
    base.mkdir(parents=True, exist_ok=True)
    return base / "user_profile.json"


async def save_user_profile(
    education: str,
    major: str,
    is_fresh_graduate: bool = False,
    graduation_year: int | None = None,
    has_grassroots_experience: bool = False,
    political_status: str | None = None,
    household_registration: str | None = None,
    target_provinces: list[str] | None = None,
    other_notes: str | None = None,
) -> UserProfile:
    """保存用户个人画像到本地。

    Args:
        education: 学历，如 "本科" / "硕士研究生" / "博士研究生"
        major: 专业全称，如 "计算机科学与技术"
        is_fresh_graduate: 是否为应届毕业生
        graduation_year: 毕业年份
        has_grassroots_experience: 是否有基层工作经历
        political_status: 政治面貌: "中共党员" / "共青团员" / "群众"
        household_registration: 户籍所在地，如 "江苏省南京市"
        target_provinces: 目标省份列表
        other_notes: 其他备注

    Returns:
        保存后的完整用户画像
    """
    profile = UserProfile(
        education=education,
        major=major,
        is_fresh_graduate=is_fresh_graduate,
        graduation_year=graduation_year,
        has_grassroots_experience=has_grassroots_experience,
        political_status=political_status,
        household_registration=household_registration,
        target_provinces=target_provinces or [],
        other_notes=other_notes,
    )

    filepath = _profile_path()
    filepath.write_text(profile.model_dump_json(indent=2, ensure_ascii=False), encoding="utf-8")
    return profile


async def load_user_profile() -> UserProfile | None:
    """加载已保存的用户个人画像。

    Returns:
        用户画像实例，如果未保存过则返回 None
    """
    filepath = _profile_path()
    if not filepath.exists():
        return None
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return UserProfile.model_validate(data)
    except (json.JSONDecodeError, KeyError):
        return None
