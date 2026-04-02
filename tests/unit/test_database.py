"""
数据库 CRUD 操作单元测试

测试模块：src/email_agent/storage/database.py

覆盖范围:
- 数据库初始化和连接管理
- 客户 CRUD 操作
- 定价政策查询
- 合规要求查询
- 邮件分析保存和查询
- Agent 执行记录保存和查询
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from email_agent.storage.database import Database, get_database
from email_agent.storage.models import Customer, Email, EmailAnalysis, AgentExecution, PricingPolicy, ComplianceRequirement
from email_agent.config import Settings


@pytest.fixture
def test_settings():
    """创建设置对象"""
    settings = Settings()
    settings.database_url = "sqlite+aiosqlite:///./test.db"
    settings.env = "development"
    return settings


@pytest.fixture
def mock_session():
    """创建模拟会话"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


class TestDatabaseInitialization:
    """数据库初始化测试"""

    def test_database_init(self, test_settings):
        """测试数据库初始化"""
        db = Database(test_settings)

        assert db.settings == test_settings
        assert db._engine is None
        assert db._session_factory is None

    @pytest.mark.asyncio
    async def test_engine_lazy_loading(self, test_settings):
        """测试引擎懒加载"""
        db = Database(test_settings)

        # 首次访问前引擎为 None
        assert db._engine is None

        # 首次访问 engine 属性
        with patch('email_agent.storage.database.create_async_engine') as mock_engine:
            mock_engine.return_value = MagicMock()
            engine = db.engine

            # 验证引擎已创建
            assert db._engine is not None
            mock_engine.assert_called_once_with(
                test_settings.database_url,
                echo=True  # development 环境
            )

    @pytest.mark.asyncio
    async def test_engine_production_mode(self, test_settings):
        """测试生产环境下引擎不输出 SQL 日志"""
        test_settings.env = "production"
        db = Database(test_settings)

        with patch('email_agent.storage.database.create_async_engine') as mock_engine:
            mock_engine.return_value = MagicMock()
            _ = db.engine

            mock_engine.assert_called_once_with(
                test_settings.database_url,
                echo=False  # production 环境
            )

    @pytest.mark.asyncio
    async def test_session_factory_creation(self, test_settings):
        """测试会话工厂创建"""
        from sqlalchemy.ext.asyncio import AsyncSession as RealAsyncSession

        db = Database(test_settings)

        # 直接设置私有属性来模拟 engine
        mock_engine = MagicMock()
        db._engine = mock_engine

        with patch('email_agent.storage.database.async_sessionmaker') as mock_factory:
            factory = db.session_factory

            mock_factory.assert_called_once_with(
                mock_engine,
                class_=RealAsyncSession,
                expire_on_commit=False
            )

    @pytest.mark.asyncio
    async def test_session_context_manager_success(self, test_settings, mock_session):
        """测试会话上下文管理器成功情况"""
        db = Database(test_settings)

        with patch.object(db, 'session_factory') as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            async with db.session() as session:
                assert session == mock_session
                # 模拟成功操作
                session.add(MagicMock())

            # 验证提交被调用
            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_context_manager_exception(self, test_settings, mock_session):
        """测试会话上下文管理器异常情况"""
        db = Database(test_settings)

        with patch.object(db, 'session_factory') as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # 模拟异常
            mock_session.commit.side_effect = Exception("Test exception")

            with pytest.raises(Exception):
                async with db.session() as session:
                    session.add(MagicMock())
                    raise Exception("Test exception")

            # 验证回滚被调用
            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_tables(self, test_settings):
        """测试表初始化"""
        db = Database(test_settings)

        mock_engine = MagicMock()
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

        db._engine = mock_engine

        await db.init_tables()

        # 验证 create_all 被调用
        mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, test_settings):
        """测试关闭数据库连接"""
        db = Database(test_settings)

        mock_engine = AsyncMock()
        db._engine = mock_engine

        await db.close()

        mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_engine(self, test_settings):
        """测试在没有引擎时关闭"""
        db = Database(test_settings)
        db._engine = None

        # 不应该抛出异常
        await db.close()


class TestCustomerOperations:
    """客户操作测试"""

    @pytest.mark.asyncio
    async def test_query_customer_by_email(self, test_settings):
        """测试通过邮箱查询客户"""
        db = Database(test_settings)

        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = 1
        mock_customer.name = "Test Customer"
        mock_customer.email = "test@example.com"
        mock_customer.tier = "A"
        mock_customer.region = "Europe"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_customer

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_customer(email="test@example.com")

            assert result is not None
            assert result["name"] == "Test Customer"
            assert result["tier"] == "A"
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_customer_by_region(self, test_settings):
        """测试通过区域查询客户"""
        db = Database(test_settings)

        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = 1
        mock_customer.name = "Brazil Customer"
        mock_customer.email = "brazil@example.com"
        mock_customer.tier = "B"
        mock_customer.region = "brazil"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_customer

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_customer(region="brazil")

            assert result is not None
            assert result["region"] == "brazil"

    @pytest.mark.asyncio
    async def test_query_customer_not_found(self, test_settings):
        """测试查询不存在的客户"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_customer(email="nonexistent@example.com")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_customer(self, test_settings):
        """测试创建客户"""
        db = Database(test_settings)

        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = 1
        mock_customer.email = "new@example.com"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None  # 不存在

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.create_customer(
                name="New Customer",
                email="new@example.com",
                tier="C",
                region="Asia"
            )

            # 验证客户被添加
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_customer_existing(self, test_settings):
        """测试创建已存在的客户"""
        db = Database(test_settings)

        mock_existing = MagicMock(spec=Customer)
        mock_existing.id = 1
        mock_existing.email = "existing@example.com"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_existing

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.create_customer(
                name="Existing Customer",
                email="existing@example.com"
            )

            # 应该返回现有客户，不创建新的
            assert result == mock_existing
            mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_customer_not_exists(self, test_settings):
        """测试获取或创建客户 - 客户不存在"""
        db = Database(test_settings)

        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = 1
        mock_customer.email = "new@example.com"

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.scalar_one_or_none.return_value = None  # 不存在
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_or_create_customer(
                email="new@example.com",
                defaults={"name": "New Customer", "region": "Europe", "tier": "B"}
            )

            # 验证客户被添加并提交
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_customer_exists(self, test_settings):
        """测试获取或创建客户 - 客户已存在"""
        db = Database(test_settings)

        mock_existing = MagicMock(spec=Customer)
        mock_existing.id = 1
        mock_existing.email = "existing@example.com"

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.scalar_one_or_none.return_value = mock_existing
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_or_create_customer(email="existing@example.com")

            assert result == mock_existing
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()


class TestPricingPolicyOperations:
    """定价政策操作测试"""

    @pytest.mark.asyncio
    async def test_query_pricing_policy_found(self, test_settings):
        """测试查询定价政策 - 找到"""
        db = Database(test_settings)

        mock_policy = MagicMock(spec=PricingPolicy)
        mock_policy.product_name = "Paracetamol"
        mock_policy.base_price = 2.5
        mock_policy.discount_rate = 0.1
        mock_policy.currency = "USD"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_policy

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_pricing_policy(
                products=["Paracetamol"],
                region="brazil"
            )

            assert len(result["policies"]) == 1
            assert result["policies"][0]["product"] == "Paracetamol"
            assert result["policies"][0]["base_price"] == 2.5
            assert result["region"] == "brazil"

    @pytest.mark.asyncio
    async def test_query_pricing_policy_fallback_to_default(self, test_settings):
        """测试查询定价政策 - 回退到默认价格"""
        db = Database(test_settings)

        # 第一次查询返回 None (特定区域无价格)
        # 第二次查询返回默认价格
        mock_default_policy = MagicMock(spec=PricingPolicy)
        mock_default_policy.product_name = "Paracetamol"
        mock_default_policy.base_price = 2.0
        mock_default_policy.discount_rate = 0.0
        mock_default_policy.currency = "USD"

        mock_result = MagicMock()
        mock_result.scalars().first.side_effect = [None, mock_default_policy]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_pricing_policy(
                products=["Paracetamol"],
                region="unknown_region"
            )

            # 应该使用默认价格
            assert len(result["policies"]) == 1
            assert result["policies"][0]["base_price"] == 2.0

    @pytest.mark.asyncio
    async def test_query_pricing_policy_not_found(self, test_settings):
        """测试查询定价政策 - 未找到"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_pricing_policy(
                products=["UnknownProduct"],
                region="brazil"
            )

            assert len(result["policies"]) == 0
            assert result["region"] == "brazil"


class TestComplianceOperations:
    """合规要求操作测试"""

    @pytest.mark.asyncio
    async def test_query_compliance_requirements_found(self, test_settings):
        """测试查询合规要求 - 找到"""
        db = Database(test_settings)

        mock_requirement = MagicMock(spec=ComplianceRequirement)
        mock_requirement.requirement_type = "certification"
        mock_requirement.requirement_name = "ANVISA"
        mock_requirement.mandatory = True
        mock_requirement.description = "Brazil health agency approval"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_requirement]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_compliance_requirements(
                products=["Paracetamol"],
                destination="brazil"
            )

            assert len(result["requirements"]) == 1
            assert result["requirements"][0]["type"] == "certification"
            assert result["requirements"][0]["name"] == "ANVISA"
            assert result["requirements"][0]["mandatory"] is True
            assert result["region"] == "brazil"

    @pytest.mark.asyncio
    async def test_query_compliance_requirements_empty(self, test_settings):
        """测试查询合规要求 - 未找到"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.query_compliance_requirements(
                products=["Paracetamol"],
                destination="unknown"
            )

            assert len(result["requirements"]) == 0
            assert result["region"] == "unknown"


class TestEmailAnalysisOperations:
    """邮件分析操作测试"""

    @pytest.mark.asyncio
    async def test_save_email_analysis(self, test_settings):
        """测试保存邮件分析"""
        db = Database(test_settings)

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            await db.save_email_analysis(
                email_id="test-email-123",
                layer1_classification={"type": "inquiry", "priority_score": 0.85},
                layer2_retrieval={"query": "test", "results": []},
                layer3_output={"quote_id": "QT-001"},
                processing_time_ms=1234.5,
                cost=0.05,
                model_used="claude-sonnet-4"
            )

            # 验证 EmailAnalysis 被添加
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_email_analysis_found(self, test_settings):
        """测试获取邮件分析 - 找到"""
        db = Database(test_settings)

        mock_analysis = MagicMock(spec=EmailAnalysis)
        mock_analysis.id = 1
        mock_analysis.email_id = "test-email-123"
        mock_analysis.layer1_classification = {"type": "inquiry"}
        mock_analysis.layer2_retrieval = {"query": "test"}
        mock_analysis.layer3_output = {"quote_id": "QT-001"}
        mock_analysis.processing_time_ms = 1234.5
        mock_analysis.cost = 0.05
        mock_analysis.model_used = "claude-sonnet-4"
        mock_analysis.created_at = datetime(2026, 4, 1, 12, 0, 0)

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_analysis

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_email_analysis(email_id="test-email-123")

            assert result is not None
            assert result["email_id"] == "test-email-123"
            assert result["layer1_classification"]["type"] == "inquiry"
            assert result["cost"] == 0.05

    @pytest.mark.asyncio
    async def test_get_email_analysis_not_found(self, test_settings):
        """测试获取邮件分析 - 未找到"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_email_analysis(email_id="nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_create_email_analysis(self, test_settings):
        """测试创建邮件分析"""
        db = Database(test_settings)

        mock_analysis = MagicMock(spec=EmailAnalysis)
        mock_analysis.id = 1
        mock_analysis.email_id = "test-email-123"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None  # 不存在

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.create_email_analysis(
                email_id="test-email-123",
                layer3_output={"quote_id": "QT-001", "total_amount": 10000},
                processing_time_ms=500.0,
                cost=0.03,
                model_used="claude-sonnet-4"
            )

            # 验证 EmailAnalysis 被添加
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_email_analysis_exists(self, test_settings):
        """测试创建邮件分析 - 已存在则更新"""
        db = Database(test_settings)

        mock_existing = MagicMock(spec=EmailAnalysis)
        mock_existing.id = 1
        mock_existing.email_id = "test-email-123"
        mock_existing.layer3_output = {"quote_id": "QT-OLD"}

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_existing

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.create_email_analysis(
                email_id="test-email-123",
                layer3_output={"quote_id": "QT-NEW"},
            )

            # 应该更新现有记录
            assert result == mock_existing
            mock_session.add.assert_not_called()


class TestAgentExecutionOperations:
    """Agent 执行记录操作测试"""

    @pytest.mark.asyncio
    async def test_save_agent_execution(self, test_settings):
        """测试保存 Agent 执行记录"""
        db = Database(test_settings)

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            await db.save_agent_execution(
                task_id="task-001",
                agent_name="price_agent",
                email_id="test-email-123",
                status="completed",
                budget_allocated=0.10,
                actual_cost=0.08,
                input_data={"product": "Paracetamol"},
                output_data={"price": 2.5},
                started_at=datetime(2026, 4, 1, 12, 0, 0),
                completed_at=datetime(2026, 4, 1, 12, 1, 0)
            )

            # 验证 AgentExecution 被添加
            mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_executions_all(self, test_settings):
        """测试获取所有 Agent 执行记录"""
        db = Database(test_settings)

        mock_execution = MagicMock(spec=AgentExecution)
        mock_execution.id = 1
        mock_execution.task_id = "task-001"
        mock_execution.agent_name = "price_agent"
        mock_execution.status = "completed"
        mock_execution.budget_allocated = 0.10
        mock_execution.actual_cost = 0.08
        mock_execution.email_id = "test-email-123"
        mock_execution.started_at = datetime(2026, 4, 1, 12, 0, 0)
        mock_execution.completed_at = datetime(2026, 4, 1, 12, 1, 0)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_execution]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_agent_executions()

            assert len(result) == 1
            assert result[0]["task_id"] == "task-001"
            assert result[0]["agent_name"] == "price_agent"

    @pytest.mark.asyncio
    async def test_get_agent_executions_by_email(self, test_settings):
        """测试根据邮件 ID 获取 Agent 执行记录"""
        db = Database(test_settings)

        mock_execution = MagicMock(spec=AgentExecution)
        mock_execution.id = 1
        mock_execution.task_id = "task-001"
        mock_execution.agent_name = "price_agent"
        mock_execution.email_id = "test-email-123"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_execution]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_agent_executions(email_id="test-email-123")

            assert len(result) == 1
            # 验证查询时使用了 email_id 过滤
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent_executions_empty(self, test_settings):
        """测试获取 Agent 执行记录 - 空结果"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_agent_executions()

            assert len(result) == 0


class TestEmailOperations:
    """邮件操作测试"""

    @pytest.mark.asyncio
    async def test_get_all_emails(self, test_settings):
        """测试获取所有邮件"""
        db = Database(test_settings)

        mock_email = MagicMock(spec=Email)
        mock_email.id = "test-email-123"
        mock_email.from_address = "customer@example.com"
        mock_email.subject = "Test Inquiry"
        mock_email.body = "Test body content"
        mock_email.priority = "high"
        mock_email.status = "pending"
        mock_email.received_at = datetime(2026, 4, 1, 12, 0, 0)
        mock_email.region = "brazil"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_email]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_all_emails(limit=50)

            assert len(result) == 1
            assert result[0]["id"] == "test-email-123"
            assert result[0]["from_address"] == "customer@example.com"
            assert result[0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_all_emails_with_empty_body(self, test_settings):
        """测试获取所有邮件 - 空正文处理"""
        db = Database(test_settings)

        mock_email = MagicMock(spec=Email)
        mock_email.id = "test-email-123"
        mock_email.from_address = "customer@example.com"
        mock_email.subject = "Test"
        mock_email.body = None  # 空正文
        mock_email.priority = "medium"
        mock_email.status = "completed"
        mock_email.received_at = datetime(2026, 4, 1, 12, 0, 0)
        mock_email.region = "europe"

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_email]

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_all_emails()

            assert len(result) == 1
            assert result[0]["preview"] == ""

    @pytest.mark.asyncio
    async def test_get_email_by_id_found(self, test_settings):
        """测试根据 ID 获取邮件 - 找到"""
        db = Database(test_settings)

        mock_email = MagicMock(spec=Email)
        mock_email.id = "test-email-123"
        mock_email.from_address = "customer@example.com"
        mock_email.subject = "Test Inquiry"
        mock_email.body = "Full email body"
        mock_email.priority = "high"
        mock_email.status = "pending"
        mock_email.received_at = datetime(2026, 4, 1, 12, 0, 0)
        mock_email.region = "brazil"

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_email

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_email_by_id(email_id="test-email-123")

            assert result is not None
            assert result["id"] == "test-email-123"
            assert result["body"] == "Full email body"

    @pytest.mark.asyncio
    async def test_get_email_by_id_not_found(self, test_settings):
        """测试根据 ID 获取邮件 - 未找到"""
        db = Database(test_settings)

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None

        with patch.object(db, 'session') as mock_session_cm:
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result
            mock_session_cm.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cm.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db.get_email_by_id(email_id="nonexistent")

            assert result is None


class TestGetDatabase:
    """get_database 函数测试"""

    def test_get_database_returns_instance(self, test_settings):
        """测试 get_database 返回 Database 实例"""
        db = get_database(test_settings)

        assert isinstance(db, Database)
        assert db.settings == test_settings
