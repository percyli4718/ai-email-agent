from enum import Enum
from typing import Any

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


class Decision(str, Enum):
    """CEO review decision."""
    PROMOTE = "promote"
    REDELEGATE = "redelegate"
    REJECT = "reject"


class CEOReviewer:
    """CEO Reviewer: Reviews sub-agent deliverables."""

    def __init__(self):
        self.review_history = []

    def review(self, task_result: Any, quality_threshold: float = 0.8) -> Decision:
        """Review a sub-agent's deliverable."""
        quality_score = self._evaluate_quality(task_result)

        if quality_score >= quality_threshold:
            decision = Decision.PROMOTE
        elif quality_score >= 0.5:
            decision = Decision.REDELEGATE
        else:
            decision = Decision.REJECT

        self.review_history.append({
            "quality_score": quality_score,
            "decision": decision.value
        })

        logger.info(
            "ceo_review_completed",
            quality=quality_score,
            decision=decision.value
        )

        return decision

    def _evaluate_quality(self, result: Any) -> float:
        """Evaluate the quality of a result."""
        if result is None:
            return 0.0

        score = 1.0

        if hasattr(result, 'output'):
            if result.output is None:
                score -= 0.5
            if hasattr(result, 'error') and result.error:
                score -= 0.3

        if hasattr(result, 'success'):
            if not result.success:
                score -= 0.4

        return max(0.0, score)
