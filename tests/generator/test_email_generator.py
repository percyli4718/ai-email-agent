"""
EmailGenerator 单元测试

测试覆盖:
    - generate_email: 生成单封邮件
    - generate_email_id_format: 邮件 ID 格式
    - generate_email_quantity_in_range: 数量在范围内
    - generate_email_priority_logic: 优先级逻辑
    - generate_batch_emails: 批量生成邮件
    - generate_no_templates: 无模板时异常
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from email_agent.generator.email_generator import EmailGenerator
from email_agent.generator.template_service import EmailTemplateService
from email_agent.storage.database import Database
from email_agent.storage.models import EmailTemplate


@pytest.fixture
def sample_template():
    """创建示例模板"""
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


@pytest.fixture
def mock_template_service():
    """创建模拟模板服务"""
    return MagicMock(spec=EmailTemplateService)


@pytest.fixture
def mock_db():
    """创建模拟数据库"""
    return MagicMock(spec=Database)


@pytest.fixture
def email_generator(mock_template_service, mock_db):
    """创建 EmailGenerator 实例"""
    return EmailGenerator(mock_template_service, mock_db)


class TestEmailGeneratorInit:
    """测试 EmailGenerator 初始化"""

    def test_init_with_template_service_and_db(self, mock_template_service, mock_db):
        """测试初始化时正确设置服务"""
        generator = EmailGenerator(mock_template_service, mock_db)

        assert generator.template_service is mock_template_service
        assert generator.db is mock_db

    def test_class_attributes_exist(self):
        """测试类属性存在"""
        assert hasattr(EmailGenerator, "CUSTOMER_NAMES")
        assert hasattr(EmailGenerator, "PACKING_OPTIONS")
        assert hasattr(EmailGenerator, "STANDARDS")

        assert isinstance(EmailGenerator.CUSTOMER_NAMES, dict)
        assert isinstance(EmailGenerator.PACKING_OPTIONS, list)
        assert isinstance(EmailGenerator.STANDARDS, list)

    def test_customer_names_by_region(self):
        """测试各区域都有客户名称"""
        regions = ["Europe", "South America", "Asia", "Middle East"]

        for region in regions:
            assert region in EmailGenerator.CUSTOMER_NAMES
            assert len(EmailGenerator.CUSTOMER_NAMES[region]) > 0

    def test_packing_options_not_empty(self):
        """测试包装选项不为空"""
        assert len(EmailGenerator.PACKING_OPTIONS) > 0

    def test_standards_not_empty(self):
        """测试标准认证列表不为空"""
        assert len(EmailGenerator.STANDARDS) > 0


class TestGenerateCustomerName:
    """测试 _generate_customer_name 方法"""

    def test_generate_customer_name_for_europe(self, email_generator):
        """测试生成欧洲客户名称"""
        result = email_generator._generate_customer_name("Europe")

        assert "name" in result
        assert "email" in result
        assert "@" in result["email"]

    def test_generate_customer_name_for_south_america(self, email_generator):
        """测试生成南美客户名称"""
        result = email_generator._generate_customer_name("South America")

        assert "name" in result
        assert "email" in result

    def test_generate_customer_name_for_asia(self, email_generator):
        """测试生成亚洲客户名称"""
        result = email_generator._generate_customer_name("Asia")

        assert "name" in result
        assert "email" in result

    def test_generate_customer_name_for_middle_east(self, email_generator):
        """测试生成中东客户名称"""
        result = email_generator._generate_customer_name("Middle East")

        assert "name" in result
        assert "email" in result

    def test_generate_customer_name_unknown_region_returns_default(self, email_generator):
        """测试未知区域返回默认客户"""
        result = email_generator._generate_customer_name("Unknown Region")

        assert result["name"] == "Global Trading Co"
        assert result["email"] == "orders@globaltrading.com"


class TestGenerateQuantity:
    """测试 _generate_quantity 方法"""

    def test_generate_quantity_in_range(self, email_generator):
        """测试生成的数量在范围内"""
        quantity = email_generator._generate_quantity("100-500")

        assert 100 <= quantity <= 500

    def test_generate_quantity_large_range(self, email_generator):
        """测试大范围数量生成"""
        quantity = email_generator._generate_quantity("1000-5000")

        assert 1000 <= quantity <= 5000

    def test_generate_quantity_invalid_format_returns_default(self, email_generator):
        """测试无效格式返回默认值"""
        quantity = email_generator._generate_quantity("invalid")

        assert quantity == 100

    def test_generate_quantity_empty_string_returns_default(self, email_generator):
        """测试空字符串返回默认值"""
        quantity = email_generator._generate_quantity("")

        assert quantity == 100


class TestGenerateEmailId:
    """测试 _generate_email_id 方法"""

    def test_generate_email_id_format(self, email_generator):
        """测试邮件 ID 格式"""
        email_id = email_generator._generate_email_id()

        # 格式：email_YYYYMMDDHHMMSS_XXXX
        assert email_id.startswith("email_")
        parts = email_id.split("_")
        assert len(parts) == 3
        assert len(parts[1]) == 14  # YYYYMMDDHHMMSS
        assert len(parts[2]) == 4  # XXXX

    def test_generate_email_id_unique(self, email_generator):
        """测试生成的 ID 唯一性"""
        ids = set()
        for _ in range(100):
            ids.add(email_generator._generate_email_id())

        # 100 次生成应该有 100 个不同的 ID（或非常接近）
        assert len(ids) >= 95  # 允许极少数重复

    def test_generate_email_id_timestamp_valid(self, email_generator):
        """测试邮件 ID 时间戳有效"""
        email_id = email_generator._generate_email_id()
        timestamp_str = email_id.split("_")[1]

        # 验证时间戳格式
        year = int(timestamp_str[0:4])
        month = int(timestamp_str[4:6])
        day = int(timestamp_str[6:8])

        assert 2020 <= year <= 2030
        assert 1 <= month <= 12
        assert 1 <= day <= 31


class TestDeterminePriority:
    """测试 _determine_priority 方法"""

    def test_priority_high_for_quantity_over_1000(self, email_generator):
        """测试数量超过 1000 为高优先级"""
        assert email_generator._determine_priority(1001) == "high"
        assert email_generator._determine_priority(2000) == "high"
        assert email_generator._determine_priority(5000) == "high"

    def test_priority_medium_for_quantity_1000_or_less(self, email_generator):
        """测试数量 1000 或以下为中优先级"""
        assert email_generator._determine_priority(1000) == "medium"
        assert email_generator._determine_priority(500) == "medium"
        assert email_generator._determine_priority(100) == "medium"
        assert email_generator._determine_priority(1) == "medium"


@pytest.mark.asyncio
class TestGenerateEmail:
    """测试 generate_email 方法"""

    async def test_generate_single_email(self, email_generator, mock_template_service, sample_template):
        """测试生成单封邮件"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert "email_id" in email
        assert "from_name" in email
        assert "from_email" in email
        assert "region" in email
        assert "product_name" in email
        assert "quantity" in email
        assert "packing" in email
        assert "standard" in email
        assert "subject" in email
        assert "body" in email
        assert "priority" in email

    async def test_generate_email_id_format(self, email_generator, mock_template_service, sample_template):
        """测试生成的邮件 ID 格式"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert email["email_id"].startswith("email_")
        parts = email["email_id"].split("_")
        assert len(parts) == 3
        assert len(parts[1]) == 14

    async def test_generate_email_quantity_in_range(self, email_generator, mock_template_service, sample_template):
        """测试生成的数量在模板范围内"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        # 多次生成验证都在范围内
        for _ in range(10):
            email = await email_generator.generate_email()
            assert 100 <= email["quantity"] <= 500

    async def test_generate_email_priority_logic(self, email_generator, mock_template_service):
        """测试优先级逻辑"""
        # 创建高数量范围模板
        high_qty_template = EmailTemplate(
            id=2,
            type="rfq",
            product_name="Ibuprofen",
            region="Asia",
            quantity_range="2000-5000",
            subject_template="RFQ for {product}",
            body_template="Quote for {product}...",
            is_active=True
        )

        # 创建低数量范围模板
        low_qty_template = EmailTemplate(
            id=3,
            type="inquiry",
            product_name="Aspirin",
            region="Europe",
            quantity_range="100-500",
            subject_template="Inquiry for {product}",
            body_template="Interested in {product}...",
            is_active=True
        )

        # 测试高优先级
        mock_template_service.get_random_template = AsyncMock(return_value=high_qty_template)
        email = await email_generator.generate_email()
        assert email["priority"] == "high"
        assert email["quantity"] > 1000

        # 测试中优先级
        mock_template_service.get_random_template = AsyncMock(return_value=low_qty_template)
        email = await email_generator.generate_email()
        assert email["priority"] == "medium"
        assert email["quantity"] <= 1000

    async def test_generate_email_subject_uses_template(self, email_generator, mock_template_service, sample_template):
        """测试主题使用模板"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert sample_template.product_name in email["subject"]

    async def test_generate_email_body_uses_template(self, email_generator, mock_template_service, sample_template):
        """测试正文使用模板"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert sample_template.product_name in email["body"]

    async def test_generate_email_no_templates_raises_error(self, email_generator, mock_template_service):
        """测试无模板时抛出异常"""
        mock_template_service.get_random_template = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="No email templates available"):
            await email_generator.generate_email()

    async def test_generate_email_packing_from_options(self, email_generator, mock_template_service, sample_template):
        """测试包装选项来自预定义列表"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert email["packing"] in EmailGenerator.PACKING_OPTIONS

    async def test_generate_email_standard_from_list(self, email_generator, mock_template_service, sample_template):
        """测试标准认证来自预定义列表"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        email = await email_generator.generate_email()

        assert email["standard"] in EmailGenerator.STANDARDS


@pytest.mark.asyncio
class TestGenerateBatchEmails:
    """测试 generate_emails 批量生成方法"""

    async def test_generate_batch_emails(self, email_generator, mock_template_service, sample_template):
        """测试批量生成邮件"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        emails = await email_generator.generate_emails(5)

        assert len(emails) == 5
        for email in emails:
            assert "email_id" in email
            assert "subject" in email
            assert "body" in email

    async def test_generate_batch_emails_unique_ids(self, email_generator, mock_template_service, sample_template):
        """测试批量生成的邮件 ID 唯一"""
        mock_template_service.get_random_template = AsyncMock(return_value=sample_template)

        emails = await email_generator.generate_emails(10)

        ids = [email["email_id"] for email in emails]
        assert len(set(ids)) == len(ids)  # 所有 ID 都唯一

    async def test_generate_batch_emails_count_zero_raises_error(self, email_generator):
        """测试数量为 0 抛出异常"""
        with pytest.raises(ValueError, match="Count must be a positive integer"):
            await email_generator.generate_emails(0)

    async def test_generate_batch_emails_negative_count_raises_error(self, email_generator):
        """测试负数数量抛出异常"""
        with pytest.raises(ValueError, match="Count must be a positive integer"):
            await email_generator.generate_emails(-5)

    async def test_generate_batch_no_templates_raises_error(self, email_generator, mock_template_service):
        """测试无模板时批量生成抛出异常"""
        mock_template_service.get_random_template = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="No email templates available"):
            await email_generator.generate_emails(5)


class TestEmailGeneratorIntegration:
    """EmailGenerator 集成测试"""

    def test_all_regions_have_valid_customers(self):
        """测试所有区域都有有效的客户"""
        for region, customers in EmailGenerator.CUSTOMER_NAMES.items():
            for customer in customers:
                assert "name" in customer
                assert "email" in customer
                assert "@" in customer["email"]

    def test_packing_options_are_valid_strings(self):
        """测试包装选项都是有效字符串"""
        for option in EmailGenerator.PACKING_OPTIONS:
            assert isinstance(option, str)
            assert len(option) > 0

    def test_standards_are_valid_strings(self):
        """测试标准认证都是有效字符串"""
        for standard in EmailGenerator.STANDARDS:
            assert isinstance(standard, str)
            assert len(standard) > 0
