import pytest
from email_agent.agents.sandbox import AgentSandbox, AgentResult


@pytest.mark.asyncio
async def test_sandbox_executes_within_budget():
    """Test that sandbox enforces budget limits."""

    async def mock_agent(input_data, db):
        class Result:
            cost = 0.05
        return Result()

    sandbox = AgentSandbox(budget=0.10)

    # First execution should succeed
    result = await sandbox.execute(mock_agent, {}, "test_agent")
    assert result.success is True

    # Second execution should succeed (total: 0.10)
    result = await sandbox.execute(mock_agent, {}, "test_agent")
    assert result.success is True

    # Third execution should fail (would exceed budget)
    result = await sandbox.execute(mock_agent, {}, "test_agent")
    assert result.success is False
    assert "Budget exceeded" in result.error


@pytest.mark.asyncio
async def test_sandbox_write_isolation():
    """Test that sandbox provides write isolation."""
    from email_agent.agents.sandbox import WriteIsolatedDB

    db = WriteIsolatedDB()

    # Write to isolated DB
    db.execute("INSERT INTO prices (product_code, base_price) VALUES (?, ?)",
               ("TEST", 100.0))

    # Should be able to read
    results = db.query("SELECT * FROM prices WHERE product_code = ?", ("TEST",))
    assert len(results) == 1
    assert results[0][1] == 100.0
