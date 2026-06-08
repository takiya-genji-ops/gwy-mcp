"""核心数据模型定义。"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExamType(str, Enum):
    """考试类型。"""

    NATIONAL = "国考"
    PROVINCIAL = "省考"
    PUBLIC_INSTITUTION = "事业编"
    SELECTED_GRADUATE = "选调生"
    OTHER = "其他"


class UserProfile(BaseModel):
    """用户个人画像，用于岗位匹配。"""

    education: str = Field(description="学历，如 本科/硕士研究生/博士研究生")
    major: str = Field(description="专业全称，如 计算机科学与技术")
    is_fresh_graduate: bool = Field(default=False, description="是否为应届毕业生")
    graduation_year: Optional[int] = Field(default=None, description="毕业年份")
    has_grassroots_experience: bool = Field(
        default=False, description="是否有基层工作经历"
    )
    political_status: Optional[str] = Field(
        default=None, description="政治面貌: 中共党员/共青团员/群众"
    )
    household_registration: Optional[str] = Field(
        default=None, description="户籍所在地，如 江苏省南京市"
    )
    target_provinces: list[str] = Field(
        default_factory=list, description="目标省份列表，如 ['江苏', '浙江']"
    )
    target_exam_types: list[ExamType] = Field(
        default_factory=list, description="目标考试类型"
    )
    other_notes: Optional[str] = Field(
        default=None, description="其他需要说明的条件"
    )


class PositionRequirements(BaseModel):
    """岗位招录条件。"""

    education: str = Field(description="学历要求")
    majors: list[str] = Field(default_factory=list, description="专业要求列表")
    is_fresh_required: bool = Field(default=False, description="是否限应届")
    grassroots_years: int = Field(default=0, description="基层工作经历年限要求")
    political_status: Optional[str] = Field(default=None, description="政治面貌要求")
    household_restriction: Optional[str] = Field(
        default=None, description="户籍限制说明"
    )
    age_limit: Optional[str] = Field(default=None, description="年龄限制")
    other_requirements: list[str] = Field(
        default_factory=list, description="其他条件"
    )


class Position(BaseModel):
    """单个岗位信息。"""

    unit_name: str = Field(description="用人单位名称")
    position_name: str = Field(description="岗位名称")
    position_code: Optional[str] = Field(default=None, description="岗位代码")
    recruitment_count: int = Field(default=1, description="招录人数")
    requirements: PositionRequirements = Field(description="招录条件")
    work_location: Optional[str] = Field(default=None, description="工作地点")
    exam_subjects: list[str] = Field(
        default_factory=list, description="考试科目"
    )
    salary_level: Optional[str] = Field(default=None, description="待遇级别")
    source_url: Optional[str] = Field(default=None, description="公告原文链接")


class ExamAnnouncement(BaseModel):
    """考试公告。"""

    title: str = Field(description="公告标题")
    province: str = Field(description="省份")
    exam_type: ExamType = Field(description="考试类型")
    announce_url: Optional[str] = Field(default=None, description="公告链接")
    positions: list[Position] = Field(default_factory=list, description="岗位列表")
    raw_text: Optional[str] = Field(default=None, description="公告原始文本")


class MatchResult(BaseModel):
    """单个岗位匹配结果。"""

    position: Position = Field(description="岗位信息")
    is_match: bool = Field(description="是否符合条件")
    matched_conditions: list[str] = Field(
        default_factory=list, description="匹配的条件"
    )
    blocked_conditions: list[str] = Field(
        default_factory=list, description="不满足的条件"
    )
    suggestion: Optional[str] = Field(default=None, description="报考建议")
