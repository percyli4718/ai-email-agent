"""
邮件生成器 API 单元测试

测试覆盖:
    - generate_emails_success: 生成邮件成功
    - generate_emails_with_auto_process: 带自动处理生成邮件
    - generate_emails_invalid_count: 无效数量验证
    - list_templates: 获取模板列表
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from email_agent.api.schemas import (
    GenerateEmailsRequest,
    GeneratedEmailsResponse,
    GeneratedEmail,
    GeneratedEmailCustomer,
    EmailTemplateResponse,
    EmailTemplatesResponse,
)
from email_agent.storage.models import EmailTemplate


# ==================== Schema 测试 ====================


class TestGenerateEmailsRequest:
    """测试 GenerateEmailsRequest Schema"""

    def test_default_values(self):
        """测试默认值"""
        request = GenerateEmailsRequest()

        assert request.count == 1
        assert request.auto_process is False
        assert request.filters is None

    def test_valid_count(self):
        """测试有效数量"""
        request = GenerateEmailsRequest(count=10)
        assert request.count == 10

    def test_auto_process_true(self):
        """测试自动处理为 True"""
        request = GenerateEmailsRequest(auto_process=True)
        assert request.auto_process is True

    def test_filters_dict(self):
        """测试过滤条件"""
        request = GenerateEmailsRequest(filters={"region": "Europe", "type": "rfq"})
        assert request.filters == {"region": "Europe", "type": "rfq"}

    def test_count_minimum_validation(self):
        """测试最小数量验证"""
        # count=1 应该有效
        request = GenerateEmailsRequest(count=1)
        assert request.count == 1

    def test_count_maximum_validation(self):
        """测试最大数量验证"""
        # count=100 应该有效
        request = GenerateEmailsRequest(count=100)
        assert request.count == 100

    def test_count_below_minimum_raises_error(self):
        """测试数量低于最小值抛出异常"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            GenerateEmailsRequest(count=0)

        assert "count" in str(exc_info.value)

    def test_count_above_maximum_raises_error(self):
        """测试数量超过最大值抛出异常"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            GenerateEmailsRequest(count=101)

        assert "count" in str(exc_info.value)


class TestGeneratedEmailCustomer:
    """测试 GeneratedEmailCustomer Schema"""

    def test_valid_customer(self):
        """测试有效客户"""
        customer = GeneratedEmailCustomer(
            name="John Doe",
            company="PharmaCom Ltd",
            email="john@pharmacom.com"
        )

        assert customer.name == "John Doe"
        assert customer.company == "PharmaCom Ltd"
        assert customer.email == "john@pharmacom.com"


class TestGeneratedEmail:
    """测试 GeneratedEmail Schema"""

    def test_valid_email(self):
        """测试有效邮件"""
        customer = GeneratedEmailCustomer(
            name="John Doe",
            company="PharmaCom Ltd",
            email="john@pharmacom.com"
        )

        email = GeneratedEmail(
            id="email_001",
            from_address="john@pharmacom.com",
            subject="RFQ for Products",
            preview="Dear Supplier, We are interested...",
            priority="high",
            status="pending",
            region="Europe",
            customer=customer
        )

        assert email.id == "email_001"
        assert email.priority == "high"
        assert email.status == "pending"
        assert email.customer.name == "John Doe"


class TestGeneratedEmailsResponse:
    """测试 GeneratedEmailsResponse Schema"""

    def test_valid_response(self):
        """测试有效响应"""
        customer = GeneratedEmailCustomer(
            name="John Doe",
            company="PharmaCom Ltd",
            email="john@pharmacom.com"
        )

        email = GeneratedEmail(
            id="email_001",
            from_address="john@pharmacom.com",
            subject="RFQ for Products",
            preview="Dear Supplier...",
            priority="high",
            status="pending",
            region="Europe",
            customer=customer
        )

        response = GeneratedEmailsResponse(
            generated_emails=[email],
            total=1,
            auto_process_started=False
        )

        assert len(response.generated_emails) == 1
        assert response.total == 1
        assert response.auto_process_started is False


class TestEmailTemplateResponse:
    """测试 EmailTemplateResponse Schema"""

    def test_valid_template_response(self):
        """测试有效模板响应"""
        response = EmailTemplateResponse(
            id=1,
            type="inquiry",
            product_name="Paracetamol",
            region="Europe",
            quantity_range="100-500",
            is_active=True,
            created_at="2025-03-30T10:00:00Z"
        )

        assert response.id == 1
        assert response.type == "inquiry"
        assert response.is_active is True


class TestEmailTemplatesResponse:
    """测试 EmailTemplatesResponse Schema"""

    def test_valid_templates_response(self):
        """测试有效模板列表响应"""
        template = EmailTemplateResponse(
            id=1,
            type="inquiry",
            product_name="Paracetamol",
            region="Europe",
            quantity_range="100-500",
            is_active=True,
            created_at="2025-03-30T10:00:00Z"
        )

        response = EmailTemplatesResponse(
            templates=[template],
            total=1
        )

        assert len(response.templates) == 1
        assert response.total == 1


# ==================== API 端点测试 ====================


@pytest.mark.asyncio
class TestGenerateEmailsEndpoint:
    """测试 /api/emails/generate 端点"""

    async def test_generate_emails_success(self, client, mock_db):
        """测试生成邮件成功"""
        # 准备测试数据
        sample_template = EmailTemplate(
            id=1,
            type="inquiry",
            product_name="Paracetamol",
            region="Europe",
            quantity_range="100-500",
            subject_template="Inquiry about {product}",
            body_template="Dear {customer_name},\n\nWe are interested in {product}...",
            is_active=True
        )

        # Mock 模板服务
        with patch('email_agent.api.routes.EmailTemplateService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_random_template = AsyncMock(return_value=sample_template)
            mock_service_class.return_value = mock_service

            # Mock 数据库
            mock_db.get_or_create_customer = AsyncMock(return_value=MagicMock(
                id=1,
                name="PharmaCom UK",
                email="orders@pharmacom.co.uk",
                region="Europe",
                tier="C"
            ))

            # 发送请求
            response = client.post("/api/emails/generate", json={"count": 1})

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "generated_emails" in data
            assert data["total"] >= 1
            assert "auto_process_started" in data

    async def test_generate_emails_with_auto_process(self, client, mock_db):
        """测试带自动处理生成邮件"""
        sample_template = EmailTemplate(
            id=1,
            type="rfq",
            product_name="Ibuprofen",
            region="Asia",
            quantity_range="500-1000",
            subject_template="RFQ for {product}",
            body_template="Quote for {product}...",
            is_active=True
        )

        with patch('email_agent.api.routes.EmailTemplateService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_random_template = AsyncMock(return_value=sample_template)
            mock_service_class.return_value = mock_service

            mock_db.get_or_create_customer = AsyncMock(return_value=MagicMock(
                id=2,
                name="Asia Meds",
                email="orders@asiameds.com",
                region="Asia",
                tier="B"
            ))

            # 发送带 auto_process=true 的请求
            response = client.post("/api/emails/generate", json={
                "count": 3,
                "auto_process": True
            })

            assert response.status_code == 200
            data = response.json()
            assert data["auto_process_started"] is True
            assert data["total"] >= 1

    async def test_generate_emails_invalid_count(self, client):
        """测试无效数量验证"""
        # 测试 count=0
        response = client.post("/api/emails/generate", json={"count": 0})
        assert response.status_code == 422  # Validation Error

        # 测试 count=101
        response = client.post("/api/emails/generate", json={"count": 101})
        assert response.status_code == 422

        # 测试 count=-1
        response = client.post("/api/emails/generate", json={"count": -1})
        assert response.status_code == 422


@pytest.mark.asyncio
class TestListTemplatesEndpoint:
    """测试 /api/emails/templates 端点"""

    async def test_list_templates(self, client, mock_db):
        """测试获取模板列表"""
        # 准备测试数据
        sample_templates = [
            EmailTemplate(
                id=1,
                type="inquiry",
                product_name="Paracetamol",
                region="Europe",
                quantity_range="100-500",
                subject_template="Inquiry about {product}",
                body_template="Dear {customer_name},\n\nWe are interested in {product}...",
                is_active=True,
                created_at=datetime(2025, 3, 30, 10, 0, 0)
            ),
            EmailTemplate(
                id=2,
                type="rfq",
                product_name="Ibuprofen",
                region="Asia",
                quantity_range="500-1000",
                subject_template="RFQ for {product}",
                body_template="Quote for {product}...",
                is_active=True,
                created_at=datetime(2025, 3, 29, 14, 30, 0)
            ),
        ]

        # Mock 模板服务
        with patch('email_agent.api.routes.EmailTemplateService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_all_templates = AsyncMock(return_value=sample_templates)
            mock_service_class.return_value = mock_service

            # 发送请求
            response = client.get("/api/emails/templates")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert data["total"] == 2
            assert len(data["templates"]) == 2

            # 验证第一个模板
            first_template = data["templates"][0]
            assert first_template["id"] == 1
            assert first_template["type"] == "inquiry"
            assert first_template["product_name"] == "Paracetamol"
            assert first_template["region"] == "Europe"
            assert first_template["quantity_range"] == "100-500"
            assert first_template["is_active"] is True


# ==================== 集成测试 ====================


@pytest.mark.asyncio
class TestGeneratorAPIIntegration:
    """邮件生成器 API 集成测试"""

    async def test_generate_then_list_templates(self, client, mock_db):
        """测试生成邮件后获取模板列表"""
        sample_templates = [
            EmailTemplate(
                id=1,
                type="inquiry",
                product_name="Paracetamol",
                region="Europe",
                quantity_range="100-500",
                subject_template="Inquiry about {product}",
                body_template="Dear {customer_name},\n\nWe are interested in {product}...",
                is_active=True,
                created_at=datetime(2025, 3, 30, 10, 0, 0)
            )
        ]

        with patch('email_agent.api.routes.EmailTemplateService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_random_template = AsyncMock(return_value=sample_templates[0])
            mock_service.get_all_templates = AsyncMock(return_value=sample_templates)
            mock_service_class.return_value = mock_service

            mock_db.get_or_create_customer = AsyncMock(return_value=MagicMock(
                id=1,
                name="Test Customer",
                email="test@example.com",
                region="Europe",
                tier="C"
            ))

            # 先生成邮件
            gen_response = client.post("/api/emails/generate", json={"count": 1})
            assert gen_response.status_code == 200

            # 再获取模板列表
            list_response = client.get("/api/emails/templates")
            assert list_response.status_code == 200
            assert list_response.json()["total"] >= 1


# ==================== Quote Generator API Tests ====================


class TestQuoteItemSchema:
    """测试 QuoteItemSchema Schema"""

    def test_valid_quote_item(self):
        """测试有效的报价项目"""
        from email_agent.api.schemas import QuoteItemSchema

        item = QuoteItemSchema(
            product_name="Paracetamol 500mg",
            product_code="PAR-500",
            quantity=1000,
            unit_price=2.50,
            currency="USD",
            incoterm="FOB",
            lead_time_days=30,
            subtotal=2500.0
        )

        assert item.product_name == "Paracetamol 500mg"
        assert item.quantity == 1000
        assert item.unit_price == 2.50
        assert item.subtotal == 2500.0


class TestQuoteSchema:
    """测试 QuoteSchema Schema"""

    def test_valid_quote(self):
        """测试有效的报价单"""
        from email_agent.api.schemas import QuoteSchema, QuoteItemSchema

        item = QuoteItemSchema(
            product_name="Paracetamol 500mg",
            quantity=1000,
            unit_price=2.50,
            incoterm="FOB",
            lead_time_days=30,
            subtotal=2500.0
        )

        quote = QuoteSchema(
            id=1,
            quote_id="QT-2026-0001",
            email_id="email_001",
            customer_email="customer@example.com",
            items=[item],
            total_amount=2500.0,
            valid_until="2026-04-30",
            shipping_port="Shanghai, China",
            payment_terms="30% advance, 70% against B/L",
            notes="Subject to ANVISA approval",
            status="draft",
            created_at="2026-04-02T10:00:00Z"
        )

        assert quote.quote_id == "QT-2026-0001"
        assert quote.total_amount == 2500.0
        assert len(quote.items) == 1
        assert quote.status == "draft"


class TestQuoteListResponse:
    """测试 QuoteListResponse Schema"""

    def test_valid_quote_list(self):
        """测试有效的报价单列表"""
        from email_agent.api.schemas import QuoteListResponse, QuoteSchema, QuoteItemSchema

        item = QuoteItemSchema(
            product_name="Paracetamol 500mg",
            quantity=1000,
            unit_price=2.50,
            incoterm="FOB",
            lead_time_days=30,
            subtotal=2500.0
        )

        quote = QuoteSchema(
            id=1,
            quote_id="QT-2026-0001",
            email_id="email_001",
            customer_email="customer@example.com",
            items=[item],
            total_amount=2500.0,
            valid_until="2026-04-30",
            shipping_port="Shanghai, China",
            payment_terms="30% advance, 70% against B/L",
            status="draft",
            created_at="2026-04-02T10:00:00Z"
        )

        response = QuoteListResponse(
            quotes=[quote],
            total=1
        )

        assert len(response.quotes) == 1
        assert response.total == 1


class TestQuoteGenerateRequest:
    """测试 QuoteGenerateRequest Schema"""

    def test_valid_request(self):
        """测试有效的报价生成请求"""
        from email_agent.api.schemas import QuoteGenerateRequest

        request = QuoteGenerateRequest(
            email_id="email_001"
        )

        assert request.email_id == "email_001"
        assert request.context is None

    def test_request_with_context(self):
        """测试带上下文的请求"""
        from email_agent.api.schemas import QuoteGenerateRequest

        request = QuoteGenerateRequest(
            email_id="email_001",
            context={"pricing_policy": {"products": ["Paracetamol"]}}
        )

        assert request.email_id == "email_001"
        assert request.context is not None


class TestQuoteGenerateResponse:
    """测试 QuoteGenerateResponse Schema"""

    def test_valid_response(self):
        """测试有效的报价生成响应"""
        from email_agent.api.schemas import QuoteGenerateResponse, QuoteSchema, QuoteItemSchema

        item = QuoteItemSchema(
            product_name="Paracetamol 500mg",
            quantity=1000,
            unit_price=2.50,
            incoterm="FOB",
            lead_time_days=30,
            subtotal=2500.0
        )

        quote = QuoteSchema(
            id=1,
            quote_id="QT-2026-0001",
            email_id="email_001",
            customer_email="customer@example.com",
            items=[item],
            total_amount=2500.0,
            valid_until="2026-04-30",
            shipping_port="Shanghai, China",
            payment_terms="30% advance, 70% against B/L",
            status="draft",
            created_at="2026-04-02T10:00:00Z"
        )

        response = QuoteGenerateResponse(
            quote=quote,
            message="Quote generated successfully"
        )

        assert response.quote.quote_id == "QT-2026-0001"
        assert response.message == "Quote generated successfully"
