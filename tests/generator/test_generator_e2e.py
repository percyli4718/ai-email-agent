"""
Email Generator E2E Tests

端到端测试覆盖:
    - test_full_generation_flow: 完整生成流程测试
    - test_database_persistence: 数据库持久化测试
    - test_batch_generation_performance: 批量生成性能测试
"""
import pytest
import asyncio
from datetime import datetime

from email_agent.generator.email_generator import EmailGenerator
from email_agent.generator.template_service import EmailTemplateService
from email_agent.storage.database import Database, get_database
from email_agent.storage.models import Email, Customer, EmailTemplate, init_db_tables
from email_agent.config import settings
from sqlalchemy import select


@pytest.fixture
async def db():
    """
    创建数据库实例用于测试

    作用:
        提供真实的数据库实例用于 E2E 测试。
        测试前初始化表，测试后清理连接。

    使用场景:
        - E2E 测试需要真实数据库
        - 验证数据持久化
    """
    database = get_database(settings)
    await database.init_tables()
    yield database
    await database.close()


@pytest.fixture
async def setup_templates(db):
    """
    创建测试邮件模板

    作用:
        在测试前创建多个邮件模板供生成器使用。
        确保测试环境有可用的模板数据。

    使用场景:
        - 需要模板的生成测试
        - 批量生成测试

    返回:
        list[EmailTemplate]: 创建的模板列表
    """
    async with db.session() as session:
        # 检查是否已有模板
        stmt = select(EmailTemplate)
        result = await session.execute(stmt)
        existing_templates = result.scalars().all()

        if existing_templates:
            return existing_templates

        # 创建测试模板 - 注意：只能使用 generate_email 支持的占位符
        # subject_template.format(product, quantity, packing)
        # body_template.format(product, quantity, packing, standard, customer_name)
        templates = [
            EmailTemplate(
                type="inquiry",
                product_name="Paracetamol",
                region="Europe",
                quantity_range="100-500",
                subject_template="Inquiry about {product} - Quantity {quantity}",
                body_template="Dear {customer_name},\n\nWe are interested in {product} for our distribution network.\n\nQuantity Required: {quantity}\nPacking: {packing}\nStandard: {standard}\n\nPlease provide your best quote.\n\nBest regards,\nProcurement Team",
                is_active=True
            ),
            EmailTemplate(
                type="rfq",
                product_name="Ibuprofen",
                region="Asia",
                quantity_range="500-1000",
                subject_template="RFQ for {product}",
                body_template="Dear Supplier,\n\nWe need quote for {product}.\n\nQuantity: {quantity}\nPacking: {packing}\nStandard: {standard}\n\nLooking forward to your competitive quote.\n\nBest regards,\nSupply Chain Manager",
                is_active=True
            ),
            EmailTemplate(
                type="inquiry",
                product_name="Amoxicillin",
                region="South America",
                quantity_range="1000-5000",
                subject_template="Purchase Inquiry: {product}",
                body_template="Hello,\n\nWe want to purchase {product}.\n\nQuantity: {quantity}\nPacking: {packing}\nStandard: {standard}\n\nPlease send us your quote.\n\nRegards,\nProcurement Director",
                is_active=True
            ),
            EmailTemplate(
                type="rfq",
                product_name="Metformin",
                region="Middle East",
                quantity_range="200-800",
                subject_template="Request for Quote - {product}",
                body_template="Dear Sir/Madam,\n\nPlease quote for {product}.\n\nQuantity: {quantity}\nPacking: {packing}\nStandard: {standard}\n\nAwaiting your prompt response.\n\nRegards,\nPurchasing Manager",
                is_active=True
            ),
            EmailTemplate(
                type="inquiry",
                product_name="Omeprazole",
                region="Europe",
                quantity_range="50-200",
                subject_template="Product Inquiry: {product}",
                body_template="Dear Team,\n\nWe are looking for {product}.\n\nQuantity: {quantity}\nPacking: {packing}\nStandard: {standard}\n\nThanks in advance.\n\nBest regards,\nOperations Team",
                is_active=True
            ),
        ]

        for template in templates:
            session.add(template)

        await session.commit()

        # 返回创建的模板
        stmt = select(EmailTemplate).where(EmailTemplate.is_active == True)
        result = await session.execute(stmt)
        return result.scalars().all()


@pytest.fixture
def email_generator(db, setup_templates):
    """
    创建 EmailGenerator 实例用于测试

    作用:
        提供配置好模板服务和数据库的生成器实例。

    使用场景:
        - 所有需要生成器的测试
    """
    template_service = EmailTemplateService(db)
    generator = EmailGenerator(template_service, db)
    return generator


class TestFullGenerationFlow:
    """测试完整生成流程"""

    @pytest.mark.asyncio
    async def test_full_generation_flow(self, email_generator, db):
        """
        测试完整生成流程

        测试步骤:
            1. 生成 5 封邮件
            2. 验证所有邮件都有必需字段
            3. 验证所有 ID 都是唯一的

        验证点:
            - 邮件数量正确
            - 每封邮件都有必需字段 (id, from_address, subject, body 等)
            - 所有邮件 ID 都是唯一的
        """
        # 生成 5 封邮件
        emails = await email_generator.generate_emails(5)

        # 验证数量
        assert len(emails) == 5, f"Expected 5 emails, got {len(emails)}"

        # 验证必需字段
        required_fields = [
            "email_id", "from_name", "from_email", "region",
            "product_name", "quantity", "packing", "standard",
            "subject", "body", "priority"
        ]

        for email in emails:
            for field in required_fields:
                assert field in email, f"Missing required field: {field}"

            # 验证字段不为空
            assert email["email_id"], "email_id cannot be empty"
            assert email["from_email"], "from_email cannot be empty"
            assert email["subject"], "subject cannot be empty"
            assert email["body"], "body cannot be empty"
            assert "@" in email["from_email"], "Invalid email format"

        # 验证所有 ID 都是唯一的
        ids = [email["email_id"] for email in emails]
        unique_ids = set(ids)
        assert len(unique_ids) == len(ids), f"Duplicate IDs found: {ids}"


class TestDatabasePersistence:
    """测试数据库持久化"""

    @pytest.mark.asyncio
    async def test_database_persistence(self, email_generator, db):
        """
        测试数据库持久化

        测试步骤:
            1. 生成一封邮件
            2. 使用 get_or_create_customer 保存客户
            3. 创建 Email 记录保存到数据库
            4. 验证可以从数据库查询回该邮件

        验证点:
            - 客户成功保存或获取
            - 邮件记录成功保存
            - 可以从数据库查询到保存的邮件
        """
        # 生成一封邮件
        emails = await email_generator.generate_emails(1)
        email_data = emails[0]

        # 使用 get_or_create_customer 保存客户
        customer = await db.get_or_create_customer(
            email=email_data["from_email"],
            defaults={
                "name": email_data["from_name"],
                "region": email_data["region"],
            }
        )

        assert customer is not None, "Customer should not be None"
        assert customer.email == email_data["from_email"], "Customer email mismatch"

        # 创建 Email 记录保存到数据库
        async with db.session() as session:
            email_record = Email(
                id=email_data["email_id"],
                from_address=email_data["from_email"],
                subject=email_data["subject"],
                body=email_data["body"],
                priority=email_data["priority"],
                status="pending",
                region=email_data["region"],
                customer_id=customer.id
            )
            session.add(email_record)
            await session.commit()

        # 从数据库查询该邮件
        async with db.session() as session:
            stmt = select(Email).where(Email.id == email_data["email_id"])
            result = await session.execute(stmt)
            saved_email = result.scalars().first()

        # 验证查询结果
        assert saved_email is not None, "Email should be found in database"
        assert saved_email.id == email_data["email_id"], "Email ID mismatch"
        assert saved_email.from_address == email_data["from_email"], "From address mismatch"
        assert saved_email.subject == email_data["subject"], "Subject mismatch"
        assert saved_email.body == email_data["body"], "Body mismatch"
        assert saved_email.priority == email_data["priority"], "Priority mismatch"
        assert saved_email.customer_id == customer.id, "Customer ID mismatch"


class TestBatchGenerationPerformance:
    """测试批量生成性能"""

    @pytest.mark.asyncio
    async def test_batch_generation_performance(self, email_generator, db):
        """
        测试批量生成性能

        测试步骤:
            1. 记录开始时间
            2. 生成 20 封邮件
            3. 记录结束时间
            4. 验证耗时在 5 秒内
            5. 验证所有 ID 都是唯一的

        验证点:
            - 生成 20 封邮件
            - 耗时小于 5 秒
            - 所有邮件 ID 都是唯一的
        """
        # 记录开始时间
        start_time = datetime.utcnow()

        # 生成 20 封邮件
        emails = await email_generator.generate_emails(20)

        # 记录结束时间
        end_time = datetime.utcnow()

        # 计算耗时
        duration = (end_time - start_time).total_seconds()

        # 验证数量
        assert len(emails) == 20, f"Expected 20 emails, got {len(emails)}"

        # 验证耗时在 5 秒内
        assert duration < 5.0, f"Generation took {duration:.2f}s, expected < 5s"

        # 验证所有 ID 都是唯一的
        ids = [email["email_id"] for email in emails]
        unique_ids = set(ids)
        assert len(unique_ids) == len(ids), f"Duplicate IDs found in batch generation"

        # 验证每封邮件都有必需字段
        for email in emails:
            assert "email_id" in email
            assert "subject" in email
            assert "body" in email
            assert "priority" in email


class TestEmailGeneratorE2EIntegration:
    """EmailGenerator 端到端集成测试"""

    @pytest.mark.asyncio
    async def test_generate_and_save_multiple_emails(self, email_generator, db):
        """
        测试生成并保存多封邮件

        测试步骤:
            1. 生成 10 封邮件
            2. 保存所有邮件到数据库
            3. 验证数据库中邮件数量

        验证点:
            - 所有邮件都成功保存
            - 数据库查询返回正确数量
        """
        # 生成 10 封邮件
        emails = await email_generator.generate_emails(10)
        assert len(emails) == 10

        # 保存所有邮件到数据库
        saved_count = 0
        for email_data in emails:
            async with db.session() as session:
                # 保存客户
                customer = await db.get_or_create_customer(
                    email=email_data["from_email"],
                    defaults={
                        "name": email_data["from_name"],
                        "region": email_data["region"],
                    }
                )

                # 检查邮件是否已存在
                stmt = select(Email).where(Email.id == email_data["email_id"])
                result = await session.execute(stmt)
                existing = result.scalars().first()

                if not existing:
                    # 创建新邮件记录
                    email_record = Email(
                        id=email_data["email_id"],
                        from_address=email_data["from_email"],
                        subject=email_data["subject"],
                        body=email_data["body"],
                        priority=email_data["priority"],
                        status="pending",
                        region=email_data["region"],
                        customer_id=customer.id
                    )
                    session.add(email_record)
                    await session.commit()
                    saved_count += 1

        # 验证保存数量
        assert saved_count == 10, f"Expected to save 10 emails, saved {saved_count}"

        # 验证数据库查询
        all_emails = await db.get_all_emails(limit=100)
        assert len(all_emails) >= 10, f"Expected at least 10 emails in database, got {len(all_emails)}"

    @pytest.mark.asyncio
    async def test_email_id_format_and_uniqueness_across_generations(self, email_generator, db):
        """
        测试跨多次生成的 ID 格式和唯一性

        测试步骤:
            1. 分 3 次生成，每次生成 5 封邮件
            2. 验证所有 15 封邮件的 ID 格式
            3. 验证所有 ID 都是唯一的

        验证点:
            - ID 格式正确 (email_YYYYMMDDHHMMSS_XXXX)
            - 跨多次生成的 ID 保持唯一性
        """
        all_emails = []

        # 分 3 次生成
        for _ in range(3):
            emails = await email_generator.generate_emails(5)
            all_emails.extend(emails)

        # 验证总数
        assert len(all_emails) == 15

        # 验证所有 ID 都是唯一的
        ids = [email["email_id"] for email in all_emails]
        assert len(set(ids)) == 15, "All IDs should be unique across multiple generations"

        # 验证 ID 格式
        for email_id in ids:
            assert email_id.startswith("email_"), "ID should start with 'email_'"
            parts = email_id.split("_")
            assert len(parts) == 3, f"ID should have 3 parts, got {len(parts)}"
            assert len(parts[1]) == 14, f"Timestamp part should be 14 chars, got {len(parts[1])}"
            assert len(parts[2]) == 4, f"Random part should be 4 chars, got {len(parts[2])}"
