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
from typing import TYPE_CHECKING, Any

from email_agent.config import Settings
from email_agent.layer1.prompts import CLASSIFIER_PROMPT, EmailClassification
from email_agent.logging_config import get_logger

# TYPE_CHECKING 用于类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    import anthropic

# 获取当前模块的日志记录器
logger = get_logger(__name__)


def create_client(api_key: str) -> "anthropic.AsyncClient":
    """
    创建 Anthropic API 客户端实例

    功能描述:
        工厂函数，使用提供的 API 密钥创建 Anthropic 异步客户端。
        将导入语句放在函数内部，避免模块加载时的依赖问题。

    参数:
        api_key: str 类型，Anthropic API 密钥

    返回值:
        anthropic.AsyncClient: Anthropic 异步客户端实例

    异常:
        无

    使用场景:
        - 分类器初始化时创建客户端
        - 需要多个客户端实例时使用
    """
    import anthropic
    return anthropic.AsyncClient(api_key=api_key)


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
        self._client = None  # 懒加载客户端，避免初始化时的代理问题

    @property
    def client(self) -> "anthropic.AsyncClient":
        """
        Anthropic 客户端属性 (懒加载)

        功能描述:
            按需创建 Anthropic 客户端，避免在构造函数中初始化可能导致的代理问题。
            首次访问时创建客户端实例，后续访问复用同一实例。

        参数:
            无

        返回值:
            anthropic.AsyncClient: Anthropic 异步客户端实例

        异常:
            无
        """
        if self._client is None:
            # 首次访问时创建客户端
            self._client = create_client(self.settings.anthropic_api_key)
        return self._client

    async def classify(
        self,
        email_body: str,
        subject: str = ""
    ) -> EmailClassification:
        """
        对电子邮件进行分类

        功能描述:
            调用 Claude 模型分析邮件内容，返回结构化的分类结果。
            包含邮件类型、优先级分数、紧急程度、语言、产品提及、客户区域、
            是否需要人工处理和建议的处理路由。

        参数:
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
            2. 调用 Claude Sonnet 模型进行分析
            3. 解析 JSON 响应
            4. 验证必需字段
            5. 记录日志并返回结果
        """
        try:
            # 构造分类提示词，限制邮件正文长度为 4000 字符以防 token 超限
            prompt = CLASSIFIER_PROMPT.format(
                email_body=email_body[:4000],
                subject=subject
            )

            # 调用 Anthropic API，使用 Claude Sonnet 模型进行分类
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,  # 分类结果较短，256 tokens 足够
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # 解析模型返回的 JSON 响应
            result_text = response.content[0].text.strip()
            result: EmailClassification = json.loads(result_text)

            # 验证分类结果包含所有必需字段
            self._validate_classification(result)

            # 记录分类成功的日志
            logger.info(
                "email_classified",
                type=result.get("type"),
                priority=result.get("priority_score"),
                route=result.get("suggested_route")
            )

            return result

        except json.JSONDecodeError as e:
            # JSON 解析失败：模型返回的响应格式不正确
            logger.error("classification_json_parse_error", error=str(e))
            raise ClassificationError(f"Failed to parse classification: {e}")
        except Exception as e:
            # 其他错误：网络问题、API 错误等
            logger.error("classification_error", error=str(e))
            raise ClassificationError(f"Classification failed: {e}")

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
