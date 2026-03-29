import pytest
from email_agent.agents.ceo_agent import CEOAgent, DependencyGraph


def test_ceo_decomposes_inquiry():
    """Test that CEO Agent decomposes inquiry into tasks."""
    ceo = CEOAgent()

    classification = {
        "type": "inquiry",
        "products_mentioned": ["Paracetamol"],
        "customer_region": "brazil"
    }

    graph = ceo.decompose_inquiry(
        email_body="We want to order",
        classification=classification
    )

    # Should have at least 3 tasks: price, compliance, logistics
    assert len(graph.tasks) >= 3


def test_dependency_graph_tracks_dependencies():
    """Test that dependency graph correctly tracks dependencies."""
    graph = DependencyGraph()

    task1 = graph.add_task("agent1", {}, budget=0.10)
    task2 = graph.add_task("agent2", {}, budget=0.10, dependencies=[task1])

    # task2 should depend on task1
    assert task1 in graph.tasks[task2].dependencies
