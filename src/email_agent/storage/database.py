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
from sqlalchemy import select, func

from email_agent.config import Settings
from email_agent.logging_config import get_logger
from email_agent.storage.models import Customer, PricingPolicy, ComplianceRequirement, EmailAnalysis, Notification, Quote, QuoteItem

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

    async def get_all_emails(self, limit: int = 50, offset: int = 0) -> tuple[list, int]:
        """
        获取所有邮件列表（支持分页）

        功能描述:
            查询数据库中的所有邮件，按接收时间倒序排列。

        参数:
            limit: int 类型，返回数量上限，默认 50
            offset: int 类型，偏移量，默认 0

        返回值:
            tuple: (邮件列表，总记录数)
        """
        from email_agent.storage.models import Email

        async with self.session() as session:
            # 获取总记录数
            count_stmt = select(func.count()).select_from(Email)
            count_result = await session.execute(count_stmt)
            total = count_result.scalar() or 0

            # 获取分页数据
            stmt = select(Email).order_by(Email.received_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            emails = result.scalars().all()

            return (
                [
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
                ],
                total
            )

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
                    "raw_content": email.body or "",
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
                model_used="claude-sonnet-20241022"
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

    async def create_notification(
        self,
        type: str,
        title: str,
        message: str,
        level: str = "info",
        related_id: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> dict:
        """
        创建通知记录

        功能描述:
            在数据库中创建新的通知记录。

        参数:
            type: str 类型，通知类型
                email_status/agent_progress/approval_request/system
            title: str 类型，通知标题
            message: str 类型，通知消息
            level: str 类型，通知级别，默认 "info"
                info/success/warning/error
            related_id: str 类型，可选，关联 ID
            extra_data: dict 类型，可选，额外数据

        返回值:
            dict: 创建的通知记录字典

        使用示例:
            await db.create_notification(
                type="email_status",
                title="邮件处理完成",
                message="邮件 email_001 已完成处理",
                level="success",
                related_id="email_001"
            )
        """
        from email_agent.storage.models import Notification
        from sqlalchemy import insert, select

        async with self.session() as session:
            stmt = insert(Notification).values(
                type=type,
                title=title,
                message=message,
                level=level,
                related_id=related_id,
                extra_data=extra_data
            )
            result = await session.execute(stmt)
            await session.commit()

            notification_id = result.inserted_primary_key[0]

            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()

            return notification.to_dict() if notification else {}

    async def get_notifications(self, limit: int = 50, unread_only: bool = False) -> list:
        """
        获取通知列表

        功能描述:
            查询通知列表，支持按未读状态过滤。

        参数:
            limit: int 类型，返回数量上限，默认 50
            unread_only: bool 类型，是否只返回未读，默认 False

        返回值:
            list: 通知列表
        """
        from email_agent.storage.models import Notification
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(Notification)
            if unread_only:
                stmt = stmt.where(Notification.is_read == False)
            stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)

            result = await session.execute(stmt)
            notifications = result.scalars().all()

            return [notification.to_dict() for notification in notifications]

    async def mark_notification_read(self, notification_id: int) -> bool:
        """
        标记通知为已读

        功能描述:
            更新通知的已读状态。

        参数:
            notification_id: int 类型，通知 ID

        返回值:
            bool: 是否成功更新
        """
        from email_agent.storage.models import Notification
        from sqlalchemy import select, update

        async with self.session() as session:
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()

            if notification:
                stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
                await session.execute(stmt)
                await session.commit()
                return True

            return False

    async def create_approval_request(
        self,
        email_id: str,
        requester: str,
        request_type: str,
        reason: str,
        amount: float = None,
        currency: str = "USD",
        details: dict = None
    ) -> dict:
        """
        创建审批请求

        功能描述:
            创建新的审批请求记录。

        参数:
            email_id: str 类型，关联邮件 ID
            requester: str 类型，申请人
            request_type: str 类型，审批类型
            reason: str 类型，申请原因
            amount: float 类型，涉及金额（可选）
            currency: str 类型，币种
            details: dict 类型，详细信息

        返回值:
            dict: 创建的审批请求记录
        """
        from email_agent.storage.models import ApprovalRequest
        from sqlalchemy import select

        async with self.session() as session:
            request = ApprovalRequest(
                email_id=email_id,
                requester=requester,
                request_type=request_type,
                reason=reason,
                amount=amount,
                currency=currency,
                details=details
            )
            session.add(request)
            await session.commit()
            await session.refresh(request)

            return request.to_dict()

    async def get_approval_requests(self, status: str = None, limit: int = 50) -> list:
        """
        获取审批请求列表

        功能描述:
            查询审批请求列表，可按状态过滤。

        参数:
            status: str 类型，审批状态（可选）
            limit: int 类型，返回数量上限

        返回值:
            list: 审批请求列表
        """
        from email_agent.storage.models import ApprovalRequest
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(ApprovalRequest)
            if status:
                stmt = stmt.where(ApprovalRequest.status == status)
            stmt = stmt.order_by(ApprovalRequest.created_at.desc()).limit(limit)

            result = await session.execute(stmt)
            requests = result.scalars().all()

            return [req.to_dict() for req in requests]

    async def get_approval_request_by_id(self, request_id: int) -> dict:
        """
        根据 ID 获取审批请求详情

        功能描述:
            查询单个审批请求的完整信息。

        参数:
            request_id: int 类型，审批请求 ID

        返回值:
            dict: 审批请求详情，不存在则返回 None
        """
        from email_agent.storage.models import ApprovalRequest
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
            result = await session.execute(stmt)
            request = result.scalars().first()

            return request.to_dict() if request else None

    async def approve_request(self, request_id: int, reviewer: str, comments: str = None) -> bool:
        """
        批准审批请求

        功能描述:
            将审批请求状态更新为 approved。

        参数:
            request_id: int 类型，审批请求 ID
            reviewer: str 类型，审批人
            comments: str 类型，审批意见

        返回值:
            bool: 是否成功更新
        """
        from email_agent.storage.models import ApprovalRequest
        from sqlalchemy import select, update
        from datetime import datetime

        async with self.session() as session:
            stmt = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
            result = await session.execute(stmt)
            request = result.scalar_one_or_none()

            if request:
                stmt = update(ApprovalRequest).where(ApprovalRequest.id == request_id).values(
                    status="approved",
                    reviewer=reviewer,
                    reviewed_at=datetime.utcnow(),
                    comments=comments
                )
                await session.execute(stmt)
                await session.commit()
                return True

            return False

    async def reject_request(self, request_id: int, reviewer: str, comments: str) -> bool:
        """
        拒绝审批请求

        功能描述:
            将审批请求状态更新为 rejected。

        参数:
            request_id: int 类型，审批请求 ID
            reviewer: str 类型，审批人
            comments: str 类型，拒绝原因

        返回值:
            bool: 是否成功更新
        """
        from email_agent.storage.models import ApprovalRequest
        from sqlalchemy import select, update
        from datetime import datetime

        async with self.session() as session:
            stmt = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
            result = await session.execute(stmt)
            request = result.scalar_one_or_none()

            if request:
                stmt = update(ApprovalRequest).where(ApprovalRequest.id == request_id).values(
                    status="rejected",
                    reviewer=reviewer,
                    reviewed_at=datetime.utcnow(),
                    comments=comments
                )
                await session.execute(stmt)
                await session.commit()
                return True

            return False

    # ============================================================================
    # Quote CRUD Methods - 报价 CRUD 方法
    # ============================================================================

    async def create_quote(
        self,
        quote_id: str,
        email_id: str,
        customer_email: str,
        total_amount: float,
        valid_until: str,
        items: list,
        shipping_port: str = None,
        payment_terms: str = None,
        notes: str = None,
        status: str = "draft"
    ) -> dict:
        """
        创建报价单

        功能描述:
            创建新的报价单及其项目。
            支持事务性创建，确保报价单和项目原子性写入。

        参数:
            quote_id: str 类型，报价单号
            email_id: str 类型，关联邮件 ID
            customer_email: str 类型，客户邮箱
            total_amount: float 类型，总金额
            valid_until: str 类型，报价有效期 (YYYY-MM-DD)
            items: list 类型，报价项目列表
                每个项目包含：product_name, product_code, quantity, unit_price,
                currency, incoterm, lead_time_days
            shipping_port: str 类型，发货港口
            payment_terms: str 类型，付款条款
            notes: str 类型，备注
            status: str 类型，报价状态 (默认 "draft")

        返回值:
            dict: 创建的报价单记录

        异常:
            SQLAlchemy 异常
        """
        from email_agent.storage.models import Quote, QuoteItem
        from sqlalchemy import select

        async with self.session() as session:
            # 检查报价单号是否已存在
            stmt = select(Quote).where(Quote.quote_id == quote_id)
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                logger.warning("quote_id_exists", quote_id=quote_id)
                # 返回基本字典，避免异步加载关系
                return {
                    "id": existing.id,
                    "quote_id": existing.quote_id,
                    "email_id": existing.email_id,
                    "customer_email": existing.customer_email,
                    "total_amount": existing.total_amount,
                    "valid_until": existing.valid_until,
                    "shipping_port": existing.shipping_port,
                    "payment_terms": existing.payment_terms,
                    "notes": existing.notes,
                    "status": existing.status,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None,
                    "items": []  # 空列表，避免异步加载
                }

            # 创建报价单
            quote = Quote(
                quote_id=quote_id,
                email_id=email_id,
                customer_email=customer_email,
                total_amount=total_amount,
                valid_until=valid_until,
                shipping_port=shipping_port or "",
                payment_terms=payment_terms or "30% advance, 70% against B/L",
                notes=notes,
                status=status
            )
            session.add(quote)
            await session.flush()  # 获取自增 ID

            # 创建报价项目
            for item_data in items:
                item = QuoteItem(
                    quote_id=quote.id,
                    product_name=item_data.get("product_name"),
                    product_code=item_data.get("product_code"),
                    quantity=item_data.get("quantity", 1),
                    unit_price=item_data.get("unit_price", 0),
                    currency=item_data.get("currency", "USD"),
                    incoterm=item_data.get("incoterm", "FOB"),
                    lead_time_days=item_data.get("lead_time_days", 30),
                    subtotal=item_data.get("quantity", 1) * item_data.get("unit_price", 0)
                )
                session.add(item)

            await session.commit()
            await session.refresh(quote)

            logger.info("quote_created", quote_id=quote_id, total=total_amount)
            return quote.to_dict()

    async def get_quote(self, quote_id: str) -> dict:
        """
        获取报价单详情

        功能描述:
            根据报价单号查询完整报价信息（包含项目列表）。

        参数:
            quote_id: str 类型，报价单号

        返回值:
            dict: 报价单详情，不存在则返回 None
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(Quote).where(Quote.quote_id == quote_id)
            result = await session.execute(stmt)
            quote = result.scalars().first()

            return quote.to_dict() if quote else None

    async def get_quote_by_id(self, id: int) -> dict:
        """
        根据 ID 获取报价单详情

        功能描述:
            根据主键 ID 查询报价单信息。

        参数:
            id: int 类型，报价单主键 ID

        返回值:
            dict: 报价单详情，不存在则返回 None
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(Quote).where(Quote.id == id)
            result = await session.execute(stmt)
            quote = result.scalars().first()

            return quote.to_dict() if quote else None

    async def get_quotes_by_email(self, email_id: str) -> list:
        """
        获取邮件的所有报价单

        功能描述:
            查询指定邮件关联的所有报价单。

        参数:
            email_id: str 类型，邮件 ID

        返回值:
            list: 报价单列表
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(Quote).where(Quote.email_id == email_id).order_by(Quote.created_at.desc())
            result = await session.execute(stmt)
            quotes = result.scalars().all()

            return [quote.to_dict() for quote in quotes]

    async def get_all_quotes(self, limit: int = 50, status: str = None) -> list:
        """
        获取所有报价单列表

        功能描述:
            查询报价单列表，支持状态过滤。

        参数:
            limit: int 类型，返回数量上限，默认 50
            status: str 类型，状态过滤条件（可选）

        返回值:
            list: 报价单列表
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import select, func

        async with self.session() as session:
            stmt = select(Quote).order_by(Quote.created_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(Quote.status == status)

            result = await session.execute(stmt)
            quotes = result.scalars().all()

            # 手动构建字典，避免异步加载 items 关系
            return [{
                "id": quote.id,
                "quote_id": quote.quote_id,
                "email_id": quote.email_id,
                "customer_email": quote.customer_email,
                "total_amount": quote.total_amount,
                "valid_until": quote.valid_until,
                "shipping_port": quote.shipping_port,
                "payment_terms": quote.payment_terms,
                "notes": quote.notes,
                "status": quote.status,
                "created_at": quote.created_at.isoformat() if quote.created_at else None,
                "items": []  # 空列表，避免异步加载
            } for quote in quotes]

    async def update_quote_status(self, quote_id: str, status: str) -> bool:
        """
        更新报价单状态

        功能描述:
            更新报价单的状态（draft/sent/accepted/rejected/expired）。

        参数:
            quote_id: str 类型，报价单号
            status: str 类型，新状态

        返回值:
            bool: 是否成功更新
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import select, update

        async with self.session() as session:
            stmt = select(Quote).where(Quote.quote_id == quote_id)
            result = await session.execute(stmt)
            quote = result.scalars().first()

            if quote:
                stmt = update(Quote).where(Quote.quote_id == quote_id).values(status=status)
                await session.execute(stmt)
                await session.commit()
                logger.info("quote_status_updated", quote_id=quote_id, status=status)
                return True

            logger.warning("quote_not_found_for_status_update", quote_id=quote_id)
            return False

    async def delete_quote(self, quote_id: str) -> bool:
        """
        删除报价单

        功能描述:
            删除报价单及其所有项目（级联删除）。

        参数:
            quote_id: str 类型，报价单号

        返回值:
            bool: 是否成功删除
        """
        from email_agent.storage.models import Quote
        from sqlalchemy import delete

        async with self.session() as session:
            stmt = delete(Quote).where(Quote.quote_id == quote_id)
            result = await session.execute(stmt)
            await session.commit()

            if result.rowcount > 0:
                logger.info("quote_deleted", quote_id=quote_id)
                return True

            logger.warning("quote_not_found_for_deletion", quote_id=quote_id)
            return False

    # ========================================================================
    # Email Workflow Methods - 邮件工作流方法
    # ========================================================================

    async def create_email_workflow(
        self,
        email_id: str,
        initial_state: str = "pending",
        requires_approval: bool = False,
        approval_reason: str = None,
        approval_amount: float = None
    ) -> dict:
        """
        创建邮件工作流

        功能描述:
            为邮件创建初始工作流记录。

        参数:
            email_id: str 类型，邮件 ID
            initial_state: str 类型，初始状态
            requires_approval: bool 类型，是否需要审批
            approval_reason: str 类型，审批原因
            approval_amount: float 类型，审批金额

        返回值:
            dict: 创建的工作流字典
        """
        from email_agent.storage.models import EmailWorkflow, WorkflowHistory
        from sqlalchemy import insert, select

        async with self.session() as session:
            # 检查工作流是否已存在
            stmt = select(EmailWorkflow).where(EmailWorkflow.email_id == email_id)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                return existing.to_dict()

            # 创建工作流
            stmt = insert(EmailWorkflow).values(
                email_id=email_id,
                current_state=initial_state,
                requires_approval=requires_approval,
                approval_reason=approval_reason,
                approval_amount=approval_amount
            )
            await session.execute(stmt)
            await session.commit()

            # 查询创建的工作流
            stmt = select(EmailWorkflow).where(EmailWorkflow.email_id == email_id)
            result = await session.execute(stmt)
            workflow = result.scalar_one_or_none()

            # 创建初始历史记录
            if workflow:
                stmt = insert(WorkflowHistory).values(
                    workflow_id=workflow.id,
                    from_state="none",
                    to_state=initial_state,
                    triggered_by="system",
                    reason="工作流已创建"
                )
                await session.execute(stmt)
                await session.commit()

                return workflow.to_dict()

            return {}

    async def transition_workflow_state(
        self,
        email_id: str,
        new_state: str,
        triggered_by: str,
        reason: str = None,
        metadata: dict = None
    ) -> dict:
        """
        转换工作流状态

        功能描述:
            将邮件工作流转换到新状态，并记录历史。

        状态机流转规则:
            pending → processing → awaiting_approval → approved → completed
                                        ↓                    ↓
                                    rejected            failed/cancelled

        参数:
            email_id: str 类型，邮件 ID
            new_state: str 类型，新状态
            triggered_by: str 类型，触发者 (system/agent/user/approval_rule)
            reason: str 类型，变更原因
            metadata: dict 类型，额外元数据

        返回值:
            dict: 更新后的工作流字典，失败返回空字典
        """
        from email_agent.storage.models import EmailWorkflow, WorkflowHistory
        from sqlalchemy import select, update, insert

        valid_transitions = {
            "pending": ["processing", "failed"],
            "processing": ["awaiting_approval", "approved", "completed", "failed"],
            "awaiting_approval": ["approved", "rejected"],
            "approved": ["completed", "failed"],
            "rejected": ["pending"],  # 可以重新提交
            "completed": [],
            "failed": ["pending"],  # 可以重试
            "cancelled": []
        }

        async with self.session() as session:
            # 获取当前工作流
            stmt = select(EmailWorkflow).where(EmailWorkflow.email_id == email_id)
            result = await session.execute(stmt)
            workflow = result.scalar_one_or_none()

            if not workflow:
                logger.warning("workflow_not_found_for_transition", email_id=email_id)
                return {}

            current_state = workflow.current_state

            # 验证状态转换是否合法
            if new_state not in valid_transitions.get(current_state, []):
                logger.warning(
                    "invalid_state_transition",
                    email_id=email_id,
                    from_state=current_state,
                    to_state=new_state
                )
                return {}

            # 更新状态
            stmt = update(EmailWorkflow).where(
                EmailWorkflow.email_id == email_id
            ).values(
                current_state=new_state,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)

            # 记录历史
            stmt = insert(WorkflowHistory).values(
                workflow_id=workflow.id,
                from_state=current_state,
                to_state=new_state,
                triggered_by=triggered_by,
                reason=reason,
                extra_data=metadata
            )
            await session.execute(stmt)
            await session.commit()

            # 返回更新后的工作流
            stmt = select(EmailWorkflow).where(EmailWorkflow.email_id == email_id)
            result = await session.execute(stmt)
            updated_workflow = result.scalar_one_or_none()

            logger.info(
                "workflow_state_transitioned",
                email_id=email_id,
                from_state=current_state,
                to_state=new_state,
                triggered_by=triggered_by
            )

            return updated_workflow.to_dict() if updated_workflow else {}

    async def get_email_workflow(self, email_id: str) -> dict:
        """
        获取邮件工作流详情

        功能描述:
            获取邮件的工作流状态和历史记录。

        参数:
            email_id: str 类型，邮件 ID

        返回值:
            dict: 包含工作流和历史的字典
        """
        from email_agent.storage.models import EmailWorkflow, WorkflowHistory
        from sqlalchemy import select

        async with self.session() as session:
            # 获取工作流
            stmt = select(EmailWorkflow).where(EmailWorkflow.email_id == email_id)
            result = await session.execute(stmt)
            workflow = result.scalar_one_or_none()

            if not workflow:
                return {}

            # 获取历史记录
            stmt = select(WorkflowHistory).where(
                WorkflowHistory.workflow_id == workflow.id
            ).order_by(WorkflowHistory.created_at.asc())
            result = await session.execute(stmt)
            history = result.scalars().all()

            return {
                **workflow.to_dict(),
                "history": [h.to_dict() for h in history]
            }

    async def check_approval_required(self, email_id: str, amount: float, threshold: float = 10000.0) -> bool:
        """
        检查是否需要审批

        功能描述:
            根据金额判断是否需要审批（金额 > $10000 触发审批）。

        参数:
            email_id: str 类型，邮件 ID
            amount: float 类型，金额
            threshold: float 类型，审批阈值 (默认 10000)

        返回值:
            bool: True 表示需要审批
        """
        if amount > threshold:
            # 更新工作流标记需要审批
            await self.transition_workflow_state(
                email_id=email_id,
                new_state="awaiting_approval",
                triggered_by="approval_rule",
                reason=f"Amount ${amount} exceeds threshold ${threshold}",
                metadata={"amount": amount, "threshold": threshold}
            )
            return True
        return False

    # ========================================================================
    # Agent Monitoring Methods - Agent 监控方法
    # ========================================================================

    async def get_agent_executions(self, limit: int = 50, email_id: Optional[str] = None) -> list[dict]:
        """
        获取 Agent 执行历史记录

        功能描述:
            查询最近的 Agent 执行记录，支持按邮件 ID 过滤。

        参数:
            limit: int 类型，返回数量限制 (默认 50)
            email_id: Optional[str] 类型，邮件 ID 过滤 (可选)

        返回值:
            list[dict]: Agent 执行记录列表
        """
        from email_agent.storage.models import AgentExecution
        from sqlalchemy import select, desc

        async with self.session() as session:
            stmt = select(AgentExecution).order_by(desc(AgentExecution.started_at)).limit(limit)

            if email_id:
                stmt = stmt.where(AgentExecution.email_id == email_id)

            result = await session.execute(stmt)
            executions = result.scalars().all()

            return [
                {
                    "id": ex.id,
                    "task_id": ex.task_id,
                    "email_id": ex.email_id,
                    "agent_name": ex.agent_name,
                    "status": ex.status,
                    "budget_allocated": ex.budget_allocated,
                    "actual_cost": ex.actual_cost,
                    "started_at": ex.started_at.isoformat() if ex.started_at else None,
                    "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                    "error_message": ex.error_message,
                    "result_summary": ex.output_data.get("summary") if ex.output_data else None,
                }
                for ex in executions
            ]

    async def get_execution_detail(self, task_id: str) -> Optional[dict]:
        """
        获取单个执行详情

        功能描述:
            根据 task_id 查询 Agent 执行的完整详情。

        参数:
            task_id: str 类型，任务 ID

        返回值:
            Optional[dict]: 执行详情字典，不存在返回 None
        """
        from email_agent.storage.models import AgentExecution, Email
        from sqlalchemy import select

        async with self.session() as session:
            stmt = select(AgentExecution).where(AgentExecution.task_id == task_id)
            result = await session.execute(stmt)
            execution = result.scalars().first()

            if not execution:
                return None

            # 获取关联的邮件信息
            email = None
            if execution.email_id:
                email_stmt = select(Email).where(Email.id == execution.email_id)
                email_result = await session.execute(email_stmt)
                email = email_result.scalars().first()

            return {
                "id": execution.id,
                "task_id": execution.task_id,
                "email_id": execution.email_id,
                "agent_name": execution.agent_name,
                "status": execution.status,
                "budget_allocated": execution.budget_allocated,
                "actual_cost": execution.actual_cost,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "error_message": execution.error_message,
                "result_summary": execution.output_data.get("summary") if execution.output_data else None,
                "email_subject": email.subject if email else None,
                "email_from": email.from_address if email else None,
                "execution_steps": execution.output_data.get("steps") if execution.output_data else [],
            }

    async def get_agent_metrics(self) -> list[dict]:
        """
        获取 Agent 性能指标

        功能描述:
            聚合统计各 Agent 的执行指标。

        参数:
            无

        返回值:
            list[dict]: Agent 性能指标列表
        """
        from email_agent.storage.models import AgentExecution
        from sqlalchemy import select, func

        async with self.session() as session:
            # 按 agent_name 分组统计
            stmt = select(
                AgentExecution.agent_name,
                func.count(AgentExecution.id).label("total_executions"),
                func.sum(func.case((AgentExecution.status == "completed", 1), else_=0)).label("successful_executions"),
                func.sum(func.case((AgentExecution.status == "failed", 1), else_=0)).label("failed_executions"),
                func.avg(AgentExecution.actual_cost).label("avg_cost"),
                func.sum(AgentExecution.actual_cost).label("total_cost"),
            ).group_by(AgentExecution.agent_name)

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "agent_name": row.agent_name,
                    "total_executions": row.total_executions,
                    "successful_executions": row.successful_executions,
                    "failed_executions": row.failed_executions,
                    "success_rate": row.successful_executions / max(1, row.total_executions),
                    "avg_cost": row.avg_cost or 0,
                    "total_cost": row.total_cost or 0,
                    "avg_execution_time_ms": 0,  # 需要从 execution_steps 计算
                }
                for row in rows
            ]

    async def get_cost_stats(self, days: int = 30) -> list[dict]:
        """
        获取成本统计数据

        功能描述:
            按日期统计成本数据。

        参数:
            days: int 类型，统计天数 (默认 30)

        返回值:
            list[dict]: 每日成本统计列表
        """
        from email_agent.storage.models import EmailAnalysis, Email
        from sqlalchemy import select, func, cast, Date
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with self.session() as session:
            stmt = (
                select(
                    cast(EmailAnalysis.created_at, Date).label("date"),
                    func.sum(EmailAnalysis.cost).label("total_cost"),
                    func.avg(EmailAnalysis.cost).label("avg_cost_per_email"),
                    func.count(EmailAnalysis.id).label("email_count"),
                )
                .where(EmailAnalysis.created_at >= cutoff_date)
                .group_by(cast(EmailAnalysis.created_at, Date))
                .order_by(cast(EmailAnalysis.created_at, Date))
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "date": str(row.date),
                    "total_cost": row.total_cost or 0,
                    "avg_cost_per_email": row.avg_cost_per_email or 0,
                    "email_count": row.email_count,
                    "sonnet_cost": 0,  # 需要根据 model_used 拆分
                    "haiku_cost": 0,
                }
                for row in rows
            ]

    async def get_cost_trend(self, days: int = 30) -> list[dict]:
        """
        获取成本趋势数据

        功能描述:
            按日期返回成本和邮件数量趋势。

        参数:
            days: int 类型，统计天数 (默认 30)

        返回值:
            list[dict]: 趋势数据点列表
        """
        from email_agent.storage.models import EmailAnalysis
        from sqlalchemy import select, func, cast, Date
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with self.session() as session:
            stmt = (
                select(
                    cast(EmailAnalysis.created_at, Date).label("date"),
                    func.sum(EmailAnalysis.cost).label("cost"),
                    func.count(EmailAnalysis.id).label("emails"),
                )
                .where(EmailAnalysis.created_at >= cutoff_date)
                .group_by(cast(EmailAnalysis.created_at, Date))
                .order_by(cast(EmailAnalysis.created_at, Date))
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "date": str(row.date),
                    "cost": row.cost or 0,
                    "emails": row.emails,
                }
                for row in rows
            ]

    async def get_performance_trend(self, days: int = 30) -> list[dict]:
        """
        获取性能趋势数据

        功能描述:
            按日期返回平均处理时间和邮件数量趋势。

        参数:
            days: int 类型，统计天数 (默认 30)

        返回值:
            list[dict]: 趋势数据点列表
        """
        from email_agent.storage.models import EmailAnalysis
        from sqlalchemy import select, func, cast, Date
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with self.session() as session:
            stmt = (
                select(
                    cast(EmailAnalysis.created_at, Date).label("date"),
                    func.avg(EmailAnalysis.processing_time_ms).label("avg_time"),
                    func.count(EmailAnalysis.id).label("emails"),
                )
                .where(EmailAnalysis.created_at >= cutoff_date)
                .group_by(cast(EmailAnalysis.created_at, Date))
                .order_by(cast(EmailAnalysis.created_at, Date))
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "date": str(row.date),
                    "avgTime": row.avg_time or 0,
                    "emails": row.emails,
                }
                for row in rows
            ]

    async def get_monitoring_dashboard(self) -> dict:
        """
        获取监控仪表板汇总数据

        功能描述:
            返回监控页面的完整汇总数据。

        参数:
            无

        返回值:
            dict: 包含汇总指标、最近执行、趋势数据的字典
        """
        from email_agent.storage.models import AgentExecution, EmailAnalysis
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        async with self.session() as session:
            # 今日统计
            today_stmt = select(
                func.count(AgentExecution.id).label("total_executions"),
                func.sum(func.case((AgentExecution.status == "completed", 1), else_=0)).label("successful"),
                func.sum(AgentExecution.actual_cost).label("total_cost"),
            ).where(AgentExecution.started_at >= today_start)

            today_result = await session.execute(today_stmt)
            today_row = today_result.one()

            # 平均处理时间
            avg_time_stmt = select(func.avg(EmailAnalysis.processing_time_ms)).where(
                EmailAnalysis.created_at >= today_start
            )
            avg_time_result = await session.execute(avg_time_stmt)
            avg_time = avg_time_result.scalar() or 0

            # 最近执行
            recent_stmt = (
                select(AgentExecution)
                .order_by(func.desc(AgentExecution.started_at))
                .limit(20)
            )
            recent_result = await session.execute(recent_stmt)
            recent_executions = recent_result.scalars().all()

            # 活跃 Agent 数
            active_stmt = select(func.count(func.distinct(AgentExecution.agent_name))).where(
                AgentExecution.status == "running"
            )
            active_result = await session.execute(active_stmt)
            active_agents = active_result.scalar() or 0

            # 成本趋势 (最近 7 天)
            cost_trend = await self.get_cost_trend(7)
            performance_trend = await self.get_performance_trend(7)

            total_executions = today_row.total_executions or 0
            successful = today_row.successful or 0
            total_cost = today_row.total_cost or 0

            return {
                "summary": {
                    "totalExecutions": total_executions,
                    "successRate": successful / max(1, total_executions),
                    "totalCostToday": total_cost,
                    "avgCostPerEmail": total_cost / max(1, total_executions),
                    "avgProcessingTimeMs": avg_time,
                    "activeAgents": active_agents,
                },
                "recentExecutions": [
                    {
                        "id": ex.id,
                        "task_id": ex.task_id,
                        "email_id": ex.email_id,
                        "agent_name": ex.agent_name,
                        "status": ex.status,
                        "budget_allocated": ex.budget_allocated,
                        "actual_cost": ex.actual_cost,
                        "started_at": ex.started_at.isoformat() if ex.started_at else None,
                        "completed_at": ex.completed_at.isoformat() if ex.completed_at else None,
                    }
                    for ex in recent_executions
                ],
                "costTrend": cost_trend,
                "performanceTrend": performance_trend,
            }


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
