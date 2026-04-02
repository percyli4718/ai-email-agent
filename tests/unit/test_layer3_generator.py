"""
Layer 3 生成器单元测试

测试模块:
- src/email_agent/layer3/generator.py - QuoteGenerator 类
- src/email_agent/layer3/router.py - ModelRouter 类
- src/email_agent/layer3/prompts.py - 提示词模板

覆盖范围:
- QuoteGenerator 报价生成
- ModelRouter 模型路由
- 成本计算
- 报价验证
- 所有私有方法和边界情况
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from email_agent.layer3.generator import QuoteGenerator, QuoteGenerationError
from email_agent.layer3.router import ModelRouter, ModelChoice
from email_agent.layer3.prompts import QUOTE_GENERATION_PROMPT, QuoteResult, QuoteItem
from email_agent.config import Settings


# ============================================================================
# ModelRouter 测试
# ============================================================================

class TestModelRouter:
    """模型路由器测试"""

    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        return ModelRouter()

    def test_init(self, router):
        """测试路由器初始化"""
        assert router.target_sonnet_rate == 0.80

    def test_route_with_low_complexity(self, router):
        """测试路由 - 低复杂度使用 Sonnet"""
        context = {
            "pricing_policy": {"products": ["Paracetamol"]},
            "compliance": {},
            "customer_history": {"tier": "A"}
        }

        result = router.route(context)

        assert result == ModelChoice.SONNET

    def test_route_with_high_complexity_many_products(self, router):
        """测试路由 - 多产品高复杂度使用 Opus"""
        context = {
            "pricing_policy": {"products": ["Product1", "Product2", "Product3", "Product4", "Product5", "Product6"]},
            "compliance": {},
            "customer_history": {"tier": "A"}
        }

        result = router.route(context)

        assert result == ModelChoice.OPUS

    def test_route_with_special_permits(self, router):
        """测试路由 - 特殊许可高复杂度使用 Opus"""
        context = {
            "pricing_policy": {"products": ["Paracetamol"]},
            "compliance": {"special_permits": True},
            "customer_history": {"tier": "A"}
        }

        result = router.route(context)

        assert result == ModelChoice.OPUS

    def test_route_with_restrictions(self, router):
        """测试路由 - 出口限制使用 Opus"""
        context = {
            "pricing_policy": {"products": ["Paracetamol"]},
            "compliance": {"restrictions": True},
            "customer_history": {"tier": "A"}
        }

        result = router.route(context)

        assert result == ModelChoice.OPUS

    def test_route_with_new_customer(self, router):
        """测试路由 - 新客户使用 Opus"""
        context = {
            "pricing_policy": {"products": ["Paracetamol"]},
            "compliance": {},
            "customer_history": None
        }

        result = router.route(context)

        assert result == ModelChoice.OPUS

    def test_route_with_c_tier_customer(self, router):
        """测试路由 - C 级客户"""
        context = {
            "pricing_policy": {"products": ["Paracetamol"]},
            "compliance": {},
            "customer_history": {"tier": "C"}
        }

        result = router.route(context)

        # C 级客户增加 0.1 分，总分 0.1 < 0.4，仍然使用 Sonnet
        assert result == ModelChoice.SONNET

    def test_route_with_combined_complexity(self, router):
        """测试路由 - 组合复杂度"""
        # 多个因素组合使复杂度超过 0.4
        context = {
            "pricing_policy": {"products": ["P1", "P2", "P3"]},  # >2 个产品：+0.1
            "compliance": {"special_permits": True},  # 特殊许可：+0.3
            "customer_history": {"tier": "C"}  # C 级客户：+0.1
        }

        result = router.route(context)

        # 0.1 + 0.3 + 0.1 = 0.5 >= 0.4，使用 Opus
        assert result == ModelChoice.OPUS

    def test_calculate_complexity_empty_context(self, router):
        """测试复杂度计算 - 空上下文"""
        complexity = router._calculate_complexity({})

        # 空上下文：无历史记录 +0.2
        assert complexity == 0.2

    def test_calculate_complexity_many_products(self, router):
        """测试复杂度计算 - 多产品"""
        context = {
            "pricing_policy": {"products": ["P" + str(i) for i in range(10)]}
        }

        complexity = router._calculate_complexity(context)

        # >5 个产品：+0.2
        assert complexity == 0.2

    def test_calculate_complexity_moderate_products(self, router):
        """测试复杂度计算 - 中等数量产品"""
        context = {
            "pricing_policy": {"products": ["P1", "P2", "P3"]}
        }

        complexity = router._calculate_complexity(context)

        # >2 个产品：+0.1
        assert complexity == 0.1

    def test_calculate_complexity_max_score(self, router):
        """测试复杂度计算 - 最高分限制"""
        context = {
            "pricing_policy": {"products": ["P" + str(i) for i in range(10)]},  # +0.2
            "compliance": {"special_permits": True, "restrictions": True},  # +0.5
            "customer_history": None  # +0.2
        }

        complexity = router._calculate_complexity(context)

        # 0.2 + 0.3 + 0.2 + 0.2 = 0.9，但不超过 1.0
        assert complexity <= 1.0
        assert complexity == 0.9

    def test_model_choice_enum_values(self):
        """测试模型枚举值"""
        assert ModelChoice.SONNET.value == "claude-sonnet-4-20250514"
        assert ModelChoice.OPUS.value == "claude-opus-4-20250514"


# ============================================================================
# QuoteGenerator 测试
# ============================================================================

class TestQuoteGenerator:
    """报价生成器测试"""

    @pytest.fixture
    def settings(self):
        """创建设置对象"""
        settings = Settings()
        settings.anthropic_api_key = "test-key"
        settings.max_sonnet_cost_per_email = 0.10
        settings.max_opus_cost_per_email = 0.50
        settings.database_url = "sqlite+aiosqlite:///./test.db"
        return settings

    @pytest.fixture
    def generator(self, settings):
        """创建生成器实例"""
        return QuoteGenerator(settings)

    def test_init(self, settings, generator):
        """测试生成器初始化"""
        assert generator.settings == settings
        assert generator._client is None  # 懒加载
        assert isinstance(generator.router, ModelRouter)
        assert generator.budget_tracker is not None
        assert generator.db is not None

    def test_client_lazy_loading(self, settings):
        """测试客户端懒加载"""
        generator = QuoteGenerator(settings)

        assert generator._client is None

        with patch('email_agent.layer3.generator.anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.AsyncClient.return_value = mock_client

            result = generator.client

            assert generator._client is not None
            mock_anthropic.AsyncClient.assert_called_once_with(api_key="test-key")

    @pytest.mark.asyncio
    async def test_generate_quote(self, generator):
        """测试生成报价单"""
        mock_response = {
            "quote_id": "QT-2026-0001",
            "customer_email": "customer@brazil.com",
            "items": [{
                "product_name": "Paracetamol 500mg",
                "product_code": "PARA-500",
                "quantity": 50000,
                "unit_price": 2.50,
                "currency": "USD",
                "incoterm": "FOB",
                "lead_time_days": 30
            }],
            "total_amount": 125000.0,
            "valid_until": "2026-04-29",
            "shipping_port": "Shanghai",
            "payment_terms": "30% advance, 70% against B/L",
            "notes": "Standard terms apply"
        }

        with patch.object(generator, '_call_llm', return_value=json.dumps(mock_response)):
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with patch.object(generator.db, 'create_email_analysis', return_value=None):
                    with patch.object(generator.budget_tracker, 'get_last_cost', return_value=0.05):
                        result = await generator.generate_quote(
                            email_id="test-123",
                            original_email="We want to order Paracetamol",
                            context={
                                "similar_emails": {"documents": []},
                                "customer_history": {"tier": "B"},
                                "pricing_policy": {"policies": [{"product": "Paracetamol", "base_price": 2.0}]},
                                "compliance": {}
                            }
                        )

                        assert result["quote_id"] == "QT-2026-0001"
                        assert result["total_amount"] == 125000.0
                        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_generate_quote_json_parse_error(self, generator):
        """测试生成报价单 - JSON 解析失败"""
        with patch.object(generator, '_call_llm', return_value="Invalid JSON"):
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with pytest.raises(QuoteGenerationError) as exc_info:
                    await generator.generate_quote(
                        email_id="test-123",
                        original_email="Test",
                        context={}
                    )

                assert "Failed to parse quote" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_quote_missing_fields(self, generator):
        """测试生成报价单 - 缺少必需字段"""
        # 缺少 items 字段
        invalid_response = {"quote_id": "123", "total_amount": 1000}

        with patch.object(generator, '_call_llm', return_value=json.dumps(invalid_response)):
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with pytest.raises(QuoteGenerationError) as exc_info:
                    await generator.generate_quote(
                        email_id="test-123",
                        original_email="Test",
                        context={}
                    )

                assert "Missing required fields" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_quote_empty_items(self, generator):
        """测试生成报价单 - 空项目列表"""
        invalid_response = {
            "quote_id": "123",
            "customer_email": "test@example.com",
            "items": [],
            "total_amount": 0
        }

        with patch.object(generator, '_call_llm', return_value=json.dumps(invalid_response)):
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with pytest.raises(QuoteGenerationError) as exc_info:
                    await generator.generate_quote(
                        email_id="test-123",
                        original_email="Test",
                        context={}
                    )

                assert "at least one item" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_quote_model_routing(self, generator):
        """测试生成报价单 - 模型路由"""
        mock_response = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "items": [{"product_name": "Product", "quantity": 100, "unit_price": 1.0, "currency": "USD", "incoterm": "FOB", "lead_time_days": 30}],
            "total_amount": 100.0
        }

        with patch.object(generator, '_call_llm', return_value=json.dumps(mock_response)) as mock_call:
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with patch.object(generator.db, 'create_email_analysis', return_value=None):
                    with patch.object(generator.budget_tracker, 'get_last_cost', return_value=0.05):
                        # 使用简单上下文，应该路由到 Sonnet
                        context = {
                            "similar_emails": {},
                            "customer_history": {"tier": "A"},
                            "pricing_policy": {"products": ["Product"]},
                            "compliance": {}
                        }

                        await generator.generate_quote(
                            email_id="test-123",
                            original_email="Test",
                            context=context
                        )

                        # 验证使用了 Sonnet 模型
                        mock_call.assert_called_once()
                        call_args = mock_call.call_args
                        assert call_args[0][0] == ModelChoice.SONNET

    @pytest.mark.asyncio
    async def test_generate_quote_truncates_email(self, generator):
        """测试生成报价单 - 截断长邮件"""
        mock_response = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "items": [{"product_name": "Product", "quantity": 100, "unit_price": 1.0, "currency": "USD", "incoterm": "FOB", "lead_time_days": 30}],
            "total_amount": 100.0
        }

        long_email = "A" * 3000

        with patch.object(generator, '_call_llm', return_value=json.dumps(mock_response)) as mock_call:
            with patch.object(generator.budget_tracker, 'check_budget', return_value=None):
                with patch.object(generator.db, 'create_email_analysis', return_value=None):
                    with patch.object(generator.budget_tracker, 'get_last_cost', return_value=0.05):
                        await generator.generate_quote(
                            email_id="test-123",
                            original_email=long_email,
                            context={
                                "similar_emails": {},
                                "customer_history": {},
                                "pricing_policy": {},
                                "compliance": {}
                            }
                        )

                        # 验证邮件被截断到 2000 字符
                        call_args = mock_call.call_args
                        prompt = call_args[0][1]
                        assert long_email[:2000] in prompt
                        assert len(long_email[:2000]) == 2000

    @pytest.mark.asyncio
    async def test_call_llm(self, generator):
        """测试调用 LLM"""
        with patch.object(generator, 'client', MagicMock()) as mock_client:
            mock_response = MagicMock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50
            mock_response.content = [MagicMock(text="Quote result")]
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            with patch.object(generator.budget_tracker, 'record_spending', return_value=None) as mock_record:
                result = await generator._call_llm(ModelChoice.SONNET, "Test prompt")

                mock_client.messages.create.assert_called_once_with(
                    model=ModelChoice.SONNET.value,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": "Test prompt"}]
                )
                assert result == "Quote result"
                mock_record.assert_called_once()

    def test_calculate_cost_sonnet(self, generator):
        """测试成本计算 - Sonnet"""
        cost = generator._calculate_cost(
            model=ModelChoice.SONNET,
            input_tokens=1000,
            output_tokens=500
        )

        # Sonnet: 输入$3/百万，输出$15/百万
        expected = (1000 * 3e-6) + (500 * 1.5e-5)
        assert cost == expected

    def test_calculate_cost_opus(self, generator):
        """测试成本计算 - Opus"""
        cost = generator._calculate_cost(
            model=ModelChoice.OPUS,
            input_tokens=1000,
            output_tokens=500
        )

        # Opus: 输入$15/百万，输出$75/百万
        expected = (1000 * 1.5e-5) + (500 * 7.5e-5)
        assert cost == expected

    def test_format_similar_emails_empty(self, generator):
        """测试格式化相似邮件 - 空结果"""
        result = generator._format_similar_emails({"documents": []})

        assert result == "No similar emails found."

    def test_format_similar_emails_with_content(self, generator):
        """测试格式化相似邮件 - 有内容"""
        similar = {
            "documents": [["Email content 1", "Email content 2"]]
        }

        result = generator._format_similar_emails(similar)

        assert "Email content 1" in result
        assert "Email content 2" in result

    def test_format_similar_emails_limits_to_three(self, generator):
        """测试格式化相似邮件 - 限制 3 封"""
        similar = {
            "documents": [["E1", "E2", "E3", "E4", "E5"]]
        }

        result = generator._format_similar_emails(similar)

        # 应该只包含前 3 封
        assert "E1" in result
        assert "E2" in result
        assert "E3" in result
        assert "E4" not in result
        assert "E5" not in result

    def test_validate_quote_valid(self, generator):
        """测试验证报价 - 有效"""
        valid_quote = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "items": [{"product_name": "Product"}],
            "total_amount": 1000.0
        }

        # 不应该抛出异常
        generator._validate_quote(valid_quote)

    def test_validate_quote_missing_quote_id(self, generator):
        """测试验证报价 - 缺少 quote_id"""
        invalid_quote = {
            "customer_email": "test@example.com",
            "items": [{"product_name": "Product"}],
            "total_amount": 1000.0
        }

        with pytest.raises(QuoteGenerationError) as exc_info:
            generator._validate_quote(invalid_quote)

        assert "quote_id" in str(exc_info.value)

    def test_validate_quote_missing_customer_email(self, generator):
        """测试验证报价 - 缺少 customer_email"""
        invalid_quote = {
            "quote_id": "QT-001",
            "items": [{"product_name": "Product"}],
            "total_amount": 1000.0
        }

        with pytest.raises(QuoteGenerationError) as exc_info:
            generator._validate_quote(invalid_quote)

        assert "customer_email" in str(exc_info.value)

    def test_validate_quote_missing_items(self, generator):
        """测试验证报价 - 缺少 items"""
        invalid_quote = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "total_amount": 1000.0
        }

        with pytest.raises(QuoteGenerationError) as exc_info:
            generator._validate_quote(invalid_quote)

        assert "items" in str(exc_info.value)

    def test_validate_quote_missing_total_amount(self, generator):
        """测试验证报价 - 缺少 total_amount"""
        invalid_quote = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "items": [{"product_name": "Product"}]
        }

        with pytest.raises(QuoteGenerationError) as exc_info:
            generator._validate_quote(invalid_quote)

        assert "total_amount" in str(exc_info.value)

    def test_validate_quote_empty_items(self, generator):
        """测试验证报价 - 空 items 列表"""
        invalid_quote = {
            "quote_id": "QT-001",
            "customer_email": "test@example.com",
            "items": [],
            "total_amount": 0
        }

        with pytest.raises(QuoteGenerationError) as exc_info:
            generator._validate_quote(invalid_quote)

        assert "at least one item" in str(exc_info.value)


# ============================================================================
# QuoteGenerationError 测试
# ============================================================================

class TestQuoteGenerationError:
    """报价生成错误异常测试"""

    def test_error_creation(self):
        """测试异常创建"""
        error = QuoteGenerationError("Test error message")

        assert str(error) == "Test error message"

    def test_error_with_missing_fields(self):
        """测试缺少字段的异常"""
        error = QuoteGenerationError("Missing required fields: items, total_amount")

        assert "Missing required fields" in str(error)

    def test_error_raise_and_catch(self):
        """测试抛出和捕获异常"""
        def raise_error():
            raise QuoteGenerationError("Quote generation failed")

        with pytest.raises(QuoteGenerationError) as exc_info:
            raise_error()

        assert "Quote generation failed" in str(exc_info.value)


# ============================================================================
# 提示词模板测试
# ============================================================================

class TestPrompts:
    """提示词模板测试"""

    def test_quote_generation_prompt_template(self):
        """测试报价生成提示词模板存在"""
        assert QUOTE_GENERATION_PROMPT is not None
        assert isinstance(QUOTE_GENERATION_PROMPT, str)
        assert len(QUOTE_GENERATION_PROMPT) > 100

    def test_quote_generation_prompt_placeholders(self):
        """测试提示词模板占位符"""
        assert "{similar_emails}" in QUOTE_GENERATION_PROMPT
        assert "{customer_history}" in QUOTE_GENERATION_PROMPT
        assert "{pricing_policy}" in QUOTE_GENERATION_PROMPT
        assert "{compliance}" in QUOTE_GENERATION_PROMPT
        assert "{original_email}" in QUOTE_GENERATION_PROMPT

    def test_quote_result_typed_dict(self):
        """测试 QuoteResult 类型定义"""
        # 验证类型注解存在
        assert hasattr(QuoteResult, '__annotations__')

    def test_quote_item_typed_dict(self):
        """测试 QuoteItem 类型定义"""
        # 验证类型注解存在
        assert hasattr(QuoteItem, '__annotations__')
        annotations = QuoteItem.__annotations__

        assert "product_name" in annotations
        assert "quantity" in annotations
        assert "unit_price" in annotations
        assert "currency" in annotations
        assert "incoterm" in annotations
        assert "lead_time_days" in annotations
