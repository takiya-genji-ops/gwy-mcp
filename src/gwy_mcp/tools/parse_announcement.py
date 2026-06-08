"""一站式公告解析 Tool。

输入 PDF 路径 / URL / 纯文本，输出结构化岗位列表。
"""

from __future__ import annotations

from gwy_mcp.llm.client import extract_positions_from_text
from gwy_mcp.models.schemas import ExamAnnouncement
from gwy_mcp.tools.input_handler import parse_announcement_input


async def parse_announcement(
    source: str,
    *,
    source_type: str = "text",
) -> ExamAnnouncement:
    """解析招考公告，提取所有岗位信息。

    Args:
        source: 公告内容。可以是纯文本、PDF 文件路径或网址 URL
        source_type: 来源类型 — "text"（纯文本，默认）、"url"（网址）、"pdf"（PDF 文件路径）

    Returns:
        结构化考试公告，包含标题、省份、考试类型和所有岗位列表
    """
    is_url = source_type == "url"
    is_file = source_type == "pdf"

    cleaned_text = await parse_announcement_input(
        source,
        is_url=is_url,
        is_file=is_file,
    )

    return await extract_positions_from_text(
        announcement_text=cleaned_text,
        announcement_url=source if is_url else None,
    )
