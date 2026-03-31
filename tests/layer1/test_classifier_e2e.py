#!/usr/bin/env python3
"""
Layer 1 分类器端到端测试

需要 API Key: 约 $0.01/次测试
预算提示：每次测试约 $0.003-0.01
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from email_agent.config import settings
from email_agent.layer1.classifier import EmailClassifier, ClassificationError


async def test_classifier():
    """运行 Layer 1 分类器测试"""
    print("=" * 60)
    print("Layer 1 分类器端到端测试")
    print("=" * 60)

    # 检查 API Key 是否配置
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n错误：请设置 ANTHROPIC_API_KEY 环境变量")
        print("预算提示：每次测试约 $0.003-0.01")
        print("\n要获取 API Key，请访问：https://console.anthropic.com/")
        return False

    classifier = EmailClassifier(settings)

    # 测试用例 1: 询价邮件
    print("\n" + "-" * 60)
    print("测试 1: 询价邮件 (欧洲客户)")
    print("-" * 60)
    try:
        result = await classifier.classify(
            email_id="test_l1_001",
            subject="Request for Quote - Paracetamol 500mg",
            email_body="""
Dear Supplier,

We are interested in purchasing the following products:
- Paracetamol 500mg: 1000 boxes
- Ibuprofen 400mg: 500 boxes

Please provide your best quote for delivery to London, UK.

Best regards,
John Smith
PharmaCom UK
john.smith@pharmacom.co.uk
            """
        )

        print(f"\n✓ 分类成功")
        print(f"  类型：{result['type']}")
        print(f"  优先级：{result['priority_score']}")
        print(f"  紧急程度：{result['urgency']}")
        print(f"  语言：{result['language']}")
        print(f"  产品：{result['products_mentioned']}")
        print(f"  区域：{result['customer_region']}")
        print(f"  需要人工：{result['requires_human']}")
        print(f"  建议路由：{result['suggested_route']}")

    except ClassificationError as e:
        print(f"\n✗ 分类失败：{e}")

    # 测试用例 2: 投诉邮件
    print("\n" + "-" * 60)
    print("测试 2: 投诉邮件 (亚洲客户，紧急)")
    print("-" * 60)
    try:
        result = await classifier.classify(
            email_id="test_l1_002",
            subject="URGENT: Product Quality Issue - Batch #ABC789",
            email_body="""
Dear Supplier,

We regret to inform you that we have encountered a serious issue with Batch #ABC789.

Multiple customers have reported:
1. Packaging damage
2. Unclear expiration dates
3. Potential contamination

This requires immediate attention. Please advise ASAP.

Urgent regards,
David Chen
HealthCare Taiwan
david.chen@healthcare.tw
            """
        )

        print(f"\n✓ 分类成功")
        print(f"  类型：{result['type']}")
        print(f"  优先级：{result['priority_score']}")
        print(f"  紧急程度：{result['urgency']}")
        print(f"  需要人工：{result['requires_human']}")
        print(f"  建议路由：{result['suggested_route']}")

    except ClassificationError as e:
        print(f"\n✗ 分类失败：{e}")

    # 测试用例 3: 订单状态查询
    print("\n" + "-" * 60)
    print("测试 3: 订单状态查询 (欧洲客户)")
    print("-" * 60)
    try:
        result = await classifier.classify(
            email_id="test_l1_003",
            subject="Order Status Inquiry - Shipment #12345",
            email_body="""
Hello,

Could you please provide an update on our order #12345?

The shipment was expected last week but we have not received any tracking information yet.

Thank you,
Maria Garcia
Salud Spain
maria.garcia@salud.es
            """
        )

        print(f"\n✓ 分类成功")
        print(f"  类型：{result['type']}")
        print(f"  优先级：{result['priority_score']}")
        print(f"  建议路由：{result['suggested_route']}")

    except ClassificationError as e:
        print(f"\n✗ 分类失败：{e}")

    # 测试用例 4: 合作伙伴询价 (南美)
    print("\n" + "-" * 60)
    print("测试 4: 大批量询价 (南美客户)")
    print("-" * 60)
    try:
        result = await classifier.classify(
            email_id="test_l1_004",
            subject="RFQ: Amoxicillin 500mg - 5000 boxes to Brazil",
            email_body="""
Good day,

We would like to request a quote for the following:

Product: Amoxicillin 500mg
Quantity: 5000 boxes
Destination: Sao Paulo, Brazil
Required delivery: Within 30 days

We are a large distributor and this is a potential long-term partnership.

Best regards,
Ana Silva
Pharma Brazil
ana.silva@pharma.br
            """
        )

        print(f"\n✓ 分类成功")
        print(f"  类型：{result['type']}")
        print(f"  优先级：{result['priority_score']}")
        print(f"  区域：{result['customer_region']}")
        print(f"  产品：{result['products_mentioned']}")
        print(f"  建议路由：{result['suggested_route']}")

    except ClassificationError as e:
        print(f"\n✗ 分类失败：{e}")

    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_classifier())
    sys.exit(0 if success else 1)
