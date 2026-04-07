"""
Anthropic LLM Adapter

模块作用:
    实现 Anthropic Claude API 的适配器。
    支持通过代理配置访问 Anthropic API。
"""
import httpx
import anthropic
from typing import Any

from email_agent.llm_adapter.base import LLMAdapter, LLMResponse
from email_agent.config import Settings


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic Claude API 适配器

    作用:
        封装 Anthropic SDK，提供统一的 chat 接口。
        支持禁用代理以避免 socks 代理协议不兼容问题。
    """

    def __init__(self, settings: Settings):
        """
        初始化 Anthropic 适配器

        参数:
            settings: Settings 类型，应用配置对象
        """
        super().__init__(settings)
        self._client = None

    @property
    def client(self) -> anthropic.AsyncClient:
        """
        懒加载 Anthropic 客户端

        使用 trust_env=False 禁用环境变量中的代理配置，
        让 v2rayn 规则模式自动处理路由。
        """
        if self._client is None:
            transport = httpx.AsyncHTTPTransport(trust_env=False)
            http_client = httpx.AsyncClient(transport=transport)
            self._client = anthropic.AsyncClient(
                api_key=self.settings.anthropic_api_key,
                http_client=http_client
            )
        return self._client

    async def chat(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024
    ) -> LLMResponse:
        """
        发送对话请求到 Anthropic API

        参数:
            user_prompt: str 类型，用户消息
            system_prompt: str 类型，系统提示
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: 响应对象
        """
        response = await self.client.messages.create(
            model="claude-sonnet-3-7-20250219",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return LLMResponse(
            content=response.content[0].text,
            model="claude-sonnet-3-7-20250219",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            raw_response=response
        )

    async def chat_with_json(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024
    ) -> LLMResponse:
        """
        发送对话请求并要求返回 JSON 格式

        参数:
            user_prompt: str 类型，用户消息
            system_prompt: str 类型，系统提示
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: 响应对象，content 为 JSON 字符串
        """
        json_system_prompt = f"{system_prompt}\n\n请只返回 JSON 格式响应，不要其他内容。"
        return await self.chat(user_prompt, json_system_prompt, max_tokens)
