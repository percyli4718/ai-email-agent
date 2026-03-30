"""
预算追踪模块

模块作用:
    本模块实现 Agent 操作的预算追踪和限制系统。
    记录每个操作的支出，在接近或超过预算时发出警告或阻止执行。

使用场景:
    - 追踪 LLM API 调用的成本
    - 在预算不足时阻止操作执行
    - 记录预算事件用于审计和分析

在项目中的位置:
    位于 src/email_agent/observability/budget_tracker.py，
    是应用成本控制系统的核心组件，
    被 generator.py 等模块调用进行预算检查。
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import threading

from email_agent.config import Settings
from email_agent.logging_config import get_logger
from email_agent.observability.metrics import metrics

# 获取当前模块的日志记录器
logger = get_logger(__name__)


@dataclass
class BudgetEvent:
    """
    预算事件的数据结构

    作用:
        封装预算相关的事件记录，包括支出、累计成本和事件类型。

    字段说明:
        operation: str 类型，操作名称
            例如："quote_generation", "email_classification"

        cost: float 类型，本次事件的成本
            单次操作的支出金额 (美元)

        cumulative_cost: float 类型，累计成本
            该操作从开始到现在的总支出

        timestamp: datetime 类型，时间戳
            事件发生的时间点

        event_type: str 类型，事件类型 (默认"spending")
            - "spending": 正常支出
            - "budget_warning": 预算警告
            - "budget_hard_kill": 预算超支强制终止

    使用场景:
        - 记录每次 API 调用的成本
        - 审计预算使用情况
        - 分析成本分布
    """
    operation: str
    cost: float
    cumulative_cost: float
    timestamp: datetime
    event_type: str = "spending"


class BudgetTracker:
    """
    预算追踪器

    作用:
        追踪和限制 Agent 操作的预算使用。
        支持预算检查、支出记录和事件历史查询。

    使用场景:
        - 在 LLM 调用前检查预算是否充足
        - 记录实际 API 支出
        - 查询预算使用历史

    主要方法:
        check_budget: 检查操作是否在预算内
        record_spending: 记录实际支出
        get_spending: 获取操作的总支出
        get_events: 获取预算事件历史

    属性:
        settings: Settings 类型，应用配置
        _lock: threading.Lock 类型，线程锁
        _spending: Dict[str, float] 类型，各操作的支出记录
        _events: List[BudgetEvent] 类型，预算事件历史 (最多 1000 条)

    线程安全:
        使用 threading.Lock 确保并发访问的安全性
    """

    def __init__(self, settings: Settings):
        """
        初始化预算追踪器

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._lock = threading.Lock()  # 线程锁
        self._spending: Dict[str, float] = {}  # 各操作的支出记录
        self._events: List[BudgetEvent] = []  # 预算事件历史

    async def check_budget(self, operation: str, estimated_cost: float) -> None:
        """
        检查操作是否在预算内

        功能描述:
            在执行操作前检查预估成本是否会超出预算。
            如果 projected > budget，记录警告事件。

        参数:
            operation: str 类型，操作名称
            estimated_cost: float 类型，预估成本 (美元)

        返回值:
            无

        异常:
            无

        处理逻辑:
            1. 获取当前已支出金额
            2. 计算预计总支出 (当前 + 预估)
            3. 如果超出预算，记录警告事件
            4. 不抛出异常，仅记录警告

        使用场景:
            - LLM 调用前检查预算
            - 决策是否使用更昂贵的模型
        """
        with self._lock:
            # 获取当前操作的已支出金额
            current = self._spending.get(operation, 0.0)
            # 计算预计总支出
            projected = current + estimated_cost

            # 检查是否超出预算
            if projected > self.settings.default_agent_budget:
                logger.warning(
                    "budget_warning",
                    operation=operation,
                    current=current,
                    projected=projected,
                    limit=self.settings.default_agent_budget
                )
                # 记录预算警告事件
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=estimated_cost,
                    cumulative_cost=projected,
                    timestamp=datetime.now(),
                    event_type="budget_warning"
                ))

    async def record_spending(self, operation: str, actual_cost: float) -> None:
        """
        记录实际支出

        功能描述:
            在操作完成后记录实际成本。
            如果超出预算，记录硬限制事件并更新指标。

        参数:
            operation: str 类型，操作名称
            actual_cost: float 类型，实际成本 (美元)

        返回值:
            无

        异常:
            无

        处理逻辑:
            1. 更新操作的累计支出
            2. 检查是否超出预算
            3. 记录支出事件或硬限制事件
            4. 更新指标仪表盘

        使用场景:
            - LLM 调用后记录实际成本
            - 追踪预算使用情况
        """
        with self._lock:
            # 获取当前已支出金额
            current = self._spending.get(operation, 0.0)
            # 计算新的总支出
            new_total = current + actual_cost
            # 更新支出记录
            self._spending[operation] = new_total

            # 检查是否超出预算
            if new_total > self.settings.default_agent_budget:
                # 记录预算超支硬限制事件
                logger.warning(
                    "budget_hard_kill",
                    operation=operation,
                    total=new_total,
                    limit=self.settings.default_agent_budget
                )
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=actual_cost,
                    cumulative_cost=new_total,
                    timestamp=datetime.now(),
                    event_type="budget_hard_kill"
                ))
            else:
                # 记录正常支出事件
                self._record_event(BudgetEvent(
                    operation=operation,
                    cost=actual_cost,
                    cumulative_cost=new_total,
                    timestamp=datetime.now()
                ))

            # 更新指标仪表盘，用于监控
            metrics.gauge(f"budget_{operation}_spent", new_total)

    def _record_event(self, event: BudgetEvent) -> None:
        """
        记录预算事件

        功能描述:
            将预算事件添加到历史记录。
            限制历史记录最多 1000 条，自动清理旧数据。

        参数:
            event: BudgetEvent 类型，预算事件对象

        返回值:
            无

        异常:
            无
        """
        self._events.append(event)
        # 限制历史记录大小，保留最近 1000 条
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

    def get_spending(self, operation: str) -> float:
        """
        获取操作的总支出

        功能描述:
            返回指定操作的累计支出金额。

        参数:
            operation: str 类型，操作名称

        返回值:
            float: 总支出金额 (美元)，不存在返回 0.0

        异常:
            无
        """
        return self._spending.get(operation, 0.0)

    def get_events(self, limit: int = 100) -> List[BudgetEvent]:
        """
        获取最近的预算事件

        功能描述:
            返回最近的 N 条预算事件记录。

        参数:
            limit: int 类型，返回数量限制 (默认 100)

        返回值:
            List[BudgetEvent]: 最近的预算事件列表

        异常:
            无
        """
        return self._events[-limit:]


class BudgetExceededError(Exception):
    """
    预算超支错误异常类

    作用:
        当预算被超支时抛出此异常。
        目前主要用于标记预算超支的情况。

    使用场景:
        - 需要在预算超支时抛出异常的场景
        - 捕获并处理预算超支的情况
    """
    pass
