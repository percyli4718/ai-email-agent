"""
Layer 2: 上下文检索器模块

模块作用:
    本模块实现 AI Email Agent 的第二层——上下文检索器。
    整合 ChromaDB 向量搜索、数据库查询等功能，为邮件生成提供全面的上下文信息，
    包括相似历史邮件、客户历史记录、适用定价政策和合规要求。

使用场景:
    - 收到分类后的邮件，检索相关上下文信息
    - 为 Layer 3 报价生成器提供丰富的参考数据
    - 支持 RAG(检索增强生成) 模式，提高回复质量

在项目中的位置:
    位于 src/email_agent/layer2/retriever.py，
    是 AI Email Agent 三层架构的第二层 (L2)，
    依赖 chroma_client、embedding_service 和 database 模块，
    被 Layer 3 生成器调用以获取上下文。
"""
from typing import Any, Dict

from email_agent.config import Settings
from email_agent.layer2.chroma_client import ChromaClient
from email_agent.layer2.embedding_service import EmbeddingService
from email_agent.logging_config import get_logger
from email_agent.storage.database import get_database

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class ContextRetriever:
    """
    上下文检索器

    作用:
        Layer 2 核心类，负责检索与邮件相关的所有上下文信息。
        整合多个数据源，为邮件处理提供全面的背景数据。

    使用场景:
        - 处理新邮件时检索相关上下文
        - 为报价生成提供历史参考和 policy 信息
        - 支持合规检查和定价策略查询

    主要方法:
        retrieve: 检索邮件的完整上下文
        _search_similar_emails: 搜索相似历史邮件
        _get_customer_history: 获取客户历史记录
        _get_pricing_policy: 获取适用定价政策
        _get_compliance_requirements: 获取合规要求

    属性:
        settings: Settings 类型，应用配置
        chroma_client: ChromaClient 类型，向量数据库客户端
        embedding_service: EmbeddingService 类型，嵌入生成服务
        db: Database 类型，数据库实例
    """

    def __init__(self, settings: Settings):
        """
        初始化上下文检索器

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        # 初始化 ChromaDB 客户端，用于相似邮件搜索
        self.chroma_client = ChromaClient(settings)
        # 初始化 Embedding 服务，用于生成查询向量
        self.embedding_service = EmbeddingService(settings)
        # 获取数据库实例，用于查询客户/定价/合规信息
        self.db = get_database(settings)

    async def retrieve(
        self,
        email_id: str,
        email_body: str,
        classification: dict
    ) -> Dict[str, Any]:
        """
        检索邮件的完整上下文信息

        功能描述:
            综合调用多个检索方法，获取与邮件相关的所有上下文信息。
            返回的上下文将用于 Layer 3 的报价生成。

        参数:
            email_id: str 类型，邮件唯一标识符
            email_body: str 类型，邮件正文内容
            classification: dict 类型，Layer 1 生成的分类结果
                - customer_region: 客户区域
                - products_mentioned: 提及的产品列表

        返回值:
            Dict[str, Any]: 上下文信息字典，包含:
                - similar_emails: 相似历史邮件搜索结果
                - customer_history: 客户历史记录
                - pricing_policy: 适用定价政策
                - compliance: 合规要求

        异常:
            无

        处理流程:
            1. 搜索相似的历史邮件
            2. 查询客户历史订单记录
            3. 获取产品定价政策
            4. 查询目的地合规要求
            5. 整合所有上下文并返回
        """
        # 搜索相似的历史邮件 (基于邮件内容和区域过滤)
        similar_emails = await self._search_similar_emails(
            email_body,
            classification.get("customer_region")
        )

        # 获取客户历史记录
        customer_history = await self._get_customer_history(classification)

        # 获取适用定价政策
        pricing_policy = await self._get_pricing_policy(
            classification.get("products_mentioned", []),
            classification.get("customer_region")
        )

        # 获取合规要求
        compliance = await self._get_compliance_requirements(
            classification.get("products_mentioned", []),
            classification.get("customer_region")
        )

        # 记录检索成功的日志
        logger.info(
            "context_retrieved",
            email_id=email_id,
            similar_count=len(similar_emails.get("documents", [])),
            has_customer=customer_history is not None
        )

        # 返回整合的上下文信息
        return {
            "similar_emails": similar_emails,
            "customer_history": customer_history,
            "pricing_policy": pricing_policy,
            "compliance": compliance
        }

    async def _search_similar_emails(self, email_body: str, region: str) -> dict:
        """
        搜索相似的历史邮件

        功能描述:
            使用邮件正文在 ChromaDB 中搜索相似的历史邮件。
            支持按区域过滤，只搜索目标区域的邮件。

        参数:
            email_body: str 类型，当前邮件正文 (用于生成查询向量)
            region: str 类型，客户区域 (用于过滤，可选)

        返回值:
            dict: ChromaDB 查询结果，包含相似邮件内容和元数据

        异常:
            无

        处理说明:
            - 限制邮件正文长度为 2000 字符
            - 返回最相似的 3 封历史邮件
            - 如果指定区域，只搜索该区域的邮件
        """
        # 构建元数据过滤条件 (如果指定了区域)
        filter_metadata = {"region": region} if region else None
        # 调用 ChromaDB 客户端进行相似性搜索
        return await self.chroma_client.search_similar(
            query_text=email_body[:2000],  # 限制查询文本长度
            n_results=3,  # 返回 3 个最相似结果
            filter_metadata=filter_metadata  # 区域过滤条件
        )

    async def _get_customer_history(self, classification: dict) -> dict:
        """
        获取客户历史订单记录

        功能描述:
            根据客户邮箱或区域查询客户的历史订单记录。
            用于了解客户等级、历史购买行为等信息。

        参数:
            classification: dict 类型，邮件分类结果
                - customer_email: 客户邮箱 (可选)
                - customer_region: 客户区域

        返回值:
            dict: 客户历史记录，包含:
                - name: 客户名称
                - tier: 客户等级 (A/B/C)
                - region: 所在区域

        异常:
            无

        使用场景:
            - 了解客户等级以应用适当的折扣
            - 查看历史订单以提供一致的报价
        """
        # 调用数据库查询客户信息
        return await self.db.query_customer(
            email=classification.get("customer_email"),
            region=classification.get("customer_region")
        )

    async def _get_pricing_policy(self, products: list, region: str) -> dict:
        """
        获取适用的产品定价政策

        功能描述:
            根据产品列表和客户区域查询适用的定价政策。
            不同区域可能有不同的价格策略和折扣。

        参数:
            products: list 类型，产品名称列表
            region: str 类型，客户区域

        返回值:
            dict: 定价政策信息，包含:
                - base_price: 基础价格
                - discount: 折扣率
                - region: 适用区域

        异常:
            无

        使用场景:
            - 生成报价时确定基准价格
            - 应用区域特定的定价策略
        """
        # 调用数据库查询定价政策
        return await self.db.query_pricing(
            products=products,
            region=region
        )

    async def _get_compliance_requirements(self, products: list, region: str) -> dict:
        """
        获取产品出口的合规要求

        功能描述:
            根据产品列表和目的地查询合规要求。
            不同国家/地区对药品进口有不同的认证要求。

        参数:
            products: list 类型，产品名称列表
            region: str 类型，目的地国家/区域

        返回值:
            dict: 合规要求信息，包含:
                - required: 必需的认证/许可列表

        异常:
            无

        使用场景:
            - 确保报价包含必要的合规成本
            - 告知客户所需的进口许可

        合规示例:
            - Brazil: ANVISA 认证
            - EU: CE 认证，GMP 合规
            - US: FDA 认证
        """
        # 调用数据库查询合规要求
        return await self.db.query_compliance(
            products=products,
            destination=region
        )
