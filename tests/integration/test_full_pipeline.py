"""
完整流程集成测试

测试 Layer 1→Layer 2→Layer 3 完整处理流程：
1. Layer 1: 邮件分类
2. Layer 2: 上下文检索
3. Layer 3: 报价生成
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from email_agent.config import Settings
from email_agent.layer1.classifier import EmailClassifier
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer3.generator import QuoteGenerator


@pytest.fixture
def settings():
    """创建测试配置"""
    settings = Settings()
    settings.anthropic_api_key = "test-key"
    settings.database_url = "sqlite+aiosqlite:///./test.db"
    return settings


class TestLayer1Classification:
    """Layer 1 分类测试"""

    @pytest.mark.asyncio
    async def test_classifier_inquiry(self, settings):
        """测试询价邮件分类"""
        import json
        mock_response = {
            "type": "inquiry",
            "priority_score": 0.85,
            "urgency": "high",
            "language": "en",
            "products_mentioned": ["Paracetamol 500mg"],
            "customer_region": "Europe",
            "requires_human": False,
            "suggested_route": "quote_flow"
        }

        with patch('email_agent.layer1.classifier.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                return_value=AsyncMock(content=[AsyncMock(text=json.dumps(mock_response))])
            )
            mock_create.return_value = mock_client

            classifier = EmailClassifier(settings)
            result = await classifier.classify(
                email_id="test-001",
                email_body="We want to order Paracetamol 500mg",
                subject="RFQ: Paracetamol"
            )

            assert result["type"] == "inquiry"
            assert result["suggested_route"] == "quote_flow"
            assert "Paracetamol 500mg" in result["products_mentioned"]

    @pytest.mark.asyncio
    async def test_classifier_complaint(self, settings):
        """测试投诉邮件分类"""
        import json
        mock_response = {
            "type": "complaint",
            "priority_score": 0.95,
            "urgency": "high",
            "language": "en",
            "products_mentioned": ["Batch #ABC789"],
            "customer_region": "Asia",
            "requires_human": True,
            "suggested_route": "complaint_flow"
        }

        with patch('email_agent.layer1.classifier.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                return_value=AsyncMock(content=[AsyncMock(text=json.dumps(mock_response))])
            )
            mock_create.return_value = mock_client

            classifier = EmailClassifier(settings)
            result = await classifier.classify(
                email_id="test-002",
                email_body="We have a problem with Batch #ABC789",
                subject="Quality Complaint"
            )

            assert result["type"] == "complaint"
            assert result["requires_human"] is True
            assert result["suggested_route"] == "complaint_flow"


class TestLayer2Retrieval:
    """Layer 2 检索测试"""

    @pytest.mark.asyncio
    async def test_retriever_with_mock_data(self, settings):
        """测试检索器返回上下文"""
        retriever = ContextRetriever(settings)

        mock_similar_emails = {
            "documents": [["Previous email content"]],
            "metadatas": [[{"email_id": "123", "type": "inquiry"}]]
        }

        with patch.object(retriever.chroma_client, 'search_similar',
                         return_value=mock_similar_emails):
            with patch.object(retriever.db, 'query_customer',
                             return_value={"name": "Test Customer", "tier": "B"}):
                with patch.object(retriever.db, 'query_pricing_policy',
                                 return_value={"policies": [], "region": "Europe"}):
                    with patch.object(retriever.db, 'query_compliance_requirements',
                                     return_value={"requirements": [{"type": "CE Marking"}]}):

                        result = await retriever.retrieve(
                            email_id="test-001",
                            email_body="We want to order Paracetamol",
                            classification={
                                "type": "inquiry",
                                "customer_region": "Europe",
                                "products_mentioned": ["Paracetamol 500mg"]
                            }
                        )

                        assert "similar_emails" in result
                        assert "customer_history" in result
                        assert "pricing_policy" in result
                        assert "compliance" in result


class TestLayer3Generation:
    """Layer 3 生成测试"""

    @pytest.mark.asyncio
    async def test_generator_creates_quote(self, settings):
        """测试生成器创建报价"""
        import json
        generator = QuoteGenerator(settings)

        mock_response = {
            "quote_id": "QT-2026-0001",
            "customer_email": "customer@test.com",
            "items": [{
                "product_name": "Paracetamol 500mg",
                "quantity": 1000,
                "unit_price": 2.50
            }],
            "total_amount": 2500.0,
            "valid_until": "2026-05-01",
            "shipping_port": "Shanghai",
            "payment_terms": "30% advance, 70% against B/L"
        }

        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(mock_response)

            result = await generator.generate_quote(
                email_id="test-001",
                original_email="We want to order Paracetamol",
                context={
                    "similar_emails": {"documents": []},
                    "customer_history": {"tier": "B"},
                    "pricing_policy": {"base_price": 2.0},
                    "compliance": {}
                }
            )

            assert result["quote_id"] == "QT-2026-0001"
            assert result["total_amount"] == 2500.0
            assert len(result["items"]) == 1


class TestFullPipeline:
    """完整流程集成测试"""

    @pytest.mark.asyncio
    async def test_full_email_processing_pipeline(self, settings):
        """测试完整邮件处理流程"""
        import json
        # Layer 1: 分类
        classification_result = {
            "type": "inquiry",
            "priority_score": 0.85,
            "urgency": "high",
            "language": "en",
            "products_mentioned": ["Paracetamol 500mg"],
            "customer_region": "Europe",
            "requires_human": False,
            "suggested_route": "quote_flow"
        }

        with patch('email_agent.layer1.classifier.create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.messages.create = AsyncMock(
                return_value=AsyncMock(content=[AsyncMock(text=json.dumps(classification_result))])
            )
            mock_create.return_value = mock_client

            classifier = EmailClassifier(settings)
            classification = await classifier.classify(
                email_id="test-full-001",
                email_body="We want to order Paracetamol 500mg",
                subject="RFQ"
            )

            assert classification["type"] == "inquiry"

        # Layer 2: 检索
        retriever = ContextRetriever(settings)

        with patch.object(retriever.chroma_client, 'search_similar',
                         return_value={
                             "documents": [["Similar inquiry from last week"]],
                             "metadatas": [[{"email_id": "prev-001"}]]
                         }):
            with patch.object(retriever.db, 'query_customer',
                             return_value={"name": "Test Customer", "tier": "A"}):
                with patch.object(retriever.db, 'query_pricing_policy',
                                 return_value={"policies": [{"product": "Paracetamol", "price": 2.5}]}):
                    with patch.object(retriever.db, 'query_compliance_requirements',
                                     return_value={"requirements": []}):

                        context = await retriever.retrieve(
                            email_id="test-full-001",
                            email_body="We want to order",
                            classification=classification
                        )

                        assert "pricing_policy" in context

        # Layer 3: 生成
        import json
        generator = QuoteGenerator(settings)

        quote_result = {
            "quote_id": "QT-2026-FULL-001",
            "customer_email": "customer@test.com",
            "items": [{"product_name": "Paracetamol 500mg", "quantity": 1000, "unit_price": 2.5}],
            "total_amount": 2500.0,
            "valid_until": "2026-05-01",
            "shipping_port": "Shanghai",
            "payment_terms": "30/70"
        }

        with patch.object(generator, '_call_llm') as mock_llm:
            mock_llm.return_value = json.dumps(quote_result)

            result = await generator.generate_quote(
                email_id="test-full-001",
                original_email="We want to order",
                context=context
            )

            assert result["quote_id"] == "QT-2026-FULL-001"
            assert result["total_amount"] == 2500.0
