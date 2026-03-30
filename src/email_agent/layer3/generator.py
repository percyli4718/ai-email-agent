"""
Layer 3: 报价生成器模块

模块作用:
    本模块实现 AI Email Agent 的第三层——报价生成器。
    基于 Layer 2 检索的上下文信息，使用 LLM 生成结构化的报价单。
    包含智能模型路由功能，根据复杂度自动选择 Sonnet 或 Opus 模型以控制成本。

使用场景:
    - 根据检索的上下文生成正式报价
    - 智能选择模型以平衡质量和成本
    - 跟踪 API 支出确保不超出预算

在项目中的位置:
    位于 src/email_agent/layer3/generator.py，
    是 AI Email Agent 三层架构的第三层 (L3)，
    依赖 router 模块进行模型选择，
    依赖 budget_tracker 进行成本控制。
"""
import json
import uuid
from typing import TYPE_CHECKING, Any, Dict

from email_agent.config import Settings
from email_agent.layer3.prompts import QUOTE_GENERATION_PROMPT, QuoteResult
from email_agent.layer3.router import ModelChoice, ModelRouter
from email_agent.logging_config import get_logger
from email_agent.observability.budget_tracker import BudgetTracker

# TYPE_CHECKING 用于类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    import anthropic

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class QuoteGenerator:
    """
    报价生成器

    作用:
        Layer 3 核心类，负责基于上下文信息生成结构化报价。
        使用智能模型路由控制成本，使用预算追踪防止超支。

    使用场景:
        - 为客户询价生成正式报价单
        - 基于历史数据和定价政策自动定价
        - 输出符合业务规范的 JSON 格式报价

    主要方法:
        generate_quote: 生成报价单
        _call_llm: 调用 LLM API
        _calculate_cost: 计算 API 成本
        _format_similar_emails: 格式化相似邮件
        _validate_quote: 验证报价完整性

    属性:
        settings: Settings 类型，应用配置
        _client: Anthropic 客户端，懒加载初始化
        router: ModelRouter 类型，模型路由器
        budget_tracker: BudgetTracker 类型，预算追踪器
    """

    def __init__(self, settings: Settings):
        """
        初始化报价生成器

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._client = None  # 懒加载客户端
        self.router = ModelRouter()  # 模型路由器，根据复杂度选择模型
        self.budget_tracker = BudgetTracker(settings)  # 预算追踪器

    @property
    def client(self) -> "anthropic.AsyncClient":
        """
        Anthropic 客户端属性 (懒加载)

        功能描述:
            按需创建 Anthropic 客户端，避免在构造函数中初始化可能导致的代理问题。

        参数:
            无

        返回值:
            anthropic.AsyncClient: Anthropic 异步客户端实例

        异常:
            无
        """
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncClient(api_key=self.settings.anthropic_api_key)
        return self._client

    async def generate_quote(
        self,
        original_email: str,
        context: Dict[str, Any]
    ) -> QuoteResult:
        """
        基于上下文生成报价单

        功能描述:
            使用模型路由器选择合适的模型，基于检索的上下文生成结构化报价。
            在调用 LLM 前检查预算，调用后记录实际支出。

        参数:
            original_email: str 类型，原始邮件内容 (限制 2000 字符)
            context: Dict[str, Any] 类型，Layer 2 检索的上下文信息
                - similar_emails: 相似历史邮件
                - customer_history: 客户历史记录
                - pricing_policy: 定价政策
                - compliance: 合规要求

        返回值:
            QuoteResult: 报价单字典，包含:
                - quote_id: 报价单 ID (UUID)
                - customer_email: 客户邮箱
                - items: 报价项目列表
                - total_amount: 总金额
                - valid_until: 报价有效期
                - shipping_port: 发货港口
                - payment_terms: 付款条款
                - notes: 备注

        异常:
            QuoteGenerationError: 当报价生成失败时抛出 (JSON 解析失败或字段缺失)

        处理流程:
            1. 使用模型路由器选择合适模型
            2. 检查预算是否充足
            3. 构造提示词
            4. 调用 LLM 生成报价
            5. 解析并验证 JSON 响应
            6. 记录日志并返回
        """
        # 使用模型路由器根据上下文复杂度选择模型
        model = self.router.route(context)

        # 根据选择的模型确定最大成本限制
        max_cost = (
            self.settings.max_sonnet_cost_per_email
            if model == ModelChoice.SONNET
            else self.settings.max_opus_cost_per_email
        )

        # 在调用 LLM 前检查预算
        await self.budget_tracker.check_budget(
            operation="quote_generation",
            estimated_cost=max_cost
        )

        # 构造报价生成提示词
        prompt = QUOTE_GENERATION_PROMPT.format(
            similar_emails=self._format_similar_emails(context.get("similar_emails", {})),
            customer_history=json.dumps(context.get("customer_history", {}), indent=2),
            pricing_policy=json.dumps(context.get("pricing_policy", {}), indent=2),
            compliance=json.dumps(context.get("compliance", {}), indent=2),
            original_email=original_email[:2000]  # 限制原始邮件长度
        )

        # 调用 LLM 生成报价
        result_text = await self._call_llm(model, prompt)

        try:
            # 解析 JSON 响应
            result: QuoteResult = json.loads(result_text)
            # 验证报价包含所有必需字段
            self._validate_quote(result)

            # 记录报价生成成功的日志
            logger.info(
                "quote_generated",
                quote_id=result.get("quote_id"),
                total=result.get("total_amount"),
                model=model.value
            )

            return result

        except json.JSONDecodeError as e:
            # JSON 解析失败
            logger.error("quote_parse_error", error=str(e))
            raise QuoteGenerationError(f"Failed to parse quote: {e}")

    async def _call_llm(self, model: ModelChoice, prompt: str) -> str:
        """
        调用 Anthropic LLM API

        功能描述:
            使用选定的模型调用 Anthropic API 生成报价。
            计算并记录实际 API 成本。

        参数:
            model: ModelChoice 类型，选择的模型 (SONNET 或 OPUS)
            prompt: str 类型，提示词内容

        返回值:
            str: LLM 返回的文本内容

        异常:
            无

        处理说明:
            - 使用 1024 tokens 的最大输出限制
            - 记录实际 token 消耗和成本
            - 更新预算追踪器
        """
        # 调用 Anthropic Messages API
        response = await self.client.messages.create(
            model=model.value,  # 模型名称
            max_tokens=1024,  # 最大输出 tokens
            messages=[{"role": "user", "content": prompt}]
        )

        # 计算实际 API 成本
        cost = self._calculate_cost(
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        # 记录实际支出到预算追踪器
        await self.budget_tracker.record_spending(
            operation="quote_generation",
            actual_cost=cost
        )

        return response.content[0].text.strip()

    def _calculate_cost(
        self,
        model: ModelChoice,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        计算 API 使用成本

        功能描述:
            根据模型类型和 token 使用量计算 API 成本。
            Sonnet 和 Opus 有不同的定价。

        参数:
            model: ModelChoice 类型，使用的模型
            input_tokens: int 类型，输入 token 数量
            output_tokens: int 类型，输出 token 数量

        返回值:
            float: API 成本 (美元)

        异常:
            无

        定价说明 (示例):
            Sonnet:
                - 输入：$3/百万 tokens
                - 输出：$15/百万 tokens
            Opus:
                - 输入：$15/百万 tokens
                - 输出：$75/百万 tokens
        """
        if model == ModelChoice.SONNET:
            # Sonnet 模型定价
            return (input_tokens * 3e-6) + (output_tokens * 1.5e-5)
        else:
            # Opus 模型定价 (更贵)
            return (input_tokens * 1.5e-5) + (output_tokens * 7.5e-5)

    def _format_similar_emails(self, similar: dict) -> str:
        """
        格式化相似邮件用于提示词

        功能描述:
            将 ChromaDB 返回的相似邮件结果格式化为可读文本。
            如果没有相似邮件，返回提示信息。

        参数:
            similar: dict 类型，ChromaDB 查询结果
                - documents: 文档内容列表

        返回值:
            str: 格式化后的相似邮件文本

        异常:
            无
        """
        # 从结果中提取文档列表
        documents = similar.get("documents", [[]])
        # 检查是否有文档
        if not documents or not documents[0]:
            return "No similar emails found."
        # 连接最多 3 封相似邮件的内容
        return "\n\n".join(documents[0][:3])

    def _validate_quote(self, quote: dict) -> None:
        """
        验证报价包含所有必需字段

        功能描述:
            检查报价字典是否包含所有必需字段。
            确保至少有一个报价项目。

        参数:
            quote: dict 类型，报价结果字典

        返回值:
            无

        异常:
            QuoteGenerationError: 当缺少必需字段或没有项目时抛出

        必需字段:
            - quote_id: 报价单 ID
            - customer_email: 客户邮箱
            - items: 报价项目列表
            - total_amount: 总金额
        """
        # 定义必需字段列表
        required = ["quote_id", "customer_email", "items", "total_amount"]
        # 找出缺失的字段
        missing = [f for f in required if f not in quote]
        if missing:
            raise QuoteGenerationError(f"Missing required fields: {missing}")
        # 检查至少有一个报价项目
        if not quote.get("items"):
            raise QuoteGenerationError("Quote must have at least one item")


class QuoteGenerationError(Exception):
    """
    报价生成错误异常类

    作用:
        当报价生成失败时抛出此异常。
        可能的失败原因包括:
        - JSON 解析失败 (模型返回格式错误)
        - 缺少必需字段
        - 没有报价项目
        - API 调用失败

    使用场景:
        - 捕获并处理报价生成失败的情况
        - 向上层调用者传达失败原因
    """
    pass
