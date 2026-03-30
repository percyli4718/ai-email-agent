"""
数据库模型模块

模块作用:
    本模块定义 SQLAlchemy 数据库模型 (ORM)。
    包含电子邮件、分类结果、报价、Agent 执行记录和提示词版本等表结构。

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
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship


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
    pass


class Email(Base):
    """
    电子邮件表模型

    作用:
        存储收到的原始电子邮件信息。
        每封邮件一条记录，用于追踪处理历史。

    表名：emails

    字段说明:
        id: str 类型，主键
            邮件唯一标识符

        raw_content: Text 类型，原始内容
            完整的邮件原始内容

        from_address: String 类型，发件人地址
            发件人的邮箱地址

        subject: String 类型，主题
            邮件主题行

        received_at: DateTime 类型，接收时间
            邮件被系统接收的时间

        processed_at: DateTime 类型，处理完成时间
            邮件被完全处理的时间

        status: String 类型，状态
            处理状态 (pending/processing/completed/failed)

    使用场景:
        - 存储收到的新邮件
        - 查询邮件处理历史
        - 追踪邮件处理状态
    """
    __tablename__ = "emails"

    id = Column(String, primary_key=True)
    raw_content = Column(Text)
    from_address = Column(String)
    subject = Column(String)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    status = Column(String)


class Classification(Base):
    """
    邮件分类结果表模型

    作用:
        存储 Layer 1 生成的邮件分类结果。
    每封邮件一条分类记录，用于追踪分类决策。

    表名：classifications

    字段说明:
        email_id: str 类型，主键/外键
            关联 emails 表的主键

        type: String 类型，邮件类型
            inquiry/complaint/status_check/other

        priority_score: Float 类型，优先级分数
            0.0-1.0 的优先级评分

        urgency: String 类型，紧急程度
            low/medium/high

        language: String 类型，语言代码
            en/pt/es/fr/de/zh/ar

        products_mentioned: JSON 类型，提及产品列表
            存储产品列表的 JSON 数组

        customer_region: String 类型，客户区域
            客户所在的国家/地区

        requires_human: Boolean 类型，是否需要人工处理
            True 表示需要人工介入

        suggested_route: String 类型，建议路由
            quote_flow/complaint_flow/status_flow/general_flow

        created_at: DateTime 类型，创建时间
            分类记录创建的时间

    使用场景:
        - 存储分类结果
        - 分析分类准确率
        - 追踪路由决策
    """
    __tablename__ = "classifications"

    email_id = Column(String, ForeignKey("emails.id"), primary_key=True)
    type = Column(String)
    priority_score = Column(Float)
    urgency = Column(String)
    language = Column(String)
    products_mentioned = Column(JSON)
    customer_region = Column(String)
    requires_human = Column(Boolean)
    suggested_route = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Quote(Base):
    """
    报价单表模型

    作用:
        存储 Layer 3 生成的报价单。
        每个报价一条记录，用于追踪报价历史。

    表名：quotes

    字段说明:
        id: str 类型，主键
            报价单唯一标识符

        email_id: str 类型，外键
            关联 emails 表的主键

        quote_json: JSON 类型，报价详情
            完整的报价 JSON 对象

        total_amount: Float 类型，总金额
            报价的总金额

        currency: String 类型，货币 (默认 USD)
            报价使用的货币

        status: String 类型，状态
            draft/sent/accepted/rejected

        created_at: DateTime 类型，创建时间
            报价单创建的时间

    使用场景:
        - 存储生成的报价单
        - 查询报价历史
        - 分析报价接受率
    """
    __tablename__ = "quotes"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.id"))
    quote_json = Column(JSON)
    total_amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentExecution(Base):
    """
    Agent 执行记录表模型

    作用:
        存储子 Agent 的执行日志。
        记录每个 Agent 的输入、输出、成本和状态。

    表名：agent_executions

    字段说明:
        id: str 类型，主键
            执行记录唯一标识符

        email_id: str 类型，外键
            关联 emails 表的主键

        agent_name: String 类型，Agent 名称
            price_agent/compliance_agent 等

        status: String 类型，执行状态
            pending/running/completed/failed

        budget_allocated: Float 类型，分配预算
            分配给该 Agent 的预算 (美元)

        actual_cost: Float 类型，实际成本
            Agent 执行的实际成本 (美元)

        input_data: JSON 类型，输入数据
            Agent 的输入参数 JSON 对象

        output_data: JSON 类型，输出数据
            Agent 的输出结果 JSON 对象

        started_at: DateTime 类型，开始时间
            Agent 开始执行的时间

        completed_at: DateTime 类型，完成时间
            Agent 完成执行的时间

    使用场景:
        - 追踪 Agent 执行情况
        - 分析 Agent 性能和成本
        - 调试 Agent 问题
    """
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.id"))
    agent_name = Column(String)
    status = Column(String)
    budget_allocated = Column(Float)
    actual_cost = Column(Float)
    input_data = Column(JSON)
    output_data = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class PromptVersion(Base):
    """
    提示词版本表模型

    作用:
        存储提示词模板的版本历史。
        用于追踪提示词的迭代和改进。

    表名：prompt_versions

    字段说明:
        id: Integer 类型，主键 (自增)
            版本记录唯一标识符

        name: String 类型，提示词名称
            例如："classifier_prompt", "quote_prompt"

        version: Integer 类型，版本号
            从 1 开始递增

        template: Text 类型，模板内容
            完整的提示词模板文本

        accuracy_score: Float 类型，准确率评分
            该版本在测试集上的准确率

        changes: Text 类型，变更说明
            相对于上一版本的变更描述

        created_at: DateTime 类型，创建时间
            版本创建的时间

    使用场景:
        - 追踪提示词版本历史
        - 对比不同版本的准确率
        - 回滚到之前的版本
    """
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    version = Column(Integer)
    template = Column(Text)
    accuracy_score = Column(Float)
    changes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
