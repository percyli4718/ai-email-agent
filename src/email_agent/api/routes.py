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

router = APIRouter()


@router.get("/emails", response_model=List[EmailInbox])
async def list_emails(status: str = "all", limit: int = 50):
    """List emails in inbox."""
    return []


@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """Get email detail with classification and quote."""
    raise HTTPException(status_code=404, detail="Email not found")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get observability metrics."""
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
    """Get recent traces."""
    return tracer.get_recent_traces(limit)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
