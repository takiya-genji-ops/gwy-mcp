"""岗位匹配引擎 — 基于规则的用户-岗位条件比对。

不依赖 LLM，纯逻辑匹配：
1. 学历匹配（向下兼容，如硕士可报要求本科的岗位）
2. 专业匹配（精确匹配 + 学科门类/专业类模糊匹配）
3. 应届限制
4. 基层经历年限
5. 政治面貌
6. 户籍限制
"""

from __future__ import annotations

import json
from pathlib import Path

from gwy_mcp.models.schemas import MatchResult, Position, UserProfile

# 加载专业分类数据
_CLASSIFICATION_PATH = Path(__file__).resolve().parent.parent / "data" / "major_classification.json"
with open(_CLASSIFICATION_PATH, "r", encoding="utf-8") as f:
    _MAJOR_CLASSIFICATION = json.load(f)

_REVERSE_INDEX: dict[str, dict[str, str]] = _MAJOR_CLASSIFICATION.get("_reverse_index", {})

# 学历层级：数字越大越高
_EDUCATION_RANK: dict[str, int] = {
    "专科": 1,
    "本科": 2,
    "硕士研究生": 3,
    "博士研究生": 4,
}


def _match_education(user_edu: str, required_edu: str) -> bool:
    """学历匹配：用户学历 >= 岗位要求即为通过。

    支持模糊匹配：
    - "本科及以上" → 本科、硕士、博士均可
    - "硕士及以上" → 硕士、博士均可
    """
    user_rank = _EDUCATION_RANK.get(user_edu, 0)
    req_rank = _EDUCATION_RANK.get(required_edu, 0)

    if req_rank == 0:
        # 岗位要求无法识别，宽松处理：仅检查是否包含关键词
        return required_edu in user_edu

    return user_rank >= req_rank


def _is_major_in_category(user_major: str, category: str) -> bool:
    """检查专业是否属于某学科门类或专业类。"""
    info = _REVERSE_INDEX.get(user_major)
    if info is None:
        return False
    return info["category"] == category or info["sub_category"] == category


def _match_major(user_major: str, required_majors: list[str]) -> tuple[bool, str]:
    """专业匹配。

    匹配逻辑：
    1. 精确匹配专业名称
    2. 匹配专业类（如要求"计算机类"，用户专业属于计算机类）
    3. 匹配学科门类（如要求"管理学"，用户专业属于管理学）
    4. 专业不限
    """
    if not required_majors:
        return True, "专业不限"

    matched = []
    for req in required_majors:
        req_clean = req.strip()
        # 精确匹配
        if user_major == req_clean:
            matched.append(req_clean)
        # 专业类匹配
        elif _is_major_in_category(user_major, req_clean):
            matched.append(f"{req_clean}(专业类匹配:{user_major})")
        # 包含匹配（处理"XX相关专业"）
        elif "相关" in req_clean:
            base = req_clean.replace("相关专业", "").replace("相关", "")
            if base and (base in user_major or _is_major_in_category(user_major, base)):
                matched.append(req_clean)

    if matched:
        return True, f"专业匹配: {', '.join(matched)}"
    else:
        return False, f"专业不匹配: 要求{required_majors}, 用户专业为{user_major}"


def _match_political_status(user_status: str | None, required_status: str | None) -> tuple[bool, str]:
    """政治面貌匹配。"""
    if not required_status:
        return True, "政治面貌不限"
    if not user_status:
        # 用户没填政治面貌，保守按不匹配处理
        return False, f"政治面貌不匹配: 要求{required_status}, 用户未填写"

    # 宽松匹配
    user_norm = user_status.strip()
    req_norm = required_status.strip()

    if user_norm == req_norm:
        return True, f"政治面貌匹配: {user_norm}"

    # 中共党员可以报"中共党员或共青团员"的岗位
    if "中共党员" in user_norm and "中共党员" in req_norm:
        return True, f"政治面貌匹配: {user_norm}"
    if "共青团员" in user_norm and "共青团员" in req_norm:
        return True, f"政治面貌匹配: {user_norm}"

    return False, f"政治面貌不匹配: 要求{required_status}, 用户为{user_status}"


def _match_household(user_household: str | None, required_household: str | None) -> tuple[bool, str]:
    """户籍限制匹配。"""
    if not required_household:
        return True, "户籍不限"
    if not user_household:
        return False, f"户籍限制: 要求{required_household}, 用户未填写户籍信息"

    # 提取省份名做宽松匹配
    HH = user_household.strip()
    RH = required_household.strip()

    if HH == RH:
        return True, f"户籍匹配: {HH}"
    if RH in HH or HH in RH:
        return True, f"户籍匹配(模糊): {HH} ↔ {RH}"

    return False, f"户籍限制不满足: 要求{required_household}, 用户户籍为{user_household}"


def match_single_position(user: UserProfile, position: Position) -> MatchResult:
    """对单个岗位执行全条件匹配。"""
    req = position.requirements
    matched = []
    blocked = []

    # 学历
    if _match_education(user.education, req.education):
        matched.append(f"学历: {user.education} ≥ {req.education}")
    else:
        blocked.append(f"学历: 要求{req.education}, 用户为{user.education}")

    # 专业
    major_ok, major_msg = _match_major(user.major, req.majors)
    if major_ok:
        matched.append(major_msg)
    else:
        blocked.append(major_msg)

    # 应届
    if req.is_fresh_required and not user.is_fresh_graduate:
        blocked.append("应届限制: 岗位限应届, 用户为非应届")
    elif req.is_fresh_required and user.is_fresh_graduate:
        matched.append("应届: 符合")

    # 基层经历
    if req.grassroots_years > 0:
        if user.has_grassroots_experience:
            matched.append(f"基层经历: 满足{req.grassroots_years}年要求")
        else:
            blocked.append(f"基层经历: 要求{req.grassroots_years}年, 用户无")

    # 政治面貌
    pol_ok, pol_msg = _match_political_status(user.political_status, req.political_status)
    if pol_ok:
        matched.append(pol_msg)
    else:
        blocked.append(pol_msg)

    # 户籍
    hh_ok, hh_msg = _match_household(user.household_registration, req.household_restriction)
    if hh_ok:
        matched.append(hh_msg)
    else:
        blocked.append(hh_msg)

    # 汇总
    is_match = len(blocked) == 0

    suggestion = ""
    if is_match:
        suggestion = f"✅ 可报考 {position.unit_name} 的 {position.position_name}（招{position.recruitment_count}人）"
    else:
        suggestion = f"❌ 不满足条件: {'; '.join(blocked[:2])}..."

    return MatchResult(
        position=position,
        is_match=is_match,
        matched_conditions=matched,
        blocked_conditions=blocked,
        suggestion=suggestion,
    )


def match_all_positions(user: UserProfile, positions: list[Position]) -> list[MatchResult]:
    """批量匹配所有岗位。返回按 is_match 排序的结果（可报岗位在前）。"""
    results = [match_single_position(user, pos) for pos in positions]
    # 可报岗位在前，然后是不满足的
    results.sort(key=lambda r: (not r.is_match, r.position.unit_name))
    return results
