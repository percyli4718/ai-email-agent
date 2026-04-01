import json
import pytest
from unittest.mock import AsyncMock, patch

from email_agent.layer1.classifier import EmailClassifier, ClassificationError
from email_agent.config import Settings


@pytest.mark.asyncio
async def test_classifier_parses_response():
    """Test that classifier correctly parses LLM response."""

    mock_response = {
        "type": "inquiry",
        "priority_score": 0.92,
        "urgency": "high",
        "language": "en",
        "products_mentioned": ["Paracetamol 500mg"],
        "customer_region": "brazil",
        "requires_human": False,
        "suggested_route": "quote_flow"
    }

    with patch('email_agent.layer1.classifier.create_client') as mock_create:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=AsyncMock(content=[AsyncMock(text=json.dumps(mock_response))])
        )
        mock_create.return_value = mock_client

        settings = Settings()
        # Override API key for testing
        settings.anthropic_api_key = "test-key"

        classifier = EmailClassifier(settings)
        result = await classifier.classify(
            email_id="test-123",
            email_body="We want to order Paracetamol",
            subject="Bulk Order Inquiry"
        )

        assert result["type"] == "inquiry"
        assert result["suggested_route"] == "quote_flow"


@pytest.mark.asyncio
async def test_classifier_validates_required_fields():
    """Test that classifier validates required fields."""
    # Missing 'type' field should fail
    invalid_response = {"priority_score": 0.5}

    with patch('email_agent.layer1.classifier.create_client') as mock_create:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(
            return_value=AsyncMock(content=[AsyncMock(text=str(invalid_response))])
        )
        mock_create.return_value = mock_client

        settings = Settings()
        settings.anthropic_api_key = "test-key"

        classifier = EmailClassifier(settings)

        with pytest.raises(ClassificationError):
            await classifier.classify(
                email_id="test-123",
                email_body="test",
                subject="test"
            )
