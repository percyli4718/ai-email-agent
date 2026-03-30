"""
API Schema 模块

模块作用:
    本模块定义 FastAPI 应用的 Pydantic 数据模式 (Schema)。
    用于 API 请求和响应的数据验证、序列化和文档生成。

使用场景:
    - 定义 API 响应的数据结构
    - 自动进行数据验证
    - 生成 OpenAPI/Swagger 文档

在项目中的位置:
    位于 src/email_agent/api/schemas.py，
    是应用 API 层的数据模式定义，
    被 routes.py 用作响应模型。
"""
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from datetime import datetime


class EmailInbox(BaseModel):
    """
    邮件列表项 Schema

    作用:
        定义邮件列表中每项的数据结构。
        用于 GET /api/emails 响应。

    字段说明:
        id: str 类型，邮件 ID
            邮件的唯一标识符

        from_address: str 类型，发件人地址
            发件人的邮箱地址

        subject: str 类型，主题
            邮件主题行

        received_at: datetime 类型，接收时间
            邮件被系统接收的时间

        status: str 类型，状态
            处理状态 (pending/processing/completed/failed)

        priority: Optional[str] 类型，优先级 (可选)
            high/medium/low

    使用场景:
        - 作为邮件列表 API 的响应模型
        - 前端展示邮件列表
    """
    id: str
    from_address: str
    subject: str
    received_at: datetime
    status: str
    priority: Optional[str] = None


class EmailDetail(EmailInbox):
    """
    邮件详情 Schema

    作用:
        定义完整邮件详情的数据结构。
        继承自 EmailInbox，添加更多详情字段。
        用于 GET /api/emails/{email_id} 响应。

    字段说明:
        raw_content: str 类型，原始内容
            完整的邮件原始内容

        classification: Optional[Dict] 类型，分类结果 (可选)
            Layer 1 生成的分类结果

        quote: Optional[Dict] 类型，报价单 (可选)
            Layer 3 生成的报价单

        agent_executions: List[Dict] 类型，Agent 执行列表
            子 Agent 的执行记录列表

    使用场景:
        - 作为邮件详情 API 的响应模型
        - 前端展示邮件完整信息
    """
    raw_content: str
    classification: Optional[Dict] = None
    quote: Optional[Dict] = None
    agent_executions: List[Dict] = []


class ClassificationResponse(BaseModel):
    """
    分类结果响应 Schema

    作用:
        定义邮件分类结果的响应数据结构。
        用于分类 API 的响应模型。

    字段说明:
        type: str 类型，邮件类型
            inquiry/complaint/status_check/other

        priority_score: float 类型，优先级分数
            0.0-1.0 的优先级评分

        urgency: str 类型，紧急程度
            low/medium/high

        language: str 类型，语言代码
            en/pt/es/fr/de/zh/ar

        products_mentioned: List[str] 类型，提及产品列表
            邮件中提及的产品名称列表

        customer_region: str 类型，客户区域
            客户所在的国家/地区

        requires_human: bool 类型，是否需要人工处理
            True 表示需要人工介入

        suggested_route: str 类型，建议路由
            quote_flow/complaint_flow/status_flow/general_flow

    使用场景:
        - 作为分类 API 的响应模型
        - 前端展示分类结果
    """
    type: str
    priority_score: float
    urgency: str
    language: str
    products_mentioned: List[str]
    customer_region: str
    requires_human: bool
    suggested_route: str


class QuoteResponse(BaseModel):
    """
    报价响应 Schema

    作用:
        定义报价单的响应数据结构。
        用于报价 API 的响应模型。

    字段说明:
        quote_id: str 类型，报价单 ID
            报价单的唯一标识符

        items: List[Dict] 类型，报价项目列表
            包含产品、数量、单价等信息

        total_amount: float 类型，总金额
            报价的总金额 (USD)

        valid_until: str 类型，有效期至
            报价的截止日期 (YYYY-MM-DD)

        shipping_port: str 类型，发货港口
            货物出发港口

        payment_terms: str 类型，付款条款
            例如："30% advance, 70% against B/L"

    使用场景:
        - 作为报价 API 的响应模型
        - 前端展示报价详情
    """
    quote_id: str
    items: List[Dict]
    total_amount: float
    valid_until: str
    shipping_port: str
    payment_terms: str


class AgentStatus(BaseModel):
    """
    Agent 状态 Schema

    作用:
        定义 Agent 执行状态的数据结构。
        用于 Agent 监控 API 的响应模型。

    字段说明:
        agent_name: str 类型，Agent 名称
            price_agent/compliance_agent 等

        status: str 类型，执行状态
            pending/running/completed/failed

        budget_allocated: float 类型，分配预算
            分配给该 Agent 的预算 (美元)

        actual_cost: float 类型，实际成本
            Agent 执行的实际成本 (美元)

        started_at: Optional[datetime] 类型，开始时间 (可选)
            Agent 开始执行的时间

        completed_at: Optional[datetime] 类型，完成时间 (可选)
            Agent 完成执行的时间

    使用场景:
        - 作为 Agent 状态 API 的响应模型
        - 前端展示 Agent 执行状态
    """
    agent_name: str
    status: str
    budget_allocated: float
    actual_cost: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MetricsResponse(BaseModel):
    """
    指标响应 Schema

    作用:
        定义可观测性指标的响应数据结构。
        用于 GET /api/metrics 响应。

    字段说明:
        emails_today: int 类型，今日邮件数
            今天处理的邮件总数

        avg_processing_time_ms: float 类型，平均处理时间
            平均每封邮件的处理时间 (毫秒)

        avg_cost_per_email: float 类型，平均每封邮件成本
            每封邮件的平均 API 成本 (美元)

        classification_accuracy: float 类型，分类准确率
            分类模型的准确率

        sonnet_routing_rate: float 类型，Sonnet 路由率
            路由到 Sonnet 模型的比例 (目标 0.80)

        prompt_versions: int 类型，提示词版本数
            系统中提示词版本的数量

    使用场景:
        - 作为指标 API 的响应模型
        - 前端展示系统性能指标
    """
    emails_today: int
    avg_processing_time_ms: float
    avg_cost_per_email: float
    classification_accuracy: float
    sonnet_routing_rate: float
    prompt_versions: int


class TraceResponse(BaseModel):
    """
    追踪响应 Schema

    作用:
        定义分布式追踪的响应数据结构。
        用于 GET /api/traces 响应。

    字段说明:
        id: str 类型，跨度 ID
            追踪跨度的唯一标识符

        name: str 类型，跨度名称
            例如："classify_email", "generate_quote"

        duration_ms: Optional[float] 类型，持续时间 (可选)
            跨度持续时间 (毫秒)

        tags: Dict[str, str] 类型，标签字典
            跨度的元数据键值对

        children: List[TraceResponse] 类型，子跨度列表
            嵌套的子追踪跨度

    使用场景:
        - 作为追踪 API 的响应模型
        - 前端展示追踪树形结构

    递归定义:
        使用 model_rebuild() 重建模型以支持递归引用
    """
    id: str
    name: str
    duration_ms: Optional[float]
    tags: Dict[str, str]
    children: List["TraceResponse"] = []


# 重建模型以支持递归引用
# Pydantic v2 需要在定义递归模型后调用 model_rebuild()
TraceResponse.model_rebuild()
