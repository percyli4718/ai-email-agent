"""
数据库模型模块

模块作用:
    本模块定义 SQLAlchemy 数据库模型 (ORM)。
    使用 SQLAlchemy 2.0 异步语法，包含客户、邮件、邮件分析、Agent 执行记录和提示词版本等表结构。

使用场景:
    - 定义数据库表结构
    - 通过 ORM 进行数据库操作
    - 存储和查询邮件处理历史

在项目中的位置:
    位于 src/email_agent/storage/models.py，
    是应用存储层的数据模型定义，
    被 database.py 和其他模块使用进行数据持久化。
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    Integer,
    ForeignKey,
    Index,
    event,
    text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)


class Base(DeclarativeBase):
    """
    SQLAlchemy 模型基类

    作用:
        所有 ORM 模型的父类。
        使用 DeclarativeBase 模式定义模型。

    使用场景:
        - 继承此类定义数据模型
        - 统一配置模型元数据

    属性:
        __abstract__: True 表示这是抽象基类，不创建表
    """
    # 类型注解映射配置
    type_annotation_map = {
        dict[str, Any]: JSON,
        Optional[dict[str, Any]]: JSON,
    }


class Customer(Base):
    """
    客户信息表模型

    作用:
        存储客户基本信息。
        每个客户一条记录，用于关联邮件和历史交互。

    表名：customers

    字段说明:
        id: int 类型，主键 (自增)
            客户唯一标识符

        name: str 类型，客户名称
            客户姓名或公司名称

        email: str 类型，邮箱地址 (唯一索引)
            客户邮箱，用于关联邮件

        tier: str 类型，客户等级
            A/B/C 三级，A 级为最重要客户

        region: str 类型，所在区域
            客户所在的国家/地区 (如：brazil, eu, us, asia)

        created_at: datetime 类型，创建时间
            客户记录创建的时间

    关系:
        emails: 一对多关系，一个客户可以有多封邮件

    使用场景:
        - 查询客户等级以决定优先级
        - 根据区域应用不同的定价策略
        - 追踪客户历史交互记录

    索引设计:
        - ix_customers_email: 邮箱唯一索引，加速根据邮箱查询客户
        - ix_customers_tier: 客户等级索引，用于按等级筛选
        - ix_customers_region: 区域索引，用于按区域统计
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(1), default="C")  # A/B/C tier
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系：一个客户可以有多封邮件
    emails: Mapped[List["Email"]] = relationship(
        "Email",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_customers_tier", "tier"),
        Index("ix_customers_region", "region"),
    )

    def __repr__(self) -> str:
        """返回客户的字符串表示，用于调试"""
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}', tier='{self.tier}')>"


class Email(Base):
    """
    电子邮件表模型

    作用:
        存储收到的原始电子邮件信息。
        每封邮件一条记录，用于追踪处理历史。

    表名：emails

    字段说明:
        id: str 类型，主键
            邮件唯一标识符 (如：email_001)

        from_address: str 类型，发件人地址
            发件人的邮箱地址

        subject: str 类型，主题
            邮件主题行

        body: Text 类型，邮件正文
            完整的邮件正文内容

        received_at: datetime 类型，接收时间
            邮件被系统接收的时间

        priority: str 类型，优先级
            high/medium/low

        status: str 类型，处理状态
            pending/processing/completed/failed

        region: str 类型，区域
            邮件来源的区域 (冗余字段，便于查询)

        customer_id: int 类型，外键
            关联 customers 表的主键

    关系:
        customer: 多对一关系，多封邮件属于一个客户
        analysis: 一对一关系，一封邮件对应一个分析结果
        agent_executions: 一对多关系，一封邮件可以有多个 Agent 执行记录

    使用场景:
        - 存储收到的新邮件
        - 查询邮件处理历史
        - 追踪邮件处理状态

    索引设计:
        - ix_emails_status: 状态索引，用于查询待处理邮件
        - ix_emails_priority: 优先级索引，用于按优先级筛选
        - ix_emails_received_at: 接收时间索引，用于按时间范围查询
        - ix_emails_region: 区域索引，用于按区域统计
        - ix_emails_customer_id: 客户 ID 索引，用于关联查询
    """
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # high/medium/low
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/processing/completed/failed
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 关系：多封邮件属于一个客户
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer",
        back_populates="emails"
    )

    # 关系：一封邮件对应一个分析结果
    analysis: Mapped[Optional["EmailAnalysis"]] = relationship(
        "EmailAnalysis",
        back_populates="email",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # 关系：一封邮件可以有多个 Agent 执行记录
    agent_executions: Mapped[List["AgentExecution"]] = relationship(
        "AgentExecution",
        back_populates="email",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("ix_emails_status", "status"),
        Index("ix_emails_priority", "priority"),
        Index("ix_emails_received_at", "received_at"),
        Index("ix_emails_region", "region"),
    )

    def __repr__(self) -> str:
        """返回邮件的字符串表示，用于调试"""
        return f"<Email(id='{self.id}', subject='{self.subject}', status='{self.status}', priority='{self.priority}')>"


class EmailAnalysis(Base):
    """
    邮件 AI 分析结果表模型

    作用:
        存储 Layer 1/2/3 的完整 AI 分析结果。
        每封邮件一条分析记录，用于追踪分析决策和成本。

    表名：email_analysis

    字段说明:
        id: int 类型，主键 (自增)
            分析记录唯一标识符

        email_id: str 类型，外键 (唯一)
            关联 emails 表的主键

        layer1_classification: JSON 类型，Layer 1 分类结果
            存储分类器输出的完整 JSON 对象，包含：
            - type: inquiry/complaint/status_check/other
            - priority_score: 0.0-1.0 优先级评分
            - urgency: low/medium/high
            - language: en/pt/es/fr/de/zh/ar
            - products_mentioned: 产品列表
            - customer_region: 客户区域
            - requires_human: 是否需要人工处理
            - suggested_route: 建议路由

        layer2_retrieval: JSON 类型，Layer 2 检索结果
            存储检索器输出的完整 JSON 对象，包含：
            - query: 检索查询语句
            - results: 检索结果列表 (doc_id, content, similarity)
            - retrieval_time_ms: 检索耗时

        layer3_output: JSON 类型，Layer 3 生成结果
            存储生成器输出的完整 JSON 对象，包含：
            - quote_id: 报价单 ID
            - items: 报价项目列表
            - total_amount: 总金额
            - valid_until: 报价有效期
            - shipping_port: 起运港
            - payment_terms: 付款条款

        processing_time_ms: float 类型，处理耗时
            完整分析流程的耗时 (毫秒)

        cost: float 类型，成本
            AI 调用的总成本 (美元)

        model_used: str 类型，使用的模型
            claude-sonnet-4 / claude-opus-4

        created_at: datetime 类型，创建时间
            分析记录创建的时间

    关系:
        email: 一对一关系，一个分析结果属于一封邮件

    使用场景:
        - 存储 AI 分析结果
        - 分析分类准确率
        - 追踪模型使用成本
        - 调试 Agent 问题

    索引设计:
        - ix_email_analysis_email_id: 邮件 ID 唯一索引
        - ix_email_analysis_created_at: 创建时间索引，用于按时间范围查询
    """
    __tablename__ = "email_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("emails.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Layer 1: 分类结果 (JSONB)
    layer1_classification: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Layer 1 classification result"
    )

    # Layer 2: 检索结果 (JSONB)
    layer2_retrieval: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Layer 2 retrieval result"
    )

    # Layer 3: 生成结果 (JSONB)
    layer3_output: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Layer 3 structured output"
    )

    # 执行指标
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系：一个分析结果属于一封邮件
    email: Mapped["Email"] = relationship(
        "Email",
        back_populates="analysis"
    )

    # 索引
    __table_args__ = (
        Index("ix_email_analysis_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回分析结果的字符串表示，用于调试"""
        return f"<EmailAnalysis(id={self.id}, email_id='{self.email_id}', cost={self.cost}, model='{self.model_used}')>"


class AgentExecution(Base):
    """
    Agent 执行记录表模型

    作用:
        存储子 Agent 的执行日志。
        记录每个 Agent 的任务、状态、成本和执行时间。

    表名：agent_executions

    字段说明:
        id: int 类型，主键 (自增)
            执行记录唯一标识符

        task_id: str 类型，任务 ID
            Agent 任务的唯一标识符 (如：task_001)

        agent_name: str 类型，Agent 名称
            price_agent / compliance_agent / logistics_agent / reply_agent

        status: str 类型，执行状态
            pending/running/completed/failed/budget_killed

        budget_allocated: float 类型，分配预算
            分配给该 Agent 的预算 (美元)

        actual_cost: float 类型，实际成本
            Agent 执行的实际成本 (美元)

        started_at: datetime 类型，开始时间
            Agent 开始执行的时间

        completed_at: datetime 类型，完成时间
            Agent 完成执行的时间

        email_id: str 类型，外键
            关联 emails 表的主键

        input_data: JSON 类型，输入数据
            Agent 的输入参数 JSON 对象

        output_data: JSON 类型，输出数据
            Agent 的输出结果 JSON 对象

        error_message: str 类型，错误信息
            执行失败时的错误信息

    关系:
        email: 多对一关系，多个 Agent 执行记录属于一封邮件

    使用场景:
        - 追踪 Agent 执行情况
        - 分析 Agent 性能和成本
        - 调试 Agent 问题
        - 预算使用统计

    索引设计:
        - ix_agent_executions_email_id: 邮件 ID 索引，用于关联查询
        - ix_agent_executions_status: 状态索引，用于查询执行中的 Agent
        - ix_agent_executions_task_id: 任务 ID 索引，用于追踪特定任务
        - ix_agent_executions_started_at: 开始时间索引，用于按时间范围查询
    """
    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    budget_allocated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 外键关联
    email_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("emails.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 关系：多个 Agent 执行记录属于一封邮件
    email: Mapped[Optional["Email"]] = relationship(
        "Email",
        back_populates="agent_executions"
    )

    # 输入输出数据 (JSON)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 索引
    __table_args__ = (
        Index("ix_agent_executions_status", "status"),
        Index("ix_agent_executions_started_at", "started_at"),
    )

    def __repr__(self) -> str:
        """返回 Agent 执行记录的字符串表示，用于调试"""
        return f"<AgentExecution(id={self.id}, task_id='{self.task_id}', agent='{self.agent_name}', status='{self.status}', cost={self.actual_cost})>"


class PromptVersion(Base):
    """
    提示词版本表模型

    作用:
        存储提示词模板的版本历史。
        用于追踪提示词的迭代和改进。

    表名：prompt_versions

    字段说明:
        id: int 类型，主键 (自增)
            版本记录唯一标识符

        name: str 类型，提示词名称
            例如："classifier_prompt", "quote_prompt"

        version: str 类型，版本号
            语义化版本号 (如：v1.0.0, v1.2.0)

        layer: str 类型，所属层
            layer1 / layer2 / layer3

        template: Text 类型，模板内容
            完整的提示词模板文本

        accuracy_score: float 类型，准确率评分
            该版本在测试集上的准确率 (0.0-1.0)

        changes: Text 类型，变更说明
            相对于上一版本的变更描述

        diff: Text 类型，代码 diff
            相对于上一版本的具体 diff

        created_at: datetime 类型，创建时间
            版本创建的时间

    使用场景:
        - 追踪提示词版本历史
        - 对比不同版本的准确率
        - 回滚到之前的版本
        - Prompt 进化分析

    索引设计:
        - ix_prompt_versions_name: 名称索引，用于查询特定提示词的版本历史
        - ix_prompt_versions_layer: 层索引，用于按层筛选
        - ix_prompt_versions_created_at: 创建时间索引，用于按时间排序
    """
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    layer: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # layer1/layer2/layer3
    template: Mapped[str] = mapped_column(Text, nullable=False)
    accuracy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    changes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    diff: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index("ix_prompt_versions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回提示词版本的字符串表示，用于调试"""
        return f"<PromptVersion(id={self.id}, name='{self.name}', version='{self.version}', layer='{self.layer}', accuracy={self.accuracy_score})>"


class PricingPolicy(Base):
    """
    产品定价政策表模型

    作用:
        存储产品在不同区域的定价政策。
        支持基础价格、折扣率和多币种定价。

    表名：pricing_policies

    字段说明:
        id: int 类型，主键 (自增)
        product_name: str 类型，产品名称
        region: str 类型，适用区域
        base_price: float 类型，基础价格
        discount_rate: float 类型，折扣率 (0.0-1.0)
        currency: str 类型，币种 (默认 USD)
        effective_date: datetime 类型，生效日期
        expiry_date: datetime 类型，过期日期
        created_at: datetime 类型，创建时间

    索引设计:
        - ix_pricing_policy_product_region: 产品 + 区域唯一索引
    """
    __tablename__ = "pricing_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_rate: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 索引：产品 + 区域唯一组合
    __table_args__ = (
        Index("ix_pricing_policy_product_region", "product_name", "region", unique=True),
    )

    def __repr__(self) -> str:
        """返回定价政策的字符串表示"""
        return f"<PricingPolicy(product='{self.product_name}', region='{self.region}', price={self.base_price})>"


class ComplianceRequirement(Base):
    """
    合规要求表模型

    作用:
        存储各区域/国家的药品进口合规要求。
        包括认证、许可等要求类型。

    表名：compliance_requirements

    字段说明:
        id: int 类型，主键 (自增)
        region: str 类型，适用区域
        product_category: str 类型，产品类别（可选）
        requirement_type: str 类型，要求类型 (certification/license/etc)
        requirement_name: str 类型，要求名称
        description: str 类型，描述说明
        mandatory: bool 类型，是否强制要求
        created_at: datetime 类型，创建时间

    索引设计:
        - ix_compliance_region_category: 区域 + 产品类别索引
    """
    __tablename__ = "compliance_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    product_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    requirement_type: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 索引：区域 + 产品类别
    __table_args__ = (
        Index("ix_compliance_region_category", "region", "product_category"),
    )

    def __repr__(self) -> str:
        """返回合规要求的字符串表示"""
        return f"<ComplianceRequirement(region='{self.region}', type='{self.requirement_type}', name='{self.requirement_name}')>"


# ==================== 数据库初始化辅助函数 ====================

async def init_db_tables(engine) -> None:
    """
    初始化数据库表

    功能描述:
        创建所有模型对应的数据库表。
        在应用启动时调用。

    参数:
        engine: SQLAlchemy 异步引擎

    返回值:
        无

    异常:
        无

    使用示例:
        from email_agent.storage.database import get_database
        from email_agent.storage.models import init_db_tables

        db = get_database(settings)
        await init_db_tables(db.engine)
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    # 确保传入的是异步引擎
    if not isinstance(engine, AsyncEngine):
        raise TypeError("Expected an AsyncEngine instance")

    # 导入 Base 以注册所有模型
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_tables(engine) -> None:
    """
    删除所有数据库表

    功能描述:
        删除所有模型对应的数据库表。
        仅在测试或重置数据时调用。

    参数:
        engine: SQLAlchemy 异步引擎

    返回值:
        无

    异常:
        无
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
