"""
EmailTemplateService 单元测试

测试覆盖:
    - get_active_templates: 获取启用模板
    - get_random_template: 随机获取模板（含过滤）
    - get_template_by_id: 根据 ID 获取模板
    - deactivate_template: 停用模板
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from contextlib import asynccontextmanager
from sqlalchemy import select

from email_agent.generator.template_service import EmailTemplateService
from email_agent.storage.database import Database
from email_agent.storage.models import EmailTemplate


@pytest.fixture
def sample_templates():
    """创建示例模板数据"""
    return [
        EmailTemplate(
            id=1,
            type="inquiry",
            product_name="Paracetamol",
            region="Europe",
            quantity_range="100-500",
            subject_template="Inquiry about {product}",
            body_template="We are interested in {product}...",
            is_active=True
        ),
        EmailTemplate(
            id=2,
            type="rfq",
            product_name="Ibuprofen",
            region="Asia",
            quantity_range="500-1000",
            subject_template="RFQ for {product}",
            body_template="Please quote for {product}...",
            is_active=True
        ),
        EmailTemplate(
            id=3,
            type="complaint",
            product_name="Aspirin",
            region="Europe",
            quantity_range="1000-5000",
            subject_template="Complaint about {product}",
            body_template="We have a complaint regarding {product}...",
            is_active=False
        ),
    ]


def create_mock_session_factory(mock_session):
    """创建模拟会话工厂的异步上下文管理器"""
    async def session_context():
        yield mock_session
    return asynccontextmanager(session_context)


@pytest.mark.asyncio
async def test_get_active_templates_returns_only_active(sample_templates):
    """测试获取所有启用的模板"""
    # 创建模拟数据库
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()

    # 只返回前两个活跃模板
    active_templates = [t for t in sample_templates if t.is_active]
    mock_result.scalars.return_value.all.return_value = active_templates
    mock_session.execute.return_value = mock_result

    # 设置异步上下文管理器
    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    result = await service.get_active_templates()

    # 验证结果
    assert len(result) == 2
    assert all(t.is_active for t in result)

    # 验证 SQL 查询
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_templates_empty_result():
    """测试没有启用模板的情况"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    result = await service.get_active_templates()

    assert result == []


@pytest.mark.asyncio
async def test_get_random_template_no_filters(sample_templates):
    """测试随机获取模板（无过滤条件）"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_templates[:2]  # 只返回活跃的
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)

    # 多次调用以验证随机性
    results = set()
    for _ in range(10):
        template = await service.get_random_template()
        results.add(template.id)

    # 应该返回了其中一个模板
    assert all(tid in [1, 2] for tid in results)


@pytest.mark.asyncio
async def test_get_random_template_with_type_filter(sample_templates):
    """测试按类型过滤随机获取模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # 只返回 inquiry 类型的模板
    inquiry_templates = [t for t in sample_templates if t.type == "inquiry"]
    mock_result.scalars.return_value.all.return_value = inquiry_templates
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_random_template(template_type="inquiry")

    assert template.type == "inquiry"


@pytest.mark.asyncio
async def test_get_random_template_with_region_filter(sample_templates):
    """测试按区域过滤随机获取模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # 只返回 Europe 区域的模板
    europe_templates = [t for t in sample_templates if t.region == "Europe" and t.is_active]
    mock_result.scalars.return_value.all.return_value = europe_templates
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_random_template(region="Europe")

    assert template.region == "Europe"


@pytest.mark.asyncio
async def test_get_random_template_with_both_filters(sample_templates):
    """测试同时按类型和区域过滤"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # 返回 Europe + inquiry 的模板
    filtered = [t for t in sample_templates if t.type == "inquiry" and t.region == "Europe"]
    mock_result.scalars.return_value.all.return_value = filtered
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_random_template(template_type="inquiry", region="Europe")

    assert template.type == "inquiry"
    assert template.region == "Europe"


@pytest.mark.asyncio
async def test_get_random_template_returns_none_when_no_match():
    """测试没有匹配模板时返回 None"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_random_template(template_type="nonexistent")

    assert template is None


@pytest.mark.asyncio
async def test_get_template_by_id_exists(sample_templates):
    """测试根据 ID 获取存在的模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = sample_templates[0]
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_template_by_id(1)

    assert template is not None
    assert template.id == 1
    assert template.type == "inquiry"


@pytest.mark.asyncio
async def test_get_template_by_id_not_exists():
    """测试根据 ID 获取不存在的模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    template = await service.get_template_by_id(999)

    assert template is None


@pytest.mark.asyncio
async def test_deactivate_template_success(sample_templates):
    """测试成功停用模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_template = sample_templates[0]
    mock_result.scalars.return_value.first.return_value = mock_template
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    result = await service.deactivate_template(1)

    assert result is True
    assert mock_template.is_active is False
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_deactivate_template_not_found():
    """测试停折不存在的模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    result = await service.deactivate_template(999)

    assert result is False
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_get_random_template_excludes_inactive(sample_templates):
    """测试随机获取模板时排除已停用的模板"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # 只返回活跃模板
    active_only = [t for t in sample_templates if t.is_active]
    mock_result.scalars.return_value.all.return_value = active_only
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)

    # 多次调用验证
    for _ in range(5):
        template = await service.get_random_template()
        assert template.is_active is True


@pytest.mark.asyncio
async def test_service_initialization_with_db():
    """测试服务初始化"""
    mock_db = MagicMock(spec=Database)
    service = EmailTemplateService(mock_db)
    assert service.db is mock_db


@pytest.mark.asyncio
async def test_get_active_templates_query_order(sample_templates):
    """测试获取活跃模板的查询包含正确的条件"""
    mock_db = MagicMock(spec=Database)
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sample_templates[:2]
    mock_session.execute.return_value = mock_result

    mock_db.session = MagicMock()
    mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)

    service = EmailTemplateService(mock_db)
    await service.get_active_templates()

    # 验证调用了 execute
    assert mock_session.execute.called

    # 验证查询对象是 select 类型
    call_args = mock_session.execute.call_args[0][0]
    assert call_args.__class__.__name__ == 'Select'
