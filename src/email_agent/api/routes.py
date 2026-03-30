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
)
from email_agent.observability.metrics import metrics
from email_agent.observability.tracing import tracer

router = APIRouter()


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
    # TODO: 替换为真实的数据库查询
    filtered_emails = MOCK_EMAILS
    if status != "all":
        filtered_emails = [e for e in MOCK_EMAILS if e["status"] == status]
    return {"emails": filtered_emails[:limit], "total": len(filtered_emails)}


@router.get("/emails/{email_id}/analysis", response_model=EmailAnalysisResponse)
async def get_email_analysis(email_id: str):
    """
    获取指定邮件的 AI 分析结果
    
    参数:
        email_id: str 类型，邮件唯一标识符
    
    返回:
        EmailAnalysisResponse: 包含 Layer 1/2/3 分析结果
    """
    # TODO: 替换为真实的数据库查询
    analysis = MOCK_ANALYSIS.get(email_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis not found for email {email_id}")
    return EmailAnalysisResponse(
        email_id=email_id,
        layer1_classification=analysis["layer1_classification"],
        layer2_retrieval=analysis.get("layer2_retrieval"),
        layer3_output=analysis.get("layer3_output")
    )


@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """获取邮件详情"""
    # TODO: 实现真实的数据库查询
    raise HTTPException(status_code=404, detail="Email not found")


@router.get("/agents/status", response_model=AgentStatusResponse)
async def get_agents_status():
    """获取 Agent 执行状态"""
    # TODO: 替换为真实的 Agent 状态查询
    return MOCK_AGENT_STATUS


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


@router.get("/traces", response_model=List[TraceResponse])
async def get_traces(limit: int = 10):
    """获取最近的追踪记录"""
    return tracer.get_recent_traces(limit)


# ==================== 健康检查端点 ====================


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
