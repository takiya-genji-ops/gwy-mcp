"""公告输入处理 — PDF 解析、URL 抓取、文本预处理。

将用户输入的公告（PDF 文件路径、网页 URL 或纯文本）统一转为
清洗后的纯文本，供 LLM 结构化提取使用。
"""

from __future__ import annotations

import re
from pathlib import Path

import httpx


# ---------------------------------------------------------------------------
# PDF 解析
# ---------------------------------------------------------------------------

async def extract_pdf_text(file_path: str | Path) -> str:
    """从 PDF 文件中提取文本内容。

    Args:
        file_path: PDF 文件路径

    Returns:
        提取的纯文本（页间用换行分隔）

    Raises:
        ImportError: pdfplumber 未安装
        FileNotFoundError: 文件不存在
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "PDF 解析需要 pdfplumber 库，请运行: pip install pdfplumber"
        )

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.suffix.lower() not in (".pdf",):
        raise ValueError(f"不支持的文件格式: {path.suffix}，仅支持 .pdf")

    pages_text: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    return chr(10).join(pages_text)


# ---------------------------------------------------------------------------
# URL 抓取
# ---------------------------------------------------------------------------

async def fetch_url_text(url: str, timeout: float = 30.0) -> str:
    """从网页 URL 抓取文本内容。

    优先从 <article>, <main>, .content 等常见内容容器提取文本，
    如果找不到则返回 <body> 的纯文本。

    Args:
        url: 网页地址
        timeout: 请求超时秒数

    Returns:
        格式化的文本: "标题: xxx\n来源: url\n正文:\n..."
    """
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    content_selectors = ["article", "main", '[class*="content"]', '[class*="article"]']
    body = ""
    for selector in content_selectors:
        container = soup.select_one(selector)
        if container:
            body = container.get_text(separator=chr(10), strip=True)
            break

    if not body:
        body = soup.body.get_text(separator=chr(10), strip=True) if soup.body else ""

    sep = chr(10)
    return f"标题: {title}{sep}来源: {url}{sep}正文:{sep}{body}"


# ---------------------------------------------------------------------------
# 文本清洗（预处理）
# ---------------------------------------------------------------------------

def clean_announcement_text(text: str) -> str:
    """清洗公告文本，移除无关内容。

    处理：
    - 合并多余空白行（保留段落结构）
    - 移除常见页眉页脚噪声
    - 保留表格数据行（以 | 或空格分隔的岗位行）
    """
    lines = text.split(chr(10))
    cleaned: list[str] = []
    blank_count = 0

    for line in lines:
        stripped = line.strip()

        if not stripped:
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
            continue
        blank_count = 0

        if re.match(r"^[-=*_#~]{5,}$", stripped):
            continue

        cleaned.append(stripped)

    return chr(10).join(cleaned)


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------

async def parse_announcement_input(
    source: str,
    *,
    is_url: bool = False,
    is_file: bool = False,
) -> str:
    """统一入口：将用户输入转为清洗后的公告纯文本。

    Args:
        source: 公告来源（纯文本 / URL / 文件路径）
        is_url: 是否将 source 作为 URL 抓取
        is_file: 是否将 source 作为文件路径读取

    Returns:
        清洗后的公告纯文本
    """
    raw_text: str

    if is_url:
        raw_text = await fetch_url_text(source)
    elif is_file:
        raw_text = await extract_pdf_text(source)
    else:
        raw_text = source

    return clean_announcement_text(raw_text)
