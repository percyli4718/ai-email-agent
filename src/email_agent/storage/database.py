"""
数据库模块

模块作用:
    本模块封装数据库连接管理和会话工厂。
    使用 SQLAlchemy 异步引擎提供数据库访问功能，
    支持上下文管理器的会话管理方式。

使用场景:
    - 应用启动时初始化数据库连接
    - 在各业务模块中获取数据库会话
    - 查询客户信息、定价政策、合规要求等

在项目中的位置:
    位于 src/email_agent/storage/database.py，
    是应用存储层的核心组件，
    被 retriever.py 等模块调用进行数据查询。
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy import select

from email_agent.config import Settings
from email_agent.logging_config import get_logger
from email_agent.storage.models import Customer, PricingPolicy, ComplianceRequirement, EmailAnalysis

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class Database:
    """
    数据库连接管理器

    作用:
        管理数据库引擎和会话工厂。
        使用懒加载初始化，避免应用启动时不必要的连接。

    使用场景:
        - 应用启动时创建实例
        - 通过上下文管理器获取会话
        - 应用关闭时清理连接

    主要方法:
        session: 获取数据库会话 (上下文管理器)
        close: 关闭数据库连接
        query_customer: 查询客户信息
        query_pricing: 查询定价政策
        query_compliance: 查询合规要求

    属性:
        settings: Settings 类型，应用配置
        _engine: Optional[AsyncEngine] 类型，数据库引擎 (懒加载)
        _session_factory: Optional[async_sessionmaker] 类型，会话工厂

    懒加载说明:
        engine 和 session_factory 都在首次访问时创建，
        避免应用启动时立即建立数据库连接
    """

    def __init__(self, settings: Settings):
        """
        初始化数据库

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    @property
    def engine(self) -> AsyncEngine:
        """
        数据库引擎属性 (懒加载)

        功能描述:
            按需创建异步数据库引擎。
            开发环境下启用 SQL 日志输出。

        参数:
            无

        返回值:
            AsyncEngine: SQLAlchemy 异步引擎实例

        异常:
            无

        配置说明:
            - echo=True (开发环境): 输出 SQL 日志
            - echo=False (生产环境): 禁用 SQL 日志
        """
        if self._engine is None:
            # 首次访问时创建引擎
            self._engine = create_async_engine(
                # 数据库连接 URL，如：sqlite+aiosqlite:///./data/email_agent.db
                self.settings.database_url,
                # 开发环境下启用 SQL 日志
                echo=self.settings.env == "development"
            )
            logger.info("database_initialized", url=self.settings.database_url)
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """
        会话工厂属性

        功能描述:
            创建或获取会话工厂。
            用于生成数据库会话。

        参数:
            无

        返回值:
            async_sessionmaker: SQLAlchemy 异步会话工厂

        异常:
            无

        配置说明:
            - class_=AsyncSession: 使用异步会话类
            - expire_on_commit=False: 提交后不过期对象属性
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                # 绑定数据库引擎
                self.engine,
                # 使用异步会话类
                class_=AsyncSession,
                # 提交后不过期对象属性，便于后续访问
                expire_on_commit=False
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取数据库会话 (上下文管理器)

        功能描述:
            使用上下文管理器自动管理会话生命周期。
            成功时自动提交，异常时自动回滚。

        参数:
            无

        返回值:
            AsyncSession: SQLAlchemy 异步会话

        异常:
            Exception: 任何异常都会触发回滚

        使用示例:
            async with db.session() as session:
                # 执行数据库操作
                session.add(model)
            # 自动提交
        """
        # 创建新会话
        async with self.session_factory() as session:
            try:
                # yield 会话给调用者使用
                yield session
                # 成功则提交
                await session.commit()
            except Exception:
                # 异常则回滚
                await session.rollback()
                # 重新抛出异常
                raise

    async def init_tables(self) -> None:
        """
        初始化数据库表

        功能描述:
            创建所有模型对应的数据库表。
            在应用启动时调用。

        参数:
            无

        返回值:
            无

        异常:
            无

        使用示例:
            db = get_database(settings)
            await db.init_tables()
        """
        from email_agent.storage.models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("database_tables_initialized")

    async def close(self) -> None:
        """
        关闭数据库连接

        功能描述:
            释放数据库引擎占用的资源。
            在应用关闭时调用。

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        if self._engine:
            # 释放引擎资源
            await self._engine.dispose()
            logger.info("database_closed")

    async def query_customer(self, email: str = None, region: str = None) -> dict:
        """
        查询客户历史记录

        功能描述:
            根据邮箱或区域查询客户信息。
            使用 SQLAlchemy 异步查询 Customer 表。

        参数:
            email: Optional[str] 类型，客户邮箱 (可选)
            region: Optional[str] 类型，客户区域 (可选)

        返回值:
            dict: 客户信息字典
                - name: 客户名称
                - tier: 客户等级 (A/B/C)
                - region: 所在区域

        异常:
            无

        使用示例:
            async with db.session() as session:
                customer = await db.query_customer(session, email="test@example.com")
        """
        async with self.session() as session:
            # 构建查询
            stmt = select(Customer)
            if email:
                stmt = stmt.where(Customer.email == email)
            if region:
                stmt = stmt.where(Customer.region == region)

            result = await session.execute(stmt)
            customer = result.scalars().first()

            if customer:
                return {
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "tier": customer.tier,
                    "region": customer.region
                }

            # 如果没有找到客户，返回 None
            return None

    async def create_customer(
        self,
        name: str,
        email: str,
        tier: str = "C",
        region: str = None
    ) -> Customer:
        """
        创建客户记录

        功能描述:
            创建新的客户记录。如果邮箱已存在则返回现有客户。

        参数:
            name: str 类型，客户名称
            email: str 类型，客户邮箱
            tier: str 类型，客户等级 (A/B/C)
            region: str 类型，客户区域

        返回值:
            Customer: 创建或查询到的客户对象

        异常:
            SQLAlchemy 异常

        使用示例:
            customer = await db.create_customer(
                name="John Smith",
                email="john@example.com",
                tier="A",
                region="Europe"
            )
        """
        from email_agent.storage.models import Customer
        from sqlalchemy import select

        async with self.session() as session:
            # 先查询是否已存在
            stmt = select(Customer).where(Customer.email == email)
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                return existing

            # 创建新客户
            customer = Customer(
                name=name,
                email=email,
                tier=tier,
                region=region
            )
            session.add(customer)
            await session.flush()  # 获取自增 ID
            logger.info("customer_created", email=email, tier=tier)
            return customer

    async def get_or_create_customer(
        self,
        email: str,
        defaults: dict = None
    ) -> Customer:
        """
        获取或创建客户

        功能描述:
            根据邮箱查找客户，如果不存在则创建新客户。
            用于邮件生成器创建邮件时快速处理客户记录。

        参数:
            email: str 类型，客户邮箱地址
            defaults: dict 类型，创建时使用的默认值
                - name: 客户名称
                - region: 客户区域
                - tier: 客户等级 (默认 C)

        返回值:
            Customer: 客户对象（已存在或新创建）

        异常:
            SQLAlchemy 异常

        使用示例:
            customer = await db.get_or_create_customer(
                email="john@example.com",
                defaults={"name": "PharmaCom UK", "region": "Europe", "tier": "A"}
            )
        """
        from email_agent.storage.models import Customer
        from sqlalchemy import select

        async with self.session() as session:
            # 尝试查找现有客户
            stmt = select(Customer).where(Customer.email == email)
            result = await session.execute(stmt)
            customer = result.scalar_one_or_none()

            if customer:
                return customer

            # 创建新客户
            if defaults is None:
                defaults = {}

            customer = Customer(
                email=email,
                name=defaults.get("name", "Unknown Customer"),
                region=defaults.get("region", "Unknown"),
                tier=defaults.get("tier", "C")
            )
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
            logger.info("customer_created", email=email, tier=customer.tier)
            return customer

    async def save_email_analysis(
        self,
        email_id: str,
        layer1_classification: dict = None,
        layer2_retrieval: dict = None,
        layer3_output: dict = None,
        processing_time_ms: float = None,
        cost: float = None,
        model_used: str = None
    ) -> None:
        """
        保存邮件分析结果

        功能描述:
            保存 Layer 1/2/3 的完整分析结果到数据库。

        参数:
            email_id: str 类型，邮件 ID
            layer1_classification: dict 类型，Layer 1 分类结果
            layer2_retrieval: dict 类型，Layer 2 检索结果
            layer3_output: dict 类型，Layer 3 生成结果
            processing_time_ms: float 类型，处理耗时 (毫秒)
            cost: float 类型，AI 调用成本 (美元)
            model_used: str 类型，使用的模型名称

        返回值:
            无

        异常:
            SQLAlchemy 异常

        使用示例:
            await db.save_email_analysis(
                email_id="email_001",
                layer1_classification={"type": "inquiry", "priority_score": 0.85},
                layer2_retrieval={"query": "...", "results": [...]},
                layer3_output={"quote_id": "QT-001", "total_amount": 5000},
                processing_time_ms=1234.5,
                cost=0.05,
                model_used="claude-sonnet-4"
            )
        """
        from email_agent.storage.models import EmailAnalysis

        async with self.session() as session:
            analysis = EmailAnalysis(
                email_id=email_id,
                layer1_classification=layer1_classification,
                layer2_retrieval=layer2_retrieval,
                layer3_output=layer3_output,
                processing_time_ms=processing_time_ms,
                cost=cost,
                model_used=model_used
            )
            session.add(analysis)
            logger.info("email_analysis_saved", email_id=email_id, cost=cost)

    async def save_agent_execution(
        self,
        task_id: str,
        agent_name: str,
        email_id: str = None,
        status: str = "pending",
        budget_allocated: float = None,
        actual_cost: float = None,
        input_data: dict = None,
        output_data: dict = None,
        error_message: str = None,
        started_at: datetime = None,
        completed_at: datetime = None
    ) -> None:
        """
        保存 Agent 执行记录

        功能描述:
            保存子 Agent 的执行日志到数据库。

        参数:
            task_id: str 类型，任务 ID
            agent_name: str 类型，Agent 名称
            email_id: str 类型，关联邮件 ID
            status: str 类型，执行状态
            budget_allocated: float 类型，分配预算
            actual_cost: float 类型，实际成本
            input_data: dict 类型，输入数据
            output_data: dict 类型，输出数据
            error_message: str 类型，错误信息
            started_at: datetime 类型，开始时间
            completed_at: datetime 类型，完成时间

        返回值:
            无

        异常:
            SQLAlchemy 异常

        使用示例:
            await db.save_agent_execution(
                task_id="task_001",
                agent_name="price_agent",
                email_id="email_001",
                status="completed",
                budget_allocated=0.10,
                actual_cost=0.08,
                output_data={"quote": {...}},
                started_at=datetime.utcnow()
            )
        """
        from email_agent.storage.models import AgentExecution

        async with self.session() as session:
            execution = AgentExecution(
                task_id=task_id,
                agent_name=agent_name,
                email_id=email_id,
                status=status,
                budget_allocated=budget_allocated,
                actual_cost=actual_cost,
                input_data=input_data,
                output_data=output_data,
                error_message=error_message,
                started_at=started_at,
                completed_at=completed_at
            )
            session.add(execution)
            logger.info("agent_execution_saved", task_id=task_id, agent=agent_name, status=status)

    async def query_pricing_policy(self, products: list, region: str) -> dict:
        """
        查询产品定价政策

        功能描述:
            根据产品列表和区域查询适用定价。
            优先查询特定区域价格，若无则返回默认价格。

        参数:
            products: list 类型，产品名称列表
            region: str 类型，客户区域

        返回值:
            dict: {
                "policies": [{"product": str, "base_price": float, "discount_rate": float, "currency": str}],
                "region": str
            }

        异常:
            无
        """
        from sqlalchemy import select

        async with self.session() as session:
            policies = []
            for product in products:
                # 先查询特定区域价格
                stmt = select(PricingPolicy).where(
                    PricingPolicy.product_name == product,
                    PricingPolicy.region == region
                )
                result = await session.execute(stmt)
                policy = result.scalars().first()

                if policy:
                    policies.append({
                        "product": policy.product_name,
                        "base_price": policy.base_price,
                        "discount_rate": policy.discount_rate,
                        "currency": policy.currency
                    })
                else:
                    # 如果没有找到特定区域价格，查找默认价格
                    stmt = select(PricingPolicy).where(
                        PricingPolicy.product_name == product,
                        PricingPolicy.region == "default"
                    )
                    result = await session.execute(stmt)
                    policy = result.scalars().first()
                    if policy:
                        policies.append({
                            "product": policy.product_name,
                            "base_price": policy.base_price,
                            "discount_rate": policy.discount_rate,
                            "currency": policy.currency
                        })

            return {"policies": policies, "region": region}

    async def query_compliance_requirements(self, products: list, destination: str) -> dict:
        """
        查询合规要求

        功能描述:
            根据产品和目的地查询合规要求。
            不同国家/地区有不同的认证要求。

        参数:
            products: list 类型，产品名称列表
            destination: str 类型，目的地国家/区域

        返回值:
            dict: {
                "requirements": [{"type": str, "name": str, "mandatory": bool, "description": str}],
                "region": str
            }

        异常:
            无

        合规示例:
            - Brazil: ANVISA 认证
            - EU: CE 认证，GMP 合规
            - US: FDA 认证
        """
        from sqlalchemy import select

        async with self.session() as session:
            # 查询该区域的通用合规要求
            stmt = select(ComplianceRequirement).where(
                ComplianceRequirement.region == destination
            )
            result = await session.execute(stmt)
            requirements = result.scalars().all()

            return {
                "requirements": [
                    {
                        "type": req.requirement_type,
                        "name": req.requirement_name,
                        "mandatory": req.mandatory,
                        "description": req.description
                    }
                    for req in requirements
                ],
                "region": destination
            }

    async def get_all_emails(self, limit: int = 50) -> list:
        """
        获取所有邮件列表

        功能描述:
            查询数据库中的所有邮件，按接收时间倒序排列。

        参数:
            limit: int 类型，返回数量上限，默认 50

        返回值:
            list: 邮件列表
        """
        from email_agent.storage.models import Email

        async with self.session() as session:
            stmt = select(Email).order_by(Email.received_at.desc()).limit(limit)
            result = await session.execute(stmt)
            emails = result.scalars().all()

            return [
                {
                    "id": email.id,
                    "from_address": email.from_address,
                    "subject": email.subject,
                    "preview": email.body[:100] + "..." if email.body else "",
                    "priority": email.priority,
                    "status": email.status,
                    "received_at": email.received_at.isoformat() if email.received_at else None,
                    "region": email.region,
                }
                for email in emails
            ]

    async def get_email_by_id(self, email_id: str) -> dict:
        """
        根据 ID 获取邮件详情

        功能描述:
            查询单封邮件的完整信息。

        参数:
            email_id: str 类型，邮件 ID

        返回值:
            dict: 邮件信息字典，不存在则返回 None
        """
        from email_agent.storage.models import Email

        async with self.session() as session:
            stmt = select(Email).where(Email.id == email_id)
            result = await session.execute(stmt)
            email = result.scalars().first()

            if email:
                return {
                    "id": email.id,
                    "from_address": email.from_address,
                    "subject": email.subject,
                    "body": email.body,
                    "priority": email.priority,
                    "status": email.status,
                    "received_at": email.received_at.isoformat() if email.received_at else None,
                    "region": email.region,
                }
            return None

    async def get_email_analysis(self, email_id: str) -> dict:
        """
        获取邮件分析结果

        功能描述:
            查询指定邮件的完整分析结果（Layer 1/2/3）。

        参数:
            email_id: str 类型，邮件 ID

        返回值:
            dict: 分析结果字典，不存在则返回 None
        """
        from email_agent.storage.models import EmailAnalysis

        async with self.session() as session:
            stmt = select(EmailAnalysis).where(EmailAnalysis.email_id == email_id)
            result = await session.execute(stmt)
            analysis = result.scalars().first()

            if analysis:
                return {
                    "id": analysis.id,
                    "email_id": analysis.email_id,
                    "layer1_classification": analysis.layer1_classification,
                    "layer2_retrieval": analysis.layer2_retrieval,
                    "layer3_output": analysis.layer3_output,
                    "processing_time_ms": analysis.processing_time_ms,
                    "cost": analysis.cost,
                    "model_used": analysis.model_used,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                }
            return None

    async def get_agent_executions(self, email_id: str = None) -> list:
        """
        获取 Agent 执行记录

        功能描述:
            查询 Agent 执行历史，可按邮件 ID 过滤。

        参数:
            email_id: Optional[str] 类型，邮件 ID 过滤条件（可选）

        返回值:
            list: Agent 执行记录列表
        """
        from email_agent.storage.models import AgentExecution

        async with self.session() as session:
            stmt = select(AgentExecution)
            if email_id:
                stmt = stmt.where(AgentExecution.email_id == email_id)
            stmt = stmt.order_by(AgentExecution.started_at.desc())

            result = await session.execute(stmt)
            executions = result.scalars().all()

            return [
                {
                    "id": ex.id,
                    "task_id": ex.task_id,
                    "agent_name": ex.agent_name,
                    "status": ex.status,
                    "budget_allocated": ex.budget_allocated,
                    "actual_cost": ex.actual_cost,
                    "started_at": ex.started_at.isoformat() if ex.started_at else None,
                    "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                    "email_id": ex.email_id
                }
                for ex in executions
            ]

    async def create_email_analysis(
        self,
        email_id: str,
        layer1_classification: dict = None,
        layer2_retrieval: dict = None,
        layer3_output: dict = None,
        processing_time_ms: float = None,
        cost: float = None,
        model_used: str = None
    ) -> dict:
        """
        创建或更新邮件分析记录

        功能描述:
            创建新的邮件分析记录，或更新已存在的记录。
            支持分层更新（Layer 1/2/3 可分别更新）。

        参数:
            email_id: str 类型，邮件唯一标识符
            layer1_classification: dict 类型，Layer 1 分类结果
            layer2_retrieval: dict 类型，Layer 2 检索结果
            layer3_output: dict 类型，Layer 3 生成结果
            processing_time_ms: float 类型，处理耗时（毫秒）
            cost: float 类型，API 调用成本（美元）
            model_used: str 类型，使用的模型名称

        返回值:
            dict: 创建或更新的分析记录字典

        异常:
            SQLAlchemy 异常

        使用示例:
            await db.create_email_analysis(
                email_id="email_001",
                layer1_classification={"type": "inquiry", "priority": 0.8},
                processing_time_ms=1500.0,
                cost=0.003,
                model_used="claude-sonnet-4-20250514"
            )
        """
        from email_agent.storage.models import EmailAnalysis
        from sqlalchemy import select

        async with self.session() as session:
            # 检查是否已存在分析记录
            stmt = select(EmailAnalysis).where(EmailAnalysis.email_id == email_id)
            result = await session.execute(stmt)
            analysis = result.scalars().first()

            if analysis:
                # 更新现有记录
                if layer1_classification:
                    analysis.layer1_classification = layer1_classification
                if layer2_retrieval:
                    analysis.layer2_retrieval = layer2_retrieval
                if layer3_output:
                    analysis.layer3_output = layer3_output
                if processing_time_ms:
                    analysis.processing_time_ms = processing_time_ms
                if cost:
                    analysis.cost = cost
                if model_used:
                    analysis.model_used = model_used
            else:
                # 创建新记录
                analysis = EmailAnalysis(
                    email_id=email_id,
                    layer1_classification=layer1_classification,
                    layer2_retrieval=layer2_retrieval,
                    layer3_output=layer3_output,
                    processing_time_ms=processing_time_ms,
                    cost=cost,
                    model_used=model_used
                )
                session.add(analysis)

            await session.commit()

            return {
                "id": analysis.id,
                "email_id": analysis.email_id,
                "layer1_classification": analysis.layer1_classification,
                "layer2_retrieval": analysis.layer2_retrieval,
                "layer3_output": analysis.layer3_output,
                "processing_time_ms": analysis.processing_time_ms,
                "cost": analysis.cost,
                "model_used": analysis.model_used
            }

    async def update_email_status(self, email_id: str, status: str) -> bool:
        """
        更新邮件处理状态

        功能描述:
            更新指定邮件的处理状态。
            用于追踪邮件处理进度（pending → processing → completed/failed）。

        参数:
            email_id: str 类型，邮件唯一标识符
            status: str 类型，新状态
                - pending: 待处理
                - processing: 处理中
                - completed: 已完成
                - failed: 处理失败

        返回值:
            bool: 是否成功更新

        异常:
            SQLAlchemy 异常

        使用示例:
            await db.update_email_status("email_001", "processing")
            await db.update_email_status("email_001", "completed")
        """
        from email_agent.storage.models import Email
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(Email).where(Email.id == email_id)
            result = await session.execute(stmt)
            email = result.scalars().first()

            if email:
                email.status = status
                await session.commit()
                logger.info("email_status_updated", email_id=email_id, status=status)
                return True

            logger.warning("email_not_found_for_status_update", email_id=email_id)
            return False


# 全局数据库实例 (延迟初始化)
_db_instance: Optional[Database] = None


def get_database(settings: Settings) -> Database:
    """
    获取或创建数据库实例

    功能描述:
        使用全局变量模式确保单例访问。
        首次调用时创建实例，后续调用复用。

    参数:
        settings: Settings 类型，应用配置对象

    返回值:
        Database: 数据库实例

    异常:
        无

    使用示例:
        db = get_database(settings)
        async with db.session() as session:
            # 执行数据库操作
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(settings)
    return _db_instance
