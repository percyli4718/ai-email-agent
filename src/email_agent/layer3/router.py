from enum import Enum
from typing import Dict, Any

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


class ModelChoice(str, Enum):
    """Available Anthropic models."""
    SONNET = "claude-sonnet-4-20250514"
    OPUS = "claude-opus-4-20250514"


class ModelRouter:
    """
    Intelligently routes requests to Sonnet or Opus.

    Per JD requirement: 80% should route to Sonnet for cost control.
    """

    def __init__(self):
        self.target_sonnet_rate = 0.80

    def route(self, context: Dict[str, Any]) -> ModelChoice:
        """
        Decide which model to use based on complexity.

        Args:
            context: Retrieved context from Layer 2

        Returns:
            ModelChoice (SONNET or OPUS)
        """
        complexity_score = self._calculate_complexity(context)

        # Route to Sonnet if below threshold (target 80%)
        if complexity_score < 0.4:
            logger.info("model_routed", model="sonnet", complexity=complexity_score)
            return ModelChoice.SONNET
        else:
            logger.info("model_routed", model="opus", complexity=complexity_score)
            return ModelChoice.OPUS

    def _calculate_complexity(self, context: Dict[str, Any]) -> float:
        """
        Calculate complexity score 0.0-1.0.

        Factors:
        - Number of products (>5 = more complex)
        - Compliance requirements (special permits = more complex)
        - Customer tier (new customers = more complex)
        - Order value estimate (high value = more complex)
        """
        score = 0.0

        # Factor 1: Number of products
        products = context.get("pricing_policy", {}).get("products", [])
        if len(products) > 5:
            score += 0.2
        elif len(products) > 2:
            score += 0.1

        # Factor 2: Compliance requirements
        compliance = context.get("compliance", {})
        if compliance.get("special_permits"):
            score += 0.3
        if compliance.get("restrictions"):
            score += 0.2

        # Factor 3: Customer history
        customer = context.get("customer_history", {})
        if not customer:
            score += 0.2  # New customer = more complex
        elif customer.get("tier") == "C":
            score += 0.1  # Lower tier = slightly more complex

        return min(score, 1.0)
