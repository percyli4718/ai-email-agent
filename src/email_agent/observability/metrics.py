"""
指标收集模块

模块作用:
    本模块实现应用的性能指标收集系统，支持计数器 (counter)、仪表盘 (gauge)
    和直方图 (histogram) 三种指标类型。使用单例模式确保全局唯一的指标收集器。

使用场景:
    - 记录 API 调用次数、处理时间、成本等指标
    - 在 metrics dashboard 中展示系统性能
    - 监控应用健康状态和性能趋势

在项目中的位置:
    位于 src/email_agent/observability/metrics.py，
    是应用可观测性系统的核心组件，
    被各业务模块调用记录性能指标。
"""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """
    单个指标数据点

    作用:
        封装指标的最小数据单元，包含指标名称、值、时间戳和标签。

    字段说明:
        name: str 类型，指标名称
            例如："email_processed_total", "processing_time_ms"

        value: float 类型，指标值
            指标的具体数值

        timestamp: datetime 类型，时间戳
            指标记录的时间点

        tags: Dict[str, str] 类型，标签字典
            用于维度分析的键值对，例如：{"model": "sonnet"}

    使用场景:
        - 作为 MetricsCollector._history 的存储单元
        - 支持时间序列查询和过滤
    """
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器 (单例模式)

    作用:
        全局唯一的指标收集器，使用单例模式确保数据一致性。
        支持三种指标类型：
        - Counter: 累加计数器 (如请求总数)
        - Gauge: 瞬时值仪表盘 (如当前连接数)
        - Histogram: 分布直方图 (如响应时间分布)

    使用场景:
        - 各业务模块记录性能指标
        - API 端点查询指标数据
        - 监控系统集成

    主要方法:
        increment: 增加计数器
        gauge: 设置仪表盘值
        histogram: 记录直方图数据
        get_counter: 获取计数器当前值
        get_gauge: 获取仪表盘当前值
        get_histogram_stats: 获取直方图统计信息
        get_recent_metrics: 获取最近的指标记录

    属性:
        _counters: Dict[str, float] 类型，计数器存储
        _gauges: Dict[str, float] 类型，仪表盘存储
        _histograms: Dict[str, List[float]] 类型，直方图存储
        _history: List[MetricPoint] 类型，历史记录 (最多 10000 条)

    线程安全:
        使用 threading.Lock 确保单例初始化的线程安全
    """

    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        """
        单例模式：创建或获取唯一实例

        功能描述:
            使用双重检查锁定实现线程安全的单例模式。
            确保整个应用只有一个 MetricsCollector 实例。

        参数:
            无

        返回值:
            MetricsCollector: 唯一的实例对象

        异常:
            无
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化指标收集器

        参数:
            无

        返回值:
            无

        异常:
            无

        说明:
            由于是单例模式，如果已初始化则直接返回
        """
        if self._initialized:
            return

        # 计数器：累加值 (如请求总数)
        self._counters: Dict[str, float] = defaultdict(float)
        # 仪表盘：瞬时值 (如当前连接数)
        self._gauges: Dict[str, float] = {}
        # 直方图：分布数据 (如响应时间)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        # 历史记录：时间序列数据
        self._history: List[MetricPoint] = []
        self._initialized = True

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict] = None) -> None:
        """
        增加计数器值

        功能描述:
            将指定计数器的值增加指定数量。
            同时记录到历史记录中用于时间序列查询。

        参数:
            name: str 类型，计数器名称
            value: float 类型，增加的值 (默认 1.0)
            tags: Optional[Dict] 类型，标签字典 (可选)

        返回值:
            无

        异常:
            无

        使用示例:
            metrics.increment("email_processed_total")  # +1
            metrics.increment("api_calls", 2.0)  # +2
        """
        # 累加计数器
        self._counters[name] += value
        # 记录到历史
        self._record(name, value, tags or {})

    def gauge(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """
        设置仪表盘值

        功能描述:
            设置指定仪表盘的当前值。
            仪表盘用于记录瞬时值，如当前活跃连接数。

        参数:
            name: str 类型，仪表盘名称
            value: float 类型，设置的值
            tags: Optional[Dict] 类型，标签字典 (可选)

        返回值:
            无

        异常:
            无

        使用示例:
            metrics.gauge("active_connections", 42)
            metrics.gauge("budget_spent", 0.75)
        """
        # 设置仪表盘值 (覆盖)
        self._gauges[name] = value
        # 记录到历史
        self._record(name, value, tags or {})

    def histogram(self, name: str, value: float, tags: Optional[Dict] = None) -> None:
        """
        记录直方图数据

        功能描述:
            将值添加到直方图中，用于统计分布。
            支持计算平均值、百分位数等统计信息。

        参数:
            name: str 类型，直方图名称
            value: float 类型，记录的值
            tags: Optional[Dict] 类型，标签字典 (可选)

        返回值:
            无

        异常:
            无

        使用示例:
            metrics.histogram("processing_time_ms", 150.5)
        """
        # 添加到直方图数据
        self._histograms[name].append(value)
        # 记录到历史
        self._record(name, value, tags or {})

    def _record(self, name: str, value: float, tags: Dict) -> None:
        """
        记录指标点到历史

        功能描述:
            创建 MetricPoint 并添加到历史记录。
            限制历史记录最多 10000 条，自动清理旧数据。

        参数:
            name: str 类型，指标名称
            value: float 类型，指标值
            tags: Dict 类型，标签字典

        返回值:
            无

        异常:
            无
        """
        # 创建指标点
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags
        )
        self._history.append(point)

        # 限制历史记录大小，保留最近 10000 条
        if len(self._history) > 10000:
            self._history = self._history[-10000:]

    def get_counter(self, name: str) -> float:
        """
        获取计数器当前值

        功能描述:
            返回指定计数器的当前累加值。

        参数:
            name: str 类型，计数器名称

        返回值:
            float: 计数器值，不存在返回 0.0

        异常:
            无
        """
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """
        获取仪表盘当前值

        功能描述:
            返回指定仪表盘的当前值。

        参数:
            name: str 类型，仪表盘名称

        返回值:
            Optional[float]: 仪表盘值，不存在返回 None

        异常:
            无
        """
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """
        获取直方图统计信息

        功能描述:
            计算并返回直方图的各项统计指标。

        参数:
            name: str 类型，直方图名称

        返回值:
            Dict[str, float]: 统计信息字典，包含:
                - count: 数据点数量
                - min: 最小值
                - max: 最大值
                - avg: 平均值
                - p50: 中位数 (50 百分位)
                - p95: 95 百分位值

        异常:
            无

        使用示例:
            stats = metrics.get_histogram_stats("processing_time_ms")
            print(f"平均处理时间：{stats['avg']}ms")
        """
        values = self._histograms.get(name, [])
        if not values:
            return {}

        sorted_values = sorted(values)
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": sorted_values[len(values) // 2],
            "p95": sorted_values[int(len(values) * 0.95)] if len(values) > 1 else max(values)
        }

    def get_recent_metrics(self, limit: int = 100) -> List[MetricPoint]:
        """
        获取最近的指标记录

        功能描述:
            返回最近的 N 条指标记录，用于时间序列展示。

        参数:
            limit: int 类型，返回数量限制 (默认 100)

        返回值:
            List[MetricPoint]: 最近的指标点列表

        异常:
            无
        """
        return self._history[-limit:]


# 全局唯一的指标收集器实例
metrics = MetricsCollector()


def record_metric(name: str, value: float = 1.0, tags: Optional[Dict] = None) -> None:
    """
    便捷函数：记录指标

    功能描述:
        封装 metrics.increment() 的便捷函数。
        用于快速记录计数器指标。

    参数:
        name: str 类型，指标名称
        value: float 类型，指标值 (默认 1.0)
        tags: Optional[Dict] 类型，标签字典 (可选)

    返回值:
        无

    异常:
        无

    使用示例:
        record_metric("email_processed")
        record_metric("api_error", tags={"type": "timeout"})
    """
    metrics.increment(name, value, tags)
