from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
import sqlite3

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResult:
    """Result of an agent execution."""
    success: bool
    output: Any
    actual_cost: float
    error: Optional[str] = None


class WriteIsolatedDB:
    """SQLite wrapper with write isolation for sandbox."""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._init_schema()

    def _init_schema(self):
        """Initialize schema in isolated DB."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS prices (
                product_code TEXT PRIMARY KEY,
                base_price REAL,
                currency TEXT
            );
            CREATE TABLE IF NOT EXISTS compliance (
                product_code TEXT,
                region TEXT,
                requirements TEXT,
                PRIMARY KEY (product_code, region)
            );
        """)

    def query(self, sql: str, params: tuple = ()) -> list:
        """Execute a read query."""
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a write query (isolated)."""
        self.conn.execute(sql, params)
        self.conn.commit()


class AgentSandbox:
    """Sandbox for executing sub-agents with budget hard kill."""

    def __init__(self, budget: float):
        self.budget = budget
        self.spent = 0.0
        self.isolated_db = WriteIsolatedDB()

    async def execute(
        self,
        agent_fn: Callable,
        input_data: Dict[str, Any],
        agent_name: str = "unknown"
    ) -> AgentResult:
        """Execute an agent function in the sandbox."""
        try:
            if self.spent >= self.budget:
                logger.warning(
                    "budget_hard_kill",
                    agent=agent_name,
                    budget=self.budget,
                    spent=self.spent
                )
                return AgentResult(
                    success=False,
                    output=None,
                    actual_cost=self.spent,
                    error=f"Budget exceeded: {self.spent} >= {self.budget}"
                )

            result = await agent_fn(
                input_data=input_data,
                db=self.isolated_db
            )

            actual_cost = getattr(result, 'cost', 0.01)
            self.spent += actual_cost

            logger.info(
                "agent_executed",
                agent=agent_name,
                cost=actual_cost,
                total_spent=self.spent
            )

            return AgentResult(
                success=True,
                output=result,
                actual_cost=self.spent
            )

        except Exception as e:
            logger.error("agent_execution_error", agent=agent_name, error=str(e))
            return AgentResult(
                success=False,
                output=None,
                actual_cost=self.spent,
                error=str(e)
            )
