"""
Layer 1: 电子邮件分类器模块

模块作用:
    本模块实现 AI Email Agent 的第一层——电子邮件分类器。
    使用 Anthropic Claude 模型对传入的电子邮件进行智能分类，
    确定邮件类型、优先级、紧急程度、语言、提及产品、客户区域等信息，
    并建议合适的处理路由。

使用场景:
    - 收到新邮件时进行自动分类
    - 根据分类结果将邮件路由到不同的处理流程
    - 为后续层级提供结构化的分类信息

在项目中的位置:
    位于 src/email_agent/layer1/classifier.py，
    是 AI Email Agent 三层架构的第一层 (L1)，
    依赖 prompts 模块定义的提示词模板，
    被主处理流程调用以启动邮件处理管道。
"""
import json
import time
import asyncio
from typing import Any

from email_agent.config import Settings
from email_agent.layer1.prompts import CLASSIFIER_PROMPT, EmailClassification
from email_agent.logging_config import get_logger
from email_agent.storage.database import get_database
from email_agent.llm_adapter import get_llm_adapter, LLMAdapter, LLMResponse

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class EmailClassifier:
    """
    电子邮件分类器

    作用:
        Layer 1 核心类，负责对传入的电子邮件进行分类分析。
        使用 Claude 模型理解邮件内容，输出结构化的分类结果。

    使用场景:
        - 处理新收到的电子邮件
        - 为每封邮件生成分类标签和路由建议
        - 作为邮件处理管道的入口点

    主要方法:
        classify: 对邮件进行分类，返回分类结果
        _validate_classification: 验证分类结果的完整性

    属性:
        settings: Settings 类型，应用配置
        _client: Anthropic 异步客户端，懒加载初始化
    """

    def __init__(self, settings: Settings):
        """
        初始化电子邮件分类器

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self.llm = get_llm_adapter()  # LLM 适配器
        self.db = get_database(settings)  # 数据库实例，用于写入分类结果

    async def classify(
        self,
        email_id: str,
        email_body: str,
        subject: str = ""
    ) -> EmailClassification:
        """
        对电子邮件进行分类（带重试逻辑和数据库写入）

        功能描述:
            调用 Claude 模型分析邮件内容，返回结构化的分类结果。
            包含邮件类型、优先级分数、紧急程度、语言、产品提及、客户区域、
            是否需要人工处理和建议的处理路由。

            重试策略:
                - 最大重试次数：3 次
                - 重试延迟：指数退避 (1s, 2s, 4s)
                - 仅在以下情况重试：网络错误、API 超时、5xx 服务器错误

        参数:
            email_id: str 类型，邮件唯一标识符
            email_body: str 类型，邮件正文内容 (自动截断至 4000 字符)
            subject: str 类型，邮件主题 (可选，默认为空字符串)

        返回值:
            EmailClassification: 分类结果字典，包含:
                - type: 邮件类型 (inquiry/complaint/status_check/other)
                - priority_score: 优先级分数 (0.0-1.0)
                - urgency: 紧急程度 (low/medium/high)
                - language: 语言代码 (en/pt/es 等)
                - products_mentioned: 提及的产品列表
                - customer_region: 客户所在区域
                - requires_human: 是否需要人工处理
                - suggested_route: 建议路由 (quote_flow/complaint_flow 等)

        异常:
            ClassificationError: 当分类失败时抛出 (JSON 解析失败或字段缺失)

        处理流程:
            1. 构造分类提示词，包含邮件主题和正文
            2. 调用 Claude Sonnet 模型进行分析（带重试）
            3. 解析 JSON 响应
            4. 验证必需字段
            5. 将分类结果写入数据库
            6. 更新邮件状态
            7. 记录日志并返回结果
        """
        max_retries = 3
        retry_delay = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                # 记录开始时间
                start_time = time.time()

                # 构造分类提示词，限制邮件正文长度为 4000 字符以防 token 超限
                prompt = CLASSIFIER_PROMPT.format(
                    email_body=email_body[:4000],
                    subject=subject
                )

                # 调用 LLM API 进行分类
                response = await self.llm.chat_with_json(
                    user_prompt=prompt,
                    system_prompt="You are an email classification assistant. Classify emails and return JSON format responses.",
                    max_tokens=256
                )

                # 解析模型返回的 JSON 响应
                result_text = response.content.strip()
                result: EmailClassification = json.loads(result_text)

                # 验证分类结果包含所有必需字段
                self._validate_classification(result)

                # 计算处理耗时
                processing_time_ms = (time.time() - start_time) * 1000

                # 将分类结果写入数据库
                await self.db.create_email_analysis(
                    email_id=email_id,
                    layer1_classification=result,
                    processing_time_ms=processing_time_ms,
                    cost=0.003,  # 预估成本
                    model_used=response.model
                )

                # 更新邮件状态
                await self.db.update_email_status(email_id, "classified")

                # 记录分类成功的日志
                logger.info(
                    "email_classified",
                    email_id=email_id,
                    type=result.get("type"),
                    priority=result.get("priority_score"),
                    route=result.get("suggested_route"),
                    processing_time_ms=f"{processing_time_ms:.2f}"
                )

                return result

            except json.JSONDecodeError as e:
                # JSON 解析失败：模型返回的响应格式不正确，不重试
                logger.error("classification_json_parse_error", error=str(e))
                raise ClassificationError(f"Failed to parse classification: {e}")

            except Exception as e:
                # 其他错误：网络问题、API 错误等，尝试重试
                last_error = e
                logger.warning(
                    "classification_attempt_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e)
                )

                if attempt < max_retries - 1:
                    # 等待后重试（指数退避）
                    await asyncio.sleep(retry_delay * (2 ** attempt))

        # 所有重试失败，更新状态为 failed 并抛出异常
        logger.error("classification_all_retries_failed", error=str(last_error))
        await self.db.update_email_status(email_id, "failed")
        raise ClassificationError(f"Classification failed after {max_retries} retries: {last_error}")

    def _validate_classification(self, result: dict) -> None:
        """
        验证分类结果包含所有必需字段

        功能描述:
            检查分类结果字典是否包含所有必需的字段。
            如果缺少字段，抛出 ClassificationError 异常。

        参数:
            result: dict 类型，分类结果字典

        返回值:
            无

        异常:
            ClassificationError: 当缺少必需字段时抛出

        必需字段:
            - type: 邮件类型
            - priority_score: 优先级分数
            - language: 语言代码
            - suggested_route: 建议路由
        """
        # 定义必需字段列表
        required_fields = ["type", "priority_score", "language", "suggested_route"]
        # 找出缺失的字段
        missing = [f for f in required_fields if f not in result]
        # 如果有缺失字段，抛出异常
        if missing:
            raise ClassificationError(f"Missing fields: {missing}")


class ClassificationError(Exception):
    """
    分类错误异常类

    作用:
        当电子邮件分类失败时抛出此异常。
        可能的失败原因包括:
        - JSON 解析失败 (模型返回格式错误)
        - 缺少必需字段
        - API 调用失败
        - 网络错误

    使用场景:
        - 捕获并处理分类失败的情况
        - 向上层调用者传达分类失败的原因
    """
    pass
