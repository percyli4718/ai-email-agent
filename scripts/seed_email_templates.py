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
        "subject_template": "报价请求：{product} - 数量 {quantity}",
        "body_template": "尊敬的供应商：\n\n我们希望采购 {product}，数量为 {quantity}。\n\n请提供最佳报价，包括：\n1. 单价\n2. 总金额\n3. 交货时间\n4. 付款条款\n\n客户：{customer_name}\n邮箱：{email}\n\n期待您的回复。\n\n此致，\n{customer_name}"
    },
    {
        "type": "rfq",
        "product_name": "Ibuprofen 400mg",
        "region": "South America",
        "quantity_range": "500-1000",
        "subject_template": "询价请求：{product}（{quantity} 盒）",
        "body_template": "尊敬的合作伙伴：\n\n我们希望就 {product} 获取报价。\n\n需求数量：{quantity} 盒\n目的地：{region}\n\n请提供：\n- FOB 价格\n- CIF 价格\n- 交货周期\n- 付款条件\n\n联系人：{customer_name}\n邮箱：{email}\n\n谢谢。\n\n{customer_name}"
    },
    {
        "type": "rfq",
        "product_name": "Amoxicillin 250mg",
        "region": "Asia",
        "quantity_range": "2000-5000",
        "subject_template": "采购咨询：{product} - 批量订单 {quantity}",
        "body_template": "尊敬的销售团队：\n\n我们希望批量采购 {product}。\n\n需求数量：{quantity}\n目标区域：{region}\n\n请发送具有竞争力的报价，包括：\n- 产品规格\n- 价格详情\n- 运输条款\n- 质量认证\n\n此致，\n{customer_name}\n{email}"
    },
    {
        "type": "rfq",
        "product_name": "Metformin 850mg",
        "region": "Middle East",
        "quantity_range": "1000-2000",
        "subject_template": "采购咨询：{product} - {quantity} 单位",
        "body_template": "尊敬的供应商：\n\n我们代表 {region} 的一家医药分销商。\n\n我们需要以下产品的报价：\n产品：{product}\n数量：{quantity}\n\n要求：\n- GMP 认证\n- 完整的文件\n- 有竞争力的价格\n\n联系人：{customer_name}\n邮箱：{email}\n\n等待您的回复。\n\n此致，\n{customer_name}"
    },

    # ==================== Inquiry 类型 (3 个模板) ====================
    {
        "type": "inquiry",
        "product_name": "Vitamin C Tablets",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "产品咨询：{product} 供应信息",
        "body_template": "尊敬的团队：\n\n我们对 {product} 感兴趣。\n\n请提供以下信息：\n- 产品供应情况\n- 最小起订量\n- 样品提供\n- 认证文件\n\n预估数量：{quantity}\n\n公司：{customer_name}\n联系人：{email}\n\n感谢您的协助。\n\n此致，\n{customer_name}"
    },
    {
        "type": "inquiry",
        "product_name": "Aspirin 100mg",
        "region": "South America",
        "quantity_range": "1000-2000",
        "subject_template": "一般咨询 - {product}",
        "body_template": "您好，\n\n我们希望了解 {product} 的相关信息。\n\n请提供：\n- 产品规格\n- 价格层级\n- 到 {region} 的配送方案\n- 监管要求\n\n意向数量：{quantity}\n\n发件人：{customer_name}\n邮箱：{email}\n\n期待您的回复。\n\n诚挚的问候，\n{customer_name}"
    },
    {
        "type": "inquiry",
        "product_name": "Omeprazole 20mg",
        "region": "Asia",
        "quantity_range": "500-1500",
        "subject_template": "信息咨询：{product}",
        "body_template": "尊敬的女士/先生：\n\n我们正在寻找 {product} 的供应商。\n\n请分享：\n- 产品目录\n- 价格表\n- 质量认证\n- 出口经验\n\n目标数量：{quantity}\n区域：{region}\n\n联系人：{customer_name}\n{email}\n\n谢谢。\n\n{customer_name}"
    },

    # ==================== Complaint 类型 (2 个模板) ====================
    {
        "type": "complaint",
        "product_name": "Cetirizine 10mg",
        "region": "Europe",
        "quantity_range": "200-500",
        "subject_template": "质量投诉：{product} - 批次问题",
        "body_template": "尊敬的质量团队：\n\n很遗憾报告 {product} 出现问题。\n\n问题详情：\n- 包装破损\n- 部分药片破碎\n- 受影响批次：待定\n\n受影响数量：{quantity}\n区域：{region}\n\n我们要求立即调查并解决。\n\n报告人：{customer_name}\n邮箱：{email}\n\n需要紧急回复。\n\n此致，\n{customer_name}"
    },
    {
        "type": "complaint",
        "product_name": "Azithromycin 500mg",
        "region": "Asia",
        "quantity_range": "100-300",
        "subject_template": "产品问题报告：{product}",
        "body_template": "尊敬的客户服务团队：\n\n我们在使用 {product} 时遇到了问题。\n\n发现的问题：\n- 有效期不清晰\n- 标签不一致\n- 存储条件问题\n\n受影响数量：{quantity}\n目的地：{region}\n\n请调查并告知纠正措施。\n\n联系人：{customer_name}\n{email}\n\n等待您的回复。\n\n{customer_name}"
    },

    # ==================== Status Check 类型 (3 个模板) ====================
    {
        "type": "status_check",
        "product_name": "Losartan 50mg",
        "region": "Europe",
        "quantity_range": "500-1000",
        "subject_template": "订单状态：{product} - 运输咨询",
        "body_template": "尊敬的物流团队：\n\n请提供我们 {product} 订单的最新状态。\n\n订单详情：\n- 数量：{quantity}\n- 目的地：{region}\n- 预计交货：待定\n\n我们尚未收到发货确认。\n\n客户：{customer_name}\n邮箱：{email}\n\n请告知当前状态。\n\n谢谢，\n{customer_name}"
    },
    {
        "type": "status_check",
        "product_name": "Atorvastatin 20mg",
        "region": "South America",
        "quantity_range": "1000-2000",
        "subject_template": "运输状态咨询 - {product}",
        "body_template": "尊敬的合作伙伴：\n\n我们写信咨询 {product} 订单的状态。\n\n详情：\n- 订购数量：{quantity}\n- 运输至：{region}\n- 订购日期：待定\n\n请提供：\n- 当前订单状态\n- 预计发货日期\n- 追踪信息\n\n联系人：{customer_name}\n{email}\n\n感谢您的及时回复。\n\n此致，\n{customer_name}"
    },
    {
        "type": "status_check",
        "product_name": "Amlodipine 5mg",
        "region": "Middle East",
        "quantity_range": "500-1500",
        "subject_template": "交货状态：{product} 订单",
        "body_template": "尊敬的销售团队：\n\n我们希望了解 {product} 的交货状态。\n\n订单信息：\n- 产品：{product}\n- 数量：{quantity}\n- 区域：{region}\n\n请更新以下信息：\n- 生产状态\n- 运输计划\n- 预计到达时间\n\n发件人：{customer_name}\n邮箱：{email}\n\n期待您的更新。\n\n此致，\n{customer_name}"
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
