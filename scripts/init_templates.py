#!/usr/bin/env python3
"""
邮件模板初始化脚本

用于初始化数据库中的邮件模板，确保生成邮件功能正常工作。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import EmailTemplate


async def init_templates():
    """初始化邮件模板"""
    db = get_database(settings)
    await db.init_tables()

    async with db.session() as session:
        from sqlalchemy import select, delete

        # 检查是否已有模板
        stmt = select(EmailTemplate)
        result = await session.execute(stmt)
        existing_templates = result.scalars().all()

        if existing_templates:
            print(f"✓ 数据库中已有 {len(existing_templates)} 个模板")
            return

        # 删除现有模板（如果有）
        await session.execute(delete(EmailTemplate))

        # 创建模板
        templates = [
            EmailTemplate(
                type="RFQ",
                product_name="Paracetamol 500mg",
                region="Europe",
                quantity_range="1000-5000",
                subject_template="Request for Quote - {product}",
                body_template="""Dear Supplier,

We are interested in purchasing the following product:
- {product}: {quantity} boxes

Destination: {region}

Please provide your best quote including:
- FOB Price
- CIF Price
- Delivery Time
- Payment Terms

Looking forward to your reply.

Best regards,
{customer_name}
""",
                is_active=True
            ),
            EmailTemplate(
                type="Order Status",
                product_name="Losartan 50mg",
                region="Europe",
                quantity_range="500-2000",
                subject_template="Order Status: {product} - Shipping Inquiry",
                body_template="""Dear Logistics Team,

Please provide the latest status of our order for {product}.

Order Details:
- Quantity: {quantity}
- Destination: {region}
- Estimated Delivery: TBD

We have not yet received shipping confirmation.

Customer: {customer_name}
Contact: {email}

Thank you.

Best regards,
{customer_name}
""",
                is_active=True
            ),
            EmailTemplate(
                type="Quality Complaint",
                product_name="Amoxicillin 500mg",
                region="Europe",
                quantity_range="1000-5000",
                subject_template="Quality Complaint: {product} - Batch Issue",
                body_template="""Dear Quality Team,

We regret to inform you of an issue with {product}.

Issue Details:
- Packaging damaged
- Partial tablets crushed
- Batch affected: {batch_number}

Affected Quantity: {quantity}
Region: {region}

We require immediate action:
1. Replacement of affected batch
2. Root cause analysis
3. Preventive measures

Customer: {customer_name}
Contact: {email}

Best regards,
{customer_name}
""",
                is_active=True
            ),
            EmailTemplate(
                type="Shipping Status",
                product_name="Atorvastatin 20mg",
                region="South America",
                quantity_range="500-3000",
                subject_template="Shipping Status Inquiry - {product}",
                body_template="""Dear Partner,

We are writing to inquire about the status of our {product} order.

Details:
- Order Quantity: {quantity}
- Ship to: {region}
- Order Date: TBD

Please provide:
- Current order status
- Estimated shipping date
- Tracking information

Contact: {customer_name}
{email}

Thank you for your prompt response.

Best regards,
{customer_name}
""",
                is_active=True
            ),
        ]

        session.add_all(templates)
        await session.commit()

        print(f"✓ 已注入 {len(templates)} 个邮件模板")


if __name__ == "__main__":
    asyncio.run(init_templates())
