import pytest
from unittest.mock import patch

from email_agent.layer3.router import ModelRouter, ModelChoice


def test_router_routes_simple_to_sonnet():
    """Test that simple contexts route to Sonnet."""
    router = ModelRouter()

    context = {
        "pricing_policy": {"products": ["Paracetamol"]},
        "compliance": {},
        "customer_history": {"tier": "A"}
    }

    result = router.route(context)
    assert result == ModelChoice.SONNET


def test_router_routes_complex_to_opus():
    """Test that complex contexts route to Opus."""
    router = ModelRouter()

    context = {
        "pricing_policy": {"products": ["P1", "P2", "P3", "P4", "P5", "P6"]},
        "compliance": {"special_permits": True, "restrictions": True},
        "customer_history": {}
    }

    result = router.route(context)
    assert result == ModelChoice.OPUS
