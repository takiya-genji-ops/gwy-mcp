"""gwy-mcp MCP Server 入口。

基于 FastMCP 实现，提供以下 Tools:
- match_positions: 根据用户画像筛选可报岗位
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from gwy_mcp.tools.position_match import match_positions

# 初始化 FastMCP 实例
mcp = FastMCP(
    name="gwy-mcp",
    instructions="公务员考试智能助手 — 选岗匹配、申论批改、面试模拟",
)


def register_tools() -> None:
    """注册所有 MCP Tools。"""
    # V1: 选岗匹配
    mcp.tool()(match_positions)

    # 后续工具在此注册:
    # mcp.tool()(interview_simulate)
    # mcp.tool()(essay_grade)


def main() -> None:
    """启动 MCP Server。"""
    register_tools()
    mcp.run()


if __name__ == "__main__":
    main()
