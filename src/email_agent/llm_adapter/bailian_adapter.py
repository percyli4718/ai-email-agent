"""
阿里百炼 LLM Adapter

模块作用:
    实现阿里百炼 (阿里云) 的适配器。
    支持接入通义千问 (Qwen) 等模型。
"""
import json
import httpx
from typing import Any

from email_agent.llm_adapter.base import LLMAdapter, LLMResponse
from email_agent.config import Settings


class BailianAdapter(LLMAdapter):
    """
    阿里百炼 API 适配器

    作用:
        封装阿里云百炼平台的 API，提供统一的 chat 接口。
        支持通义千问 (Qwen) 系列模型。
    """

    def __init__(self, settings: Settings):
        """
        初始化阿里百炼适配器

        参数:
            settings: Settings 类型，应用配置对象
        """
        super().__init__(settings)
        # 百炼 API Key
        self.api_key = getattr(settings, 'bailian_api_key', '')
        # 百炼 API 端点
        self.base_url = getattr(settings, 'bailian_base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        # 默认模型
        self.default_model = getattr(settings, 'bailian_model', 'qwen-max')

    async def chat(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024
    ) -> LLMResponse:
        """
        发送对话请求到阿里百炼 API

        参数:
            user_prompt: str 类型，用户消息
            system_prompt: str 类型，系统提示
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: 响应对象
        """
        # 构建请求体
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False
        }

        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()

        # 解析响应
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=self.default_model,
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0)
            },
            raw_response=data
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
