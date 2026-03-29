from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from datetime import datetime


class EmailInbox(BaseModel):
    """Schema for email inbox listing."""
    id: str
    from_address: str
    subject: str
    received_at: datetime
    status: str
    priority: Optional[str] = None


class EmailDetail(EmailInbox):
    """Schema for email detail view."""
    raw_content: str
    classification: Optional[Dict] = None
    quote: Optional[Dict] = None
    agent_executions: List[Dict] = []


class ClassificationResponse(BaseModel):
    """Schema for classification result."""
    type: str
    priority_score: float
    urgency: str
    language: str
    products_mentioned: List[str]
    customer_region: str
    requires_human: bool
    suggested_route: str


class QuoteResponse(BaseModel):
    """Schema for quote result."""
    quote_id: str
    items: List[Dict]
    total_amount: float
    valid_until: str
    shipping_port: str
    payment_terms: str


class AgentStatus(BaseModel):
    """Schema for agent status."""
    agent_name: str
    status: str
    budget_allocated: float
    actual_cost: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MetricsResponse(BaseModel):
    """Schema for metrics dashboard."""
    emails_today: int
    avg_processing_time_ms: float
    avg_cost_per_email: float
    classification_accuracy: float
    sonnet_routing_rate: float
    prompt_versions: int


class TraceResponse(BaseModel):
    """Schema for trace view."""
    id: str
    name: str
    duration_ms: Optional[float]
    tags: Dict[str, str]
    children: List["TraceResponse"] = []


TraceResponse.model_rebuild()
