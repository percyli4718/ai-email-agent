"""
Mock LLM Adapter

模块作用:
    实现 Mock 模式的 LLM 适配器。
    用于测试和演示，无需调用真实的 API。
"""
import json
from typing import Any

from email_agent.llm_adapter.base import LLMAdapter, LLMResponse
from email_agent.config import Settings


class MockAdapter(LLMAdapter):
    """
    Mock LLM 适配器

    作用:
        模拟 LLM API 响应，用于测试和演示。
        无需 API Key 即可运行。
    """

    def __init__(self, settings: Settings):
        """
        初始化 Mock 适配器

        参数:
            settings: Settings 类型，应用配置对象
        """
        super().__init__(settings)

    async def chat(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024
    ) -> LLMResponse:
        """
        模拟对话响应

        参数:
            user_prompt: str 类型，用户消息
            system_prompt: str 类型，系统提示
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: 模拟的响应对象
        """
        # 根据提示词内容生成模拟响应
        if "classification" in system_prompt.lower() or "classify" in user_prompt.lower():
            content = json.dumps({
                "type": "inquiry",
                "priority_score": 0.7,
                "urgency": "medium",
                "language": "en",
                "products_mentioned": ["Paracetamol 500mg"],
                "customer_region": "Europe",
                "requires_human": False,
                "suggested_route": "quote_flow"
            }, indent=2)
        elif "quote" in system_prompt.lower() or "pricing" in user_prompt.lower():
            content = json.dumps({
                "quote_id": "mock-quote-001",
                "customer_email": "customer@example.com",
                "items": [
                    {
                        "product": "Paracetamol 500mg",
                        "quantity": 1000,
                        "unit_price": 2.80,
                        "subtotal": 2800.00
                    }
                ],
                "total_amount": 2800.00,
                "valid_until": "2026-05-07",
                "shipping_port": "Shanghai",
                "payment_terms": "T/T 30% advance, 70% before shipment",
                "notes": "Price based on current market rate. Subject to change."
            }, indent=2)
        else:
            content = "This is a mock response from the LLM adapter."

        return LLMResponse(
            content=content,
            model="mock-model-v1",
            usage={
                "input_tokens": len(user_prompt) // 4,
                "output_tokens": len(content) // 4
            },
            raw_response={"mock": True, "content": content}
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
        return await self.chat(user_prompt, system_prompt, max_tokens)
