from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Task:
    """A task to be executed by a sub-agent."""
    id: str
    agent_name: str
    input_data: Dict[str, Any]
    budget: float
    dependencies: List[str] = field(default_factory=list)
    output: Optional[Any] = None
    status: str = "pending"


@dataclass
class DependencyGraph:
    """Graph of tasks with dependencies."""
    tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        budget: float,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Add a task to the graph."""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = Task(
            id=task_id,
            agent_name=agent_name,
            input_data=input_data,
            budget=budget,
            dependencies=dependencies or []
        )
        return task_id

    def add_dependency(self, from_task: str, to_task: str) -> None:
        """Add a dependency between tasks."""
        if to_task in self.tasks:
            self.tasks[to_task].dependencies.append(from_task)

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run."""
        ready = []
        for task in self.tasks.values():
            if task.status != "pending":
                continue
            deps_satisfied = all(
                self.tasks[dep].status == "completed"
                for dep in task.dependencies
            )
            if deps_satisfied:
                ready.append(task)
        return ready

    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            t.status in ("completed", "failed")
            for t in self.tasks.values()
        )


class CEOAgent:
    """CEO Agent: Decomposes goals into sub-agent tasks."""

    def decompose_inquiry(
        self,
        email_body: str,
        classification: dict
    ) -> DependencyGraph:
        """Decompose an inquiry into sub-agent tasks."""
        graph = DependencyGraph()
        products = classification.get("products_mentioned", [])
        region = classification.get("customer_region", "other")

        # Task 1: Price lookup
        price_task = graph.add_task(
            agent_name="price_agent",
            input_data={"products": products},
            budget=0.10
        )

        # Task 2: Compliance check
        if region != "domestic":
            compliance_task = graph.add_task(
                agent_name="compliance_agent",
                input_data={"products": products, "destination": region},
                budget=0.15,
                dependencies=[price_task]
            )
        else:
            compliance_task = price_task

        # Task 3: Logistics calculation
        logistics_task = graph.add_task(
            agent_name="logistics_agent",
            input_data={"products": products, "destination": region},
            budget=0.12,
            dependencies=[compliance_task]
        )

        # Task 4: Reply generation
        graph.add_task(
            agent_name="reply_agent",
            input_data={"email_body": email_body, "classification": classification},
            budget=0.08,
            dependencies=[logistics_task]
        )

        logger.info(
            "ceo_decomposed_goal",
            task_count=len(graph.tasks)
        )

        return graph
