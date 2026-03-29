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
    """Base class for all models."""
    pass


class Email(Base):
    """Email table."""
    __tablename__ = "emails"

    id = Column(String, primary_key=True)
    raw_content = Column(Text)
    from_address = Column(String)
    subject = Column(String)
    received_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    status = Column(String)


class Classification(Base):
    """Classification results table."""
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
    """Quotes table."""
    __tablename__ = "quotes"

    id = Column(String, primary_key=True)
    email_id = Column(String, ForeignKey("emails.id"))
    quote_json = Column(JSON)
    total_amount = Column(Float)
    currency = Column(String, default="USD")
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentExecution(Base):
    """Agent execution logs table."""
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
    """Prompt versions table."""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    version = Column(Integer)
    template = Column(Text)
    accuracy_score = Column(Float)
    changes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
