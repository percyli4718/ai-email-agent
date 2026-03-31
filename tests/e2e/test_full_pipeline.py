#!/usr/bin/env python3
"""
完整流程端到端测试：L1 → L2 → L3

测试完整的 AI Email Agent 数据处理流程：
1. Layer 1: 邮件分类（Anthropic API）
2. Layer 2: 上下文检索（ChromaDB + Ollama + 数据库）
3. Layer 3: 报价生成（Anthropic API + 智能路由）

需要 API Key: 约 $0.02-0.10/次完整测试
预算提示:
  - Layer 1: ~$0.003/次
  - Layer 3: ~$0.01-0.05/次 (Sonnet) 或 ~$0.05-0.10/次 (Opus)
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_agent.config import settings
from email_agent.layer1.classifier import EmailClassifier, ClassificationError
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer3.generator import QuoteGenerator, QuoteGenerationError
from email_agent.storage.database import get_database
from email_agent.storage.models import Email, Customer


async def setup_test_email(db, email_data):
    """设置测试邮件到数据库"""
    async with db.session() as session:
        from sqlalchemy import select

        # 查找或创建客户
        stmt = select(Customer).where(Customer.email == email_data["from_email"])
        result = await session.execute(stmt)
        customer = result.scalars().first()

        if not customer:
            customer = Customer(
                name=email_data.get("customer_name", "Test Customer"),
                email=email_data["from_email"],
                tier=email_data.get("tier", "B"),
                region=email_data.get("region", "Europe")
            )
            session.add(customer)
            await session.flush()

        # 创建或更新邮件
        stmt = select(Email).where(Email.id == email_data["id"])
        result = await session.execute(stmt)
        email = result.scalars().first()

        if not email:
            email = Email(
                id=email_data["id"],
                from_address=email_data["from_email"],
                subject=email_data["subject"],
                body=email_data["body"],
                priority=email_data.get("priority", "medium"),
                status="pending",
                region=email_data.get("region", "Europe"),
                customer_id=customer.id
            )
            session.add(email)
        else:
            email.status = "pending"
            email.body = email_data["body"]

        await session.commit()
        return email


async def run_full_pipeline(test_email_data):
    """
    运行完整的 L1 → L2 → L3 流程

    参数:
        test_email_data: 测试邮件数据字典

    返回:
        bool: 测试是否通过
    """
    db = get_database(settings)
    classifier = EmailClassifier(settings)
    retriever = ContextRetriever(settings)
    generator = QuoteGenerator(settings)

    # 设置测试邮件
    print("\n步骤 0: 设置测试邮件...")
    email = await setup_test_email(db, test_email_data)
    print(f"  ✓ 邮件已设置：{email.id}")

    # ========== Layer 1: 分类 ==========
    print("\n" + "-" * 60)
    print("Layer 1: 电子邮件分类")
    print("-" * 60)

    try:
        classification = await classifier.classify(
            email_id=email.id,
            subject=email.subject,
            email_body=email.body
        )

        print(f"✓ 分类成功")
        print(f"  类型：{classification.get('type')}")
        print(f"  优先级：{classification.get('priority_score')}")
        print(f"  紧急程度：{classification.get('urgency')}")
        print(f"  语言：{classification.get('language')}")
        print(f"  产品：{classification.get('products_mentioned')}")
        print(f"  区域：{classification.get('customer_region')}")
        print(f"  建议路由：{classification.get('suggested_route')}")

    except ClassificationError as e:
        print(f"✗ 分类失败：{e}")
        return False
    except Exception as e:
        print(f"✗ 意外错误：{e}")
        return False

    # ========== Layer 2: 检索 ==========
    print("\n" + "-" * 60)
    print("Layer 2: 上下文检索")
    print("-" * 60)

    try:
        context = await retriever.retrieve(
            email_id=email.id,
            email_body=email.body,
            classification=classification
        )

        print(f"✓ 检索成功")
        similar_count = len(context['similar_emails'].get('documents', []))
        policy_count = len(context['pricing_policy'].get('policies', []))
        compliance_count = len(context['compliance'].get('requirements', []))
        print(f"  相似邮件：{similar_count} 封")
        print(f"  定价政策：{policy_count} 条")
        print(f"  合规要求：{compliance_count} 条")

        # 打印定价详情
        if context['pricing_policy'].get('policies'):
            print("  定价详情:")
            for p in context['pricing_policy']['policies']:
                print(f"    - {p['product']}: ${p['base_price']:.2f} (折扣：{p['discount_rate']*100:.0f}%)")

        # 打印合规详情
        if context['compliance'].get('requirements'):
            print("  合规要求:")
            for r in context['compliance']['requirements']:
                mandatory = "强制" if r['mandatory'] else "建议"
                print(f"    - [{mandatory}] {r['name']}")

    except Exception as e:
        print(f"✗ 检索失败：{e}")
        return False

    # ========== Layer 3: 生成 ==========
    print("\n" + "-" * 60)
    print("Layer 3: 报价生成")
    print("-" * 60)

    try:
        quote = await generator.generate_quote(
            email_id=email.id,
            original_email=email.body,
            context=context
        )

        print(f"✓ 报价生成成功")
        print(f"  报价 ID: {quote.get('quote_id')}")
        print(f"  客户邮箱：{quote.get('customer_email')}")
        print(f"  总金额：${quote.get('total_amount', 'N/A')}")
        print(f"  有效期：{quote.get('valid_until', 'N/A')}")
        print(f"  发货港：{quote.get('shipping_port', 'N/A')}")
        print(f"  付款条款：{quote.get('payment_terms', 'N/A')}")
        print(f"  产品数量：{len(quote.get('items', []))} 项")

        # 打印报价项目详情
        if quote.get('items'):
            print("  报价项目:")
            for item in quote['items']:
                print(f"    - {item.get('product')}: {item.get('quantity')} boxes @ ${item.get('unit_price', 'N/A')}")

    except QuoteGenerationError as e:
        print(f"✗ 报价失败：{e}")
        return False
    except Exception as e:
        print(f"✗ 意外错误：{e}")
        return False

    # ========== 验证数据库 ==========
    print("\n" + "-" * 60)
    print("验证数据库记录")
    print("-" * 60)

    try:
        analysis = await db.get_email_analysis(email.id)
        if analysis:
            print(f"✓ 分析记录已保存")
            print(f"  Layer 1 分类：{'✓' if analysis.get('layer1_classification') else '✗'}")
            print(f"  Layer 2 检索：{'✓' if analysis.get('layer2_retrieval') else '✗'}")
            print(f"  Layer 3 输出：{'✓' if analysis.get('layer3_output') else '✗'}")
            print(f"  处理耗时：{analysis.get('processing_time_ms', 'N/A'):.2f}ms")
            print(f"  成本：${analysis.get('cost', 'N/A')}")
            print(f"  使用模型：{analysis.get('model_used', 'N/A')}")
        else:
            print(f"✗ 未找到分析记录")
            return False

    except Exception as e:
        print(f"✗ 验证失败：{e}")
        return False

    return True


async def main():
    """主测试函数"""
    print("\n" + "█" * 60)
    print("█ AI Email Agent 完整流程测试 (L1 → L2 → L3)")
    print("█" * 60)

    # 检查 API Key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠ 错误：未设置 ANTHROPIC_API_KEY 环境变量")
        print("  完整流程测试需要 Anthropic API Key")
        print("  预算提示：每次测试约 $0.02-0.10")
        print("\n  要设置 API Key:")
        print("  export ANTHROPIC_API_KEY=your_api_key")
        return False

    # 初始化 ChromaDB
    print("\n初始化 ChromaDB...")
    from email_agent.retriever.chroma_init import initialize_chromadb
    initialize_chromadb()
    print("✓ ChromaDB 已初始化")

    # 测试用例 1: 欧洲客户询价
    print("\n" + "=" * 60)
    print("测试用例 1: 欧洲客户询价 (Paracetamol + Ibuprofen)")
    print("=" * 60)

    test_email_1 = {
        "id": "e2e_test_001",
        "from_email": "john.smith@pharmacom.co.uk",
        "subject": "Request for Quote - Paracetamol 500mg & Ibuprofen 400mg",
        "body": """
Dear Supplier,

We are interested in purchasing the following products:

1. Paracetamol 500mg
   - Quantity: 1000 boxes
   - Packing: Blister, 10x10 tablets
   - Standard: USP/BP

2. Ibuprofen 400mg
   - Quantity: 500 boxes
   - Packing: Bottle, 100 tablets
   - Standard: USP/BP

Please provide your best quote for delivery to London, UK.

We are a leading pharmaceutical distributor in the UK and this is a potential
long-term partnership. Please provide your competitive quote with:
- FOB price
- MOQ
- Lead time
- Payment terms

Best regards,
John Smith
Procurement Manager
PharmaCom UK Ltd.
john.smith@pharmacom.co.uk
+44 20 1234 5678
        """,
        "customer_name": "PharmaCom UK",
        "tier": "A",
        "region": "Europe",
        "priority": "high"
    }

    result1 = await run_full_pipeline(test_email_1)

    # 测试用例 2: 南美客户询价
    print("\n" + "=" * 60)
    print("测试用例 2: 南美客户询价 (Amoxicillin)")
    print("=" * 60)

    test_email_2 = {
        "id": "e2e_test_002",
        "from_email": "ana.silva@pharma.br",
        "subject": "RFQ: Amoxicillin 500mg - 5000 boxes to Brazil",
        "body": """
Good day,

We would like to request a quote for:

Product: Amoxicillin 500mg
Quantity: 5000 boxes
Packing: Blister packing, 10 capsules per blister
Standard: USP/BP/EP
Destination: Sao Paulo, Brazil
Required delivery: Within 30 days

We are a large distributor in Brazil and this is a potential long-term partnership.
Please provide your best CIF Santos price.

Required documents:
- Certificate of Analysis
- GMP Certificate
- Free Sale Certificate
- ANVISA registration

Best regards,
Ana Silva
Director of Procurement
Pharma Brazil Ltda.
ana.silva@pharma.br
+55 11 1234 5678
        """,
        "customer_name": "Pharma Brazil",
        "tier": "A",
        "region": "South America",
        "priority": "high"
    }

    result2 = await run_full_pipeline(test_email_2)

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"  测试用例 1 (欧洲询价): {'✓ 通过' if result1 else '✗ 失败'}")
    print(f"  测试用例 2 (南美询价): {'✓ 通过' if result2 else '✗ 失败'}")
    print(f"\n  总结果：{'✓ 全部通过' if (result1 and result2) else '⚠ 部分失败'}")

    return result1 and result2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
