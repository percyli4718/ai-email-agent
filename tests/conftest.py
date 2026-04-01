"""
Pytest 测试配置

提供全局的测试夹具 (fixtures) 和配置。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from email_agent.main import app
from email_agent.storage.database import Database


@pytest.fixture
def client():
    """
    创建 FastAPI 测试客户端

    作用:
        提供用于测试 API 端点的 TestClient 实例。

    使用场景:
        - 测试 API 端点响应
        - 验证请求/响应数据
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_db():
    """
    创建模拟数据库实例

    作用:
        提供用于测试的 Mock Database 实例。

    使用场景:
        - 单元测试中替代真实数据库
        - 隔离测试环境
    """
    db = MagicMock(spec=Database)
    db.get_or_create_customer = AsyncMock()
    db.get_all_emails = AsyncMock(return_value=[])
    db.get_email_by_id = AsyncMock()
    db.get_email_analysis = AsyncMock()
    db.get_agent_executions = AsyncMock(return_value=[])
    db.close = AsyncMock()
    return db


@pytest.fixture
def sample_email_template():
    """
    创建示例邮件模板

    作用:
        提供用于测试的标准 EmailTemplate 实例。

    使用场景:
        - 作为模板服务的测试数据
        - 作为 API 响应的预期数据
    """
    from email_agent.storage.models import EmailTemplate

    return EmailTemplate(
        id=1,
        type="inquiry",
        product_name="Paracetamol",
        region="Europe",
        quantity_range="100-500",
        subject_template="Inquiry about {product} - Quantity {quantity}",
        body_template="Dear {customer_name},\n\nWe are interested in {product}...\nQuantity: {quantity}\nPacking: {packing}\nStandard: {standard}",
        is_active=True
    )
