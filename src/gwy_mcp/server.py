"""gwy-mcp MCP Server 入口。

基于 FastMCP 实现，提供以下 Tools:
- extract_positions: 从公告文本提取结构化岗位信息
- match_positions: 根据用户画像筛选可报岗位
- save_user_profile: 保存用户个人画像
- load_user_profile: 加载用户个人画像
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from gwy_mcp.tools.position_match import match_positions
from gwy_mcp.tools.user_profile import save_user_profile, load_user_profile
from gwy_mcp.llm.client import extract_positions_from_text

# 初始化 FastMCP 实例
mcp = FastMCP(
    name="gwy-mcp",
    instructions="公务员考试智能助手 — 选岗匹配、申论批改、面试模拟",
)


def register_tools() -> None:
    """注册所有 MCP Tools。"""
    # V1 Phase 2: 公告解析 + 选岗匹配 + 用户画像
    mcp.tool()(extract_positions_from_text)
    mcp.tool()(match_positions)
    mcp.tool()(save_user_profile)
    mcp.tool()(load_user_profile)

    # 后续工具在此注册:
    # mcp.tool()(interview_simulate)
    # mcp.tool()(essay_grade)


def main() -> None:
    """启动 MCP Server。"""
    register_tools()
    mcp.run()


if __name__ == "__main__":
    main()
