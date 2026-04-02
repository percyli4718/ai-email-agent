"""
数据库 CRUD 操作单元测试

测试覆盖:
- 通知 CRUD 操作
- 审批请求 CRUD 操作
- 报价单 CRUD 操作
- 工作流 CRUD 操作
- 客户查询
- 定价政策查询
- 合规要求查询
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from email_agent.storage.database import Database
from email_agent.config import Settings


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_settings():
    """创建模拟配置"""
    settings = MagicMock(spec=Settings)
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    return settings


@pytest.fixture
def mock_session():
    """创建模拟数据库会话"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_db(mock_settings, mock_session):
    """创建模拟数据库实例"""
    with patch('email_agent.storage.database.create_async_engine') as mock_engine, \
         patch('email_agent.storage.database.async_sessionmaker') as mock_sessionmaker:

        mock_engine.return_value = MagicMock()
        mock_sessionmaker.return_value = MagicMock()
        mock_sessionmaker.return_value.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_sessionmaker.return_value.return_value.__aexit__ = AsyncMock(return_value=None)

        db = Database(mock_settings)
        return db


# ============================================================================
# 通知 CRUD 测试
# ============================================================================

@pytest.mark.asyncio
async def test_create_notification(mock_db, mock_session):
    """测试创建通知"""
    # 模拟数据库返回
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = MagicMock(
        id=1,
        type="system",
        level="info",
        title="Test Notification",
        message="Test Message",
        is_read=False,
        created_at=datetime.utcnow()
    )
    mock_session.execute.return_value = mock_result

    # 执行创建
    notification = await mock_db.create_notification(
        type="system",
        title="Test Notification",
        message="Test Message",
        level="info"
    )

    # 验证结果
    assert notification is not None
    assert notification["type"] == "system"
    assert notification["title"] == "Test Notification"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_notifications(mock_db, mock_session):
    """测试获取通知列表"""
    # 模拟数据库返回
    mock_notification = MagicMock(
        id=1,
        type="system",
        level="info",
        title="Test",
        message="Test Message",
        is_read=False,
        created_at=datetime.utcnow()
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_notification]
    mock_session.execute.return_value = mock_result

    # 执行查询
    notifications = await mock_db.get_notifications(limit=10, unread_only=False)

    # 验证结果
    assert len(notifications) == 1
    assert notifications[0]["id"] == 1


@pytest.mark.asyncio
async def test_mark_notification_read(mock_db, mock_session):
    """测试标记通知为已读"""
    # 模拟通知存在
    mock_notification = MagicMock(id=1, is_read=False)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_notification
    mock_session.execute.return_value = mock_result

    # 执行标记
    result = await mock_db.mark_notification_read(1)

    # 验证结果
    assert result is not None
    assert mock_notification.is_read == True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mark_notification_read_not_found(mock_db, mock_session):
    """测试标记不存在的通知"""
    # 模拟通知不存在
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    # 执行标记
    result = await mock_db.mark_notification_read(999)

    # 验证结果
    assert result is None


# ============================================================================
# 审批请求 CRUD 测试
# ============================================================================

@pytest.mark.asyncio
async def test_create_approval_request(mock_db, mock_session):
    """测试创建审批请求"""
    # 模拟数据库返回
    mock_request = MagicMock(
        id=1,
        email_id="email_001",
        request_type="high_amount",
        status="pending",
        amount=50000,
        currency="USD"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_request
    mock_session.execute.return_value = mock_result

    # 执行创建
    request = await mock_db.create_approval_request(
        email_id="email_001",
        requester="price_agent",
        request_type="high_amount",
        reason="Amount exceeds threshold",
        amount=50000,
        currency="USD"
    )

    # 验证结果
    assert request is not None
    assert request["email_id"] == "email_001"
    assert request["request_type"] == "high_amount"
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_approval_requests(mock_db, mock_session):
    """测试获取审批请求列表"""
    # 模拟数据库返回
    mock_request = MagicMock(
        id=1,
        email_id="email_001",
        request_type="high_amount",
        status="pending"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_request]
    mock_session.execute.return_value = mock_result

    # 执行查询
    requests = await mock_db.get_approval_requests(status="pending")

    # 验证结果
    assert len(requests) == 1
    assert requests[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_approve_request(mock_db, mock_session):
    """测试批准请求"""
    # 模拟请求存在
    mock_request = MagicMock(
        id=1,
        status="pending"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_request
    mock_session.execute.return_value = mock_result

    # 执行批准
    result = await mock_db.approve_request(1, reviewer="admin", comments="Approved")

    # 验证结果
    assert result is not None
    assert mock_request.status == "approved"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_reject_request(mock_db, mock_session):
    """测试拒绝请求"""
    # 模拟请求存在
    mock_request = MagicMock(
        id=1,
        status="pending"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_request
    mock_session.execute.return_value = mock_result

    # 执行拒绝
    result = await mock_db.reject_request(1, reviewer="admin", comments="Rejected")

    # 验证结果
    assert result is not None
    assert mock_request.status == "rejected"


# ============================================================================
# 报价单 CRUD 测试
# ============================================================================

@pytest.mark.asyncio
async def test_create_quote(mock_db, mock_session):
    """测试创建报价单"""
    # 模拟数据库返回
    mock_quote = MagicMock(
        id=1,
        quote_id="QT-001",
        total_amount=10000,
        status="draft"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_quote
    mock_session.execute.return_value = mock_result

    # 执行创建
    quote = await mock_db.create_quote(
        quote_id="QT-001",
        total_amount=10000,
        currency="USD"
    )

    # 验证结果
    assert quote is not None
    assert quote["quote_id"] == "QT-001"


@pytest.mark.asyncio
async def test_get_quote(mock_db, mock_session):
    """测试获取报价单"""
    # 模拟报价单存在
    mock_quote = MagicMock(
        id=1,
        quote_id="QT-001",
        total_amount=10000
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_quote
    mock_session.execute.return_value = mock_result

    # 执行查询
    quote = await mock_db.get_quote("QT-001")

    # 验证结果
    assert quote is not None
    assert quote["quote_id"] == "QT-001"


@pytest.mark.asyncio
async def test_get_quote_not_found(mock_db, mock_session):
    """测试获取不存在的报价单"""
    # 模拟报价单不存在
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    # 执行查询
    quote = await mock_db.get_quote("NON_EXISTENT")

    # 验证结果
    assert quote is None


@pytest.mark.asyncio
async def test_update_quote_status(mock_db, mock_session):
    """测试更新报价单状态"""
    # 模拟报价单存在
    mock_quote = MagicMock(
        id=1,
        quote_id="QT-001",
        status="draft"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_quote
    mock_session.execute.return_value = mock_result

    # 执行更新
    result = await mock_db.update_quote_status("QT-001", "sent")

    # 验证结果
    assert result is not None
    assert mock_quote.status == "sent"


# ============================================================================
# 工作流 CRUD 测试
# ============================================================================

@pytest.mark.asyncio
async def test_create_workflow(mock_db, mock_session):
    """测试创建工作流"""
    # 模拟数据库返回
    mock_workflow = MagicMock(
        id=1,
        email_id="email_001",
        status="pending",
        current_step="layer1_classification"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_workflow
    mock_session.execute.return_value = mock_result

    # 执行创建
    workflow = await mock_db.create_workflow(
        email_id="email_001",
        initial_status="pending"
    )

    # 验证结果
    assert workflow is not None
    assert workflow["email_id"] == "email_001"


@pytest.mark.asyncio
async def test_get_workflow(mock_db, mock_session):
    """测试获取工作流"""
    # 模拟工作流存在
    mock_workflow = MagicMock(
        id=1,
        email_id="email_001",
        status="pending"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_workflow
    mock_session.execute.return_value = mock_result

    # 执行查询
    workflow = await mock_db.get_workflow("email_001")

    # 验证结果
    assert workflow is not None


@pytest.mark.asyncio
async def test_transition_workflow_status(mock_db, mock_session):
    """测试工作流状态转换"""
    # 模拟工作流存在
    mock_workflow = MagicMock(
        id=1,
        status="pending",
        current_step="layer1_classification"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_workflow
    mock_session.execute.return_value = mock_result

    # 执行转换
    result = await mock_db.transition_workflow_status(
        "email_001",
        new_status="processing",
        triggered_by="system",
        reason="Auto transition"
    )

    # 验证结果
    assert result is not None


# ============================================================================
# 客户和定价查询测试
# ============================================================================

@pytest.mark.asyncio
async def test_query_customer_by_email(mock_db, mock_session):
    """测试通过邮箱查询客户"""
    # 模拟客户存在
    mock_customer = MagicMock(
        id=1,
        name="Test Customer",
        email="test@example.com",
        tier="A"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_customer
    mock_session.execute.return_value = mock_result

    # 执行查询
    customer = await mock_db.query_customer(email="test@example.com")

    # 验证结果
    assert customer is not None
    assert customer["name"] == "Test Customer"


@pytest.mark.asyncio
async def test_query_customer_not_found(mock_db, mock_session):
    """测试查询不存在的客户"""
    # 模拟客户不存在
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    # 执行查询
    customer = await mock_db.query_customer(email="nonexistent@example.com")

    # 验证结果
    assert customer is None


@pytest.mark.asyncio
async def test_query_pricing_policy(mock_db, mock_session):
    """测试查询定价政策"""
    # 模拟定价政策存在
    mock_policy = MagicMock(
        id=1,
        product_name="Paracetamol 500mg",
        region="Europe",
        base_price=2.80,
        discount_rate=0.05,
        currency="USD"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_policy
    mock_session.execute.return_value = mock_result

    # 执行查询
    result = await mock_db.query_pricing_policy(
        products=["Paracetamol 500mg"],
        region="Europe"
    )

    # 验证结果
    assert "policies" in result
    assert len(result["policies"]) == 1
    assert result["policies"][0]["base_price"] == 2.80


@pytest.mark.asyncio
async def test_query_compliance_requirements(mock_db, mock_session):
    """测试查询合规要求"""
    # 模拟合规要求存在
    mock_compliance = MagicMock(
        id=1,
        region="Europe",
        requirement_type="certification",
        requirement_name="CE Marking",
        mandatory=True,
        description="CE marking required"
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_compliance]
    mock_session.execute.return_value = mock_result

    # 执行查询
    result = await mock_db.query_compliance_requirements(
        products=[],
        destination="Europe"
    )

    # 验证结果
    assert "requirements" in result
    assert len(result["requirements"]) == 1
    assert result["requirements"][0]["mandatory"] == True
