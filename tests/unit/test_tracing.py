import pytest
from email_agent.observability.tracing import Tracer, tracer, trace_span


def test_tracer_singleton():
    """Test that tracer is a singleton."""
    tracer1 = Tracer()
    tracer2 = Tracer()
    assert tracer1 is tracer2


def test_tracer_creates_spans():
    """Test span creation."""
    with tracer.span("test_span", tags={"key": "value"}) as span:
        assert span.name == "test_span"
        assert span.tags["key"] == "value"
        assert span.start_time is not None

    assert span.end_time is not None
    assert span.duration_ms() is not None


def test_trace_span_context_manager():
    """Test trace_span context manager."""
    with trace_span("outer", tags={"level": "outer"}) as outer:
        with trace_span("inner", tags={"level": "inner"}) as inner:
            assert inner.parent_id == outer.id
