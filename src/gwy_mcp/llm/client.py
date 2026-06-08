"""LLM 客户端 — 多 Provider 后端，支持 Anthropic 和 DeepSeek。"""

from __future__ import annotations

from typing import Type, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from gwy_mcp.config import config
from gwy_mcp.llm._prompt import POSITION_EXTRACTION_SYSTEM
from gwy_mcp.models.schemas import ExamAnnouncement

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """统一 LLM 客户端，自动选择 Provider。

    Provider 支持:
    - deepseek: DeepSeek API（OpenAI 兼容，默认）
    - anthropic: Anthropic Claude API
    """

    def __init__(self, provider: str | None = None) -> None:
        self._provider = provider or config.llm_provider
        self._client: AsyncOpenAI | None = None
        self._anthropic_client: object | None = None

    def _get_openai_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url,
            )
        return self._client

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            import anthropic
            self._anthropic_client = anthropic.Anthropic(
                api_key=config.anthropic_api_key,
            )
        return self._anthropic_client

    @property
    def model(self) -> str:
        return config.model

    async def extract_structured(
        self,
        text: str,
        schema: Type[T],
        system_prompt: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> T:
        """从文本中提取结构化数据。

        使用 tool calling（Anthropic tool_use / OpenAI function calling）
        强制 LLM 输出符合 Pydantic schema 的结构化数据。
        """
        if self._provider == "anthropic":
            return await self._extract_anthropic(
                text, schema, system_prompt,
                temperature=temperature, max_tokens=max_tokens,
            )
        return await self._extract_deepseek(
            text, schema, system_prompt,
            temperature=temperature, max_tokens=max_tokens,
        )

    async def _extract_deepseek(
        self,
        text: str,
        schema: Type[T],
        system_prompt: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> T:
        """DeepSeek / OpenAI 兼容的结构化提取。

        使用 json_object 模式 + 内嵌 JSON Schema 于 prompt 中。
        """
        import json

        client = self._get_openai_client()
        raw_schema = schema.model_json_schema()
        flat_schema = _flatten_json_schema(raw_schema)
        schema_text = json.dumps(flat_schema, ensure_ascii=False, indent=2)

        full_system = (
            system_prompt
            + f"{chr(10)}{chr(10)}你必须严格按照以下 JSON Schema 输出，不要添加任何额外字段：{chr(10)}"
            + schema_text
        )

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": full_system},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body={"thinking": {"type": "disabled"}},
        )

        raw = response.choices[0].message.content
        args = json.loads(raw)
        return schema.model_validate(args)

    async def _extract_anthropic(
        self,
        text: str,
        schema: Type[T],
        system_prompt: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> T:
        """Anthropic tool_use 的结构化提取。"""
        client = self._get_anthropic_client()
        json_schema = schema.model_json_schema()
        tool_name = schema.__name__

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
            tools=[{
                "name": tool_name,
                "description": json_schema.get("description", ""),
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

        raise RuntimeError(
            f"LLM 未返回结构化数据 {tool_name}，响应: {response.content}"
        )


# 全局单例
_client: LLMClient | None = None


def _flatten_json_schema(schema: dict) -> dict:
    """将含 $defs/$ref 的 JSON Schema 展平为自包含 schema。

    Pydantic model_json_schema() 默认将嵌套模型放到 $defs，
    但 DeepSeek 的 response_format 对 $ref 支持有限。
    此函数将所有 $ref 内联展开。
    """
    defs = schema.get("$defs", {})

    def resolve(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_name = obj["$ref"].split("/")[-1]
                resolved = defs.get(ref_name, {})
                return resolve(resolved)
            return {k: resolve(v) for k, v in obj.items() if k != "$defs"}
        if isinstance(obj, list):
            return [resolve(item) for item in obj]
        return obj

    result = resolve(schema)
    result.pop("$defs", None)
    return result



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

    Args:
        announcement_text: 招考公告全文（纯文本）
        announcement_url: 公告原文链接（可选）

    Returns:
        包含所有岗位的 ExamAnnouncement 实例
    """
    client = get_client()

    full_text = announcement_text
    if announcement_url:
        full_text = f"公告原文链接: {announcement_url}{chr(10)}{chr(10)}公告正文:{chr(10)}{announcement_text}"

    return await client.extract_structured(
        text=full_text,
        schema=ExamAnnouncement,
        system_prompt=POSITION_EXTRACTION_SYSTEM,
        temperature=0.1,
    )
