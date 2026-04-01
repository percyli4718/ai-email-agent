"""
批量邮件生成压力测试

测试系统在高负载下的性能表现：
- 批量生成 50/100/500 封邮件
- 测量响应时间和吞吐量
- 验证数据库写入性能
"""
import pytest
import time
from datetime import datetime

from email_agent.config import settings
from email_agent.generator.template_service import EmailTemplateService
from email_agent.generator.email_generator import EmailGenerator
from email_agent.storage.database import get_database
from email_agent.storage.models import Email
from sqlalchemy import select, func


@pytest.fixture
async def generator():
    """创建邮件生成器"""
    db = get_database(settings)
    await db.init_tables()
    template_service = EmailTemplateService(db)
    return EmailGenerator(template_service, db)


@pytest.fixture
async def db():
    """创建数据库连接"""
    db = get_database(settings)
    await db.init_tables()
    return db


class TestBatchGenerationPerformance:
    """批量生成性能测试"""

    @pytest.mark.asyncio
    async def test_generate_10_emails(self, generator, db):
        """测试生成 10 封邮件的性能"""
        start_time = time.perf_counter()

        emails = await generator.generate_emails(10)

        end_time = time.perf_counter()
        duration = end_time - start_time

        assert len(emails) == 10
        assert duration < 5.0  # 应在 5 秒内完成

        # 记录性能指标
        print(f"\n✓ 生成 10 封邮件：{duration:.3f}秒 | 平均每封：{duration/10*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_generate_50_emails(self, generator, db):
        """测试生成 50 封邮件的性能"""
        start_time = time.perf_counter()

        emails = await generator.generate_emails(50)

        end_time = time.perf_counter()
        duration = end_time - start_time

        assert len(emails) == 50
        assert duration < 20.0  # 应在 20 秒内完成

        # 记录性能指标
        print(f"\n✓ 生成 50 封邮件：{duration:.3f}秒 | 平均每封：{duration/50*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_generate_100_emails(self, generator, db):
        """测试生成 100 封邮件的性能"""
        start_time = time.perf_counter()

        emails = await generator.generate_emails(100)

        end_time = time.perf_counter()
        duration = end_time - start_time

        assert len(emails) == 100
        assert duration < 45.0  # 应在 45 秒内完成

        # 记录性能指标
        print(f"\n✓ 生成 100 封邮件：{duration:.3f}秒 | 平均每封：{duration/100*1000:.1f}ms")


class TestDatabaseWritePerformance:
    """数据库写入性能测试"""

    @pytest.mark.asyncio
    async def test_batch_insert_emails(self, generator, db):
        """测试批量插入邮件的性能"""
        from email_agent.storage.models import Email as EmailModel
        from sqlalchemy import insert

        # 生成 50 封邮件
        emails_data = await generator.generate_emails(50)

        start_time = time.perf_counter()

        # 批量插入
        async with db.session() as session:
            for email_data in emails_data:
                stmt = insert(EmailModel).values(
                    id=email_data["email_id"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    from_address=email_data["from_email"],
                    priority=email_data["priority"],
                    status="pending",
                    received_at=datetime.now(),
                )
                await session.execute(stmt)
            await session.commit()

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证插入数量
        stmt = select(func.count()).select_from(Email)
        result = await session.execute(stmt)
        count = result.scalar()

        assert count >= 50
        assert duration < 10.0  # 应在 10 秒内完成

        # 记录性能指标
        print(f"\n✓ 批量插入 50 封邮件：{duration:.3f}秒 | 平均每秒：{50/duration:.1f}封")


class TestConcurrentGeneration:
    """并发生成测试"""

    @pytest.mark.asyncio
    async def test_concurrent_email_generation(self, generator, db):
        """测试并发邮件生成"""
        import asyncio

        async def generate_batch(count):
            return await generator.generate_emails(count)

        # 并发生成 3 批邮件
        tasks = [
            asyncio.create_task(generate_batch(10)),
            asyncio.create_task(generate_batch(10)),
            asyncio.create_task(generate_batch(10))
        ]

        start_time = time.perf_counter()

        results = await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 验证结果
        assert len(results) == 3
        assert all(len(batch) == 10 for batch in results)
        assert duration < 10.0  # 应在 10 秒内完成

        # 记录性能指标
        total_emails = sum(len(batch) for batch in results)
        print(f"\n✓ 并发生成 30 封邮件 (3 批)：{duration:.3f}秒 | 吞吐量：{total_emails/duration:.1f}封/秒")


class TestSystemStress:
    """系统压力测试"""

    @pytest.mark.asyncio
    async def test_sustained_load(self, generator, db):
        """测试持续负载下的性能"""
        import asyncio

        batches = 5
        batch_size = 20
        total_expected = batches * batch_size

        async def generate_and_store():
            emails = await generator.generate_emails(batch_size)
            return len(emails)

        start_time = time.perf_counter()

        # 连续生成 5 批
        tasks = [asyncio.create_task(generate_and_store()) for _ in range(batches)]
        results = await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        duration = end_time - start_time

        total_generated = sum(results)

        assert total_generated == total_expected
        assert duration < 30.0  # 应在 30 秒内完成

        # 记录性能指标
        print(f"\n✓ 持续负载测试：{duration:.3f}秒")
        print(f"  总生成：{total_generated}封 | 平均：{total_generated/duration:.1f}封/秒")
