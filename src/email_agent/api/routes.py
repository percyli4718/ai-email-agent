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
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import List
from datetime import datetime

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
)
from email_agent.observability.metrics import metrics
from email_agent.observability.tracing import tracer
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate
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
            created_at=template.created_at.isoformat() if template.created_at else ""
        )
        for template in templates
    ]

    return EmailTemplatesResponse(
        templates=template_responses,
        total=len(template_responses)
    )


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


# ==================== 健康检查端点 ====================


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
