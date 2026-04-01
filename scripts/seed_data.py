"""
数据注入脚本

用于将模拟数据注入到 SQLite 数据库中，方便测试和演示。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.storage.database import get_database, Database
from email_agent.storage.models import Customer, Email, EmailAnalysis, AgentExecution
from datetime import datetime, timedelta
import random


# 模拟客户数据
CUSTOMERS = [
    {"name": "PharmaCom UK", "email": "john.smith@pharmacom.co.uk", "tier": "A", "region": "Europe"},
    {"name": "Salud Spain", "email": "maria.garcia@salud.es", "tier": "A", "region": "Europe"},
    {"name": "HealthCare Taiwan", "email": "david.chen@healthcare.tw", "tier": "B", "region": "Asia"},
    {"name": "MedPharm UAE", "email": "ahmed.hassan@medpharm.ae", "tier": "B", "region": "Middle East"},
    {"name": "Pharma Brazil", "email": "ana.silva@pharma.br", "tier": "C", "region": "South America"},
]

# 模拟邮件正文
EMAIL_BODIES = [
    """Dear Supplier,

We are interested in purchasing the following products:
- Paracetamol 500mg: 1000 boxes
- Ibuprofen 400mg: 500 boxes
- Amoxicillin 250mg: 300 boxes

Please provide your best quote including:
1. Unit prices
2. Total amount
3. Delivery time
4. Payment terms

Looking forward to your prompt response.

Best regards,
John Smith
PharmaCom UK""",

    """Dear Team,

Could you please provide an update on our order #12345?
The shipment was expected last week but we have not received any tracking information.

Please advise on the current status and expected delivery date.

Thank you,
Maria Garcia
Salud Spain""",

    """Dear Quality Team,

We regret to inform you that we have encountered an issue with Batch #ABC789.

Several customers have reported:
- Packaging damage
- Expiration date unclear

Please investigate and provide a resolution.

Urgent response required.

David Chen
HealthCare Taiwan""",

    """Dear Partner,

We are a leading pharmaceutical distributor in the Middle East region.

We would like to explore a potential partnership for distributing your products in UAE and surrounding markets.

Our company has:
- 15+ years experience
- Strong distribution network
- Regulatory expertise

Let us schedule a call to discuss further.

Best regards,
Ahmed Hassan
MedPharm UAE""",

    """Good day,

We would like to request a quote for the following:

1. Amoxicillin 500mg - 5000 boxes
2. Paracetamol 1000mg - 3000 boxes
3. Ibuprofen 600mg - 2000 boxes

Destination: Sao Paulo, Brazil
Required certifications: ANVISA

Please include shipping and all applicable fees.

Ana Silva
Pharma Brazil""",
]

# 模拟邮件数据
EMAILS = [
    {
        "id": "email_001",
        "from_email": "john.smith@pharmacom.co.uk",
        "subject": "Request for Quote - Pharmaceutical Products",
        "body": EMAIL_BODIES[0],
        "priority": "high",
        "status": "completed",
        "region": "Europe",
        "received_at": datetime.now() - timedelta(days=5, hours=3)
    },
    {
        "id": "email_002",
        "from_email": "maria.garcia@salud.es",
        "subject": "Order Status Inquiry - Shipment #12345",
        "body": EMAIL_BODIES[1],
        "priority": "medium",
        "status": "processing",
        "region": "Europe",
        "received_at": datetime.now() - timedelta(days=4, hours=8)
    },
    {
        "id": "email_003",
        "from_email": "david.chen@healthcare.tw",
        "subject": "Product Quality Complaint - Batch #ABC789",
        "body": EMAIL_BODIES[2],
        "priority": "high",
        "status": "pending",
        "region": "Asia",
        "received_at": datetime.now() - timedelta(days=3, hours=2)
    },
    {
        "id": "email_004",
        "from_email": "ahmed.hassan@medpharm.ae",
        "subject": "New Partnership Opportunity",
        "body": EMAIL_BODIES[3],
        "priority": "low",
        "status": "pending",
        "region": "Middle East",
        "received_at": datetime.now() - timedelta(days=2, hours=12)
    },
    {
        "id": "email_005",
        "from_email": "ana.silva@pharma.br",
        "subject": "RFQ: Antibiotics and Painkillers",
        "body": EMAIL_BODIES[4],
        "priority": "high",
        "status": "completed",
        "region": "South America",
        "received_at": datetime.now() - timedelta(days=1, hours=6)
    },
]


async def inject_data():
    """注入模拟数据到数据库"""
    print("开始注入数据...")

    db = get_database(settings)

    # 初始化数据库表
    await db.init_tables()
    print("数据库表已初始化")

    # 清除现有数据（避免 UNIQUE 约束冲突）
    print("\n清除现有数据...")
    async with db.session() as session:
        from sqlalchemy import delete
        # 先删除 EmailAnalysis（外键依赖 Email）
        await session.execute(delete(EmailAnalysis))
        # 再删除所有 Email
        await session.execute(delete(Email))
        # 删除所有 Customer
        await session.execute(delete(Customer))
        print("  现有数据已清除")

    # 注入客户数据
    print("\n注入客户数据...")
    for customer_data in CUSTOMERS:
        customer = await db.create_customer(
            name=customer_data["name"],
            email=customer_data["email"],
            tier=customer_data["tier"],
            region=customer_data["region"]
        )
        print(f"  - 客户：{customer.name} ({customer.email})")

    # 注入邮件数据
    print("\n注入邮件数据...")
    async with db.session() as session:
        for email_data in EMAILS:
            # 查找对应的客户
            from sqlalchemy import select
            stmt = select(Customer).where(Customer.email == email_data["from_email"])
            result = await session.execute(stmt)
            customer = result.scalars().first()

            if customer:
                email = Email(
                    id=email_data["id"],
                    from_address=email_data["from_email"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    priority=email_data["priority"],
                    status=email_data["status"],
                    region=email_data["region"],
                    received_at=email_data["received_at"],
                    customer_id=customer.id
                )
                session.add(email)
                print(f"  - 邮件：{email_data['subject']}")

        # 提交事务
        await session.commit()

    print(f"\n成功注入 {len(EMAILS)} 封邮件")

    # 验证数据
    print("\n验证数据...")
    all_emails = await db.get_all_emails()
    print(f"数据库中共有 {len(all_emails)} 封邮件")

    print("\n数据注入完成！")


if __name__ == "__main__":
    asyncio.run(inject_data())
