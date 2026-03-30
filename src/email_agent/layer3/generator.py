import json
import uuid
from typing import TYPE_CHECKING, Any, Dict

from email_agent.config import Settings
from email_agent.layer3.prompts import QUOTE_GENERATION_PROMPT, QuoteResult
from email_agent.layer3.router import ModelChoice, ModelRouter
from email_agent.logging_config import get_logger
from email_agent.observability.budget_tracker import BudgetTracker

if TYPE_CHECKING:
    import anthropic

logger = get_logger(__name__)


class QuoteGenerator:
    """Layer 3: Generates structured quotes from context."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self.router = ModelRouter()
        self.budget_tracker = BudgetTracker(settings)

    @property
    def client(self) -> "anthropic.AsyncClient":
        """Lazy initialization of Anthropic client to avoid proxy issues."""
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncClient(api_key=self.settings.anthropic_api_key)
        return self._client

    async def generate_quote(
        self,
        original_email: str,
        context: Dict[str, Any]
    ) -> QuoteResult:
        """Generate a quote based on retrieved context."""
        model = self.router.route(context)

        max_cost = (
            self.settings.max_sonnet_cost_per_email
            if model == ModelChoice.SONNET
            else self.settings.max_opus_cost_per_email
        )

        await self.budget_tracker.check_budget(
            operation="quote_generation",
            estimated_cost=max_cost
        )

        prompt = QUOTE_GENERATION_PROMPT.format(
            similar_emails=self._format_similar_emails(context.get("similar_emails", {})),
            customer_history=json.dumps(context.get("customer_history", {}), indent=2),
            pricing_policy=json.dumps(context.get("pricing_policy", {}), indent=2),
            compliance=json.dumps(context.get("compliance", {}), indent=2),
            original_email=original_email[:2000]
        )

        result_text = await self._call_llm(model, prompt)

        try:
            result: QuoteResult = json.loads(result_text)
            self._validate_quote(result)

            logger.info(
                "quote_generated",
                quote_id=result.get("quote_id"),
                total=result.get("total_amount"),
                model=model.value
            )

            return result

        except json.JSONDecodeError as e:
            logger.error("quote_parse_error", error=str(e))
            raise QuoteGenerationError(f"Failed to parse quote: {e}")

    async def _call_llm(self, model: ModelChoice, prompt: str) -> str:
        """Call Anthropic API."""
        response = await self.client.messages.create(
            model=model.value,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        cost = self._calculate_cost(
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        await self.budget_tracker.record_spending(
            operation="quote_generation",
            actual_cost=cost
        )

        return response.content[0].text.strip()

    def _calculate_cost(
        self,
        model: ModelChoice,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate API cost based on tokens and model."""
        if model == ModelChoice.SONNET:
            return (input_tokens * 3e-6) + (output_tokens * 1.5e-5)
        else:
            return (input_tokens * 1.5e-5) + (output_tokens * 7.5e-5)

    def _format_similar_emails(self, similar: dict) -> str:
        """Format similar emails for prompt."""
        documents = similar.get("documents", [[]])
        if not documents or not documents[0]:
            return "No similar emails found."
        return "\n\n".join(documents[0][:3])

    def _validate_quote(self, quote: dict) -> None:
        """Validate quote has required fields."""
        required = ["quote_id", "customer_email", "items", "total_amount"]
        missing = [f for f in required if f not in quote]
        if missing:
            raise QuoteGenerationError(f"Missing required fields: {missing}")
        if not quote.get("items"):
            raise QuoteGenerationError("Quote must have at least one item")


class QuoteGenerationError(Exception):
    """Raised when quote generation fails."""
    pass
