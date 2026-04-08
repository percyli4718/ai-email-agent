#!/usr/bin/env python3
"""
定价政策数据注入脚本

用于向数据库注入产品定价政策测试数据
支持不同区域的差异化定价
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import PricingPolicy
from sqlalchemy import select, delete


def now():
    """获取当前时间（timezone-aware）"""
    return datetime.now(timezone.utc)


# 定价数据
PRICING_DATA = [
    # Paracetamol 系列
    {"product_name": "Paracetamol 500mg", "region": "default", "base_price": 2.50, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Paracetamol 500mg", "region": "Europe", "base_price": 2.80, "discount_rate": 0.05, "currency": "USD"},
    {"product_name": "Paracetamol 500mg", "region": "Asia", "base_price": 2.20, "discount_rate": 0.08, "currency": "USD"},
    {"product_name": "Paracetamol 500mg", "region": "South America", "base_price": 2.60, "discount_rate": 0.03, "currency": "USD"},

    {"product_name": "Paracetamol 1000mg", "region": "default", "base_price": 4.00, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Paracetamol 1000mg", "region": "South America", "base_price": 4.50, "discount_rate": 0.03, "currency": "USD"},

    # Ibuprofen 系列
    {"product_name": "Ibuprofen 400mg", "region": "default", "base_price": 3.20, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Ibuprofen 400mg", "region": "Europe", "base_price": 3.60, "discount_rate": 0.05, "currency": "USD"},
    {"product_name": "Ibuprofen 400mg", "region": "Asia", "base_price": 2.90, "discount_rate": 0.06, "currency": "USD"},

    {"product_name": "Ibuprofen 600mg", "region": "default", "base_price": 5.00, "discount_rate": 0.0, "currency": "USD"},

    # Amoxicillin 系列
    {"product_name": "Amoxicillin 250mg", "region": "default", "base_price": 4.80, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Amoxicillin 250mg", "region": "Asia", "base_price": 5.20, "discount_rate": 0.05, "currency": "USD"},

    {"product_name": "Amoxicillin 500mg", "region": "default", "base_price": 7.50, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Amoxicillin 500mg", "region": "South America", "base_price": 8.00, "discount_rate": 0.02, "currency": "USD"},
    {"product_name": "Amoxicillin 500mg", "region": "Europe", "base_price": 8.20, "discount_rate": 0.04, "currency": "USD"},

    # Azithromycin 系列
    {"product_name": "Azithromycin 250mg", "region": "default", "base_price": 6.00, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Azithromycin 500mg", "region": "default", "base_price": 9.50, "discount_rate": 0.0, "currency": "USD"},
    {"product_name": "Azithromycin 500mg", "region": "Asia", "base_price": 9.00, "discount_rate": 0.05, "currency": "USD"},
]


async def seed_pricing_data():
    """注入定价政策数据"""
    print("\n" + "=" * 60)
    print("定价政策数据注入脚本")
    print("=" * 60)

    db = get_database(settings)
    await db.init_tables()

    async with db.session() as session:
        # 1. 清理现有定价数据
        print("\n清理现有定价数据...")
        await session.execute(delete(PricingPolicy))
        await session.commit()
        print("  ✓ 现有数据已清理")

        # 2. 注入新数据
        print("\n注入定价政策数据...")
        for pricing in PRICING_DATA:
            policy = PricingPolicy(**pricing)
            session.add(policy)
        await session.commit()

        # 3. 验证数据
        result = await session.execute(select(PricingPolicy))
        policies = result.scalars().all()

    print(f"\n成功注入 {len(PRICING_DATA)} 条定价记录")
    print("\n按区域统计:")
    region_count = {}
    for p in PRICING_DATA:
        region = p['region']
        region_count[region] = region_count.get(region, 0) + 1
    for region, count in sorted(region_count.items()):
        print(f"  - {region}: {count} 条")

    print("\n" + "=" * 60)
    print("数据注入完成!")
    print("=" * 60)
    print("\n现在可以访问邮件详情页，点击「检索结果」查看定价政策")


async def main():
    await seed_pricing_data()


if __name__ == "__main__":
    asyncio.run(main())
