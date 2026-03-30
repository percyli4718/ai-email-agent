#!/usr/bin/env python3
"""
Layer 2 检索器端到端测试

测试 ContextRetriever 的完整功能，包括：
- 相似邮件搜索
- 客户历史查询
- 定价政策查询
- 合规要求查询
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_agent.config import settings
from email_agent.layer2.retriever import ContextRetriever


async def test_retriever():
    """运行 Layer 2 检索器测试"""
    print("=" * 60)
    print("Layer 2 检索器端到端测试")
    print("=" * 60)

    # 初始化检索器
    retriever = ContextRetriever(settings)
    print("\n✓ ContextRetriever 初始化成功\n")

    # 测试用例 1: 欧洲客户询价
    print("-" * 60)
    print("测试 1: 欧洲客户询价 (Paracetamol + Ibuprofen)")
    print("-" * 60)
    classification = {
        "customer_region": "Europe",
        "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg"]
    }
    result = await retriever.retrieve(
        email_id="test_001",
        email_body="Request for quote: Paracetamol 500mg 1000 boxes, Ibuprofen 400mg 500 boxes",
        classification=classification
    )

    print(f"\n相似邮件搜索：{len(result['similar_emails'].get('documents', []))} 条")
    if result['similar_emails'].get('documents'):
        for i, doc in enumerate(result['similar_emails']['documents'][0][:2]):
            print(f"  [{i+1}] {doc[:80]}...")

    print(f"\n定价政策：{len(result['pricing_policy'].get('policies', []))} 条")
    for policy in result['pricing_policy'].get('policies', []):
        print(f"  - {policy['product']}: ${policy['base_price']:.2f} (折扣：{policy['discount_rate']*100:.0f}%)")

    print(f"\n合规要求：{len(result['compliance'].get('requirements', []))} 条")
    for req in result['compliance'].get('requirements', []):
        mandatory = "强制" if req['mandatory'] else "建议"
        print(f"  - [{mandatory}] {req['type']}: {req['name']}")

    # 测试用例 2: 南美客户询价
    print("\n" + "-" * 60)
    print("测试 2: 南美客户询价 (Amoxicillin)")
    print("-" * 60)
    classification = {
        "customer_region": "South America",
        "products_mentioned": ["Amoxicillin 500mg"]
    }
    result = await retriever.retrieve(
        email_id="test_002",
        email_body="RFQ: Amoxicillin 500mg 5000 boxes to Sao Paulo, Brazil",
        classification=classification
    )

    print(f"\n定价政策：{len(result['pricing_policy'].get('policies', []))} 条")
    for policy in result['pricing_policy'].get('policies', []):
        print(f"  - {policy['product']}: ${policy['base_price']:.2f} ({policy['currency']})")

    print(f"\n合规要求：{len(result['compliance'].get('requirements', []))} 条")
    for req in result['compliance'].get('requirements', []):
        mandatory = "强制" if req['mandatory'] else "建议"
        print(f"  - [{mandatory}] {req['type']}: {req['name']} - {req['description'][:50]}...")

    # 测试用例 3: 亚洲客户询价
    print("\n" + "-" * 60)
    print("测试 3: 亚洲客户询价 (Amoxicillin 250mg)")
    print("-" * 60)
    classification = {
        "customer_region": "Asia",
        "products_mentioned": ["Amoxicillin 250mg"]
    }
    result = await retriever.retrieve(
        email_id="test_003",
        email_body="Inquiry: Amoxicillin 250mg 300 boxes to Taiwan",
        classification=classification
    )

    print(f"\n定价政策：{len(result['pricing_policy'].get('policies', []))} 条")
    for policy in result['pricing_policy'].get('policies', []):
        print(f"  - {policy['product']}: ${policy['base_price']:.2f} (折扣：{policy['discount_rate']*100:.0f}%)")

    print(f"\n合规要求：{len(result['compliance'].get('requirements', []))} 条")
    for req in result['compliance'].get('requirements', []):
        print(f"  - {req['type']}: {req['name']}")

    # 测试用例 4: 中东客户询价
    print("\n" + "-" * 60)
    print("测试 4: 中东客户询价 (Paracetamol)")
    print("-" * 60)
    classification = {
        "customer_region": "Middle East",
        "products_mentioned": ["Paracetamol 500mg"]
    }
    result = await retriever.retrieve(
        email_id="test_004",
        email_body="Partnership inquiry for Paracetamol distribution in UAE",
        classification=classification
    )

    print(f"\n定价政策：{len(result['pricing_policy'].get('policies', []))} 条")
    for policy in result['pricing_policy'].get('policies', []):
        print(f"  - {policy['product']}: ${policy['base_price']:.2f} (默认价格)")

    print(f"\n合规要求：{len(result['compliance'].get('requirements', []))} 条")
    for req in result['compliance'].get('requirements', []):
        print(f"  - {req['type']}: {req['name']} - {req['description'][:50]}...")

    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_retriever())
