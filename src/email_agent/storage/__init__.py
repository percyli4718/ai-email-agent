from email_agent.storage.database import Database, get_database
from email_agent.storage.models import (
    Base,
    Customer,
    Email,
    EmailAnalysis,
    AgentExecution,
    PromptVersion,
    EmailTemplate,
    init_db_tables,
    drop_db_tables,
)

__all__ = [
    "Database",
    "get_database",
    "Base",
    "Customer",
    "Email",
    "EmailAnalysis",
    "AgentExecution",
    "PromptVersion",
    "EmailTemplate",
    "init_db_tables",
    "drop_db_tables",
]
