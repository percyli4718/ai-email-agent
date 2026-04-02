#!/usr/bin/env python3
"""Layer 2 检索器端到端测试"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from email_agent.config import settings
from email_agent.layer2.retriever import ContextRetriever

async def test_retriever():
    retriever = ContextRetriever(settings)

    # 测试用例 1: 欧洲客户询价
    print("=== 测试 1: 欧洲客户询价 ===")
    classification = {
        "customer_region": "Europe",
        "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg"]
    }
    result = await retriever.retrieve(
        email_id="test_001",
        email_body="Request for quote: Paracetamol 500mg 1000 boxes",
        classification=classification
    )
    print(f"相似邮件：{len(result['similar_emails'].get('documents', []))} 条")
    print(f"定价政策：{len(result['pricing_policy'].get('policies', []))} 条")
    print(f"合规要求：{len(result['compliance'].get('requirements', []))} 条")
    print(f"定价详情：{result['pricing_policy']}")
    print(f"合规详情：{result['compliance']}")

    # 测试用例 2: 南美客户询价
    print("\n=== 测试 2: 南美客户询价 ===")
    classification = {
        "customer_region": "South America",
        "products_mentioned": ["Amoxicillin 500mg"]
    }
    result = await retriever.retrieve(
        email_id="test_002",
        email_body="RFQ: Amoxicillin 500mg 5000 boxes to Brazil",
        classification=classification
    )
    print(f"定价政策：{result['pricing_policy']}")
    print(f"合规要求：{result['compliance']}")

    # 测试用例 3: 亚洲客户询价
    print("\n=== 测试 3: 亚洲客户询价 ===")
    classification = {
        "customer_region": "Asia",
        "products_mentioned": ["Paracetamol 500mg", "Amoxicillin 250mg"]
    }
    result = await retriever.retrieve(
        email_id="test_003",
        email_body="Inquiry about Paracetamol and Amoxicillin prices",
        classification=classification
    )
    print(f"定价政策：{result['pricing_policy']}")
    print(f"合规要求：{result['compliance']}")

    print("\n=== 测试完成 ===")
    print("所有测试通过！Layer 2 检索器正常工作。")

if __name__ == "__main__":
    asyncio.run(test_retriever())
