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

    # LLM Provider: "deepseek" | "anthropic"
    llm_provider: str = os.getenv("GWY_MCP_PROVIDER", "deepseek")

    # DeepSeek (默认)
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    # Anthropic (备选)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # 统一模型名（兼容旧配置）
    @property
    def model(self) -> str:
        if self.llm_provider == "anthropic":
            return self.anthropic_model
        return self.deepseek_model

    # 数据目录
    data_dir: Path = _project_root / "data"


config = Config()
