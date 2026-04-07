"""
LLM Adapter Module

模块作用:
    本模块提供统一的 LLM 接口，支持多种模型供应商。
    使用策略模式，可以在不修改业务代码的情况下切换模型 provider。

支持的 Provider:
    - anthropic: Anthropic Claude API
    - bailian: 阿里百炼 (阿里云)
    - mock: Mock 模式，用于测试和演示

使用方式:
    from email_agent.llm_adapter import get_llm_adapter
    adapter = get_llm_adapter()
    response = await adapter.chat(prompt, system_prompt)
"""
from email_agent.llm_adapter.base import LLMAdapter, LLMResponse
from email_agent.llm_adapter.anthropic_adapter import AnthropicAdapter
from email_agent.llm_adapter.bailian_adapter import BailianAdapter
from email_agent.llm_adapter.mock_adapter import MockAdapter
from email_agent.config import settings


def get_llm_adapter(provider: str | None = None) -> LLMAdapter:
    """
    获取 LLM 适配器实例

    参数:
        provider: str 类型，可选，模型提供商
            - "anthropic": Anthropic Claude API
            - "bailian": 阿里百炼
            - "mock": Mock 模式
            如果不传，从环境变量 LLM_PROVIDER 读取，默认为 "anthropic"

    返回值:
        LLMAdapter: LLM 适配器实例

    使用示例:
        adapter = get_llm_adapter()
        response = await adapter.chat("用户消息", "系统提示")
    """
    # 从参数或环境变量获取 provider
    if provider is None:
        provider = getattr(settings, 'llm_provider', 'anthropic')

    # 根据 provider 返回对应的适配器
    if provider == 'bailian':
        return BailianAdapter(settings)
    elif provider == 'mock':
        return MockAdapter(settings)
    else:  # anthropic 或默认
        return AnthropicAdapter(settings)


__all__ = ['LLMAdapter', 'LLMResponse', 'get_llm_adapter']
