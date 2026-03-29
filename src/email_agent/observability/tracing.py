from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading
import uuid

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Span:
    """A tracing span."""
    id: str
    name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)

    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if not self.start_time or not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000


class Tracer:
    """Simple distributed tracer."""

    _instance: Optional["Tracer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "Tracer":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._spans: Dict[str, Span] = {}
        self._current_span: List[Optional[str]] = [None]
        self._traces: List[str] = []
        self._initialized = True

    @contextmanager
    def span(self, name: str, tags: Optional[Dict] = None):
        """Create and manage a span."""
        span_id = str(uuid.uuid4())[:8]
        parent_id = self._current_span[-1]

        span = Span(
            id=span_id,
            name=name,
            start_time=datetime.now(),
            tags=tags or {},
            parent_id=parent_id
        )

        self._spans[span_id] = span

        if parent_id and parent_id in self._spans:
            self._spans[parent_id].children.append(span_id)
        else:
            self._traces.append(span_id)

        self._current_span.append(span_id)

        try:
            yield span
        finally:
            span.end_time = datetime.now()
            self._current_span.pop()

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get a complete trace with all spans."""
        if trace_id not in self._spans:
            return None

        def build_tree(span_id: str) -> Dict:
            span = self._spans[span_id]
            return {
                "id": span.id,
                "name": span.name,
                "duration_ms": span.duration_ms(),
                "tags": span.tags,
                "children": [build_tree(c) for c in span.children]
            }

        return build_tree(trace_id)

    def get_recent_traces(self, limit: int = 10) -> List[Dict]:
        """Get recent root traces."""
        return [self.get_trace(trace_id) for trace_id in self._traces[-limit:]]


tracer = Tracer()


@contextmanager
def trace_span(name: str, tags: Optional[Dict] = None):
    """Convenience function to create a span."""
    with tracer.span(name, tags):
        yield
