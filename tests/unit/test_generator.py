import json
import pytest
from unittest.mock import AsyncMock, patch

from email_agent.layer3.generator import QuoteGenerator, QuoteGenerationError
from email_agent.config import Settings


@pytest.mark.asyncio
async def test_generator_creates_quote():
    """Test that generator creates valid quote."""

    settings = Settings()
    settings.anthropic_api_key = "test-key"
    generator = QuoteGenerator(settings)

    mock_response = {
        "quote_id": "QT-2026-0001",
        "customer_email": "customer@brazil.com",
        "items": [{
            "product_name": "Paracetamol 500mg",
            "quantity": 50000,
            "unit_price": 2.50
        }],
        "total_amount": 125000.0,
        "valid_until": "2026-04-29",
        "shipping_port": "Shanghai",
        "payment_terms": "30% advance, 70% against B/L"
    }

    with patch.object(generator, '_call_llm') as mock_llm:
        mock_llm.return_value = json.dumps(mock_response)

        result = await generator.generate_quote(
            original_email="We want to order Paracetamol",
            context={
                "similar_emails": {"documents": []},
                "customer_history": {"tier": "B"},
                "pricing_policy": {"base_price": 2.0},
                "compliance": {}
            }
        )

        assert result["quote_id"] == "QT-2026-0001"
        assert result["total_amount"] == 125000.0


@pytest.mark.asyncio
async def test_generator_validates_required_fields():
    """Test that generator validates quote fields."""

    settings = Settings()
    settings.anthropic_api_key = "test-key"
    generator = QuoteGenerator(settings)

    # Missing 'items' field
    invalid_response = {"quote_id": "123", "total_amount": 1000}

    with patch.object(generator, '_call_llm') as mock_llm:
        mock_llm.return_value = str(invalid_response)

        with pytest.raises(QuoteGenerationError):
            await generator.generate_quote(
                original_email="test",
                context={}
            )
