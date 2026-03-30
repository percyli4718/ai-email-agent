from typing import Any, Dict

from email_agent.config import Settings
from email_agent.layer2.chroma_client import ChromaClient
from email_agent.layer2.embedding_service import EmbeddingService
from email_agent.logging_config import get_logger
from email_agent.storage.database import get_database

logger = get_logger(__name__)


class ContextRetriever:
    """Layer 2: Retrieves context for email processing."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.chroma_client = ChromaClient(settings)
        self.embedding_service = EmbeddingService(settings)
        self.db = get_database(settings)

    async def retrieve(
        self,
        email_id: str,
        email_body: str,
        classification: dict
    ) -> Dict[str, Any]:
        """Retrieve all relevant context for an email."""
        similar_emails = await self._search_similar_emails(
            email_body,
            classification.get("customer_region")
        )

        customer_history = await self._get_customer_history(classification)

        pricing_policy = await self._get_pricing_policy(
            classification.get("products_mentioned", []),
            classification.get("customer_region")
        )

        compliance = await self._get_compliance_requirements(
            classification.get("products_mentioned", []),
            classification.get("customer_region")
        )

        logger.info(
            "context_retrieved",
            email_id=email_id,
            similar_count=len(similar_emails.get("documents", [])),
            has_customer=customer_history is not None
        )

        return {
            "similar_emails": similar_emails,
            "customer_history": customer_history,
            "pricing_policy": pricing_policy,
            "compliance": compliance
        }

    async def _search_similar_emails(self, email_body: str, region: str) -> dict:
        """Search for similar historical emails."""
        filter_metadata = {"region": region} if region else None
        return await self.chroma_client.search_similar(
            query_text=email_body[:2000],
            n_results=3,
            filter_metadata=filter_metadata
        )

    async def _get_customer_history(self, classification: dict) -> dict:
        """Get customer order history."""
        return await self.db.query_customer(
            email=classification.get("customer_email"),
            region=classification.get("customer_region")
        )

    async def _get_pricing_policy(self, products: list, region: str) -> dict:
        """Get applicable pricing policy."""
        return await self.db.query_pricing(
            products=products,
            region=region
        )

    async def _get_compliance_requirements(self, products: list, region: str) -> dict:
        """Get compliance requirements for products/region."""
        return await self.db.query_compliance(
            products=products,
            destination=region
        )
