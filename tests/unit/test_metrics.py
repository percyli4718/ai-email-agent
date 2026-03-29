import pytest
from email_agent.observability.metrics import MetricsCollector, metrics


def test_metrics_collector_singleton():
    """Test that metrics collector is a singleton."""
    collector1 = MetricsCollector()
    collector2 = MetricsCollector()
    assert collector1 is collector2


def test_metrics_increment():
    """Test metric increment."""
    # Use fresh global instance
    metrics._counters["test_counter"] = 0
    metrics.increment("test_counter", 1)
    assert metrics.get_counter("test_counter") == 1

    metrics.increment("test_counter", 2)
    assert metrics.get_counter("test_counter") == 3


def test_metrics_gauge():
    """Test gauge setting."""
    metrics.gauge("test_gauge", 50.0)
    assert metrics.get_gauge("test_gauge") == 50.0

    metrics.gauge("test_gauge", 75.0)
    assert metrics.get_gauge("test_gauge") == 75.0


def test_metrics_histogram():
    """Test histogram recording."""
    metrics._histograms["test_histogram"] = []

    metrics.histogram("test_histogram", 10)
    metrics.histogram("test_histogram", 20)
    metrics.histogram("test_histogram", 30)

    stats = metrics.get_histogram_stats("test_histogram")
    assert stats["count"] == 3
    assert stats["avg"] == 20
