import json
from typing import Any

import anthropic

from email_agent.config import Settings
from email_agent.layer1.prompts import CLASSIFIER_PROMPT, EmailClassification
from email_agent.logging_config import get_logger

logger = get_logger(__name__)


def create_client(api_key: str) -> anthropic.AsyncClient:
    """Create Anthropic client instance."""
    return anthropic.AsyncClient(api_key=api_key)


class EmailClassifier:
    """Layer 1: Classifies incoming emails and routes them."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = create_client(settings.anthropic_api_key)

    async def classify(
        self,
        email_body: str,
        subject: str = ""
    ) -> EmailClassification:
        """
        Classify an email and return routing decision.

        Args:
            email_body: Raw email body text
            subject: Email subject line

        Returns:
            EmailClassification dict with routing decision

        Raises:
            ClassificationError: If classification fails
        """
        try:
            prompt = CLASSIFIER_PROMPT.format(
                email_body=email_body[:4000],
                subject=subject
            )

            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result_text = response.content[0].text.strip()
            result: EmailClassification = json.loads(result_text)

            # Validate required fields
            self._validate_classification(result)

            logger.info(
                "email_classified",
                type=result.get("type"),
                priority=result.get("priority_score"),
                route=result.get("suggested_route")
            )

            return result

        except json.JSONDecodeError as e:
            logger.error("classification_json_parse_error", error=str(e))
            raise ClassificationError(f"Failed to parse classification: {e}")
        except Exception as e:
            logger.error("classification_error", error=str(e))
            raise ClassificationError(f"Classification failed: {e}")

    def _validate_classification(self, result: dict) -> None:
        """Validate classification has required fields."""
        required_fields = ["type", "priority_score", "language", "suggested_route"]
        missing = [f for f in required_fields if f not in result]
        if missing:
            raise ClassificationError(f"Missing fields: {missing}")


class ClassificationError(Exception):
    """Raised when email classification fails."""
    pass
