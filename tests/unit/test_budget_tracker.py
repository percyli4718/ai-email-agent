"""
预算追踪器单元测试

测试覆盖:
- BudgetEvent 数据类
- BudgetTracker 单例和线程安全
- 预算检查和警告
- 支出记录
- 事件历史查询
"""
import pytest
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock

from email_agent.observability.budget_tracker import BudgetTracker, BudgetEvent, BudgetExceededError
from email_agent.config import Settings


@pytest.fixture
def settings():
    """创建测试配置"""
    settings = Settings()
    settings.default_agent_budget = 1.00  # 设置较小的预算方便测试
    return settings


@pytest.fixture
def tracker(settings):
    """创建预算追踪器实例"""
    return BudgetTracker(settings)


# ============================================================================
# BudgetEvent 测试
# ============================================================================

class TestBudgetEvent:
    """BudgetEvent 数据类测试"""

    def test_budget_event_creation(self):
        """测试预算事件创建"""
        event = BudgetEvent(
            operation="test_op",
            cost=0.10,
            cumulative_cost=0.50,
            timestamp=datetime.now()
        )

        assert event.operation == "test_op"
        assert event.cost == 0.10
        assert event.cumulative_cost == 0.50
        assert event.event_type == "spending"  # 默认类型

    def test_budget_event_with_explicit_type(self):
        """测试指定事件类型"""
        event = BudgetEvent(
            operation="test_op",
            cost=0.10,
            cumulative_cost=1.50,
            timestamp=datetime.now(),
            event_type="budget_warning"
        )

        assert event.event_type == "budget_warning"


# ============================================================================
# BudgetTracker 基础测试
# ============================================================================

class TestBudgetTracker:
    """BudgetTracker 基础功能测试"""

    def test_tracker_initialization(self, settings):
        """测试追踪器初始化"""
        tracker = BudgetTracker(settings)

        assert tracker.settings is settings
        assert tracker.get_last_cost() == 0.0

    def test_get_spending_empty(self, tracker):
        """测试获取不存在的操作支出"""
        spending = tracker.get_spending("nonexistent_op")
        assert spending == 0.0

    def test_get_spending_after_record(self, tracker):
        """测试记录支出后获取"""
        tracker._spending["test_op"] = 0.50
        spending = tracker.get_spending("test_op")
        assert spending == 0.50

    def test_get_events_empty(self, tracker):
        """测试获取空事件列表"""
        events = tracker.get_events()
        assert events == []

    def test_get_events_with_limit(self, tracker):
        """测试获取限制数量的事件"""
        # 手动添加事件
        for i in range(10):
            tracker._events.append(BudgetEvent(
                operation=f"op_{i}",
                cost=0.01,
                cumulative_cost=0.01 * (i + 1),
                timestamp=datetime.now()
            ))

        # 获取前 5 个
        events = tracker.get_events(limit=5)
        assert len(events) == 5
        # 应该是最近 5 个
        assert events[0].operation == "op_5"


# ============================================================================
# BudgetTracker 预算检查测试
# ============================================================================

class TestBudgetCheck:
    """预算检查功能测试"""

    @pytest.mark.asyncio
    async def test_check_budget_within_limit(self, tracker):
        """测试预算内的检查"""
        # 预估成本在预算内，不应有警告
        with patch.object(tracker, '_record_event') as mock_record:
            await tracker.check_budget("test_op", estimated_cost=0.50)
            # 预算内不应记录警告
            mock_record.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_limit(self, tracker):
        """测试超出预算的检查"""
        # 先记录一些支出
        tracker._spending["test_op"] = 0.80

        with patch.object(tracker, '_record_event') as mock_record:
            await tracker.check_budget("test_op", estimated_cost=0.50)
            # 应该记录警告 (0.80 + 0.50 = 1.30 > 1.00)
            mock_record.assert_called_once()
            event = mock_record.call_args[0][0]
            assert event.event_type == "budget_warning"

    @pytest.mark.asyncio
    async def test_record_spending_within_budget(self, tracker):
        """测试记录预算内的支出"""
        await tracker.record_spending("test_op", actual_cost=0.30)

        assert tracker.get_spending("test_op") == 0.30
        assert tracker.get_last_cost() == 0.30

    @pytest.mark.asyncio
    async def test_record_spending_exceeds_budget(self, tracker):
        """测试记录超出预算的支出"""
        # 先记录一些支出
        tracker._spending["test_op"] = 0.80

        await tracker.record_spending("test_op", actual_cost=0.50)

        # 总支出应该是 1.30
        assert tracker.get_spending("test_op") == 1.30
        assert tracker.get_last_cost() == 0.50

        # 检查是否记录了硬限制事件
        events = tracker.get_events()
        assert len(events) == 1
        assert events[0].event_type == "budget_hard_kill"


# ============================================================================
# BudgetTracker 指标更新测试
# ============================================================================

class TestMetricsUpdate:
    """指标更新测试"""

    @pytest.mark.asyncio
    async def test_metrics_gauge_updated(self, tracker):
        """测试指标仪表盘更新"""
        with patch('email_agent.observability.budget_tracker.metrics') as mock_metrics:
            await tracker.record_spending("test_op", actual_cost=0.25)

            # 验证 metrics.gauge 被调用
            mock_metrics.gauge.assert_called_once()
            args = mock_metrics.gauge.call_args[0]
            assert "budget_test_op_spent" in args[0]
            assert args[1] == 0.25


# ============================================================================
# BudgetTracker 线程安全测试
# ============================================================================

class TestThreadSafety:
    """线程安全测试"""

    @pytest.mark.asyncio
    async def test_concurrent_record_spending(self, tracker):
        """测试并发记录支出的线程安全性"""
        results = []

        def record_spending():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            coro = tracker.record_spending("concurrent_op", 0.01)
            result = loop.run_until_complete(coro)
            results.append(result)
            loop.close()

        # 创建 10 个线程同时记录
        threads = []
        for _ in range(10):
            t = threading.Thread(target=record_spending)
            threads.append(t)

        # 启动所有线程
        for t in threads:
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证总支出
        total_spending = tracker.get_spending("concurrent_op")
        assert abs(total_spending - 0.10) < 0.0001  # 10 * 0.01，允许浮点误差


# ============================================================================
# BudgetTracker 事件历史限制测试
# ============================================================================

class TestEventHistoryLimit:
    """事件历史限制测试"""

    @pytest.mark.asyncio
    async def test_events_limited_to_1000(self, tracker):
        """测试事件历史限制在 1000 条"""
        # 记录 1100 个事件
        for i in range(1100):
            await tracker.record_spending(f"op_{i % 100}", 0.001)

        # 验证事件数量不超过 1000
        events = tracker.get_events(limit=2000)
        assert len(events) == 1000

        # 验证保留的是最近的事件
        # 最后一个事件应该是 op_99 (1099 % 100)
        assert events[-1].operation.startswith("op_")


# ============================================================================
# BudgetExceededError 测试
# ============================================================================

class TestBudgetExceededError:
    """预算超支错误测试"""

    def test_budget_exceeded_error_creation(self):
        """测试预算超支错误创建"""
        error = BudgetExceededError("Budget exceeded for test_op")

        assert str(error) == "Budget exceeded for test_op"

    def test_budget_exceeded_error_raise(self):
        """测试抛出预算超支错误"""
        with pytest.raises(BudgetExceededError):
            raise BudgetExceededError("Test error")
