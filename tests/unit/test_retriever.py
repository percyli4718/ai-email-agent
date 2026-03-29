import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from email_agent.layer2.retriever import ContextRetriever
from email_agent.config import Settings


@pytest.mark.asyncio
async def test_retriever_returns_all_context():
    """Test that retriever returns all context components."""

    settings = Settings()
    settings.anthropic_api_key = "test-key"
    settings.database_url = "sqlite+aiosqlite:///./test.db"

    retriever = ContextRetriever(settings)

    mock_similar_emails = {
        "documents": [["Previous email content"]],
        "metadatas": [[{"email_id": "123", "type": "inquiry"}]]
    }

    with patch.object(retriever.chroma_client, 'search_similar',
                      return_value=mock_similar_emails):
        with patch.object(retriever.db, 'query_customer',
                         return_value={"name": "Test Customer", "tier": "B"}):
            with patch.object(retriever.db, 'query_pricing',
                             return_value={"discount": 0.15}):
                with patch.object(retriever.db, 'query_compliance',
                                 return_value={"required": ["ANVISA"]}):

                    result = await retriever.retrieve(
                        email_id="test-123",
                        email_body="We want to order",
                        classification={
                            "type": "inquiry",
                            "customer_region": "brazil",
                            "products_mentioned": ["Paracetamol"]
                        }
                    )

                    assert "similar_emails" in result
                    assert "customer_history" in result
                    assert "pricing_policy" in result
                    assert "compliance" in result
