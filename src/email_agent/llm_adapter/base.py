"""
LLM Adapter Base Module

模块作用:
    定义 LLM 适配器的基础接口和响应类型。
    所有具体的适配器都必须继承此基类。
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    LLM 响应数据类

    属性:
        content: str 类型，模型生成的文本内容
        model: str 类型，使用的模型名称
        usage: dict 类型，token 使用统计
            - input_tokens: 输入 token 数
            - output_tokens: 输出 token 数
        raw_response: Any 类型，原始响应对象 (可选)
    """
    content: str
    model: str
    usage: dict[str, int]
    raw_response: Any = None


class LLMAdapter(ABC):
    """
    LLM 适配器抽象基类

    作用:
        定义所有 LLM 适配器必须实现的接口。
        使用策略模式，使业务逻辑与具体模型实现解耦。

    使用场景:
        - 统一不同模型供应商的 API 调用方式
        - 方便切换模型 provider
        - 便于测试和 Mock

    主要方法:
        chat: 发送对话请求并获取响应
        chat_with_json: 发送对话请求并要求返回 JSON 格式
    """

    def __init__(self, settings):
        """
        初始化 LLM 适配器

        参数:
            settings: Settings 类型，应用配置对象
        """
        self.settings = settings

    @abstractmethod
    async def chat(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1024
    ) -> LLMResponse:
        """
        发送对话请求

        参数:
            user_prompt: str 类型，用户消息
            system_prompt: str 类型，系统提示 (可选)
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: LLM 响应对象

        异常:
            由具体实现抛出
        """
        pass

    @abstractmethod
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
            system_prompt: str 类型，系统提示 (可选)
            max_tokens: int 类型，最大生成 token 数

        返回值:
            LLMResponse: LLM 响应对象，content 字段包含 JSON 字符串

        异常:
            由具体实现抛出
        """
        pass
