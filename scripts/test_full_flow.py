#!/usr/bin/env python3
"""
AI Email Agent 全流程测试脚本

测试 Layer 1 -> Layer 2 -> Layer 3 完整流程
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.layer1.classifier import EmailClassifier
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer3.generator import QuoteGenerator
from email_agent.layer1.prompts import CLASSIFIER_PROMPT

async def test_full_flow(email_id: str):
    """测试完整流程"""
    db = get_database(settings)

    print("=" * 60)
    print(f"测试邮件：{email_id}")
    print("=" * 60)

    # 获取邮件详情
    print("\n[1] 获取邮件详情...")
    email = await db.get_email_by_id(email_id)
    if not email:
        print(f"错误：邮件 {email_id} 不存在")
        return
    print(f"  主题：{email['subject']}")
    print(f"  发件人：{email['from_address']}")
    print(f"  区域：{email.get('region', 'Unknown')}")

    # Layer 1: 分类
    print("\n[2] Layer 1: 分类与路由...")
    try:
        classifier = EmailClassifier(settings)
        classification = await classifier.classify(
            email_id=email_id,
            email_body=email.get('body', ''),
            subject=email.get('subject', '')
        )
        print(f"  类型：{classification.get('type', 'Unknown')}")
        print(f"  优先级：{classification.get('priority_score', 0):.2f}")
        print(f"  紧急程度：{classification.get('urgency', 'Unknown')}")
        print(f"  区域：{classification.get('customer_region', 'Unknown')}")
        print(f"  产品：{classification.get('products_mentioned', [])}")
        print(f"  需要人工：{classification.get('requires_human', False)}")
        print(f"  路由：{classification.get('suggested_route', 'Unknown')}")

        # 保存分类结果
        print("\n[2.1] 保存分类结果到数据库...")
        await db.save_email_analysis(
            email_id=email_id,
            layer1_classification=classification,
            layer2_retrieval=None,
            layer3_output=None
        )
        print("  分类结果已保存")

    except Exception as e:
        print(f"  错误：{e}")
        classification = None

    # Layer 2: 检索
    print("\n[3] Layer 2: 向量检索...")
    try:
        retriever = ContextRetriever(settings)
        retrieval_result = await retriever.retrieve(
            email_id=email_id,
            email_body=email.get('body', ''),
            classification=classification or {}
        )

        similar = retrieval_result.get('similar_emails', {})
        print(f"  相似邮件数：{len(similar.get('documents', []))}")
        print(f"  客户历史：{retrieval_result.get('customer_history', {})}")
        print(f"  定价政策：{len(retrieval_result.get('pricing_policy', {}).get('policies', []))} 条")
        print(f"  合规要求：{len(retrieval_result.get('compliance', {}).get('requirements', []))} 条")

        # 保存检索结果
        print("\n[3.1] 保存检索结果到数据库...")
        # 获取已保存的分析
        existing_analysis = await db.get_email_analysis(email_id)
        await db.save_email_analysis(
            email_id=email_id,
            layer1_classification=existing_analysis.get('layer1_classification') if existing_analysis else classification,
            layer2_retrieval={
                "query": "test query",
                "retrieval_time_ms": 100.0,
                "results": similar.get('metadatas', [])
            },
            layer3_output=None
        )
        print("  检索结果已保存")

    except Exception as e:
        print(f"  错误：{e}")
        retrieval_result = None

    # Layer 3: 报价生成
    print("\n[4] Layer 3: 报价生成...")
    try:
        generator = QuoteGenerator(settings)

        # 构建上下文
        context = {}
        if retrieval_result:
            context['pricing_policy'] = retrieval_result.get('pricing_policy', {})
            context['compliance'] = retrieval_result.get('compliance', {})
            context['customer_history'] = retrieval_result.get('customer_history', {})

        quote_result = await generator.generate_quote(
            email_id=email_id,
            original_email=email.get('body', ''),
            context=context
        )

        print(f"  报价 ID: {quote_result.get('quote_id', 'N/A')}")
        print(f"  总金额：${quote_result.get('total_amount', 0):.2f}")
        print(f"  项目数：{len(quote_result.get('items', []))}")
        print(f"  有效期：{quote_result.get('valid_until', 'N/A')}")

    except Exception as e:
        print(f"  错误：{e}")

    print("\n" + "=" * 60)
    print("全流程测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python scripts/test_full_flow.py <email_id>")
        print("例如：python scripts/test_full_flow.py email_20260407204758_8033")
        sys.exit(1)

    email_id = sys.argv[1]
    asyncio.run(test_full_flow(email_id))
