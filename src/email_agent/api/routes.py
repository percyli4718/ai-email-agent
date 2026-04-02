"""
API 路由模块

模块作用:
    本模块定义 FastAPI 应用的所有 API 路由端点。
    提供邮件查询、指标查看、追踪查看和健康检查等功能。

使用场景:
    - 前端应用调用 API 获取数据
    - 监控系统调用健康检查端点
    - 开发者调试和测试

在项目中的位置:
    位于 src/email_agent/api/routes.py，
    是应用 API 层的路由定义，
    依赖 schemas.py 定义数据模式，
    依赖 observability 模块获取指标和追踪数据。
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Body
from fastapi.responses import Response
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from email_agent.api.schemas import (
    EmailInbox,
    EmailDetail,
    MetricsResponse,
    TraceResponse,
    EmailListResponse,
    EmailAnalysisResponse,
    Layer1Analysis,
    Layer2Retrieval,
    Layer3StructuredOutput,
    AgentStatusResponse,
    SubAgentStatus,
    PromptVersionsResponse,
    PromptVersion,
    GenerateEmailsRequest,
    GeneratedEmailsResponse,
    GeneratedEmail,
    GeneratedEmailCustomer,
    EmailTemplateResponse,
    EmailTemplatesResponse,
    EmailTemplateUpdateRequest,
    EmailTemplateCreateRequest,
    QuoteSchema,
    QuoteListResponse,
    QuoteGenerateRequest,
    QuoteGenerateResponse,
    WorkflowResponse,
    WorkflowTransitionRequest,
    RetrievalResultResponse,
)
from email_agent.observability.metrics import metrics
from email_agent.observability.tracing import tracer
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate, Email as EmailModel
from email_agent.generator.email_generator import EmailGenerator
from email_agent.generator.template_service import EmailTemplateService
from email_agent.config import settings

router = APIRouter()

# 获取数据库实例
db = get_database(settings)


# ==================== Mock 数据 ====================

MOCK_EMAILS = [
    {
        "id": "email_001",
        "from_address": "john.smith@pharmacom.co.uk",
        "subject": "Request for Quote - Pharmaceutical Products",
        "preview": "Dear Supplier, We are interested in purchasing the following products...",
        "priority": "high",
        "status": "completed",
        "received_at": "2025-03-30T09:15:00Z",
        "region": "Europe"
    },
    {
        "id": "email_002",
        "from_address": "maria.garcia@salud.es",
        "subject": "Order Status Inquiry - Shipment #12345",
        "preview": "Hello, Could you please provide an update on our order...",
        "priority": "medium",
        "status": "completed",
        "received_at": "2025-03-30T08:30:00Z",
        "region": "Europe"
    },
    {
        "id": "email_003",
        "from_address": "david.chen@healthcare.tw",
        "subject": "Product Quality Complaint - Batch #ABC789",
        "preview": "We regret to inform you that we have encountered an issue...",
        "priority": "high",
        "status": "processing",
        "received_at": "2025-03-30T07:45:00Z",
        "region": "Asia"
    },
    {
        "id": "email_004",
        "from_address": "ahmed.hassan@medpharm.ae",
        "subject": "New Partnership Opportunity",
        "preview": "We are a leading pharmaceutical distributor in the Middle East...",
        "priority": "low",
        "status": "pending",
        "received_at": "2025-03-30T06:00:00Z",
        "region": "Middle East"
    },
    {
        "id": "email_005",
        "from_address": "ana.silva@pharma.br",
        "subject": "RFQ: Antibiotics and Painkillers",
        "preview": "Good day, We would like to request a quote for the following...",
        "priority": "high",
        "status": "completed",
        "received_at": "2025-03-29T18:20:00Z",
        "region": "South America"
    }
]

MOCK_ANALYSIS = {
    "email_001": {
        "layer1_classification": {
            "type": "inquiry",
            "priority_score": 0.85,
            "urgency": "high",
            "language": "en",
            "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 250mg"],
            "customer_region": "Europe",
            "requires_human": False,
            "suggested_route": "quote_flow"
        },
        "layer2_retrieval": {
            "query": "pharmaceutical products quote paracetamol ibuprofen amoxicillin",
            "results": [
                {"doc_id": "prod_001", "content": "Paracetamol 500mg - $2.50/box, MOQ: 1000 boxes", "similarity": 0.92},
                {"doc_id": "prod_002", "content": "Ibuprofen 400mg - $3.20/box, MOQ: 500 boxes", "similarity": 0.89},
                {"doc_id": "prod_003", "content": "Amoxicillin 250mg - $4.80/box, MOQ: 300 boxes", "similarity": 0.87}
            ],
            "retrieval_time_ms": 45.2
        },
        "layer3_output": {
            "quote_id": "QT-2025-001",
            "items": [
                {"product": "Paracetamol 500mg", "quantity": 1000, "unit_price": 2.50, "subtotal": 2500.00},
                {"product": "Ibuprofen 400mg", "quantity": 500, "unit_price": 3.20, "subtotal": 1600.00},
                {"product": "Amoxicillin 250mg", "quantity": 300, "unit_price": 4.80, "subtotal": 1440.00}
            ],
            "total_amount": 5540.00,
            "valid_until": "2025-04-30",
            "shipping_port": "Shanghai, China",
            "payment_terms": "30% advance, 70% against B/L"
        }
    },
    "email_002": {
        "layer1_classification": {
            "type": "status_check",
            "priority_score": 0.60,
            "urgency": "medium",
            "language": "en",
            "products_mentioned": [],
            "customer_region": "Europe",
            "requires_human": False,
            "suggested_route": "status_flow"
        },
        "layer2_retrieval": None,
        "layer3_output": None
    },
    "email_003": {
        "layer1_classification": {
            "type": "complaint",
            "priority_score": 0.95,
            "urgency": "high",
            "language": "en",
            "products_mentioned": ["Product Batch #ABC789"],
            "customer_region": "Asia",
            "requires_human": True,
            "suggested_route": "complaint_flow"
        },
        "layer2_retrieval": {
            "query": "product quality complaint batch ABC789",
            "results": [
                {"doc_id": "qa_001", "content": "Quality Complaint Handling Procedure - Section 4.2", "similarity": 0.88},
                {"doc_id": "batch_001", "content": "Batch #ABC789 - Production Date: 2025-02-15, QC Passed", "similarity": 0.85}
            ],
            "retrieval_time_ms": 38.7
        },
        "layer3_output": None
    }
}

MOCK_AGENT_STATUS = {
    "ceo_agent_status": "processing",
    "sub_agents": [
        {
            "agent_name": "price_agent",
            "status": "completed",
            "budget_allocated": 0.10,
            "actual_cost": 0.08,
            "started_at": "2025-03-30T09:16:00Z",
            "completed_at": "2025-03-30T09:16:15Z",
            "task_id": "task_001"
        },
        {
            "agent_name": "compliance_agent",
            "status": "completed",
            "budget_allocated": 0.15,
            "actual_cost": 0.12,
            "started_at": "2025-03-30T09:16:15Z",
            "completed_at": "2025-03-30T09:16:45Z",
            "task_id": "task_002"
        },
        {
            "agent_name": "logistics_agent",
            "status": "running",
            "budget_allocated": 0.12,
            "actual_cost": 0.05,
            "started_at": "2025-03-30T09:16:45Z",
            "completed_at": None,
            "task_id": "task_003"
        },
        {
            "agent_name": "reply_agent",
            "status": "pending",
            "budget_allocated": 0.08,
            "actual_cost": 0.00,
            "started_at": None,
            "completed_at": None,
            "task_id": "task_004"
        }
    ],
    "total_budget": 0.45,
    "total_spent": 0.25,
    "budget_utilization": 0.56
}

MOCK_PROMPT_VERSIONS = [
    {
        "version": "v1.2.0",
        "created_at": "2025-03-28T10:00:00Z",
        "layer": "layer1",
        "accuracy": 0.94,
        "change_summary": "Improved product extraction accuracy",
        "diff": "+ Added few-shot examples for product recognition\n+ Enhanced region detection logic"
    },
    {
        "version": "v1.1.0",
        "created_at": "2025-03-25T14:30:00Z",
        "layer": "layer1",
        "accuracy": 0.91,
        "change_summary": "Added urgency detection",
        "diff": "+ New urgency field in output\n+ Updated prompt instructions"
    },
    {
        "version": "v1.0.0",
        "created_at": "2025-03-20T09:00:00Z",
        "layer": "layer1",
        "accuracy": 0.88,
        "change_summary": "Initial release",
        "diff": None
    },
    {
        "version": "v1.0.0",
        "created_at": "2025-03-20T09:00:00Z",
        "layer": "layer3",
        "accuracy": 0.92,
        "change_summary": "Initial release - Quote generation",
        "diff": None
    }
]


# ==================== 邮件生成器端点 ====================
# 注意：这些端点必须在 /emails/{email_id} 之前定义，因为 FastAPI 按顺序匹配路由


@router.post("/emails/generate", response_model=GeneratedEmailsResponse)
async def generate_emails(request: GenerateEmailsRequest) -> GeneratedEmailsResponse:
    """
    生成测试邮件

    参数:
        request: GenerateEmailsRequest 类型，生成请求
            - count: 生成数量 (1-100)
            - auto_process: 是否自动处理
            - filters: 过滤条件

    返回:
        GeneratedEmailsResponse: 包含生成的邮件列表和总数

    使用场景:
        - 生成测试邮件用于系统测试
        - 批量生成模拟邮件数据
    """
    from email_agent.storage.models import Email as EmailModel
    from sqlalchemy import insert
    from datetime import datetime

    # 初始化服务
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)

    # 生成邮件
    emails_data = await generator.generate_emails(request.count)

    # 转换为响应格式并保存到数据库
    generated_emails = []
    for email_data in emails_data:
        # 保存客户到数据库
        customer = await db.get_or_create_customer(
            email=email_data["from_email"],
            defaults={
                "name": email_data["from_name"],
                "region": email_data["region"],
            }
        )

        # 保存邮件到数据库
        async with db.session() as session:
            stmt = insert(EmailModel).values(
                id=email_data["email_id"],
                customer_id=customer.id,
                subject=email_data["subject"],
                body=email_data["body"],
                from_address=email_data["from_email"],
                priority=email_data["priority"],
                status="pending",
                received_at=datetime.utcnow(),
            )
            await session.execute(stmt)
            await session.commit()

        # 构建生成的邮件对象
        generated_email = GeneratedEmail(
            id=email_data["email_id"],
            from_address=email_data["from_email"],
            subject=email_data["subject"],
            preview=email_data["body"][:200] + "..." if len(email_data["body"]) > 200 else email_data["body"],
            priority=email_data["priority"],
            status="pending",
            region=email_data["region"],
            customer=GeneratedEmailCustomer(
                name=email_data["from_name"],
                company=email_data["from_name"],
                email=email_data["from_email"],
            )
        )
        generated_emails.append(generated_email)

    return GeneratedEmailsResponse(
        generated_emails=generated_emails,
        total=len(generated_emails),
        auto_process_started=request.auto_process
    )


@router.get("/emails/templates", response_model=EmailTemplatesResponse)
async def list_templates() -> EmailTemplatesResponse:
    """
    获取所有邮件模板

    返回:
        EmailTemplatesResponse: 包含模板列表和总数

    使用场景:
        - 前端展示可用模板列表
        - 管理后台配置模板
    """
    # 初始化服务
    template_service = EmailTemplateService(db)

    # 获取所有模板
    templates = await template_service.get_all_templates()

    # 转换为响应格式
    template_responses = [
        EmailTemplateResponse(
            id=template.id,
            type=template.type,
            product_name=template.product_name,
            region=template.region,
            quantity_range=template.quantity_range,
            is_active=template.is_active,
            created_at=template.created_at.isoformat() if template.created_at else "",
            subject_template=template.subject_template,
            body_template=template.body_template,
        )
        for template in templates
    ]

    return EmailTemplatesResponse(
        templates=template_responses,
        total=len(template_responses)
    )


@router.get("/emails/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(template_id: int):
    """
    获取单个邮件模板详情

    参数:
        template_id: int 类型，模板 ID

    返回:
        EmailTemplateResponse: 包含模板详情

    使用场景:
        - 前端模板编辑器加载
        - 查看模板完整内容
    """
    from sqlalchemy import select

    async with db.session() as session:
        stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    return EmailTemplateResponse(
        id=template.id,
        type=template.type,
        product_name=template.product_name,
        region=template.region,
        quantity_range=template.quantity_range,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        subject_template=template.subject_template,
        body_template=template.body_template,
    )


@router.put("/emails/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(template_id: int, request: EmailTemplateUpdateRequest):
    """
    更新邮件模板

    参数:
        template_id: int 类型，模板 ID
        request: EmailTemplateUpdateRequest 类型，更新请求

    返回:
        EmailTemplateResponse: 更新后的模板

    使用场景:
        - 前端模板编辑器保存
        - 启用/禁用模板
    """
    from sqlalchemy import select, update

    async with db.session() as session:
        # 检查模板是否存在
        stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # 更新字段
        update_data = {}
        if request.subject_template is not None:
            update_data["subject_template"] = request.subject_template
        if request.body_template is not None:
            update_data["body_template"] = request.body_template
        if request.is_active is not None:
            update_data["is_active"] = request.is_active

        if update_data:
            stmt = update(EmailTemplate).where(EmailTemplate.id == template_id).values(**update_data)
            await session.execute(stmt)
            await session.commit()

        # 重新查询
        stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
        result = await session.execute(stmt)
        updated_template = result.scalar_one_or_none()

    return EmailTemplateResponse(
        id=updated_template.id,
        type=updated_template.type,
        product_name=updated_template.product_name,
        region=updated_template.region,
        quantity_range=updated_template.quantity_range,
        is_active=updated_template.is_active,
        created_at=updated_template.created_at.isoformat() if updated_template.created_at else "",
    )


@router.post("/emails/templates", response_model=EmailTemplateResponse)
async def create_template(request: EmailTemplateCreateRequest):
    """
    创建新邮件模板

    参数:
        request: EmailTemplateCreateRequest 类型，创建请求

    返回:
        EmailTemplateResponse: 新创建的模板

    使用场景:
        - 前端创建新模板
        - 批量导入模板
    """
    from sqlalchemy import insert, select

    async with db.session() as session:
        # 插入新模板
        stmt = insert(EmailTemplate).values(
            type=request.type,
            product_name=request.product_name,
            region=request.region,
            quantity_range=request.quantity_range,
            subject_template=request.subject_template,
            body_template=request.body_template,
            is_active=True,
        )
        result = await session.execute(stmt)
        await session.commit()

        template_id = result.inserted_primary_key[0]

        # 查询新创建的模板
        stmt = select(EmailTemplate).where(EmailTemplate.id == template_id)
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()

    return EmailTemplateResponse(
        id=template.id,
        type=template.type,
        product_name=template.product_name,
        region=template.region,
        quantity_range=template.quantity_range,
        is_active=template.is_active,
        created_at=template.created_at.isoformat() if template.created_at else "",
        subject_template=template.subject_template,
        body_template=template.body_template,
    )


@router.delete("/emails/templates/{template_id}")
async def delete_template(template_id: int):
    """
    删除邮件模板

    参数:
        template_id: int 类型，模板 ID

    返回:
        删除成功返回 204

    使用场景:
        - 前端删除不需要的模板
        - 清理过期模板
    """
    from sqlalchemy import delete

    async with db.session() as session:
        stmt = delete(EmailTemplate).where(EmailTemplate.id == template_id)
        result = await session.execute(stmt)
        await session.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    return {"message": f"Template {template_id} deleted"}


# ==================== 数据端点 ====================


@router.get("/emails", response_model=EmailListResponse)
async def list_emails(status: str = "all", limit: int = 50):
    """
    获取邮件列表

    参数:
        status: str 类型，过滤状态 (默认"all")
        limit: int 类型，返回数量限制 (默认 50)

    返回:
        EmailListResponse: 包含 emails 列表和 total 总数
    """
    # 从数据库获取邮件列表
    emails = await db.get_all_emails(limit=limit)

    # 状态过滤
    if status != "all":
        emails = [e for e in emails if e["status"] == status]

    return {"emails": emails, "total": len(emails)}


@router.get("/emails/{email_id}/analysis", response_model=EmailAnalysisResponse)
async def get_email_analysis(email_id: str):
    """
    获取指定邮件的 AI 分析结果

    参数:
        email_id: str 类型，邮件唯一标识符

    返回:
        EmailAnalysisResponse: 包含 Layer 1/2/3 分析结果
    """
    # 从数据库获取分析结果
    analysis = await db.get_email_analysis(email_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis not found for email {email_id}")

    return EmailAnalysisResponse(
        email_id=email_id,
        layer1_classification=analysis.get("layer1_classification"),
        layer2_retrieval=analysis.get("layer2_retrieval"),
        layer3_output=analysis.get("layer3_output")
    )


@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """获取邮件详情"""
    # 从数据库获取邮件详情
    email = await db.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email


@router.get("/emails/{email_id}/retrieval", response_model=RetrievalResultResponse)
async def get_email_retrieval(email_id: str):
    """
    获取指定邮件的 Layer 2 检索结果

    参数:
        email_id: str 类型，邮件唯一标识符

    返回:
        RetrievalResultResponse: 包含相似邮件、客户历史、定价政策、合规要求
    """
    from email_agent.layer2.retriever import ContextRetriever

    # 从数据库获取邮件分类结果
    email_data = await db.get_email_by_id(email_id)
    if not email_data:
        raise HTTPException(status_code=404, detail=f"Email not found: {email_id}")

    # 获取分类结果
    classification = email_data.get("classification", {})
    if not classification:
        # 如果没有分类结果，使用默认值
        classification = {
            "customer_region": email_data.get("region", "default"),
            "products_mentioned": [],
            "customer_email": email_data.get("from_address"),
        }

    # 使用检索器获取上下文
    retriever = ContextRetriever(settings)
    result = await retriever.retrieve(
        email_id=email_id,
        email_body=email_data.get("raw_content", ""),
        classification=classification
    )

    return RetrievalResultResponse(
        similar_emails=result.get("similar_emails", {}),
        customer_history=result.get("customer_history"),
        pricing_policy=result.get("pricing_policy", {"policies": [], "region": ""}),
        compliance=result.get("compliance", {"requirements": [], "region": ""})
    )


@router.get("/agents/status", response_model=AgentStatusResponse)
async def get_agents_status():
    """获取 Agent 执行状态"""
    # 从数据库获取 Agent 执行记录
    executions = await db.get_agent_executions()

    # 构建返回结构
    sub_agents = [
        SubAgentStatus(
            agent_name=ex["agent_name"],
            status=ex["status"],
            budget_allocated=ex["budget_allocated"],
            actual_cost=ex["actual_cost"],
            started_at=ex["started_at"],
            completed_at=ex["completed_at"],
            task_id=ex["task_id"]
        )
        for ex in executions[:10]  # 限制返回 10 条
    ]

    total_budget = sum(ex["budget_allocated"] or 0 for ex in executions)
    total_spent = sum(ex["actual_cost"] or 0 for ex in executions)

    return AgentStatusResponse(
        ceo_agent_status="processing" if any(ex["status"] == "running" for ex in executions) else "idle",
        sub_agents=sub_agents,
        total_budget=total_budget,
        total_spent=total_spent,
        budget_utilization=total_spent / max(1, total_budget)
    )


@router.get("/prompts/versions", response_model=PromptVersionsResponse)
async def get_prompt_versions():
    """获取 Prompt 版本历史"""
    # TODO: 替换为真实的 Prompt 版本查询
    return PromptVersionsResponse(
        versions=MOCK_PROMPT_VERSIONS,
        total_versions=len(MOCK_PROMPT_VERSIONS)
    )


# ==================== 可观测性端点 ====================


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """获取可观测性指标"""
    total_emails = metrics.get_counter("email_processed_total") or 0
    total_cost = metrics.get_counter("total_cost") or 0
    return MetricsResponse(
        emails_today=total_emails,
        avg_processing_time_ms=metrics.get_histogram_stats("processing_time_ms").get("avg", 0),
        avg_cost_per_email=total_cost / max(1, total_emails),
        classification_accuracy=metrics.get_gauge("classification_accuracy") or 0.95,
        sonnet_routing_rate=metrics.get_gauge("sonnet_routing_rate") or 0.80,
        prompt_versions=int(metrics.get_counter("prompt_versions"))
    )


@router.get("/metrics/prometheus")
async def get_metrics_prometheus():
    """
    导出 Prometheus 格式指标

    用于 Prometheus 抓取或 Grafana 展示。
    返回 Prometheus Exposition Format 格式的指标数据。
    """
    from email_agent.observability.metrics import metrics as metrics_collector

    prometheus_metrics = metrics_collector.to_prometheus()

    return Response(
        content=prometheus_metrics,
        media_type="text/plain"
    )


@router.get("/traces", response_model=List[TraceResponse])
async def get_traces(limit: int = 10):
    """获取最近的追踪记录"""
    return tracer.get_recent_traces(limit)


# ==================== 通知系统端点 ====================


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """接受 WebSocket 连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """断开 WebSocket 连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)


# 创建连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, client_id: str = Query(default="anonymous")):
    """
    WebSocket 通知端点

    功能描述:
        建立实时通知连接，推送邮件处理状态、Agent 执行进度等事件。

    参数:
        client_id: str 类型，客户端唯一标识

    使用场景:
        - 前端建立 WebSocket 连接接收实时通知
        - 系统推送邮件处理状态变更
        - 推送 Agent 执行进度
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            # 可以处理客户端消息
    except WebSocketDisconnect:
        manager.disconnect(client_id)


@router.get("/notifications")
async def get_notifications(limit: int = 50, unread_only: bool = False):
    """
    获取通知列表

    参数:
        limit: int 类型，返回数量限制
        unread_only: bool 类型，是否只返回未读

    返回:
        通知列表
    """
    notifications = await db.get_notifications(limit=limit, unread_only=unread_only)
    return {"notifications": notifications, "total": len(notifications)}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """
    标记通知为已读

    参数:
        notification_id: int 类型，通知 ID

    返回:
        操作结果
    """
    success = await db.mark_notification_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


# ==================== 审批工作流端点 ====================


class ApprovalRequestCreate(BaseModel):
    """审批请求创建模型"""
    email_id: str
    requester: str
    request_type: str
    reason: str
    amount: Optional[float] = None
    currency: str = "USD"
    details: Optional[Dict[str, Any]] = None


class ApprovalAction(BaseModel):
    """审批操作模型"""
    reviewer: str
    comments: Optional[str] = None


@router.post("/approvals", response_model=Dict[str, Any])
async def create_approval_request(request: ApprovalRequestCreate):
    """
    创建审批请求

    参数:
        request: ApprovalRequestCreate 类型，审批请求数据
            - email_id: 关联邮件 ID
            - requester: 申请人
            - request_type: 审批类型
            - reason: 申请原因
            - amount: 涉及金额（可选）
            - currency: 币种
            - details: 详细信息

    返回:
        创建的审批请求
    """
    created = await db.create_approval_request(
        email_id=request.email_id,
        requester=request.requester,
        request_type=request.request_type,
        reason=request.reason,
        amount=request.amount,
        currency=request.currency,
        details=request.details
    )

    # 创建通知
    await db.create_notification(
        type="approval_request",
        title=f"新的审批请求 | New Approval Request",
        message=f"{request.request_type} 审批待处理 | Pending approval",
        level="warning",
        related_id=str(created["id"]),
        extra_data={"email_id": request.email_id, "amount": request.amount, "currency": request.currency}
    )

    return created


@router.get("/approvals")
async def get_approval_requests(status: str = Query(default=None), limit: int = 50):
    """
    获取审批请求列表

    参数:
        status: 审批状态过滤（pending/approved/rejected/cancelled）
        limit: 返回数量限制

    返回:
        审批请求列表
    """
    requests = await db.get_approval_requests(status=status, limit=limit)
    return {"requests": requests, "total": len(requests)}


@router.get("/approvals/{request_id}")
async def get_approval_request(request_id: int):
    """
    获取审批请求详情

    参数:
        request_id: 审批请求 ID

    返回:
        审批请求详情
    """
    request = await db.get_approval_request_by_id(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.post("/approvals/{request_id}/approve", response_model=Dict[str, Any])
async def approve_request(request_id: int, action: ApprovalAction):
    """
    批准审批请求

    参数:
        request_id: 审批请求 ID
        action: ApprovalAction 类型，审批操作数据
            - reviewer: 审批人
            - comments: 审批意见

    返回:
        操作结果
    """
    success = await db.approve_request(request_id, action.reviewer, action.comments)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # 创建通知
    await db.create_notification(
        type="approval_request",
        title="审批已通过 | Approval Approved",
        message=f"审批请求 #{request_id} 已批准 | Request approved",
        level="success",
        related_id=str(request_id)
    )

    return {"message": "Request approved", "request_id": request_id}


@router.post("/approvals/{request_id}/reject", response_model=Dict[str, Any])
async def reject_request(request_id: int, action: ApprovalAction):
    """
    拒绝审批请求

    参数:
        request_id: 审批请求 ID
        action: ApprovalAction 类型，审批操作数据
            - reviewer: 审批人
            - comments: 拒绝原因

    返回:
        操作结果
    """
    success = await db.reject_request(request_id, action.reviewer, action.comments)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # 创建通知
    await db.create_notification(
        type="approval_request",
        title="审批已拒绝 | Approval Rejected",
        message=f"审批请求 #{request_id} 已拒绝 | Request rejected",
        level="error",
        related_id=str(request_id)
    )

    return {"message": "Request rejected", "request_id": request_id}


# ==================== Email Workflow Endpoints ====================


@router.get("/emails/{email_id}/workflow", response_model=WorkflowResponse)
async def get_email_workflow(email_id: str):
    """
    获取邮件工作流详情

    参数:
        email_id: str 类型，邮件 ID

    返回:
        WorkflowResponse: 包含工作流状态和历史记录

    使用场景:
        - 前端展示流程时间线
        - 查询邮件处理状态
        - 审计流程历史
    """
    workflow = await db.get_email_workflow(email_id)

    if not workflow:
        # 如果工作流不存在，创建一个初始工作流
        workflow = await db.create_email_workflow(email_id=email_id, initial_state="pending")

    if not workflow:
        raise HTTPException(status_code=404, detail="Email not found")

    return workflow


@router.post("/emails/{email_id}/workflow/transition")
async def transition_workflow_state(email_id: str, request: WorkflowTransitionRequest):
    """
    转换邮件工作流状态

    参数:
        email_id: str 类型，邮件 ID
        request: WorkflowTransitionRequest 类型，状态转换请求

    返回:
        更新后的工作流

    状态机流转规则:
        pending → processing → awaiting_approval → approved → completed
                                    ↓                    ↓
                                rejected            failed/cancelled

    使用场景:
        - 系统自动状态流转
        - 用户手动审批操作
        - Agent 执行完成更新
    """
    result = await db.transition_workflow_state(
        email_id=email_id,
        new_state=request.new_state,
        triggered_by=request.triggered_by,
        reason=request.reason,
        metadata=request.metadata
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition or workflow not found"
        )

    return {"workflow": result, "message": "State transitioned successfully"}


@router.post("/emails/{email_id}/workflow/check-approval")
async def check_approval_required(
    email_id: str,
    amount: float = Query(..., description="Amount to check against threshold"),
    threshold: float = Query(default=10000.0, description="Approval threshold")
):
    """
    检查是否需要审批

    参数:
        email_id: str 类型，邮件 ID
        amount: float 类型，金额
        threshold: float 类型，审批阈值 (默认 10000)

    返回:
        {"requires_approval": bool, "reason": str}

    使用场景:
        - 报价生成后自动检查审批要求
        - 高金额交易触发审批流程

    自动审批规则:
        - 金额 > $10000: 需要审批
        - 新客户首次交易：需要审批 (未来扩展)
        - 特殊付款条款：需要审批 (未来扩展)
    """
    requires_approval = await db.check_approval_required(email_id, amount, threshold)

    if requires_approval:
        return {
            "requires_approval": True,
            "reason": f"Amount ${amount} exceeds threshold ${threshold}",
            "next_state": "awaiting_approval"
        }

    return {
        "requires_approval": False,
        "reason": "Amount within threshold",
        "next_state": "approved"
    }


# ==================== 报价生成器端点 ====================


@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(status: str = Query(default=None), limit: int = Query(default=50)):
    """
    获取报价单列表

    参数:
        status: str 类型，状态过滤 (可选)
            draft/sent/accepted/rejected/expired
        limit: int 类型，返回数量限制 (默认 50)

    返回:
        QuoteListResponse: 包含报价单列表和总数

    使用场景:
        - 前端展示报价列表
        - 查询报价历史
    """
    # 从数据库获取报价单列表
    quotes = await db.get_all_quotes(limit=limit, status=status)

    return QuoteListResponse(
        quotes=quotes,
        total=len(quotes)
    )


@router.get("/quotes/{quote_id}", response_model=QuoteSchema)
async def get_quote(quote_id: str):
    """
    获取报价单详情

    参数:
        quote_id: str 类型，报价单号

    返回:
        QuoteSchema: 包含报价单详情

    使用场景:
        - 前端展示报价详情
        - 查看报价项目明细
    """
    # 从数据库获取报价单
    quote = await db.get_quote(quote_id)

    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")

    return quote


@router.post("/quotes/generate", response_model=QuoteGenerateResponse)
async def generate_quote(request: QuoteGenerateRequest):
    """
    基于邮件内容生成报价单

    参数:
        request: QuoteGenerateRequest 类型，生成请求
            - email_id: 邮件 ID
            - context: 额外上下文信息 (可选)

    返回:
        QuoteGenerateResponse: 包含生成的报价单

    使用场景:
        - 为客户询价生成正式报价
        - 基于历史数据和定价政策自动定价

    处理流程:
        1. 获取邮件详情
        2. 使用 Layer 3 报价生成器生成报价
        3. 保存到数据库
        4. 返回报价单
    """
    from email_agent.layer3.generator import QuoteGenerator
    from email_agent.layer3.prompts import QuoteResult

    # 获取邮件详情
    email = await db.get_email_by_id(request.email_id)
    if not email:
        raise HTTPException(status_code=404, detail=f"Email {request.email_id} not found")

    # 初始化报价生成器
    generator = QuoteGenerator(settings)

    # 构建上下文
    context = {}

    # 获取客户信息
    customer = await db.query_customer(email=email.get("from_address"))
    if customer:
        context["customer_history"] = customer

    # 获取定价政策
    # 从邮件分析中提取产品名称
    analysis = await db.get_email_analysis(request.email_id)
    products = []
    if analysis and analysis.get("layer1_classification"):
        products = analysis["layer1_classification"].get("products_mentioned", [])

    if products:
        region = email.get("region", "default")
        pricing = await db.query_pricing_policy(products, region)
        context["pricing_policy"] = pricing

    # 获取合规要求
    if region:
        compliance = await db.query_compliance_requirements(products, region)
        context["compliance"] = compliance

    # 生成报价单
    try:
        quote_result = await generator.generate_quote(
            email_id=request.email_id,
            original_email=email.get("body", "") or email.get("subject", ""),
            context=context
        )

        # 从结果中提取报价项目
        items = quote_result.get("items", [])

        # 创建报价单记录
        quote = await db.create_quote(
            quote_id=quote_result.get("quote_id"),
            email_id=request.email_id,
            customer_email=quote_result.get("customer_email", email.get("from_address", "")),
            total_amount=quote_result.get("total_amount", 0),
            valid_until=quote_result.get("valid_until", ""),
            items=items,
            shipping_port=quote_result.get("shipping_port", ""),
            payment_terms=quote_result.get("payment_terms", "30% advance, 70% against B/L"),
            notes=quote_result.get("notes"),
            status="draft"
        )

        return QuoteGenerateResponse(
            quote=quote,
            message="Quote generated successfully"
        )

    except Exception as e:
        logger.error("quote_generation_failed", email_id=request.email_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate quote: {str(e)}")


@router.post("/quotes/{quote_id}/status")
async def update_quote_status(quote_id: str, status: str = Query(...)):
    """
    更新报价单状态

    参数:
        quote_id: str 类型，报价单号
        status: str 类型，新状态
            draft/sent/accepted/rejected/expired

    返回:
        操作结果

    使用场景:
        - 标记报价单为已发送
        - 记录客户接受/拒绝
    """
    valid_statuses = ["draft", "sent", "accepted", "rejected", "expired"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    success = await db.update_quote_status(quote_id, status)
    if not success:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")

    # 创建通知
    await db.create_notification(
        type="quote_status",
        title=f"Quote Status Updated | 报价状态更新",
        message=f"Quote {quote_id} status changed to {status}",
        level="info",
        related_id=quote_id,
        extra_data={"status": status}
    )

    return {"message": f"Quote status updated to {status}", "quote_id": quote_id}


@router.delete("/quotes/{quote_id}")
async def delete_quote(quote_id: str):
    """
    删除报价单

    参数:
        quote_id: str 类型，报价单号

    返回:
        删除成功返回 204

    使用场景:
        - 删除错误的报价单
        - 清理过期报价
    """
    success = await db.delete_quote(quote_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")

    return {"message": f"Quote {quote_id} deleted"}


@router.get("/emails/{email_id}/quotes")
async def get_email_quotes(email_id: str):
    """
    获取邮件的所有报价单

    参数:
        email_id: str 类型，邮件 ID

    返回:
        报价单列表

    使用场景:
        - 查看邮件相关的报价历史
        - 追踪报价处理进度
    """
    quotes = await db.get_quotes_by_email(email_id)
    return {"quotes": quotes, "total": len(quotes)}


# ==================== 健康检查端点 ====================


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# ==================== Agent 监控端点 ====================


@router.get("/agents/executions")
async def list_agent_executions(limit: int = Query(default=50, ge=1, le=200)):
    """
    获取 Agent 执行历史记录

    参数:
        limit: int 类型，返回数量限制 (默认 50, 1-200)

    返回:
        Agent 执行记录列表
    """
    executions = await db.get_agent_executions(limit=limit)
    return {"executions": executions, "total": len(executions)}


@router.get("/agents/executions/{task_id}")
async def get_execution_detail(task_id: str):
    """
    获取单个执行详情

    参数:
        task_id: str 类型，任务 ID

    返回:
        执行详情字典
    """
    detail = await db.get_execution_detail(task_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Execution not found for task {task_id}")
    return detail


@router.get("/agents/metrics")
async def get_agent_metrics():
    """
    获取 Agent 性能指标

    返回:
        Agent 性能指标列表
    """
    metrics = await db.get_agent_metrics()
    return metrics


@router.get("/metrics/cost-stats")
async def get_cost_stats(days: int = Query(default=30, ge=1, le=365)):
    """
    获取成本统计数据

    参数:
        days: int 类型，统计天数 (默认 30)

    返回:
        每日成本统计列表
    """
    stats = await db.get_cost_stats(days=days)
    return {"stats": stats, "days": days}


@router.get("/metrics/cost-trend")
async def get_cost_trend(days: int = Query(default=30, ge=1, le=365)):
    """
    获取成本趋势数据

    参数:
        days: int 类型，统计天数 (默认 30)

    返回:
        成本趋势数据点列表
    """
    trend = await db.get_cost_trend(days=days)
    return {"trend": trend, "days": days}


@router.get("/metrics/performance-trend")
async def get_performance_trend(days: int = Query(default=30, ge=1, le=365)):
    """
    获取性能趋势数据

    参数:
        days: int 类型，统计天数 (默认 30)

    返回:
        性能趋势数据点列表
    """
    trend = await db.get_performance_trend(days=days)
    return {"trend": trend, "days": days}


@router.get("/metrics/dashboard")
async def get_monitoring_dashboard():
    """
    获取监控仪表板汇总数据

    返回:
        包含汇总指标、最近执行、趋势数据的字典
    """
    dashboard = await db.get_monitoring_dashboard()
    return dashboard
