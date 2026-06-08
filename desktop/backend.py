"""gwy-mcp 桌面应用后端 — FastAPI 薄层封装。

将 MCP Tool 暴露为 REST API，供 Tauri 前端调用。
启动: python desktop/backend.py
端口: 8711
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 将项目源码加入 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

app = FastAPI(
    title="gwy-mcp Desktop API",
    description="公务员考试智能助手 — 选岗匹配 + 申论批改",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 请求模型
# ---------------------------------------------------------------------------

class AnnouncementInput(BaseModel):
    source: str = Field(description="公告内容/PDF路径/URL")
    source_type: str = Field(default="text", description="text / pdf / url")


class MatchInput(BaseModel):
    education: str = Field(description="学历")
    major: str = Field(description="专业")
    is_fresh_graduate: bool = False
    graduation_year: int | None = None
    has_grassroots_experience: bool = False
    political_status: str | None = None
    household_registration: str | None = None
    target_provinces: list[str] = []
    announcement_text: str = Field(description="公告文本")
    announcement_url: str | None = None


class GradeInput(BaseModel):
    question: str = Field(description="申论题目")
    user_answer: str = Field(description="考生作答")
    essay_type: str | None = Field(default=None, description="题型")


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "gwy-mcp"}


@app.post("/api/parse-announcement")
async def parse_announcement(input: AnnouncementInput):
    """解析公告（PDF/URL/文本）→ 结构化岗位列表"""
    from gwy_mcp.tools.input_handler import parse_announcement_input
    from gwy_mcp.llm.client import extract_positions_from_text

    cleaned = await parse_announcement_input(
        input.source,
        is_url=(input.source_type == "url"),
        is_file=(input.source_type == "pdf"),
    )
    result = await extract_positions_from_text(cleaned, input.source if input.source_type == "url" else None)
    return result.model_dump()


@app.post("/api/match-positions")
async def match_positions(input: MatchInput):
    """用户画像 + 公告 → 匹配结果"""
    from gwy_mcp.models.schemas import UserProfile
    from gwy_mcp.tools.position_match import match_positions as _match

    profile = UserProfile(
        education=input.education,
        major=input.major,
        is_fresh_graduate=input.is_fresh_graduate,
        graduation_year=input.graduation_year,
        has_grassroots_experience=input.has_grassroots_experience,
        political_status=input.political_status,
        household_registration=input.household_registration,
        target_provinces=input.target_provinces,
    )
    results = await _match(profile, input.announcement_text, input.announcement_url)
    return [r.model_dump() for r in results]


@app.post("/api/grade-essay")
async def grade_essay(input: GradeInput):
    """批改申论答卷"""
    from gwy_mcp.engines.essay_grader import grade_essay as _grade
    result = await _grade(input.question, input.user_answer, input.essay_type)
    return result.model_dump()


@app.get("/api/reference-essays")
async def reference_essays():
    """范文库列表"""
    from gwy_mcp.engines.essay_grader import list_reference_topics
    return list_reference_topics()


@app.get("/api/question-types")
async def question_types():
    """支持题型列表"""
    from gwy_mcp.engines.essay_grader import list_question_types
    return list_question_types()


@app.post("/api/save-profile")
async def save_profile(
    education: str, major: str,
    is_fresh_graduate: bool = False,
    graduation_year: int | None = None,
    has_grassroots_experience: bool = False,
    political_status: str | None = None,
    household_registration: str | None = None,
):
    """保存用户画像"""
    from gwy_mcp.tools.user_profile import save_user_profile as _save
    profile = await _save(
        education=education, major=major,
        is_fresh_graduate=is_fresh_graduate,
        graduation_year=graduation_year,
        has_grassroots_experience=has_grassroots_experience,
        political_status=political_status,
        household_registration=household_registration,
    )
    return profile.model_dump()


@app.get("/api/load-profile")
async def load_profile():
    """加载用户画像"""
    from gwy_mcp.tools.user_profile import load_user_profile as _load
    profile = await _load()
    if profile is None:
        return None
    return profile.model_dump()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8711, log_level="info")
