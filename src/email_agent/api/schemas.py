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
from pydantic import BaseModel, EmailStr, Field
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


# ==================== 新增 Schema：用于 AI Email Agent 数据端点 ====================


class EmailListResponse(BaseModel):
    """
    邮件列表响应 Schema

    作用:
        定义 GET /api/emails 响应的数据结构。

    字段说明:
        emails: List[Dict] 类型，邮件列表
            邮件列表，每项包含:
            - id: 邮件 ID
            - from_address: 发件人地址
            - subject: 主题
            - preview: 预览内容
            - priority: 优先级
            - status: 处理状态
            - received_at: 接收时间 (ISO 8601 格式)
            - region: 客户区域

        total: int 类型，总数
            邮件总数

    使用场景:
        - 作为邮件列表 API 的响应模型
        - 前端展示邮件列表
    """
    emails: List[Dict]
    total: int


class Layer1Analysis(BaseModel):
    """
    Layer 1 分类结果 Schema

    作用:
        定义邮件分类分析结果的数据结构。

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
        - 作为邮件分析 API 的 Layer 1 响应
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


class Layer2Retrieval(BaseModel):
    """
    Layer 2 检索结果 Schema

    作用:
        定义向量检索结果的数据结构。

    字段说明:
        query: str 类型，检索查询
            用于检索的查询文本

        results: List[Dict] 类型，检索结果列表
            每个结果包含文档内容和相似度分数

        retrieval_time_ms: float 类型，检索耗时
            检索操作的执行时间 (毫秒)

    使用场景:
        - 作为邮件分析 API 的 Layer 2 响应
        - 前端展示检索结果
    """
    query: str
    results: List[Dict]
    retrieval_time_ms: float


class Layer3StructuredOutput(BaseModel):
    """
    Layer 3 结构化输出 Schema

    作用:
        定义结构化输出结果的数据结构。

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
        - 作为邮件分析 API 的 Layer 3 响应
        - 前端展示报价详情
    """
    quote_id: str
    items: List[Dict]
    total_amount: float
    valid_until: str
    shipping_port: str
    payment_terms: str


class EmailAnalysisResponse(BaseModel):
    """
    邮件分析响应 Schema

    作用:
        定义 GET /api/emails/{id}/analysis 响应的数据结构。
        包含 Layer 1/2/3 的完整分析结果。

    字段说明:
        email_id: str 类型，邮件 ID
            被分析的邮件 ID

        layer1_classification: Layer1Analysis 类型，Layer 1 分类结果
            邮件分类和路由建议

        layer2_retrieval: Optional[Layer2Retrieval] 类型，Layer 2 检索结果 (可选)
            向量检索结果

        layer3_output: Optional[Layer3StructuredOutput] 类型，Layer 3 结构化输出 (可选)
            生成的报价单或结构化响应

    使用场景:
        - 作为邮件分析 API 的响应模型
        - 前端展示完整的 AI 分析结果
    """
    email_id: str
    layer1_classification: Layer1Analysis
    layer2_retrieval: Optional[Layer2Retrieval] = None
    layer3_output: Optional[Layer3StructuredOutput] = None


class SubAgentStatus(BaseModel):
    """
    子 Agent 状态 Schema

    作用:
        定义子 Agent 执行状态的数据结构。

    字段说明:
        agent_name: str 类型，Agent 名称
            price_agent/compliance_agent/logistics_agent/reply_agent

        status: str 类型，执行状态
            pending/running/completed/failed

        budget_allocated: float 类型，分配预算
            分配给该 Agent 的预算 (美元)

        actual_cost: float 类型，实际成本
            Agent 执行的实际成本 (美元)

        started_at: Optional[str] 类型，开始时间 (可选)
            ISO 8601 格式的开始时间

        completed_at: Optional[str] 类型，完成时间 (可选)
            ISO 8601 格式的完成时间

        task_id: str 类型，任务 ID
            任务的唯一标识符

    使用场景:
        - 作为 Agent 状态 API 的子 Agent 响应
        - 前端展示 Agent 执行状态
    """
    agent_name: str
    status: str
    budget_allocated: float
    actual_cost: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    task_id: str


class AgentStatusResponse(BaseModel):
    """
    Agent 执行状态响应 Schema

    作用:
        定义 GET /api/agents/status 响应的数据结构。

    字段说明:
        ceo_agent_status: str 类型，CEO Agent 状态
            idle/processing/completed

        sub_agents: List[SubAgentStatus] 类型，子 Agent 状态列表
            所有子 Agent 的执行状态

        total_budget: float 类型，总预算
            分配的总预算 (美元)

        total_spent: float 类型，总消耗
            已消耗的总预算 (美元)

        budget_utilization: float 类型，预算利用率
            已用预算占总预算的比例 (0.0-1.0)

    使用场景:
        - 作为 Agent 状态 API 的响应模型
        - 前端展示 Agent 监控面板
    """
    ceo_agent_status: str
    sub_agents: List[SubAgentStatus]
    total_budget: float
    total_spent: float
    budget_utilization: float


class PromptVersion(BaseModel):
    """
    Prompt 版本 Schema

    作用:
        定义 Prompt 版本的数据结构。

    字段说明:
        version: str 类型，版本号
            例如："v1.0.0", "v1.1.0"

        created_at: str 类型，创建时间
            ISO 8601 格式的日期时间字符串

        layer: str 类型，所属层级
            layer1/layer2/layer3

        accuracy: float 类型，准确率
            该版本的准确率 (0.0-1.0)

        change_summary: str 类型，变更摘要
            本次版本的变更描述

        diff: Optional[str] 类型，变更 diff (可选)
            与上一版本的差异对比

    使用场景:
        - 作为 Prompt 版本 API 的响应项
        - 前端展示 Prompt 版本历史
    """
    version: str
    created_at: str
    layer: str
    accuracy: float
    change_summary: str
    diff: Optional[str] = None


class PromptVersionsResponse(BaseModel):
    """
    Prompt 版本历史响应 Schema

    作用:
        定义 GET /api/prompts/versions 响应的数据结构。

    字段说明:
        versions: List[PromptVersion] 类型，Prompt 版本列表
            按创建时间倒序排列的版本列表

        total_versions: int 类型，总版本数
            系统中 Prompt 版本的总数量

    使用场景:
        - 作为 Prompt 版本 API 的响应模型
        - 前端展示 Prompt 版本管理界面
    """
    versions: List[PromptVersion]
    total_versions: int


# ==================== 新增 Schema: 邮件生成器 API ====================


class GenerateEmailsRequest(BaseModel):
    """
    邮件生成请求 Schema

    作用:
        定义 POST /api/emails/generate 请求的数据结构。

    字段说明:
        count: int 类型，生成数量 (可选，默认 1)
            要生成的邮件数量，范围 1-100

        auto_process: bool 类型，是否自动处理 (可选，默认 False)
            是否生成后立即开始处理流程

        filters: Optional[Dict[str, str]] 类型，过滤条件 (可选)
            用于过滤模板的字典，如 {"region": "Europe", "type": "rfq"}

    使用场景:
        - 作为邮件生成 API 的请求模型
        - 前端提交生成请求
    """
    count: int = Field(1, ge=1, le=100)
    auto_process: bool = Field(False)
    filters: Optional[Dict[str, str]] = None


class GeneratedEmailCustomer(BaseModel):
    """
    生成邮件的客户信息 Schema

    作用:
        定义生成邮件中客户信息的数据结构。

    字段说明:
        name: str 类型，客户名称
            客户公司名称

        company: str 类型，公司名称
            与客户名称相同，用于兼容性

        email: str 类型，邮箱地址
            客户的邮箱地址

    使用场景:
        - 作为生成邮件响应中的客户信息
        - 前端展示发件人信息
    """
    name: str
    company: str
    email: str


class GeneratedEmail(BaseModel):
    """
    生成的邮件 Schema

    作用:
        定义生成邮件的数据结构。

    字段说明:
        id: str 类型，邮件 ID
            邮件的唯一标识符

        from_address: str 类型，发件人地址
            发件人的邮箱地址

        subject: str 类型，邮件主题
            生成的邮件主题

        preview: str 类型，邮件预览
            邮件正文的预览内容

        priority: str 类型，优先级
            high/medium/low

        status: str 类型，状态
            pending/processing/completed

        region: str 类型，区域
            客户所在区域

        customer: GeneratedEmailCustomer 类型，客户信息
            发件客户的详细信息

    使用场景:
        - 作为邮件生成 API 响应中的邮件项
        - 前端展示生成的邮件列表
    """
    id: str
    from_address: str
    subject: str
    preview: str
    priority: str
    status: str
    region: str
    customer: GeneratedEmailCustomer


class GeneratedEmailsResponse(BaseModel):
    """
    邮件生成响应 Schema

    作用:
        定义 POST /api/emails/generate 响应的数据结构。

    字段说明:
        generated_emails: List[GeneratedEmail] 类型，生成的邮件列表
            成功生成的邮件列表

        total: int 类型，总数
            生成的邮件总数量

        auto_process_started: bool 类型，是否开始自动处理
            表示是否已启动自动处理流程

    使用场景:
        - 作为邮件生成 API 的响应模型
        - 前端展示生成结果
    """
    generated_emails: List[GeneratedEmail]
    total: int
    auto_process_started: bool


class EmailTemplateResponse(BaseModel):
    """
    邮件模板响应 Schema

    作用:
        定义单个邮件模板的响应数据结构。

    字段说明:
        id: int 类型，模板 ID
            模板的唯一标识符

        type: str 类型，邮件类型
            inquiry/rfq/complaint/status_check

        product_name: str 类型，产品名称
            模板关联的产品名称

        region: str 类型，目标地区
            Europe/Asia/South America/Middle East

        quantity_range: str 类型，数量范围
            如 "100-500", "500-1000"

        is_active: bool 类型，是否启用
            控制模板是否可用于生成

        created_at: str 类型，创建时间
            ISO 8601 格式的日期时间字符串

        subject_template: Optional[str] 类型，主题模板 (可选)
            邮件主题模板，包含占位符

        body_template: Optional[str] 类型，正文模板 (可选)
            邮件正文模板，包含占位符

    使用场景:
        - 作为模板列表 API 响应中的模板项
        - 前端展示模板配置
        - 前端模板编辑器加载完整模板内容
    """
    id: int
    type: str
    product_name: str
    region: str
    quantity_range: str
    is_active: bool
    created_at: str
    subject_template: Optional[str] = None
    body_template: Optional[str] = None


class EmailTemplatesResponse(BaseModel):
    """
    邮件模板列表响应 Schema

    作用:
        定义 GET /api/emails/templates 响应的数据结构。

    字段说明:
        templates: List[EmailTemplateResponse] 类型，模板列表
            所有可用模板的列表

        total: int 类型，总模板数
            系统中模板的总数量

    使用场景:
        - 作为模板列表 API 的响应模型
        - 前端展示模板管理界面
    """
    templates: List[EmailTemplateResponse]
    total: int


class EmailTemplateUpdateRequest(BaseModel):
    """
    邮件模板更新请求 Schema

    作用:
        定义更新邮件模板的请求数据结构。

    字段说明:
        subject_template: Optional[str] 类型，主题模板
            可选，更新的主题模板

        body_template: Optional[str] 类型，正文模板
            可选，更新的正文模板

        is_active: Optional[bool] 类型，是否启用
            可选，启用/禁用模板

    使用场景:
        - PUT /api/emails/templates/{id} 请求体
        - 前端模板编辑器表单提交
    """
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateCreateRequest(BaseModel):
    """
    邮件模板创建请求 Schema

    作用:
        定义创建新邮件模板的请求数据结构。

    字段说明:
        type: str 类型，邮件类型
            inquiry/rfq/complaint/status_check

        product_name: str 类型，产品名称

        region: str 类型，目标地区

        quantity_range: str 类型，数量范围

        subject_template: str 类型，主题模板

        body_template: str 类型，正文模板

    使用场景:
        - POST /api/emails/templates 请求体
        - 前端创建新模板表单提交
    """
    type: str
    product_name: str
    region: str
    quantity_range: str
    subject_template: str
    body_template: str
