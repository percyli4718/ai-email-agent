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
)
from email_agent.observability.metrics import metrics
from email_agent.observability.tracing import tracer

# 创建 API 路由器
# 所有路由都将通过此路由器注册到 FastAPI 应用
router = APIRouter()


@router.get("/emails", response_model=List[EmailInbox])
async def list_emails(status: str = "all", limit: int = 50):
    """
    获取邮件列表

    功能描述:
        返回系统收到的邮件列表。
        支持按状态过滤和数量限制。

    参数:
        status: str 类型，过滤状态 (默认"all")
            - "all": 显示所有邮件
            - "pending": 仅显示待处理邮件
            - "completed": 仅显示已完成邮件
            - "failed": 仅显示失败邮件

        limit: int 类型，返回数量限制 (默认 50)
            最多返回的邮件数量

    返回值:
        List[EmailInbox]: 邮件列表，每项包含:
            - id: 邮件 ID
            - from_address: 发件人地址
            - subject: 主题
            - received_at: 接收时间
            - status: 处理状态
            - priority: 优先级 (可选)

    异常:
        无

    使用示例:
        GET /api/emails?status=pending&limit=20
    """
    # TODO: 实现真实的数据库查询
    return []


@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """
    获取邮件详情

    功能描述:
        根据邮件 ID 获取完整的邮件详情。
        包含分类结果、报价单和 Agent 执行记录。

    参数:
        email_id: str 类型，邮件唯一标识符

    返回值:
        EmailDetail: 邮件详情，包含:
            - 基本信息 (继承自 EmailInbox)
            - raw_content: 原始内容
            - classification: 分类结果
            - quote: 报价单
            - agent_executions: Agent 执行记录

    异常:
        HTTPException 404: 当邮件不存在时抛出

    使用示例:
        GET /api/emails/abc12345
    """
    # TODO: 实现真实的数据库查询
    # 如果邮件不存在，抛出 404 错误
    raise HTTPException(status_code=404, detail="Email not found")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    获取可观测性指标

    功能描述:
        返回系统的性能指标和统计信息。
        用于监控仪表盘展示。

    参数:
        无

    返回值:
        MetricsResponse: 指标响应，包含:
            - emails_today: 今日处理邮件数
            - avg_processing_time_ms: 平均处理时间
            - avg_cost_per_email: 平均每封邮件成本
            - classification_accuracy: 分类准确率
            - sonnet_routing_rate: Sonnet 路由率
            - prompt_versions: 提示词版本数

    异常:
        无

    指标说明:
        - emails_today: 从 counter 获取
        - total_cost: 总 API 成本
        - avg_cost_per_email: total_cost / emails_today
        - classification_accuracy: 从 gauge 获取
        - sonnet_routing_rate: 从 gauge 获取 (目标 0.80)

    使用示例:
        GET /api/metrics
    """
    # 获取总处理邮件数
    total_emails = metrics.get_counter("email_processed_total") or 0
    # 获取总成本
    total_cost = metrics.get_counter("total_cost") or 0

    return MetricsResponse(
        emails_today=total_emails,
        # 平均处理时间从直方图统计中获取
        avg_processing_time_ms=metrics.get_histogram_stats("processing_time_ms").get("avg", 0),
        # 计算平均每封邮件成本，防止除以 0
        avg_cost_per_email=total_cost / max(1, total_emails),
        # 分类准确率从 gauge 获取，默认 0.95
        classification_accuracy=metrics.get_gauge("classification_accuracy") or 0.95,
        # Sonnet 路由率从 gauge 获取，默认 0.80
        sonnet_routing_rate=metrics.get_gauge("sonnet_routing_rate") or 0.80,
        # 提示词版本数从 counter 获取
        prompt_versions=int(metrics.get_counter("prompt_versions"))
    )


@router.get("/traces", response_model=List[TraceResponse])
async def get_traces(limit: int = 10):
    """
    获取最近的追踪记录

    功能描述:
        返回最近的 N 个追踪树。
        用于调试和性能分析。

    参数:
        limit: int 类型，返回数量限制 (默认 10)
            最多返回的追踪数量

    返回值:
        List[TraceResponse]: 追踪树列表，每个追踪包含:
            - id: 根跨度 ID
            - name: 根跨度名称
            - duration_ms: 总持续时间
            - tags: 标签
            - children: 子跨度树

    异常:
        无

    使用示例:
        GET /api/traces?limit=20
    """
    return tracer.get_recent_traces(limit)


@router.get("/health")
async def health_check():
    """
    健康检查端点

    功能描述:
        返回应用的健康状态。
        用于负载均衡器和监控系统检查。

    参数:
        无

    返回值:
        dict: 健康状态，包含:
            - status: "healthy" 表示健康
            - timestamp: 检查时间 (UTC)

    异常:
        无

    使用示例:
        GET /api/health

    响应示例:
        {
            "status": "healthy",
            "timestamp": "2025-03-30T10:00:00Z"
        }
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}
