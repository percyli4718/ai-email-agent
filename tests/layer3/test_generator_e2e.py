#!/usr/bin/env python3
"""
Layer 3 报价生成器端到端测试

需要 API Key: 约 $0.01-0.05/次测试
预算提示：每次测试约 $0.01-0.05 (Sonnet) 或 $0.05-0.10 (Opus)
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_agent.config import settings
from email_agent.layer3.generator import QuoteGenerator, QuoteGenerationError
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer1.classifier import EmailClassifier


# 模拟的 Layer 2 上下文数据（用于不使用 API Key 的测试）
MOCK_CONTEXT = {
    "similar_emails": {
        "documents": [[
            "Previous quote for Paracetamol 500mg: $2.80/box, 1000 boxes, total $2800",
            "Previous quote for Ibuprofen 400mg: $3.60/box, 500 boxes, total $1800"
        ]]
    },
    "customer_history": {
        "name": "PharmaCom UK",
        "tier": "A",
        "region": "Europe",
        "total_orders": 15,
        "total_revenue": 125000
    },
    "pricing_policy": {
        "policies": [
            {"product": "Paracetamol 500mg", "base_price": 2.80, "discount_rate": 0.05, "currency": "USD"},
            {"product": "Ibuprofen 400mg", "base_price": 3.60, "discount_rate": 0.05, "currency": "USD"}
        ],
        "region": "Europe"
    },
    "compliance": {
        "requirements": [
            {"type": "certification", "name": "CE Marking", "mandatory": True},
            {"type": "certification", "name": "GMP", "mandatory": True}
        ],
        "region": "Europe"
    }
}


async def test_generator_with_mock():
    """使用模拟数据测试报价生成器（不需要 API Key）"""
    print("=" * 60)
    print("Layer 3 报价生成器测试（模拟数据）")
    print("=" * 60)

    generator = QuoteGenerator(settings)

    print("\n测试：生成报价单（模拟上下文）")
    print("-" * 60)

    # 注意：这个测试需要 API Key，如果没有会失败
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠ 未设置 ANTHROPIC_API_KEY，跳过实际生成测试")
        print("  要运行完整测试，请设置环境变量:")
        print("  export ANTHROPIC_API_KEY=your_api_key")
        return False

    try:
        result = await generator.generate_quote(
            email_id="test_l3_001",
            original_email="""
            Dear Supplier,

            We are interested in purchasing:
            - Paracetamol 500mg: 1000 boxes
            - Ibuprofen 400mg: 500 boxes

            Please provide your best quote for delivery to London, UK.

            Best regards,
            PharmaCom UK
            """,
            context=MOCK_CONTEXT
        )

        print(f"\n✓ 报价生成成功")
        print(f"  报价 ID: {result.get('quote_id')}")
        print(f"  总金额：${result.get('total_amount', 'N/A')}")
        print(f"  有效期：{result.get('valid_until', 'N/A')}")
        print(f"  发货港：{result.get('shipping_port', 'N/A')}")
        print(f"  付款条款：{result.get('payment_terms', 'N/A')}")
        print(f"  产品数量：{len(result.get('items', []))} 项")

        return True

    except QuoteGenerationError as e:
        print(f"\n✗ 报价生成失败：{e}")
        return False
    except Exception as e:
        print(f"\n✗ 意外错误：{e}")
        return False


async def test_full_pipeline():
    """测试完整 L1→L2→L3 流程（需要 API Key）"""
    print("\n" + "=" * 60)
    print("完整流程测试：L1 → L2 → L3")
    print("=" * 60)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠ 未设置 ANTHROPIC_API_KEY，跳过完整流程测试")
        return False

    classifier = EmailClassifier(settings)
    retriever = ContextRetriever(settings)
    generator = QuoteGenerator(settings)

    # 测试邮件
    test_email = {
        "id": "test_pipeline_001",
        "subject": "Request for Quote - Paracetamol 500mg",
        "body": """
        Dear Supplier,

        We are interested in purchasing the following products:
        - Paracetamol 500mg: 1000 boxes
        - Ibuprofen 400mg: 500 boxes

        Please provide your best quote for delivery to London, UK.

        Specifications:
        - Paracetamol 500mg: USP/BP standard, blister packing
        - Ibuprofen 400mg: USP/BP standard, bottle of 100 tablets

        We are a leading pharmaceutical distributor in the UK and this is a potential
        long-term partnership. Please provide your competitive quote.

        Best regards,
        John Smith
        PharmaCom UK Ltd.
        john.smith@pharmacom.co.uk
        """
    }

    print("\n步骤 1: Layer 1 分类...")
    try:
        classification = await classifier.classify(
            email_id=test_email["id"],
            subject=test_email["subject"],
            email_body=test_email["body"]
        )
        print(f"  ✓ 分类完成：{classification['type']}, 优先级={classification['priority_score']}")
    except Exception as e:
        print(f"  ✗ 分类失败：{e}")
        return False

    print("\n步骤 2: Layer 2 检索上下文...")
    try:
        context = await retriever.retrieve(
            email_id=test_email["id"],
            email_body=test_email["body"],
            classification=classification
        )
        print(f"  ✓ 检索完成：{len(context['similar_emails'].get('documents', []))} 封相似邮件")
        print(f"  定价政策：{len(context['pricing_policy'].get('policies', []))} 条")
        print(f"  合规要求：{len(context['compliance'].get('requirements', []))} 条")
    except Exception as e:
        print(f"  ✗ 检索失败：{e}")
        return False

    print("\n步骤 3: Layer 3 生成报价...")
    try:
        quote = await generator.generate_quote(
            email_id=test_email["id"],
            original_email=test_email["body"],
            context=context
        )
        print(f"  ✓ 报价生成成功")
        print(f"  报价 ID: {quote.get('quote_id')}")
        print(f"  总金额：${quote.get('total_amount', 'N/A')}")
        print(f"  产品数量：{len(quote.get('items', []))} 项")
    except QuoteGenerationError as e:
        print(f"  ✗ 报价失败：{e}")
        return False
    except Exception as e:
        print(f"  ✗ 意外错误：{e}")
        return False

    print("\n" + "=" * 60)
    print("✓ 完整流程测试通过")
    print("=" * 60)
    return True


async def main():
    """主测试函数"""
    print("\n" + "█" * 60)
    print("█ Layer 3 报价生成器端到端测试")
    print("█" * 60)

    # 检查 API Key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠ 警告：未设置 ANTHROPIC_API_KEY 环境变量")
        print("  部分测试将跳过或失败")
        print("  预算提示：完整测试约 $0.01-0.05")

    # 运行模拟测试
    mock_result = await test_generator_with_mock()

    # 运行完整流程测试
    if os.environ.get("ANTHROPIC_API_KEY"):
        pipeline_result = await test_full_pipeline()
    else:
        pipeline_result = False

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"  模拟数据测试：{'✓ 通过' if mock_result else '✗ 失败/跳过'}")
    print(f"  完整流程测试：{'✓ 通过' if pipeline_result else '✗ 失败/跳过'}")

    return mock_result or pipeline_result


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
