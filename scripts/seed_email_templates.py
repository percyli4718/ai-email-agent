"""
邮件模板数据注入脚本

用于将 12 个邮件模板注入到 SQLite 数据库中，方便测试和演示。
覆盖 4 种类型 × 3-4 个区域的组合。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.storage.database import get_database, Database
from email_agent.storage.models import EmailTemplate
from sqlalchemy import delete, select


# 12 个邮件模板数据
# 覆盖 4 种类型：rfq, inquiry, complaint, status_check
# 覆盖 4 个区域：Europe, South America, Asia, Middle East
TEMPLATES = [
    # ==================== RFQ 类型 (4 个模板) ====================
    {
        "type": "rfq",
        "product_name": "Paracetamol 500mg",
        "region": "Europe",
        "quantity_range": "1000-5000",
        "subject_template": "RFQ: {product} - Quantity {quantity}",
        "body_template": "Dear Supplier,\n\nWe are interested in purchasing {product} with quantity {quantity}.\n\nPlease provide your best quote including:\n1. Unit price\n2. Total amount\n3. Delivery time\n4. Payment terms\n\nCustomer: {customer_name}\nEmail: {email}\n\nLooking forward to your prompt response.\n\nBest regards,\n{customer_name}"
    },
    {
        "type": "rfq",
        "product_name": "Ibuprofen 400mg",
        "region": "South America",
        "quantity_range": "500-1000",
        "subject_template": "Request for Quote: {product} ({quantity} boxes)",
        "body_template": "Dear Partner,\n\nWe would like to request a quote for {product}.\n\nRequired quantity: {quantity} boxes\nDestination: {region}\n\nPlease include:\n- FOB price\n- CIF price\n- Lead time\n- Payment conditions\n\nContact: {customer_name}\nEmail: {email}\n\nThank you.\n\n{customer_name}"
    },
    {
        "type": "rfq",
        "product_name": "Amoxicillin 250mg",
        "region": "Asia",
        "quantity_range": "2000-5000",
        "subject_template": "Inquiry: {product} - Bulk Order {quantity}",
        "body_template": "Dear Sales Team,\n\nWe are looking to purchase {product} in bulk.\n\nQuantity required: {quantity}\nTarget region: {region}\n\nPlease send us your competitive quote with:\n- Product specifications\n- Pricing details\n- Shipping terms\n- Quality certifications\n\nBest regards,\n{customer_name}\n{email}"
    },
    {
        "type": "rfq",
        "product_name": "Metformin 850mg",
        "region": "Middle East",
        "quantity_range": "1000-2000",
        "subject_template": "Purchase Inquiry: {product} - {quantity} units",
        "body_template": "Dear Supplier,\n\nWe represent a pharmaceutical distributor in {region}.\n\nWe need quotation for:\nProduct: {product}\nQuantity: {quantity}\n\nRequirements:\n- GMP certification\n- Proper documentation\n- Competitive pricing\n\nContact person: {customer_name}\nEmail: {email}\n\nWaiting for your reply.\n\nRegards,\n{customer_name}"
    },

    # ==================== Inquiry 类型 (3 个模板) ====================
    {
        "type": "inquiry",
        "product_name": "Vitamin C Tablets",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "Product Inquiry: {product} Availability",
        "body_template": "Dear Team,\n\nWe are interested in learning more about {product}.\n\nCould you please provide:\n- Product availability\n- Minimum order quantity\n- Sample availability\n- Certification documents\n\nEstimated quantity: {quantity}\n\nCompany: {customer_name}\nContact: {email}\n\nThank you for your assistance.\n\nBest regards,\n{customer_name}"
    },
    {
        "type": "inquiry",
        "product_name": "Aspirin 100mg",
        "region": "South America",
        "quantity_range": "1000-2000",
        "subject_template": "General Inquiry - {product}",
        "body_template": "Hello,\n\nWe would like to inquire about {product}.\n\nPlease provide information on:\n- Product specifications\n- Pricing tiers\n- Delivery options to {region}\n- Regulatory requirements\n\nQuantity interest: {quantity}\n\nSender: {customer_name}\nEmail: {email}\n\nLooking forward to hearing from you.\n\nSincerely,\n{customer_name}"
    },
    {
        "type": "inquiry",
        "product_name": "Omeprazole 20mg",
        "region": "Asia",
        "quantity_range": "500-1500",
        "subject_template": "Information Request: {product}",
        "body_template": "Dear Sir/Madam,\n\nWe are exploring suppliers for {product}.\n\nKindly share:\n- Product catalog\n- Price list\n- Quality certifications\n- Export experience\n\nTarget quantity: {quantity}\nRegion: {region}\n\nContact: {customer_name}\n{email}\n\nThank you.\n\n{customer_name}"
    },

    # ==================== Complaint 类型 (2 个模板) ====================
    {
        "type": "complaint",
        "product_name": "Cetirizine 10mg",
        "region": "Europe",
        "quantity_range": "200-500",
        "subject_template": "Quality Complaint: {product} - Batch Issue",
        "body_template": "Dear Quality Team,\n\nWe regret to report an issue with {product}.\n\nProblem details:\n- Packaging damage observed\n- Some tablets crushed\n- Batch number affected: TBD\n\nQuantity affected: {quantity}\nRegion: {region}\n\nWe request immediate investigation and resolution.\n\nReporter: {customer_name}\nEmail: {email}\n\nUrgent response needed.\n\nRegards,\n{customer_name}"
    },
    {
        "type": "complaint",
        "product_name": "Azithromycin 500mg",
        "region": "Asia",
        "quantity_range": "100-300",
        "subject_template": "Product Issue Report: {product}",
        "body_template": "Dear Customer Service,\n\nWe have encountered a problem with {product}.\n\nIssues identified:\n- Expiration date unclear\n- Labeling inconsistencies\n- Storage condition concerns\n\nAffected quantity: {quantity}\nDestination: {region}\n\nPlease investigate and advise on corrective actions.\n\nContact: {customer_name}\n{email}\n\nAwaiting your prompt response.\n\n{customer_name}"
    },

    # ==================== Status Check 类型 (3 个模板) ====================
    {
        "type": "status_check",
        "product_name": "Losartan 50mg",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "Order Status: {product} - Shipment Inquiry",
        "body_template": "Dear Logistics Team,\n\nCould you please provide an update on our order for {product}?\n\nOrder details:\n- Quantity: {quantity}\n- Destination: {region}\n- Expected delivery: TBD\n\nWe have not received shipping confirmation yet.\n\nCustomer: {customer_name}\nEmail: {email}\n\nPlease advise on current status.\n\nThank you,\n{customer_name}"
    },
    {
        "type": "status_check",
        "product_name": "Atorvastatin 20mg",
        "region": "South America",
        "quantity_range": "1000-2000",
        "subject_template": "Shipment Status Inquiry - {product}",
        "body_template": "Dear Partner,\n\nWe are writing to check the status of our {product} order.\n\nDetails:\n- Ordered quantity: {quantity}\n- Shipping to: {region}\n- Order date: TBD\n\nPlease provide:\n- Current order status\n- Expected ship date\n- Tracking information\n\nContact: {customer_name}\n{email}\n\nYour prompt response is appreciated.\n\nBest regards,\n{customer_name}"
    },
    {
        "type": "status_check",
        "product_name": "Amlodipine 5mg",
        "region": "Middle East",
        "quantity_range": "500-1500",
        "subject_template": "Delivery Status: {product} Order",
        "body_template": "Dear Sales Team,\n\nWe would like to inquire about the delivery status of {product}.\n\nOrder information:\n- Product: {product}\n- Quantity: {quantity}\n- Region: {region}\n\nCould you please update us on:\n- Production status\n- Shipping schedule\n- Estimated arrival\n\nSender: {customer_name}\nEmail: {email}\n\nLooking forward to your update.\n\nRegards,\n{customer_name}"
    },
]


async def seed_templates():
    """注入邮件模板数据到数据库"""
    print("=" * 60)
    print("邮件模板数据注入脚本")
    print("=" * 60)
    print()

    db = get_database(settings)

    # 初始化数据库表
    await db.init_tables()

    print("开始注入邮件模板数据...")
    print()

    # [1/3] 清除现有模板数据
    print("[1/3] 清除现有模板数据...")
    async with db.session() as session:
        await session.execute(delete(EmailTemplate))
        print("      现有数据已清除")
    print()

    # [2/3] 注入新模板数据
    print("[2/3] 注入新模板数据...")
    async with db.session() as session:
        for template_data in TEMPLATES:
            template = EmailTemplate(
                type=template_data["type"],
                product_name=template_data["product_name"],
                region=template_data["region"],
                quantity_range=template_data["quantity_range"],
                subject_template=template_data["subject_template"],
                body_template=template_data["body_template"],
                is_active=True
            )
            session.add(template)

        await session.commit()

    print(f"      成功注入 {len(TEMPLATES)} 个邮件模板")
    print()

    # [3/3] 验证注入数据
    print("[3/3] 验证注入数据...")
    async with db.session() as session:
        stmt = select(EmailTemplate)
        result = await session.execute(stmt)
        templates = result.scalars().all()

    print(f"      数据库中共有 {len(templates)} 个模板")

    # 按类型统计
    type_counts = {}
    for t in templates:
        type_counts[t.type] = type_counts.get(t.type, 0) + 1

    print()
    print("      模板分布:")
    for template_type, count in sorted(type_counts.items()):
        print(f"        - {template_type}: {count} 个")

    print()
    print("=" * 60)
    print("模板注入完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_templates())
