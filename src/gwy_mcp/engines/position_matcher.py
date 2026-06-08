"""岗位匹配引擎 — 基于规则的用户-岗位条件比对。

不依赖 LLM，纯逻辑匹配：
1. 学历匹配（向下兼容）
2. 专业匹配（精确 + 学科门类/专业类 + 补丁映射 + 别名）
3. 应届限制
4. 基层经历年限
5. 政治面貌
6. 户籍限制
"""

from __future__ import annotations

import json
from pathlib import Path

from gwy_mcp.models.schemas import MatchResult, Position, UserProfile

# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

with open(_DATA_DIR / "major_classification.json", "r", encoding="utf-8") as _f:
    _MAJOR_CLASSIFICATION = json.load(_f)
_REVERSE_INDEX: dict[str, dict[str, str]] = _MAJOR_CLASSIFICATION.get("_reverse_index", {})

with open(_DATA_DIR / "major_patches.json", "r", encoding="utf-8") as _f:
    _MAJOR_PATCHES = json.load(_f)
_VOC_TO_UG: dict[str, str] = _MAJOR_PATCHES.get("专科→本科专业类", {})
_GRAD_TO_UG: dict[str, str] = _MAJOR_PATCHES.get("研究生→本科专业类", {})
_ALIASES: dict[str, str] = _MAJOR_PATCHES.get("别名映射", {})

# 学历层级
_EDUCATION_RANK: dict[str, int] = {
    "专科": 1, "本科": 2, "硕士研究生": 3, "博士研究生": 4,
}


def _resolve_alias(major: str) -> str:
    return _ALIASES.get(major, major)


def _get_patch_category(major: str) -> str | None:
    return _VOC_TO_UG.get(major) or _GRAD_TO_UG.get(major)


# ---------------------------------------------------------------------------
# 匹配函数
# ---------------------------------------------------------------------------

def _match_education(user_edu: str, required_edu: str) -> bool:
    user_rank = _EDUCATION_RANK.get(user_edu, 0)
    req_rank = _EDUCATION_RANK.get(required_edu, 0)
    if req_rank == 0:
        return required_edu in user_edu
    return user_rank >= req_rank


def _is_major_in_category(user_major: str, category: str) -> bool:
    # 1. 主表
    info = _REVERSE_INDEX.get(user_major)
    if info and (info["category"] == category or info["sub_category"] == category):
        return True
    # 2. 补丁
    pc = _get_patch_category(user_major)
    if pc and pc == category:
        return True
    # 3. 别名
    resolved = _resolve_alias(user_major)
    if resolved != user_major:
        info2 = _REVERSE_INDEX.get(resolved)
        if info2 and (info2["category"] == category or info2["sub_category"] == category):
            return True
        pc2 = _get_patch_category(resolved)
        if pc2 and pc2 == category:
            return True
    return False


def _match_major(user_major: str, required_majors: list[str]) -> tuple[bool, str]:
    if not required_majors:
        return True, "专业不限"
    matched = []
    for req in required_majors:
        req_clean = req.strip()
        if user_major == req_clean:
            matched.append(req_clean)
        elif _is_major_in_category(user_major, req_clean):
            matched.append(f"{req_clean}(类别/补丁匹配)")
        elif "相关" in req_clean:
            base = req_clean.replace("相关专业", "").replace("相关", "")
            if base and (base in user_major or _is_major_in_category(user_major, base)):
                matched.append(req_clean)
    if matched:
        return True, f"专业匹配: {'，'.join(matched)}"
    return False, f"专业不匹配: 要求{required_majors}, 用户专业为{user_major}"
    return False, f"专业不匹配: 要求{required_majors}, 用户专业为{user_major}"


def _match_political_status(user_status: str | None, required_status: str | None) -> tuple[bool, str]:
    if not required_status:
        return True, "政治面貌不限"
    if not user_status:
        return False, f"政治面貌不匹配: 要求{required_status}, 用户未填写"
    if required_status in user_status or user_status in required_status:
        return True, f"政治面貌匹配: {user_status}"
    return False, f"政治面貌不匹配: 要求{required_status}, 用户为{user_status}"


def _match_household(user_hh: str | None, required_hh: str | None) -> tuple[bool, str]:
    if not required_hh:
        return True, "户籍不限"
    if not user_hh:
        return False, f"户籍限制: 要求{required_hh}, 用户未填写"
    if required_hh in user_hh or user_hh in required_hh:
        return True, f"户籍匹配: {user_hh}"
    return False, f"户籍限制: 要求{required_hh}, 用户为{user_hh}"


# ---------------------------------------------------------------------------
# 岗位匹配
# ---------------------------------------------------------------------------

def match_single_position(user: UserProfile, position: Position) -> MatchResult:
    matched = []
    blocked = []
    req = position.requirements

    if _match_education(user.education, req.education):
        matched.append(f"学历: {user.education}")
    else:
        blocked.append(f"学历: 要求{req.education}, 用户为{user.education}")

    m_ok, m_msg = _match_major(user.major, req.majors)
    (matched if m_ok else blocked).append(m_msg)

    if req.is_fresh_required and not user.is_fresh_graduate:
        blocked.append("应届限制: 岗位限应届")
    elif req.is_fresh_required:
        matched.append("应届: 符合")

    if req.grassroots_years > 0:
        if user.has_grassroots_experience:
            matched.append(f"基层经历: {req.grassroots_years}年")
        else:
            blocked.append(f"基层经历: 要求{req.grassroots_years}年")

    p_ok, p_msg = _match_political_status(user.political_status, req.political_status)
    (matched if p_ok else blocked).append(p_msg)

    h_ok, h_msg = _match_household(user.household_registration, req.household_restriction)
    (matched if h_ok else blocked).append(h_msg)

    is_match = len(blocked) == 0
    bstr = "; ".join(blocked[:2])
    suggestion = (
        f"可报考 {position.unit_name}（招{position.recruitment_count}人）"
        if is_match else
        f"不满足: {bstr}"
    )

    return MatchResult(
        position=position, is_match=is_match,
        matched_conditions=matched, blocked_conditions=blocked,
        suggestion=suggestion,
    )


def match_all_positions(user: UserProfile, positions: list[Position]) -> list[MatchResult]:
    results = [match_single_position(user, pos) for pos in positions]
    results.sort(key=lambda r: (not r.is_match, r.position.unit_name))
    return results
