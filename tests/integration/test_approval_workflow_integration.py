"""
审批工作流集成测试

测试场景:
1. 创建审批请求并自动生成通知
2. 审批通过流程
3. 审批拒绝流程
4. 审批状态查询
5. 自动审批规则（金额阈值）
6. 审批历史记录

集成测试说明:
- 测试数据库、API 和业务逻辑的集成
- 使用真实数据库（SQLite 内存）
- 验证端到端流程
"""
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from email_agent.main import app
from email_agent.config import Settings
from email_agent.storage.database import get_database


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """创建测试配置"""
    settings = Settings()
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.env = "test"
    return settings


@pytest.fixture(autouse=True)
def override_db(test_settings):
    """覆盖数据库依赖"""
    async def get_test_db():
        db = get_database(test_settings)
        await db.init_tables()
        return db

    app.dependency_overrides[get_database] = get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """创建测试客户端"""
    with TestClient(app) as client:
        yield client


# ============================================================================
# 审批请求创建测试
# ============================================================================

@pytest.mark.asyncio
async def test_create_approval_request_auto_approved(test_settings):
    """测试创建审批请求 - 低于阈值自动批准"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建低于阈值的审批请求（< $10000）
    request = await db.create_approval_request(
        email_id="email_001",
        requester="price_agent",
        request_type="high_amount",
        reason="Quote amount verification",
        amount=5000,  # 低于阈值
        currency="USD",
        details={"quote_id": "QT-001"}
    )

    # 验证请求创建成功
    assert request is not None
    assert request["email_id"] == "email_001"
    assert request["amount"] == 5000
    # 应该自动批准
    assert request["status"] == "approved"


@pytest.mark.asyncio
async def test_create_approval_request_pending(test_settings):
    """测试创建审批请求 - 高于阈值待审批"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建高于阈值的审批请求（> $10000）
    request = await db.create_approval_request(
        email_id="email_002",
        requester="price_agent",
        request_type="high_amount",
        reason="Amount exceeds threshold",
        amount=50000,  # 高于阈值
        currency="USD",
        details={"quote_id": "QT-002"}
    )

    # 验证请求创建成功
    assert request is not None
    assert request["email_id"] == "email_002"
    assert request["amount"] == 50000
    # 应该待审批
    assert request["status"] == "pending"


@pytest.mark.asyncio
async def test_create_approval_request_creates_notification(test_settings):
    """测试创建审批请求时自动生成通知"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建审批请求
    request = await db.create_approval_request(
        email_id="email_003",
        requester="price_agent",
        request_type="high_amount",
        reason="Requires manual review",
        amount=30000,
        currency="USD"
    )

    # 验证通知创建
    notifications = await db.get_notifications(limit=10)
    approval_notifications = [n for n in notifications if n.get("type") == "approval_request"]

    assert len(approval_notifications) > 0
    notification = approval_notifications[0]
    assert notification["related_id"] == str(request["id"])


# ============================================================================
# 审批操作测试
# ============================================================================

@pytest.mark.asyncio
async def test_approve_request(test_settings):
    """测试批准请求"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建待审批请求
    request = await db.create_approval_request(
        email_id="email_004",
        requester="price_agent",
        request_type="high_amount",
        reason="Test approval",
        amount=20000,
        currency="USD",
        status="pending"
    )

    # 批准请求
    result = await db.approve_request(
        request_id=request["id"],
        reviewer="admin",
        comments="Approved for testing"
    )

    # 验证批准结果
    assert result is not None
    assert result["status"] == "approved"
    assert result["reviewer"] == "admin"


@pytest.mark.asyncio
async def test_reject_request(test_settings):
    """测试拒绝请求"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建待审批请求
    request = await db.create_approval_request(
        email_id="email_005",
        requester="price_agent",
        request_type="high_amount",
        reason="Test rejection",
        amount=25000,
        currency="USD",
        status="pending"
    )

    # 拒绝请求
    result = await db.reject_request(
        request_id=request["id"],
        reviewer="manager",
        comments="Rejected due to budget constraints"
    )

    # 验证拒绝结果
    assert result is not None
    assert result["status"] == "rejected"
    assert result["reviewer"] == "manager"
    assert result["comments"] == "Rejected due to budget constraints"


# ============================================================================
# API 端点测试
# ============================================================================

def test_get_approval_requests_api(client):
    """测试获取审批请求列表 API"""
    # 请求 API
    response = client.get("/api/approvals")

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "requests" in data
    assert "total" in data


def test_get_approval_requests_by_status_api(client):
    """测试按状态获取审批请求 API"""
    # 请求 API - 只获取 pending 状态
    response = client.get("/api/approvals?status=pending")

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "requests" in data

    # 验证返回的都是 pending 状态
    for request in data["requests"]:
        assert request["status"] == "pending"


# ============================================================================
# 审批规则测试
# ============================================================================

def test_auto_approval_rule_below_threshold(test_settings):
    """测试自动审批规则 - 低于阈值"""
    db = get_database(test_settings)

    # 测试不同金额
    test_amounts = [1000, 5000, 9999]

    for amount in test_amounts:
        request = db.create_approval_request_sync(
            email_id=f"email_auto_{amount}",
            requester="price_agent",
            request_type="high_amount",
            reason="Auto approval test",
            amount=amount,
            currency="USD"
        )
        # 低于阈值应该自动批准
        assert request["status"] == "approved", f"Amount {amount} should be auto-approved"


def test_auto_approval_rule_above_threshold(test_settings):
    """测试自动审批规则 - 高于阈值"""
    db = get_database(test_settings)

    # 测试不同金额
    test_amounts = [10001, 20000, 50000, 100000]

    for amount in test_amounts:
        request = db.create_approval_request_sync(
            email_id=f"email_manual_{amount}",
            requester="price_agent",
            request_type="high_amount",
            reason="Manual approval required",
            amount=amount,
            currency="USD"
        )
        # 高于阈值需要人工审批
        assert request["status"] == "pending", f"Amount {amount} should require manual approval"


# ============================================================================
# 边界情况测试
# ============================================================================

@pytest.mark.asyncio
async def test_approve_nonexistent_request(test_settings):
    """测试批准不存在的请求"""
    db = get_database(test_settings)
    await db.init_tables()

    # 尝试批准不存在的请求
    result = await db.approve_request(
        request_id=99999,
        reviewer="admin",
        comments="Test"
    )

    # 应该返回 None
    assert result is None


@pytest.mark.asyncio
async def test_reject_nonexistent_request(test_settings):
    """测试拒绝不存在的请求"""
    db = get_database(test_settings)
    await db.init_tables()

    # 尝试拒绝不存在的请求
    result = await db.reject_request(
        request_id=99999,
        reviewer="admin",
        comments="Test"
    )

    # 应该返回 None
    assert result is None


@pytest.mark.asyncio
async def test_double_approval(test_settings):
    """测试重复批准"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建并批准请求
    request = await db.create_approval_request(
        email_id="email_double",
        requester="price_agent",
        request_type="high_amount",
        reason="Test double approval",
        amount=15000,
        currency="USD",
        status="pending"
    )

    # 第一次批准
    result1 = await db.approve_request(request["id"], "admin", "First approval")
    assert result1 is not None
    assert result1["status"] == "approved"

    # 尝试第二次批准（应该失败或返回已批准状态）
    result2 = await db.approve_request(request["id"], "another_admin", "Second approval")
    # 根据实现可能返回 None 或保持原状态
    # 这里验证不会改变状态
    if result2 is not None:
        assert result2["status"] == "approved"


@pytest.mark.asyncio
async def test_approval_with_empty_comments(test_settings):
    """测试空注释的批准"""
    db = get_database(test_settings)
    await db.init_tables()

    # 创建请求
    request = await db.create_approval_request(
        email_id="email_empty_comment",
        requester="price_agent",
        request_type="high_amount",
        reason="Test empty comments",
        amount=8000,
        currency="USD",
        status="pending"
    )

    # 批准时不带注释
    result = await db.approve_request(request["id"], "admin", "")

    # 验证批准成功（注释可以为空）
    assert result is not None
    assert result["status"] == "approved"


# ============================================================================
# 集成场景测试
# ============================================================================

@pytest.mark.asyncio
async def test_full_approval_workflow(test_settings):
    """测试完整审批工作流"""
    db = get_database(test_settings)
    await db.init_tables()

    # 1. 创建审批请求
    request = await db.create_approval_request(
        email_id="email_workflow",
        requester="price_agent",
        request_type="high_amount",
        reason="Large order requires approval",
        amount=75000,
        currency="USD",
        details={"quote_id": "QT-WORKFLOW", "customer": "VIP Customer"}
    )

    # 2. 验证初始状态
    assert request["status"] == "pending"

    # 3. 获取待审批列表
    requests = await db.get_approval_requests(status="pending")
    pending_ids = [r["id"] for r in requests]
    assert request["id"] in pending_ids

    # 4. 审批通过
    approved = await db.approve_request(
        request["id"],
        reviewer="director",
        comments="Approved - VIP customer order"
    )
    assert approved["status"] == "approved"

    # 5. 验证不再在待审批列表中
    requests = await db.get_approval_requests(status="pending")
    pending_ids = [r["id"] for r in requests]
    assert request["id"] not in pending_ids

    # 6. 验证在已批准列表中
    approved_requests = await db.get_approval_requests(status="approved")
    approved_ids = [r["id"] for r in approved_requests]
    assert request["id"] in approved_ids
