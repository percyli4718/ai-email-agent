#!/usr/bin/env python3
"""
AI Email Agent - 全面测试脚本

用于测试所有前端功能和后端 API
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.layer1.classifier import EmailClassifier
from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer3.generator import QuoteGenerator

db = get_database(settings)


async def test_layer1_classification():
    """测试 Layer 1 分类功能"""
    print("\n" + "=" * 60)
    print("测试 Layer 1: 邮件分类")
    print("=" * 60)

    # 获取一封未分类的邮件
    emails, _ = await db.get_all_emails(limit=5)

    for email in emails:
        if email.get("status") == "pending":
            email_id = email["id"]
            email_body = email.get("preview", "")

            print(f"\n处理邮件：{email_id}")
            print(f"主题：{email.get('subject', 'N/A')}")

            try:
                classifier = EmailClassifier(settings)
                result = await classifier.classify(
                    email_id=email_id,
                    email_body=email_body,
                    subject=email.get("subject", "")
                )

                print(f"✓ 分类成功:")
                print(f"  - 类型：{result.get('type')}")
                print(f"  - 优先级：{result.get('priority_score')}")
                print(f"  - 路由：{result.get('suggested_route')}")
                return True

            except Exception as e:
                print(f"✗ 分类失败：{e}")
                return False

    print("没有待处理的邮件")
    return False


async def test_layer2_retrieval():
    """测试 Layer 2 检索功能"""
    print("\n" + "=" * 60)
    print("测试 Layer 2: 向量检索")
    print("=" * 60)

    try:
        retriever = ContextRetriever(settings)

        # 使用测试查询
        query = "Paracetamol price inquiry"
        result = await retriever.retrieve(query, email_id="test_001")

        print(f"✓ 检索成功:")
        print(f"  - 查询：{query}")
        print(f"  - 结果数量：{len(result.get('results', []))}")

        return True

    except Exception as e:
        print(f"✗ 检索失败：{e}")
        return False


async def test_layer3_quote():
    """测试 Layer 3 报价生成功能"""
    print("\n" + "=" * 60)
    print("测试 Layer 3: 报价生成")
    print("=" * 60)

    # 获取一封邮件测试
    emails, _ = await db.get_all_emails(limit=1)

    if not emails:
        print("没有邮件可以测试")
        return False

    email = emails[0]
    email_id = email["id"]

    try:
        generator = QuoteGenerator(settings)

        context = {
            "similar_emails": {"documents": [["Previous quote"]]},
            "customer_history": {"name": "Test Customer"},
            "pricing_policy": {"base_price": 2.80},
            "compliance": {"requirements": []}
        }

        result = await generator.generate_quote(
            email_id=email_id,
            original_email=email.get("subject", ""),
            context=context
        )

        print(f"✓ 报价生成成功:")
        print(f"  - 报价 ID: {result.get('quote_id')}")
        print(f"  - 总金额：${result.get('total_amount')}")

        return True

    except Exception as e:
        print(f"✗ 报价生成失败：{e}")
        return False


async def check_approvals():
    """检查审批数据"""
    print("\n" + "=" * 60)
    print("检查审批数据")
    print("=" * 60)

    try:
        requests = await db.get_approval_requests(limit=10)

        print(f"审批请求总数：{len(requests)}")

        pending = sum(1 for r in requests if r.get("status") == "pending")
        approved = sum(1 for r in requests if r.get("status") == "approved")
        rejected = sum(1 for r in requests if r.get("status") == "rejected")

        print(f"  - 待处理：{pending}")
        print(f"  - 已批准：{approved}")
        print(f"  - 已拒绝：{rejected}")

        return len(requests) > 0

    except Exception as e:
        print(f"✗ 获取审批失败：{e}")
        return False


async def check_classifications():
    """检查分类数据"""
    print("\n" + "=" * 60)
    print("检查分类数据")
    print("=" * 60)

    try:
        from sqlalchemy import select
        from email_agent.storage.models import EmailAnalysis

        async with db.session() as session:
            stmt = select(EmailAnalysis).where(EmailAnalysis.layer1_classification != None)
            result = await session.execute(stmt)
            analyses = result.scalars().all()

        print(f"已分类邮件数：{len(analyses)}")

        return len(analyses) > 0

    except Exception as e:
        print(f"✗ 获取分类数据失败：{e}")
        return False


async def main():
    """主测试函数"""
    print("\n")
    print("*" * 60)
    print("*  AI Email Agent - 全面功能测试                     *")
    print("*" * 60)

    results = {
        "Layer 1 分类": await test_layer1_classification(),
        "Layer 2 检索": await test_layer2_retrieval(),
        "Layer 3 报价": await test_layer3_quote(),
        "审批数据": await check_approvals(),
        "分类数据": await check_classifications(),
    }

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {test}: {status}")

    total_passed = sum(results.values())
    total = len(results)
    print(f"\n总计：{total_passed}/{total} 测试通过")

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
