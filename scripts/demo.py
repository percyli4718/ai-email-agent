#!/usr/bin/env python3
"""
AI Email Agent 演示脚本

用于面试演示，展示完整的 L1→L2→L3 处理流程。

使用方法:
    python scripts/demo.py

需要设置 ANTHROPIC_API_KEY 环境变量。
预算估算：每次演示约 $0.02-0.10
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.layer1.classifier import EmailClassifier
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer3.generator import QuoteGenerator
from email_agent.agents.ceo_agent import CEOAgent
from email_agent.storage.database import get_database
from email_agent.storage.models import Email, Customer


def print_header(text: str, char: str = "="):
    """打印标题"""
    print(f"\n{char * 80}")
    print(f"{text:^80}")
    print(f"{char * 80}\n")


def print_section(text: str):
    """打印小标题"""
    print(f"\n--- {text} ---\n")


async def demo_scenario_1_europe_inquiry():
    """
    场景 1: 欧洲客户标准询价

    演示点:
    - 标准 L1→L2→L3 流程
    - 80% 概率使用 Sonnet (低成本)
    - 欧洲定价政策和合规要求检索
    """
    print_header("场景 1: 欧洲客户标准询价 (Paracetamol 500mg)")

    email_data = {
        "id": f"demo_europe_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "from_email": "john.smith@pharmacom.co.uk",
        "subject": "Request for Quote - Paracetamol 500mg",
        "body": """
Dear Supplier,

We are interested in purchasing the following products:

- Paracetamol 500mg: 1000 boxes
  - Packing: Blister, 10x10 tablets
  - Standard: USP/BP

Please provide your best quote for delivery to London, UK.

We are a leading pharmaceutical distributor in the UK and this is a potential
long-term partnership.

Best regards,
John Smith
Procurement Manager
PharmaCom UK Ltd.
john.smith@pharmacom.co.uk
        """
    }

    db = get_database(settings)
    classifier = EmailClassifier(settings)
    retriever = ContextRetriever(settings)
    generator = QuoteGenerator(settings)

    # 设置测试邮件
    print_section("步骤 1: 设置测试邮件")
    async with db.session() as session:
        customer = Customer(
            name="PharmaCom UK",
            email=email_data["from_email"],
            tier="A",
            region="Europe"
        )
        session.add(customer)
        await session.flush()

        email = Email(
            id=email_data["id"],
            from_address=email_data["from_email"],
            subject=email_data["subject"],
            body=email_data["body"],
            priority="high",
            region="Europe",
            customer_id=customer.id
        )
        session.add(email)
        await session.commit()

    print(f"✓ 邮件已创建：{email.id}")
    print(f"  发件人：{email.from_address}")
    print(f"  主题：{email.subject}")

    # Layer 1: 分类
    print_section("步骤 2: Layer 1 分类 (Claude Sonnet 4)")
    print("正在调用 Anthropic API 进行分类...")

    classification = await classifier.classify(
        email_id=email.id,
        email_body=email.body,
        subject=email.subject
    )

    print(f"✓ 分类完成:")
    print(f"  类型：{classification.type}")
    print(f"  优先级：{classification.priority_score}")
    print(f"  语言：classification.language}")
    print(f"  产品：{classification.products_mentioned}")
    print(f"  区域：{classification.customer_region}")
    print(f"  建议路由：{classification.suggested_route}")

    # Layer 2: 检索
    print_section("步骤 3: Layer 2 检索 (ChromaDB + Ollama + Database)")
    print("正在检索相似邮件、定价政策和合规要求...")

    context = await retriever.retrieve(
        email_id=email.id,
        email_body=email.body,
        classification=classification
    )

    print(f"✓ 检索完成:")
    similar_count = len(context['similar_emails'].get('documents', []))
    policy_count = len(context['pricing_policy'].get('policies', []))
    compliance_count = len(context['compliance'].get('requirements', []))
    print(f"  相似邮件：{similar_count} 封")
    print(f"  定价政策：{policy_count} 条")
    print(f"  合规要求：{compliance_count} 条")

    if context['pricing_policy'].get('policies'):
        print("\n  定价详情:")
        for p in context['pricing_policy']['policies']:
            print(f"    - {p['product']}: ${p['base_price']:.2f} (折扣：{p['discount_rate']*100:.0f}%)")

    if context['compliance'].get('requirements'):
        print("\n  合规要求:")
        for r in context['compliance']['requirements']:
            mandatory = "强制" if r['mandatory'] else "建议"
            print(f"    - [{mandatory}] {r['name']}: {r['description']}")

    # Layer 3: 生成
    print_section("步骤 4: Layer 3 报价生成 (智能路由)")
    print("正在生成报价单...")

    quote = await generator.generate_quote(
        email_id=email.id,
        original_email=email.body,
        context=context
    )

    print(f"✓ 报价生成成功:")
    print(f"  报价 ID: {quote.quote_id}")
    print(f"  总金额：${quote.total_amount:.2f}")
    print(f"  有效期：{quote.valid_until}")
    print(f"  发货港：{quote.shipping_port}")
    print(f"  付款条款：{quote.payment_terms}")

    if quote.items:
        print("\n  报价项目:")
        for item in quote.items:
            print(f"    - {item['product']}: {item['quantity']} boxes @ ${item['unit_price']:.2f}")

    # 查看分析记录
    print_section("步骤 5: 查看数据库分析记录")
    analysis = await db.get_email_analysis(email.id)
    if analysis:
        print(f"✓ 分析记录已保存:")
        print(f"  处理耗时：{analysis.get('processing_time_ms', 0):.2f}ms")
        print(f"  总成本：${analysis.get('cost', 0):.4f}")
        print(f"  使用模型：{analysis.get('model_used', 'N/A')}")

    return True


async def demo_scenario_2_south_america_complex():
    """
    场景 2: 南美客户复杂询价

    演示点:
    - 高复杂度任务可能使用 Opus
    - 特殊合规要求 (ANVISA, Import Permit)
    - 多证书需求
    """
    print_header("场景 2: 南美客户复杂询价 (Amoxicillin 500mg)")

    email_data = {
        "id": f"demo_brazil_{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
        """
    }

    db = get_database(settings)
    classifier = EmailClassifier(settings)
    retriever = ContextRetriever(settings)
    generator = QuoteGenerator(settings)

    # 设置测试邮件
    print_section("步骤 1: 设置测试邮件")
    async with db.session() as session:
        customer = Customer(
            name="Pharma Brazil",
            email=email_data["from_email"],
            tier="A",
            region="South America"
        )
        session.add(customer)
        await session.flush()

        email = Email(
            id=email_data["id"],
            from_address=email_data["from_email"],
            subject=email_data["subject"],
            body=email_data["body"],
            priority="high",
            region="South America",
            customer_id=customer.id
        )
        session.add(email)
        await session.commit()

    print(f"✓ 邮件已创建：{email.id}")

    # Layer 1: 分类
    print_section("步骤 2: Layer 1 分类")
    classification = await classifier.classify(
        email_id=email.id,
        email_body=email.body,
        subject=email.subject
    )

    print(f"✓ 分类完成:")
    print(f"  类型：{classification.type}")
    print(f"  优先级：{classification.priority_score}")
    print(f"  区域：{classification.customer_region}")

    # Layer 2: 检索
    print_section("步骤 3: Layer 2 检索")
    context = await retriever.retrieve(
        email_id=email.id,
        email_body=email.body,
        classification=classification
    )

    print(f"✓ 检索完成:")
    print(f"  定价政策：{len(context['pricing_policy'].get('policies', []))} 条")
    print(f"  合规要求：{len(context['compliance'].get('requirements', []))} 条")

    # 显示南美特殊合规要求
    if context['compliance'].get('requirements'):
        print("\n  巴西合规要求:")
        for r in context['compliance']['requirements']:
            mandatory = "强制" if r['mandatory'] else "建议"
            print(f"    - [{mandatory}] {r['name']}: {r.get('description', 'N/A')}")

    # Layer 3: 生成
    print_section("步骤 4: Layer 3 报价生成")
    quote = await generator.generate_quote(
        email_id=email.id,
        original_email=email.body,
        context=context
    )

    print(f"✓ 报价生成成功:")
    print(f"  总金额：${quote.total_amount:.2f}")
    print(f"  贸易条款：{quote.shipping_terms}")

    return True


async def demo_scenario_3_ceo_agent():
    """
    场景 3: CEO Agent 任务分解

    演示点:
    - 任务依赖图创建
    - 多 Agent 并行执行
    - 预算追踪
    """
    print_header("场景 3: CEO Agent 任务分解与执行")

    ceo = CEOAgent(settings)

    classification = {
        "type": "inquiry",
        "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "customer_region": "Europe",
        "priority_score": 0.8,
        "suggested_route": "quote_flow"
    }

    email_body = """
    Dear Supplier,

    We are interested in purchasing:
    - Paracetamol 500mg: 1000 boxes
    - Ibuprofen 400mg: 500 boxes

    Please provide quote for delivery to London, UK.

    Best regards,
    PharmaCom UK
    """

    # 任务分解
    print_section("步骤 1: 任务分解")
    print("正在分解任务...")

    graph = ceo.decompose_inquiry(email_body, classification)

    print(f"✓ 任务分解成功:")
    print(f"  任务数量：{len(graph.tasks)}")

    print("\n  任务列表:")
    for task_id, task in graph.tasks.items():
        deps = task.dependencies if task.dependencies else "无"
        print(f"    [{task.agent_name}]")
        print(f"      预算：${task.budget:.2f}")
        print(f"      依赖：{deps}")

    # 任务执行
    print_section("步骤 2: 任务执行")
    print("正在并行执行任务...")

    email_id = f"demo_ceo_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    results = await ceo.execute_graph(graph, email_id)

    print(f"✓ 任务执行完成:")
    print(f"  完成的任务：{len(results)}")

    total_cost = 0
    print("\n  执行结果:")
    for task_id, result in results.items():
        task = graph.tasks[task_id]
        cost = result.get("cost", 0)
        total_cost += cost
        print(f"    [{task.agent_name}]")
        print(f"      状态：{task.status}")
        print(f"      预算：${task.budget:.2f}")
        print(f"      实际成本：${cost:.4f}")

    print(f"\n  总成本：${total_cost:.4f}")
    print(f"  总预算：${sum(t.budget for t in graph.tasks.values()):.2f}")

    return True


async def main():
    """主演示函数"""
    print_header("AI Email Agent 演示", char="█")

    # 检查 API Key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠  警告：未设置 ANTHROPIC_API_KEY 环境变量")
        print("  完整演示需要 Anthropic API Key")
        print("  预算估算：每次完整演示约 $0.02-0.10")
        print("\n  要设置 API Key:")
        print("  export ANTHROPIC_API_KEY=your_api_key")
        print("\n  或者运行 CEO Agent 演示 (不需要 API Key):")
        print("  python scripts/demo.py ceo")
        return

    # 初始化 ChromaDB
    print("\n初始化 ChromaDB...")
    from email_agent.retriever.chroma_init import initialize_chromadb
    initialize_chromadb()
    print("✓ ChromaDB 已初始化")

    # 运行演示场景
    try:
        # 场景 1: 欧洲客户
        await demo_scenario_1_europe_inquiry()

        # 场景 2: 南美客户
        await demo_scenario_2_south_america_complex()

        # 场景 3: CEO Agent
        await demo_scenario_3_ceo_agent()

        print_header("演示完成", char="★")
        print("\n✓ 所有演示场景执行成功")
        print("\n  下一步:")
        print("  1. 访问前端界面：http://localhost:5173")
        print("  2. 查看 API 文档：http://localhost:8000/docs")
        print("  3. 查看测试报告：打开 coverage/index.html")

    except Exception as e:
        print(f"\n✗ 演示失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "ceo":
            # 只运行 CEO Agent 演示
            asyncio.run(demo_scenario_3_ceo_agent())
        elif sys.argv[1] == "europe":
            asyncio.run(demo_scenario_1_europe_inquiry())
        elif sys.argv[1] == "brazil":
            asyncio.run(demo_scenario_2_south_america_complex())
        else:
            print(f"未知参数：{sys.argv[1]}")
            print("用法：python scripts/demo.py [ceo|europe|brazil]")
    else:
        asyncio.run(main())
