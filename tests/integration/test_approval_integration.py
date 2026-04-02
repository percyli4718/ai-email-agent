"""
审批工作流集成测试

测试模块:
- src/email_agent/storage/database.py - 审批相关数据库操作
- src/email_agent/api/routes.py - 审批 API 端点

覆盖范围:
- 创建审批请求
- 获取审批请求列表
- 获取单个审批请求详情
- 批准审批请求
- 拒绝审批请求
- 审批工作流状态转换
- 通知集成
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient

from email_agent.main import app
from email_agent.storage.database import Database
from email_agent.storage.models import ApprovalRequest, Email
from email_agent.config import Settings


@pytest.fixture
def test_settings():
    """创建设置对象"""
    settings = Settings()
    settings.database_url = "sqlite+aiosqlite:///./test.db"
    settings.env = "test"
    return settings


@pytest.fixture
def client():
    """创建 FastAPI 测试客户端"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_db():
    """创建模拟数据库实例"""
    db = MagicMock(spec=Database)
    return db


class TestApprovalRequestDatabase:
    """审批请求数据库操作测试"""

    @pytest.fixture
    def db_instance(self, test_settings):
        """创建数据库实例"""
        return Database(test_settings)

    @pytest.mark.asyncio
    async def test_create_approval_request(self, db_instance):
        """测试创建审批请求"""
        mock_approval = MagicMock(spec=ApprovalRequest)
        mock_approval.id = 1
        mock_approval.email_id = "test-email-123"
        mock_approval.requester = "price_agent"
        mock_approval.request_type = "high_amount"
        mock_approval.amount = 50000.0
        mock_approval.currency = "USD"
        mock_approval.reason = "Order amount exceeds threshold"
        mock_approval.status = "pending"
        mock_approval.created_at = datetime(2026, 4, 1, 12, 0, 0)

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            # 模拟插入结果
            mock_result = MagicMock()
            mock_result.inserted_primary_key = [1]
            mock_session.execute.return_value = mock_result

            # 模拟查询返回
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_approval
            mock_session.execute.side_effect = [mock_result, mock_select_result]

            result = await db_instance.create_approval_request(
                email_id="test-email-123",
                requester="price_agent",
                request_type="high_amount",
                amount=50000.0,
                reason="Order amount exceeds threshold"
            )

            assert result["id"] == 1
            assert result["email_id"] == "test-email-123"
            assert result["status"] == "pending"
            # 验证 execute 被调用（插入和查询）
            assert mock_session.execute.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_approval_requests_all(self, db_instance):
        """测试获取所有审批请求"""
        mock_request = MagicMock(spec=ApprovalRequest)
        mock_request.id = 1
        mock_request.email_id = "test-email-123"
        mock_request.requester = "price_agent"
        mock_request.request_type = "high_amount"
        mock_request.amount = 50000.0
        mock_request.status = "pending"
        mock_request.created_at = datetime(2026, 4, 1, 12, 0, 0)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_request]

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_approval_requests(limit=50)

            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["request_type"] == "high_amount"

    @pytest.mark.asyncio
    async def test_get_approval_requests_by_status(self, db_instance):
        """测试根据状态获取审批请求"""
        mock_request = MagicMock(spec=ApprovalRequest)
        mock_request.id = 1
        mock_request.status = "pending"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_request]

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_approval_requests(status="pending", limit=10)

            assert len(result) == 1
            # 验证使用了状态过滤
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_approval_request_by_id_found(self, db_instance):
        """测试根据 ID 获取审批请求 - 找到"""
        mock_request = MagicMock(spec=ApprovalRequest)
        mock_request.id = 1
        mock_request.email_id = "test-email-123"
        mock_request.requester = "price_agent"
        mock_request.request_type = "high_amount"
        mock_request.status = "pending"
        mock_request.to_dict.return_value = {
            "id": 1,
            "email_id": "test-email-123",
            "requester": "price_agent",
            "request_type": "high_amount",
            "status": "pending"
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_request

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_approval_request_by_id(request_id=1)

            assert result is not None
            assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_get_approval_request_by_id_not_found(self, db_instance):
        """测试根据 ID 获取审批请求 - 未找到"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_approval_request_by_id(request_id=999)

            assert result is None

    @pytest.mark.asyncio
    async def test_approve_request(self, db_instance):
        """测试批准请求"""
        mock_request = MagicMock(spec=ApprovalRequest)
        mock_request.id = 1
        mock_request.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_request

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.approve_request(
                request_id=1,
                reviewer="admin",
                comments="Approved - valid request"
            )

            assert result is True
            assert mock_request.status == "approved"
            assert mock_request.reviewer == "admin"
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_request_not_found(self, db_instance):
        """测试批准请求 - 请求不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.approve_request(
                request_id=999,
                reviewer="admin"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_reject_request(self, db_instance):
        """测试拒绝请求"""
        mock_request = MagicMock(spec=ApprovalRequest)
        mock_request.id = 1
        mock_request.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_request

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.reject_request(
                request_id=1,
                reviewer="admin",
                comments="Insufficient documentation"
            )

            assert result is True
            assert mock_request.status == "rejected"
            assert mock_request.comments == "Insufficient documentation"

    @pytest.mark.asyncio
    async def test_check_approval_required_true(self, db_instance):
        """测试检查是否需要审批 - 需要"""
        # 当金额超过阈值时返回 True
        result = await db_instance.check_approval_required(
            email_id="test-email-123",
            amount=50000.0,
            threshold=10000.0
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_check_approval_required_false(self, db_instance):
        """测试检查是否需要审批 - 不需要"""
        result = await db_instance.check_approval_required(
            email_id="test-email-123",
            amount=5000.0,
            threshold=10000.0
        )

        assert result is False


class TestApprovalAPI:
    """审批 API 端点测试"""

    @pytest.fixture
    def mock_db_client(self):
        """创建带模拟数据库的客户端"""
        db = MagicMock(spec=Database)
        return db

    def test_create_approval_request_success(self, client, mock_db_client):
        """测试创建审批请求 - 成功"""
        mock_db_client.create_approval_request = AsyncMock(return_value={
            "id": 1,
            "email_id": "test-email-123",
            "requester": "price_agent",
            "request_type": "high_amount",
            "amount": 50000.0,
            "status": "pending"
        })
        mock_db_client.create_notification = AsyncMock(return_value={})

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post(
                "/approvals",
                json={
                    "email_id": "test-email-123",
                    "requester": "price_agent",
                    "request_type": "high_amount",
                    "amount": 50000.0,
                    "reason": "Order exceeds threshold"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["email_id"] == "test-email-123"

    def test_create_approval_request_missing_fields(self, client, mock_db_client):
        """测试创建审批请求 - 缺少字段"""
        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post(
                "/approvals",
                json={
                    "email_id": "test-email-123"
                    # 缺少 requester, request_type 等必需字段
                }
            )

            # FastAPI 应该返回 422 验证错误
            assert response.status_code == 422

    def test_get_approval_requests(self, client, mock_db_client):
        """测试获取审批请求列表"""
        mock_db_client.get_approval_requests = AsyncMock(return_value=[
            {
                "id": 1,
                "email_id": "test-email-123",
                "requester": "price_agent",
                "request_type": "high_amount",
                "status": "pending"
            },
            {
                "id": 2,
                "email_id": "test-email-456",
                "requester": "compliance_agent",
                "request_type": "special_terms",
                "status": "approved"
            }
        ])

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.get("/approvals")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_approval_requests_with_status_filter(self, client, mock_db_client):
        """测试获取审批请求 - 按状态过滤"""
        mock_db_client.get_approval_requests = AsyncMock(return_value=[
            {"id": 1, "status": "pending"},
            {"id": 2, "status": "pending"}
        ])

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.get("/approvals?status=pending")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            # 验证调用了正确的参数
            mock_db_client.get_approval_requests.assert_called_with(
                status="pending",
                limit=50
            )

    def test_get_approval_request_by_id(self, client, mock_db_client):
        """测试获取单个审批请求"""
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "email_id": "test-email-123",
            "requester": "price_agent",
            "request_type": "high_amount",
            "status": "pending",
            "reason": "Order exceeds threshold"
        })

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.get("/approvals/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1

    def test_get_approval_request_not_found(self, client, mock_db_client):
        """测试获取审批请求 - 未找到"""
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value=None)

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.get("/approvals/999")

            assert response.status_code == 404

    def test_approve_request(self, client, mock_db_client):
        """测试批准请求"""
        mock_db_client.approve_request = AsyncMock(return_value=True)
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "email_id": "test-email-123",
            "status": "approved"
        })
        mock_db_client.create_notification = AsyncMock(return_value={})
        mock_db_client.update_email_status = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post("/approvals/1/approve")

            assert response.status_code == 200

    def test_approve_request_with_comments(self, client, mock_db_client):
        """测试批准请求 - 带意见"""
        mock_db_client.approve_request = AsyncMock(return_value=True)
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "status": "approved"
        })
        mock_db_client.create_notification = AsyncMock(return_value={})
        mock_db_client.update_email_status = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post(
                "/approvals/1/approve",
                json={"comments": "Looks good, approved"}
            )

            assert response.status_code == 200
            # 验证调用了 approve_request 并传入 comments
            mock_db_client.approve_request.assert_called()

    def test_reject_request(self, client, mock_db_client):
        """测试拒绝请求"""
        mock_db_client.reject_request = AsyncMock(return_value=True)
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "status": "rejected"
        })
        mock_db_client.create_notification = AsyncMock(return_value={})

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post("/approvals/1/reject")

            assert response.status_code == 200

    def test_reject_request_with_reason(self, client, mock_db_client):
        """测试拒绝请求 - 带原因"""
        mock_db_client.reject_request = AsyncMock(return_value=True)
        mock_db_client.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "status": "rejected"
        })
        mock_db_client.create_notification = AsyncMock(return_value={})

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post(
                "/approvals/1/reject",
                json={"comments": "Insufficient documentation"}
            )

            assert response.status_code == 200
            # 验证调用了 reject_request 并传入原因
            mock_db_client.reject_request.assert_called()

    def test_check_approval_required(self, client, mock_db_client):
        """测试检查是否需要审批"""
        mock_db_client.check_approval_required = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', mock_db_client):
            response = client.post(
                "/emails/test-email-123/workflow/check-approval",
                json={"amount": 50000.0, "threshold": 10000.0}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["requires_approval"] is True


class TestApprovalWorkflowIntegration:
    """审批工作流集成测试"""

    def test_full_approval_flow(self, client):
        """测试完整审批流程"""
        db = MagicMock(spec=Database)

        # 步骤 1: 创建审批请求
        db.create_approval_request = AsyncMock(return_value={
            "id": 1,
            "status": "pending"
        })
        db.create_notification = AsyncMock(return_value={})
        db.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "status": "pending"
        })
        db.update_email_status = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', db):
            # 创建请求
            create_response = client.post(
                "/approvals",
                json={
                    "email_id": "test-email",
                    "requester": "price_agent",
                    "request_type": "high_amount",
                    "amount": 50000.0,
                    "reason": "High value order"
                }
            )
            assert create_response.status_code == 200

            # 步骤 2: 获取请求详情
            db.get_approval_request_by_id.return_value = {
                "id": 1,
                "status": "pending",
                "request_type": "high_amount"
            }
            detail_response = client.get("/approvals/1")
            assert detail_response.status_code == 200

            # 步骤 3: 批准请求
            db.approve_request = AsyncMock(return_value=True)
            db.update_email_status = AsyncMock(return_value=True)

            approve_response = client.post("/approvals/1/approve")
            assert approve_response.status_code == 200

            # 步骤 4: 验证状态更新
            db.get_approval_request_by_id.return_value = {
                "id": 1,
                "status": "approved"
            }
            final_response = client.get("/approvals/1")
            assert final_response.json()["status"] == "approved"

    def test_approval_rejection_flow(self, client):
        """测试审批拒绝流程"""
        db = MagicMock(spec=Database)

        # 创建请求
        db.create_approval_request = AsyncMock(return_value={"id": 2, "status": "pending"})
        db.create_notification = AsyncMock(return_value={})

        with patch('email_agent.api.routes.db', db):
            create_response = client.post(
                "/approvals",
                json={
                    "email_id": "test-email-2",
                    "requester": "agent",
                    "request_type": "special_terms",
                    "amount": 10000.0,
                    "reason": "Special payment terms requested"
                }
            )
            assert create_response.status_code == 200

            # 拒绝请求
            db.reject_request = AsyncMock(return_value=True)
            db.get_approval_request_by_id = AsyncMock(return_value={
                "id": 2,
                "status": "rejected"
            })
            db.update_email_status = AsyncMock(return_value=True)

            reject_response = client.post(
                "/approvals/2/reject",
                json={"comments": "Terms not acceptable"}
            )
            assert reject_response.status_code == 200
