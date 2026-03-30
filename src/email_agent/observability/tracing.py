"""
分布式追踪模块

模块作用:
    本模块实现简单的分布式追踪系统，支持创建和管理追踪跨度 (span)。
    通过树形结构记录操作的调用链和耗时，用于性能分析和问题排查。

使用场景:
    - 追踪请求在系统中的完整处理流程
    - 分析各组件的性能瓶颈
    - 排查分布式系统中的问题

在项目中的位置:
    位于 src/email_agent/observability/tracing.py，
    是应用可观测性系统的核心组件，
    被各业务模块调用记录操作追踪。
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading
import uuid

from email_agent.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@dataclass
class Span:
    """
    追踪跨度 (Span)

    作用:
        封装追踪中的一个操作单元，记录操作的开始/结束时间和元数据。
        支持父子关系，形成追踪树。

    字段说明:
        id: str 类型，跨度唯一标识符
            使用 UUID 的前 8 位字符

        name: str 类型，跨度名称
            例如："classify_email", "generate_quote"

        start_time: Optional[datetime] 类型，开始时间
            跨度开始的时间点

        end_time: Optional[datetime] 类型，结束时间
            跨度结束的时间点

        tags: Dict[str, str] 类型，标签字典
            跨度的元数据，如：{"model": "sonnet"}

        parent_id: Optional[str] 类型，父跨度 ID
            用于构建追踪树

        children: List[str] 类型，子跨度 ID 列表
            记录所有子跨度

    主要方法:
        duration_ms: 获取跨度持续时间 (毫秒)

    使用场景:
        - 记录 API 调用的完整生命周期
        - 分析嵌套操作的性能
    """
    id: str
    name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)

    def duration_ms(self) -> Optional[float]:
        """
        获取跨度持续时间 (毫秒)

        功能描述:
            计算 span 从开始到结束的时间差，转换为毫秒。

        参数:
            无

        返回值:
            Optional[float]: 持续时间 (毫秒)
                - 如果 start_time 或 end_time 为空，返回 None
                - 否则返回毫秒数

        异常:
            无

        使用示例:
            span.duration_ms()  # 返回 150.5 表示 150.5 毫秒
        """
        # 检查开始和结束时间是否都存在
        if not self.start_time or not self.end_time:
            return None
        # 计算时间差并转换为毫秒
        return (self.end_time - self.start_time).total_seconds() * 1000


class Tracer:
    """
    分布式追踪器 (单例模式)

    作用:
        管理追踪跨度的创建、关联和查询。
        使用单例模式确保全局追踪状态一致。

    使用场景:
        - 在关键操作中创建追踪跨度
        - 查询完整追踪树用于分析
        - 获取最近的追踪记录

    主要方法:
        span: 创建和管理跨度的上下文管理器
        get_trace: 获取完整追踪树
        get_recent_traces: 获取最近的根跨度

    属性:
        _spans: Dict[str, Span] 类型，所有跨度存储
        _current_span: List[Optional[str]] 类型，当前跨度栈
        _traces: List[str] 类型，根跨度 ID 列表

    线程安全:
        使用 threading.Lock 确保单例初始化的线程安全
    """

    _instance: Optional["Tracer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "Tracer":
        """
        单例模式：创建或获取唯一实例

        功能描述:
            使用双重检查锁定实现线程安全的单例模式。

        参数:
            无

        返回值:
            Tracer: 唯一的实例对象

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
        初始化追踪器

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        if self._initialized:
            return

        # 存储所有跨度，key 为 span ID
        self._spans: Dict[str, Span] = {}
        # 当前跨度栈，支持嵌套追踪
        self._current_span: List[Optional[str]] = [None]
        # 根跨度 ID 列表，用于获取追踪
        self._traces: List[str] = []
        self._initialized = True

    @contextmanager
    def span(self, name: str, tags: Optional[Dict] = None):
        """
        创建和管理追踪跨度 (上下文管理器)

        功能描述:
            使用上下文管理器自动管理跨度的生命周期。
            支持嵌套跨度，自动建立父子关系。

        参数:
            name: str 类型，跨度名称
            tags: Optional[Dict] 类型，跨度标签 (可选)

        返回值:
            Span: 创建的跨度对象

        异常:
            无

        使用示例:
            with tracer.span("process_email") as span:
                span.tags["email_id"] = "123"
                # 执行操作...
        """
        # 生成跨度 ID (UUID 前 8 位)
        span_id = str(uuid.uuid4())[:8]
        # 获取父跨度 ID (当前栈顶)
        parent_id = self._current_span[-1]

        # 创建新跨度
        span = Span(
            id=span_id,
            name=name,
            start_time=datetime.now(),
            tags=tags or {},
            parent_id=parent_id
        )

        # 存储跨度
        self._spans[span_id] = span

        # 建立父子关系
        if parent_id and parent_id in self._spans:
            # 添加到父跨度的子节点列表
            self._spans[parent_id].children.append(span_id)
        else:
            # 记录为根跨度
            self._traces.append(span_id)

        # 将当前跨度压入栈
        self._current_span.append(span_id)

        try:
            # yield 给调用者使用
            yield span
        finally:
            # 跨度结束，记录结束时间
            span.end_time = datetime.now()
            # 弹出当前跨度
            self._current_span.pop()

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """
        获取完整的追踪树

        功能描述:
            根据追踪 ID 获取完整的追踪树结构。
            递归构建包含所有子跨度的树形结构。

        参数:
            trace_id: str 类型，根跨度 ID

        返回值:
            Optional[Dict]: 追踪树字典，包含:
                - id: 跨度 ID
                - name: 跨度名称
                - duration_ms: 持续时间
                - tags: 标签
                - children: 子追踪树列表
                如果 trace_id 不存在，返回 None

        异常:
            无

        使用示例:
            trace = tracer.get_trace("abc12345")
            print(trace['children'])  # 查看所有子跨度
        """
        # 检查跨度是否存在
        if trace_id not in self._spans:
            return None

        def build_tree(span_id: str) -> Dict:
            """递归构建追踪树"""
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
        """
        获取最近的追踪记录

        功能描述:
            返回最近的 N 个根跨度及其完整追踪树。

        参数:
            limit: int 类型，返回数量限制 (默认 10)

        返回值:
            List[Dict]: 追踪树列表，每个元素是一个完整的追踪树

        异常:
            无

        使用示例:
            traces = tracer.get_recent_traces(limit=20)
        """
        # 获取最近的根跨度，构建追踪树
        return [self.get_trace(trace_id) for trace_id in self._traces[-limit:]]


# 全局唯一的追踪器实例
tracer = Tracer()


@contextmanager
def trace_span(name: str, tags: Optional[Dict] = None):
    """
    便捷函数：创建追踪跨度

    功能描述:
        封装 tracer.span() 的便捷函数。
        用于快速创建追踪跨度。

    参数:
        name: str 类型，跨度名称
        tags: Optional[Dict] 类型，跨度标签 (可选)

    返回值:
        Span: 创建的跨度对象

    异常:
        无

    使用示例:
        with trace_span("classify_email") as span:
            # 执行分类操作...
            pass
    """
    with tracer.span(name, tags) as span:
        yield span
