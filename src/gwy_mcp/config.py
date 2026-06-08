"""配置管理，从环境变量或 .env 文件加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 自动加载项目根目录的 .env
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


class Config:
    """全局配置，所有值从环境变量读取，带默认值。"""

    # LLM
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    model: str = os.getenv("GWY_MCP_MODEL", "claude-sonnet-4-20250514")

    # 数据目录
    data_dir: Path = _project_root / "data"


config = Config()
