#!/usr/bin/env python3
"""
LLM Adapter Strategy Pattern Test

测试策略模式 LLM 适配器的工作情况。
支持在 Anthropi, Bailian, Mock 之间切换。
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings, Settings
from email_agent.llm_adapter import get_llm_adapter
from email_agent.layer1.classifier import EmailClassifier
from email_agent.layer3.generator import QuoteGenerator


async def test_adapter_switching():
    """测试适配器切换功能"""
    print("=" * 60)
    print("测试 1: LLM 适配器切换")
    print("=" * 60)

    # 测试 Mock 适配器
    print("\n1.1 测试 Mock 适配器...")
    mock_adapter = get_llm_adapter("mock")
    print(f"    Adapter: {type(mock_adapter).__name__}")
    response = await mock_adapter.chat("Hello")
    print(f"    Response: {response.content[:50]}...")

    # 测试 Anthropic 适配器
    print("\n1.2 测试 Anthropic 适配器...")
    anthropic_adapter = get_llm_adapter("anthropic")
    print(f"    Adapter: {type(anthropic_adapter).__name__}")

    # 测试 Bailian 适配器
    print("\n1.3 测试 Bailian 适配器...")
    bailian_adapter = get_llm_adapter("bailian")
    print(f"    Adapter: {type(bailian_adapter).__name__}")

    print("\n✓ 适配器切换测试完成")


async def test_classifier_with_mock():
    """测试分类器使用 Mock 适配器"""
    print("\n" + "=" * 60)
    print("测试 2: Layer 1 分类器 (Mock 模式)")
    print("=" * 60)

    classifier = EmailClassifier(settings)
    print(f"    LLM Provider: {settings.llm_provider}")
    print(f"    Classifier LLM: {type(classifier.llm).__name__}")

    test_email = """
    Dear Sir/Madam,

    We are interested in purchasing Paracetamol 500mg tablets.
    Please send us your best quote for 1000 boxes CIF Hamburg, Germany.

    We need this information urgently for our pharmaceutical distribution.

    Best regards,
    Hans Mueller
    Euro Pharma GmbH
    """

    print(f"\n    测试邮件：{test_email[:100]}...")

    try:
        result = await classifier.classify(
            email_id="test_001",
            email_body=test_email,
            subject="RFQ: Paracetamol 500mg"
        )
        print(f"\n    分类结果:")
        print(f"    - Type: {result.get('type')}")
        print(f"    - Priority: {result.get('priority_score')}")
        print(f"    - Region: {result.get('customer_region')}")
        print(f"    - Products: {result.get('products_mentioned')}")
        print(f"    - Route: {result.get('suggested_route')}")
        print("\n✓ 分类器测试成功")
    except Exception as e:
        print(f"\n✗ 分类器测试失败：{e}")


async def test_generator_with_mock():
    """测试报价生成器使用 Mock 适配器"""
    print("\n" + "=" * 60)
    print("测试 3: Layer 3 报价生成器 (Mock 模式)")
    print("=" * 60)

    generator = QuoteGenerator(settings)
    print(f"    LLM Provider: {settings.llm_provider}")
    print(f"    Generator LLM: {type(generator.llm).__name__}")

    context = {
        "similar_emails": {"documents": [["Previous quote for Paracetamol"]]},
        "customer_history": {"name": "Euro Pharma", "region": "Europe"},
        "pricing_policy": {"base_price": 2.80, "currency": "USD"},
        "compliance": {"requirements": ["CE Marking"]}
    }

    original_email = "Please quote for Paracetamol 500mg, 1000 boxes"

    try:
        result = await generator.generate_quote(
            email_id="test_001",
            original_email=original_email,
            context=context
        )
        print(f"\n    报价结果:")
        print(f"    - Quote ID: {result.get('quote_id')}")
        print(f"    - Total: ${result.get('total_amount')}")
        print(f"    - Items: {len(result.get('items', []))}")
        print("\n✓ 报价生成器测试成功")
    except Exception as e:
        print(f"\n✗ 报价生成器测试失败：{e}")


async def test_provider_switch():
    """测试环境变量切换 provider"""
    print("\n" + "=" * 60)
    print("测试 4: Provider 切换")
    print("=" * 60)

    providers = ["mock", "anthropic", "bailian"]

    for provider in providers:
        adapter = get_llm_adapter(provider)
        print(f"    Provider '{provider}': {type(adapter).__name__}")

    print("\n✓ Provider 切换测试完成")


async def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("*  LLM Adapter Strategy Pattern Test Suite        *")
    print("*" * 60)

    await test_adapter_switching()
    await test_classifier_with_mock()
    await test_generator_with_mock()
    await test_provider_switch()

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
    print("\n提示:")
    print("  - 修改 .env 中的 LLM_PROVIDER 切换 provider")
    print("  - LLM_PROVIDER=anthropic: 使用 Anthropic Claude")
    print("  - LLM_PROVIDER=bailian: 使用阿里百炼 Qwen")
    print("  - LLM_PROVIDER=mock: Mock 模式 (无需 API Key)")


if __name__ == "__main__":
    asyncio.run(main())
