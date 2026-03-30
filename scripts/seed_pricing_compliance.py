#!/usr/bin/env python3
"""
定价和合规数据注入脚本

用于将模拟的定价政策和合规要求数据注入到 SQLite 数据库中。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import PricingPolicy, ComplianceRequirement


# 定价数据
PRICING_DATA = [
    {"product_name": "Paracetamol 500mg", "region": "default", "base_price": 2.50, "discount_rate": 0.0},
    {"product_name": "Paracetamol 500mg", "region": "Europe", "base_price": 2.80, "discount_rate": 0.05},
    {"product_name": "Paracetamol 500mg", "region": "Asia", "base_price": 2.20, "discount_rate": 0.08},
    {"product_name": "Paracetamol 1000mg", "region": "default", "base_price": 4.00, "discount_rate": 0.0},
    {"product_name": "Paracetamol 1000mg", "region": "South America", "base_price": 4.50, "discount_rate": 0.03},
    {"product_name": "Ibuprofen 400mg", "region": "default", "base_price": 3.20, "discount_rate": 0.0},
    {"product_name": "Ibuprofen 400mg", "region": "Europe", "base_price": 3.60, "discount_rate": 0.05},
    {"product_name": "Ibuprofen 600mg", "region": "default", "base_price": 5.00, "discount_rate": 0.0},
    {"product_name": "Amoxicillin 250mg", "region": "default", "base_price": 4.80, "discount_rate": 0.0},
    {"product_name": "Amoxicillin 250mg", "region": "Asia", "base_price": 5.20, "discount_rate": 0.05},
    {"product_name": "Amoxicillin 500mg", "region": "default", "base_price": 7.50, "discount_rate": 0.0},
    {"product_name": "Amoxicillin 500mg", "region": "South America", "base_price": 8.00, "discount_rate": 0.02},
]

# 合规数据
COMPLIANCE_DATA = [
    {"region": "Europe", "requirement_type": "certification", "requirement_name": "CE Marking", "description": "CE marking required for pharmaceutical products", "mandatory": True},
    {"region": "Europe", "requirement_type": "certification", "requirement_name": "GMP", "description": "Good Manufacturing Practice certification", "mandatory": True},
    {"region": "Asia", "requirement_type": "license", "requirement_name": "Import License", "description": "Pharmaceutical import license required", "mandatory": True},
    {"region": "Middle East", "requirement_type": "certification", "requirement_name": "GCC Certification", "description": "Gulf Cooperation Council certification", "mandatory": True},
    {"region": "South America", "requirement_type": "certification", "requirement_name": "ANVISA", "description": "Brazilian Health Regulatory Agency certification", "mandatory": True},
    {"region": "South America", "requirement_type": "license", "requirement_name": "Import Permit", "description": "Local health authority import permit", "mandatory": True},
]


async def inject_data():
    """注入定价和合规数据到数据库"""
    print("开始注入定价和合规数据...")

    db = get_database(settings)

    # 初始化数据库表
    await db.init_tables()
    print("数据库表已初始化")

    # 清除现有数据
    print("\n清除现有定价和合规数据...")
    async with db.session() as session:
        from sqlalchemy import delete
        await session.execute(delete(PricingPolicy))
        await session.execute(delete(ComplianceRequirement))
        print("  现有数据已清除")

    # 注入定价数据
    print("\n注入定价数据...")
    async with db.session() as session:
        for pricing in PRICING_DATA:
            policy = PricingPolicy(
                product_name=pricing["product_name"],
                region=pricing["region"],
                base_price=pricing["base_price"],
                discount_rate=pricing["discount_rate"]
            )
            session.add(policy)
        await session.commit()
    print(f"  成功注入 {len(PRICING_DATA)} 条定价记录")

    # 注入合规数据
    print("\n注入合规数据...")
    async with db.session() as session:
        for compliance in COMPLIANCE_DATA:
            req = ComplianceRequirement(
                region=compliance["region"],
                requirement_type=compliance["requirement_type"],
                requirement_name=compliance["requirement_name"],
                description=compliance["description"],
                mandatory=compliance["mandatory"]
            )
            session.add(req)
        await session.commit()
    print(f"  成功注入 {len(COMPLIANCE_DATA)} 条合规记录")

    print("\n数据注入完成！")


if __name__ == "__main__":
    asyncio.run(inject_data())
