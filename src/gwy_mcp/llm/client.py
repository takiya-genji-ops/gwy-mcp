\
"""LLM 客户端 — Anthropic API 封装，支持结构化输出提取岗位信息。"""

from __future__ import annotations

from typing import Type, TypeVar

import anthropic
from pydantic import BaseModel

from gwy_mcp.config import config
from gwy_mcp.llm._prompt import POSITION_EXTRACTION_SYSTEM
from gwy_mcp.models.schemas import ExamAnnouncement

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """封装 Anthropic Messages API，提供结构化输出能力。"""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._client = anthropic.Anthropic(api_key=api_key or config.anthropic_api_key)
        self._model = model or config.model

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: str = "",
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """发送对话请求，返回文本响应。"""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
        )
        return response.content[0].text

    async def extract_structured(
        self,
        text: str,
        schema: Type[T],
        system_prompt: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> T:
        """从文本中提取结构化数据（使用 Anthropic tool_use）。"""
        json_schema = schema.model_json_schema()
        tool_name = schema.__name__

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
            tools=[{
                "name": tool_name,
                "description": json_schema.get("description", f"Extract {tool_name}"),
                "input_schema": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }],
            tool_choice={"type": "tool", "name": tool_name},
            temperature=temperature,
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return schema.model_validate(block.input)

        raise RuntimeError(f"LLM 未返回结构化数据 {tool_name}，响应: {response.content}")


# 全局单例
_client: LLMClient | None = None


def get_client() -> LLMClient:
    """获取 LLMClient 单例。"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


async def extract_positions_from_text(
    announcement_text: str,
    announcement_url: str | None = None,
) -> ExamAnnouncement:
    """从公告文本中提取结构化岗位信息。

    使用 Claude API + structured output 解析公告文本。

    Args:
        announcement_text: 招考公告全文（纯文本）
        announcement_url: 公告原文链接（可选）

    Returns:
        包含所有岗位的 ExamAnnouncement 实例
    """
    client = get_client()

    full_text = announcement_text
    if announcement_url:
        full_text = f"公告原文链接: {announcement_url}\n\n公告正文:\n{announcement_text}"

    return await client.extract_structured(
        text=full_text,
        schema=ExamAnnouncement,
        system_prompt=POSITION_EXTRACTION_SYSTEM,
        temperature=0.1,
    )
