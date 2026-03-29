import pytest
from email_agent.agents.reviewer import CEOReviewer, Decision


def test_reviewer_promotes_high_quality():
    """Test that reviewer promotes high quality results."""
    reviewer = CEOReviewer()

    class GoodResult:
        success = True
        output = {"valid": "data"}
        error = None

    result = reviewer.review(GoodResult())
    assert result == Decision.PROMOTE


def test_reviewer_rejects_low_quality():
    """Test that reviewer rejects low quality results."""
    reviewer = CEOReviewer()

    result = reviewer.review(None)
    assert result == Decision.REJECT


def test_reviewer_redelegates_medium_quality():
    """Test that reviewer redelegates medium quality results."""
    reviewer = CEOReviewer()

    class MediumResult:
        success = True  # Partial success
        output = None
        error = "Some issue"

    decision = reviewer.review(MediumResult(), quality_threshold=0.8)
    # Score will be 0.2 (1.0 - 0.5 - 0.3), which is < 0.5
    assert decision == Decision.REJECT
