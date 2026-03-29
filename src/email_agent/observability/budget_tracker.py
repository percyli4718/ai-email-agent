from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import threading

from email_agent.config import Settings
from email_agent.logging_config import get_logger
from email_agent.observability.metrics import metrics

logger = get_logger(__name__)


@dataclass
class BudgetEvent:
    """A budget-related event."""
    operation: str
    cost: float
    cumulative_cost: float
    timestamp: datetime
    event_type: str = "spending"


class BudgetTracker:
    """Tracks and enforces budget limits for agent operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._spending: Dict[str, float] = {}
        self._events: List[BudgetEvent] = []

    async def check_budget(self, operation: str, estimated_cost: float) -> None:
        """Check if operation is within budget."""
        with self._lock:
            current = self._spending.get(operation, 0.0)
            projected = current + estimated_cost

            if projected > self.settings.default_agent_budget:
                logger.warning(
                    "budget_warning",
                    operation=operation,
                    current=current,
                    projected=projected,
                    limit=self.settings.default_agent_budget
                )
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=estimated_cost,
                    cumulative_cost=projected,
                    timestamp=datetime.now(),
                    event_type="budget_warning"
                ))

    async def record_spending(self, operation: str, actual_cost: float) -> None:
        """Record actual spending for an operation."""
        with self._lock:
            current = self._spending.get(operation, 0.0)
            new_total = current + actual_cost
            self._spending[operation] = new_total

            if new_total > self.settings.default_agent_budget:
                logger.warning(
                    "budget_hard_kill",
                    operation=operation,
                    total=new_total,
                    limit=self.settings.default_agent_budget
                )
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=actual_cost,
                    cumulative_cost=new_total,
                    timestamp=datetime.now(),
                    event_type="budget_hard_kill"
                ))
            else:
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=actual_cost,
                    cumulative_cost=new_total,
                    timestamp=datetime.now()
                ))

            metrics.gauge(f"budget_{operation}_spent", new_total)

    def _record_event(self, event: BudgetEvent) -> None:
        """Record a budget event."""
        self._events.append(event)
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

    def get_spending(self, operation: str) -> float:
        """Get total spending for an operation."""
        return self._spending.get(operation, 0.0)

    def get_events(self, limit: int = 100) -> List[BudgetEvent]:
        """Get recent budget events."""
        return self._events[-limit:]


class BudgetExceededError(Exception):
    """Raised when budget would be exceeded."""
    pass
