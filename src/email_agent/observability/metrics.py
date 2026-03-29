from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading

from email_agent.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """In-memory metrics collector for observability."""

    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._history: List[MetricPoint] = []
        self._initialized = True

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict] = None) -> None:
        """Increment a counter."""
        self._counters[name] += value
        self._record(name, value, tags or {})

    def gauge(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """Set a gauge value."""
        self._gauges[name] = value
        self._record(name, value, tags or {})

    def histogram(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """Record a histogram value."""
        self._histograms[name].append(value)
        self._record(name, value, tags or {})

    def _record(self, name: str, value: float, tags: Dict) -> None:
        """Record a metric point."""
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags
        )
        self._history.append(point)

        if len(self._history) > 10000:
            self._history = self._history[-10000:]

    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """Get current gauge value."""
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self._histograms.get(name, [])
        if not values:
            return {}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": sorted(values)[len(values) // 2],
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else max(values)
        }

    def get_recent_metrics(self, limit: int = 100) -> List[MetricPoint]:
        """Get recent metric points."""
        return self._history[-limit:]


metrics = MetricsCollector()


def record_metric(name: str, value: float = 1.0, tags: Optional[Dict] = None) -> None:
    """Convenience function to record a metric."""
    metrics.increment(name, value, tags)
