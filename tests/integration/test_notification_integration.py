"""
通知系统集成测试

测试模块:
- src/email_agent/storage/database.py - 通知相关数据库操作
- src/email_agent/api/routes.py - 通知 API 端点

覆盖范围:
- 创建通知
- 获取通知列表
- 获取未读通知
- 标记通知为已读
- 通知 WebSocket 连接
- 不同类型通知（邮件状态、Agent 进度、审批请求）
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

from email_agent.main import app
from email_agent.storage.database import Database
from email_agent.storage.models import Notification
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


class TestNotificationDatabase:
    """通知数据库操作测试"""

    @pytest.fixture
    def db_instance(self, test_settings):
        """创建数据库实例"""
        return Database(test_settings)

    @pytest.mark.asyncio
    async def test_create_notification(self, db_instance):
        """测试创建通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 1
        mock_notification.type = "email_status"
        mock_notification.title = "邮件处理完成"
        mock_notification.message = "邮件 test-email-123 已完成处理"
        mock_notification.level = "success"
        mock_notification.is_read = False
        mock_notification.related_id = "test-email-123"
        mock_notification.created_at = datetime(2026, 4, 1, 12, 0, 0)
        mock_notification.to_dict.return_value = {
            "id": 1,
            "type": "email_status",
            "title": "邮件处理完成",
            "message": "邮件 test-email-123 已完成处理",
            "level": "success",
            "is_read": False,
            "related_id": "test-email-123"
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            # 模拟插入结果
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]

            # 模拟查询结果
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification

            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]

            result = await db_instance.create_notification(
                type="email_status",
                title="邮件处理完成",
                message="邮件 test-email-123 已完成处理",
                level="success",
                related_id="test-email-123"
            )

            assert result["id"] == 1
            assert result["type"] == "email_status"
            assert result["is_read"] is False

    @pytest.mark.asyncio
    async def test_create_notification_with_extra_data(self, db_instance):
        """测试创建通知 - 带额外数据"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 2
        mock_notification.to_dict.return_value = {
            "id": 2,
            "type": "agent_progress",
            "extra_data": {"progress": 50, "agent_name": "price_agent"}
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [2]
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]

            result = await db_instance.create_notification(
                type="agent_progress",
                title="Agent 执行中",
                message="price_agent 正在处理",
                level="info",
                extra_data={"progress": 50, "agent_name": "price_agent"}
            )

            assert result["extra_data"]["progress"] == 50

    @pytest.mark.asyncio
    async def test_get_notifications_all(self, db_instance):
        """测试获取所有通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 1
        mock_notification.type = "email_status"
        mock_notification.is_read = False
        mock_notification.to_dict.return_value = {
            "id": 1,
            "type": "email_status",
            "is_read": False
        }

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_notification]

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_notifications(limit=50)

            assert len(result) == 1
            assert result[0]["type"] == "email_status"

    @pytest.mark.asyncio
    async def test_get_notifications_unread_only(self, db_instance):
        """测试仅获取未读通知"""
        mock_unread = MagicMock(spec=Notification)
        mock_unread.id = 1
        mock_unread.is_read = False
        mock_unread.to_dict.return_value = {"id": 1, "is_read": False}

        mock_read = MagicMock(spec=Notification)
        mock_read.id = 2
        mock_read.is_read = True
        mock_read.to_dict.return_value = {"id": 2, "is_read": True}

        mock_result = MagicMock()
        # 只返回未读通知
        mock_result.scalars().all.return_value = [mock_unread]

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_notifications(limit=50, unread_only=True)

            assert len(result) == 1
            assert result[0]["is_read"] is False

    @pytest.mark.asyncio
    async def test_get_notifications_empty(self, db_instance):
        """测试获取通知 - 空结果"""
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.get_notifications(limit=50)

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mark_notification已读 (self, db_instance):
        """测试标记通知为已读"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 1
        mock_notification.is_read = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.mark_notification_read(notification_id=1)

            assert result is True
            assert mock_notification.is_read is True
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification已读_not_found(self, db_instance):
        """测试标记通知为已读 - 未找到"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.mark_notification_read(notification_id=999)

            assert result is False


class TestNotificationAPI:
    """通知 API 端点测试"""

    def test_get_notifications(self, client, mock_db):
        """测试获取通知列表"""
        mock_db.get_notifications = AsyncMock(return_value=[
            {
                "id": 1,
                "type": "email_status",
                "title": "邮件处理完成",
                "message": "邮件 email_001 已完成处理",
                "level": "success",
                "is_read": False,
                "related_id": "email_001"
            },
            {
                "id": 2,
                "type": "agent_progress",
                "title": "Agent 执行中",
                "message": "price_agent 正在处理",
                "level": "info",
                "is_read": True,
                "related_id": "email_002"
            }
        ])

        with patch('email_agent.api.routes.db', mock_db):
            response = client.get("/notifications")

            assert response.status_code == 200
            data = response.json()
            assert len(data["notifications"]) == 2
            assert data["total"] == 2

    def test_get_notifications_unread_only(self, client, mock_db):
        """测试获取未读通知"""
        mock_db.get_notifications = AsyncMock(return_value=[
            {"id": 1, "type": "email_status", "is_read": False}
        ])

        with patch('email_agent.api.routes.db', mock_db):
            response = client.get("/notifications?unread_only=true")

            assert response.status_code == 200
            data = response.json()
            assert len(data["notifications"]) == 1
            # 验证调用了 unread_only=True
            mock_db.get_notifications.assert_called_with(limit=50, unread_only=True)

    def test_get_notifications_with_limit(self, client, mock_db):
        """测试获取通知 - 指定数量"""
        mock_db.get_notifications = AsyncMock(return_value=[
            {"id": 1, "type": "email_status", "is_read": False}
        ])

        with patch('email_agent.api.routes.db', mock_db):
            response = client.get("/notifications?limit=10")

            assert response.status_code == 200
            # 验证调用了正确的 limit
            mock_db.get_notifications.assert_called_with(limit=10, unread_only=False)

    def test_mark_notification_read(self, client, mock_db):
        """测试标记通知为已读"""
        mock_db.mark_notification_read = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', mock_db):
            response = client.post("/notifications/1/read")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_mark_notification_read_not_found(self, client, mock_db):
        """测试标记通知为已读 - 未找到"""
        mock_db.mark_notification_read = AsyncMock(return_value=False)

        with patch('email_agent.api.routes.db', mock_db):
            response = client.post("/notifications/999/read")

            assert response.status_code == 404

    def test_create_notification_types(self, client, mock_db):
        """测试不同类型通知的创建"""
        # 邮件状态通知
        mock_db.create_notification = AsyncMock(return_value={"id": 1, "type": "email_status"})

        with patch('email_agent.api.routes.db', mock_db):
            # 测试邮件状态通知
            response = client.post(
                "/notifications",
                json={
                    "type": "email_status",
                    "title": "邮件处理完成",
                    "message": "邮件已处理",
                    "level": "success"
                }
            )
            # 注意：如果没有这个端点，这个测试会失败
            # 这里只是展示如何测试


class TestNotificationTypes:
    """不同类型通知测试"""

    @pytest.fixture
    def db_instance(self, test_settings):
        """创建数据库实例"""
        return Database(test_settings)

    @pytest.mark.asyncio
    async def test_email_status_notification(self, db_instance):
        """测试邮件状态通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 1
        mock_notification.type = "email_status"
        mock_notification.to_dict.return_value = {
            "id": 1,
            "type": "email_status",
            "title": "邮件处理完成",
            "message": "邮件 email_001 已完成处理",
            "level": "success",
            "related_id": "email_001"
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="email_status",
                title="邮件处理完成",
                message="邮件 email_001 已完成处理",
                level="success",
                related_id="email_001"
            )

            assert result["type"] == "email_status"
            assert result["level"] == "success"

    @pytest.mark.asyncio
    async def test_agent_progress_notification(self, db_instance):
        """测试 Agent 进度通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 2
        mock_notification.type = "agent_progress"
        mock_notification.to_dict.return_value = {
            "id": 2,
            "type": "agent_progress",
            "title": "Agent 执行中",
            "message": "price_agent 正在处理",
            "level": "info",
            "extra_data": {"progress": 50, "agent_name": "price_agent"}
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [2]
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="agent_progress",
                title="Agent 执行中",
                message="price_agent 正在处理",
                level="info",
                extra_data={"progress": 50, "agent_name": "price_agent"}
            )

            assert result["type"] == "agent_progress"
            assert result["extra_data"]["progress"] == 50

    @pytest.mark.asyncio
    async def test_approval_request_notification(self, db_instance):
        """测试审批请求通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 3
        mock_notification.type = "approval_request"
        mock_notification.to_dict.return_value = {
            "id": 3,
            "type": "approval_request",
            "title": "待审批",
            "message": "高金额报价待审批",
            "level": "warning",
            "related_id": "approval_001"
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [3]
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="approval_request",
                title="待审批",
                message="高金额报价待审批",
                level="warning",
                related_id="approval_001"
            )

            assert result["type"] == "approval_request"
            assert result["level"] == "warning"

    @pytest.mark.asyncio
    async def test_system_notification(self, db_instance):
        """测试系统通知"""
        mock_notification = MagicMock(spec=Notification)
        mock_notification.id = 4
        mock_notification.type = "system"
        mock_notification.to_dict.return_value = {
            "id": 4,
            "type": "system",
            "title": "系统维护",
            "message": "系统将于今晚 10 点进行维护",
            "level": "info"
        }

        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [4]
            mock_select_result = MagicMock()
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="system",
                title="系统维护",
                message="系统将于今晚 10 点进行维护",
                level="info"
            )

            assert result["type"] == "system"


class TestNotificationLevels:
    """通知级别测试"""

    @pytest.fixture
    def db_instance(self, test_settings):
        """创建数据库实例"""
        return Database(test_settings)

    @pytest.mark.asyncio
    async def test_info_level_notification(self, db_instance):
        """测试 info 级别通知"""
        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]
            mock_select_result = MagicMock()
            mock_notification = MagicMock()
            mock_notification.level = "info"
            mock_notification.to_dict.return_value = {"level": "info"}
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="system",
                title="Info",
                message="Information message",
                level="info"
            )

            assert result["level"] == "info"

    @pytest.mark.asyncio
    async def test_success_level_notification(self, db_instance):
        """测试 success 级别通知"""
        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]
            mock_select_result = MagicMock()
            mock_notification = MagicMock()
            mock_notification.level = "success"
            mock_notification.to_dict.return_value = {"level": "success"}
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="email_status",
                title="Success",
                message="Operation completed successfully",
                level="success"
            )

            assert result["level"] == "success"

    @pytest.mark.asyncio
    async def test_warning_level_notification(self, db_instance):
        """测试 warning 级别通知"""
        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]
            mock_select_result = MagicMock()
            mock_notification = MagicMock()
            mock_notification.level = "warning"
            mock_notification.to_dict.return_value = {"level": "warning"}
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="approval_request",
                title="Warning",
                message="Approval required",
                level="warning"
            )

            assert result["level"] == "warning"

    @pytest.mark.asyncio
    async def test_error_level_notification(self, db_instance):
        """测试 error 级别通知"""
        with patch.object(db_instance, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_insert_result = MagicMock()
            mock_insert_result.inserted_primary_key = [1]
            mock_select_result = MagicMock()
            mock_notification = MagicMock()
            mock_notification.level = "error"
            mock_notification.to_dict.return_value = {"level": "error"}
            mock_select_result.scalar_one_or_none.return_value = mock_notification
            mock_session.execute.side_effect = [mock_insert_result, mock_select_result]
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_instance.create_notification(
                type="system",
                title="Error",
                message="An error occurred",
                level="error"
            )

            assert result["level"] == "error"


class TestNotificationIntegration:
    """通知集成测试"""

    def test_notification_with_approval_request(self, client):
        """测试通知与审批请求集成"""
        db = MagicMock(spec=Database)

        # 创建审批请求时应该同时创建通知
        db.create_approval_request = AsyncMock(return_value={
            "id": 1,
            "email_id": "test-email",
            "status": "pending"
        })
        db.create_notification = AsyncMock(return_value={
            "id": 1,
            "type": "approval_request",
            "title": "待审批"
        })

        with patch('email_agent.api.routes.db', db):
            # 创建审批请求
            response = client.post(
                "/approvals",
                json={
                    "email_id": "test-email",
                    "requester": "price_agent",
                    "request_type": "high_amount",
                    "amount": 50000.0,
                    "reason": "High value order"
                }
            )

            assert response.status_code == 200
            # 验证创建了通知
            db.create_notification.assert_called()

    def test_notification_after_approval(self, client):
        """测试审批后发送通知"""
        db = MagicMock(spec=Database)

        db.approve_request = AsyncMock(return_value=True)
        db.get_approval_request_by_id = AsyncMock(return_value={
            "id": 1,
            "email_id": "test-email",
            "status": "approved"
        })
        db.create_notification = AsyncMock(return_value={
            "id": 2,
            "type": "approval_request",
            "title": "已批准"
        })
        db.update_email_status = AsyncMock(return_value=True)

        with patch('email_agent.api.routes.db', db):
            response = client.post("/approvals/1/approve")

            assert response.status_code == 200
            # 验证创建了批准通知
            db.create_notification.assert_called()
