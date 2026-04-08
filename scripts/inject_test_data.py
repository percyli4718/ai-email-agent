#!/usr/bin/env python3
"""
简单数据注入脚本

不依赖分类器，直接注入模拟数据到数据库
用于演示前端功能
"""
import asyncio
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import (
    Email, EmailAnalysis, Quote, QuoteItem,
    Notification, ApprovalRequest, Customer,
    AgentExecution, PromptVersion
)
from sqlalchemy import select, delete


def now():
    """获取当前时间（timezone-aware）"""
    return datetime.now(timezone.utc)


# ============================================================================
# 测试数据
# ============================================================================

TEST_EMAILS = [
    {
        "id": "email_001",
        "subject": "Request for Quote - Paracetamol 500mg",
        "from_address": "john.smith@pharmacom.co.uk",
        "body": """Dear Supplier,

We are interested in purchasing the following products:
- Paracetamol 500mg: 1000 boxes
- Ibuprofen 400mg: 500 boxes

Please provide your best quote including:
- Unit price
- Total amount
- Delivery time
- Payment terms

Looking forward to your reply.

Best regards,
John Smith
Procurement Manager
PharmaCom UK Ltd.
Tel: +44-20-1234-5678
""",
        "received_at": now() - timedelta(hours=2),
        "region": "Europe",
        "status": "completed",
        "priority": "high"
    },
    {
        "id": "email_002",
        "subject": "Product Quality Complaint - Batch #ABC789",
        "from_address": "maria.garcia@salud.es",
        "body": """Dear Support Team,

We regret to inform you that we have encountered a quality issue with the following product:

Product: Amoxicillin 500mg
Batch Number: ABC789
Quantity Received: 5000 boxes

Issue Description:
Several tablets show discoloration and unusual odor. This is a serious quality concern.

We request immediate action:
1. Replacement of the defective batch
2. Root cause analysis report
3. Preventive measures

Awaiting your urgent response.

Best regards,
Maria Garcia
Quality Assurance Manager
Salud Pharmaceuticals Spain
""",
        "received_at": now() - timedelta(hours=5),
        "region": "Europe",
        "status": "completed",
        "priority": "high"
    },
    {
        "id": "email_003",
        "subject": "Order Status Inquiry - Shipment #12345",
        "from_address": "david.chen@healthcare.tw",
        "body": """Hello,

Could you please provide an update on our order status?

Order Number: #12345
Order Date: March 15, 2026
Expected Delivery: March 30, 2026

We need to plan our inventory accordingly. Please advise:
- Current production status
- Expected shipment date
- Tracking information (if shipped)

Thank you for your assistance.

Best regards,
David Chen
Supply Chain Director
Healthcare Taiwan Co. Ltd.
""",
        "received_at": now() - timedelta(hours=8),
        "region": "Asia",
        "status": "completed",
        "priority": "medium"
    },
    {
        "id": "email_004",
        "subject": "RFQ: Amoxicillin 500mg - Brazil Market",
        "from_address": "carlos.silva@pharmabrasil.com.br",
        "body": """Greetings!

We are a leading pharmaceutical distributor in Brazil and need a competitive quote for:

Product: Amoxicillin 500mg
Quantity: 10,000 boxes
Packaging: 20 tablets per blister, 50 blisters per carton
Destination: Sao Paulo, Brazil

Please include:
- CIF Santos port pricing
- MOQ (Minimum Order Quantity)
- Lead time from order confirmation
- Required documentation for Brazilian import
- ANVISA certification status

This is a priority project for Q2 2026.

Best regards,
Carlos Silva
Import Director
PharmaBrasil Distribuidora
Tel: +55-11-9876-5432
""",
        "received_at": now() - timedelta(hours=12),
        "region": "South America",
        "status": "completed",
        "priority": "high"
    }
]

CLASSIFICATIONS = {
    "email_001": {
        "type": "inquiry", "priority_score": 0.7, "urgency": "medium",
        "language": "en", "products_mentioned": ["Paracetamol 500mg", "Ibuprofen 400mg"],
        "customer_region": "Europe", "requires_human": False, "suggested_route": "quote_flow"
    },
    "email_002": {
        "type": "complaint", "priority_score": 0.9, "urgency": "high",
        "language": "en", "products_mentioned": ["Amoxicillin 500mg"],
        "customer_region": "Europe", "requires_human": True, "suggested_route": "complaint_flow"
    },
    "email_003": {
        "type": "status_check", "priority_score": 0.5, "urgency": "low",
        "language": "en", "products_mentioned": [],
        "customer_region": "Asia", "requires_human": False, "suggested_route": "status_flow"
    },
    "email_004": {
        "type": "inquiry", "priority_score": 0.8, "urgency": "high",
        "language": "en", "products_mentioned": ["Amoxicillin 500mg"],
        "customer_region": "South America", "requires_human": True, "suggested_route": "quote_flow"
    }
}


async def inject_test_data(db):
    """注入测试数据"""
    print("\n" + "=" * 60)
    print("数据注入脚本")
    print("=" * 60)

    async with db.session() as session:
        # 1. 清理现有数据
        print("\n清理现有数据...")
        await session.execute(delete(EmailAnalysis))
        await session.execute(delete(ApprovalRequest))
        await session.execute(delete(AgentExecution))
        await session.execute(delete(QuoteItem))
        await session.execute(delete(Quote))
        await session.execute(delete(Email))
        await session.commit()
        print("  ✓ 数据已清理")

        # 2. 创建邮件
        print("\n创建测试邮件...")
        for email_data in TEST_EMAILS:
            email = Email(**email_data)
            session.add(email)
            print(f"  ✓ {email_data['subject'][:50]}...")
        await session.commit()

        # 3. 创建分类分析
        print("\n创建分类分析...")
        for email_id, classification in CLASSIFICATIONS.items():
            analysis = EmailAnalysis(
                email_id=email_id,
                layer1_classification=json.dumps(classification),
                processing_time_ms=1500 + uuid.uuid4().int % 3000,
                cost=0.003,
                model_used="qwen-max"
            )
            session.add(analysis)
            print(f"  ✓ {email_id}: {classification['type']} - {classification['suggested_route']}")
        await session.commit()

        # 4. 创建 Agent 执行记录
        print("\n创建 Agent 执行记录...")
        agent_executions = [
            {"task_id": str(uuid.uuid4()), "email_id": "email_001", "agent_name": "classification_agent", "status": "completed", "budget_allocated": 0.10, "actual_cost": 0.0823, "started_at": now() - timedelta(hours=1, minutes=55), "completed_at": now() - timedelta(hours=1, minutes=53)},
            {"task_id": str(uuid.uuid4()), "email_id": "email_001", "agent_name": "retrieval_agent", "status": "completed", "budget_allocated": 0.15, "actual_cost": 0.1247, "started_at": now() - timedelta(hours=1, minutes=52), "completed_at": now() - timedelta(hours=1, minutes=50)},
            {"task_id": str(uuid.uuid4()), "email_id": "email_001", "agent_name": "quote_generation_agent", "status": "completed", "budget_allocated": 0.20, "actual_cost": 0.1856, "started_at": now() - timedelta(hours=1, minutes=48), "completed_at": now() - timedelta(hours=1, minutes=45)},
            {"task_id": str(uuid.uuid4()), "email_id": "email_004", "agent_name": "classification_agent", "status": "completed", "budget_allocated": 0.10, "actual_cost": 0.0789, "started_at": now() - timedelta(hours=11, minutes=30), "completed_at": now() - timedelta(hours=11, minutes=28)},
            {"task_id": str(uuid.uuid4()), "email_id": "email_004", "agent_name": "compliance_check_agent", "status": "completed", "budget_allocated": 0.12, "actual_cost": 0.0956, "started_at": now() - timedelta(hours=11, minutes=25), "completed_at": now() - timedelta(hours=11, minutes=23)},
            {"task_id": str(uuid.uuid4()), "email_id": "email_002", "agent_name": "complaint_handler_agent", "status": "running", "budget_allocated": 0.25, "actual_cost": 0.1200, "started_at": now() - timedelta(hours=4, minutes=30), "completed_at": None},
        ]
        for exec_data in agent_executions:
            execution = AgentExecution(**exec_data)
            session.add(execution)
            print(f"  ✓ {exec_data['agent_name']} - {exec_data['status']}")
        await session.commit()

        # 5. 创建 Prompt 版本
        print("\n创建 Prompt 版本...")
        prompt_versions = [
            {"name": "classifier_prompt", "version": "v1.0.0", "layer": "layer1", "template": "You are an email classifier...", "accuracy_score": 0.85, "changes": "Initial version", "diff": "N/A"},
            {"name": "classifier_prompt", "version": "v1.1.0", "layer": "layer1", "template": "You are an expert classifier...", "accuracy_score": 0.92, "changes": "Added product extraction", "diff": "+ Added product extraction"},
            {"name": "classifier_prompt", "version": "v1.2.0", "layer": "layer1", "template": "You are a world-class classifier...", "accuracy_score": 0.96, "changes": "Structured prompt", "diff": "+ Improved structure"},
            {"name": "quote_generator_prompt", "version": "v1.0.0", "layer": "layer3", "template": "Generate a quote...", "accuracy_score": 0.88, "changes": "Initial version", "diff": "N/A"},
            {"name": "quote_generator_prompt", "version": "v2.0.0", "layer": "layer3", "template": "You are an expert quote generator...", "accuracy_score": 0.94, "changes": "Complete rewrite", "diff": "+ Added structured sections"},
        ]
        for pv_data in prompt_versions:
            prompt_version = PromptVersion(**pv_data)
            session.add(prompt_version)
            print(f"  ✓ {pv_data['name']} - {pv_data['version']} (准确率：{pv_data['accuracy_score']})")
        await session.commit()

        # 6. 创建审批请求
        print("\n创建审批请求...")
        approval_requests = [
            {"email_id": "email_001", "requester": "Quote Agent", "request_type": "high_amount", "amount": 2800.00, "currency": "USD", "reason": "Standard quote approval", "details": {"products": ["Paracetamol 500mg", "Ibuprofen 400mg"], "customer": "john.smith@pharmacom.co.uk", "discount": 0.0}, "status": "pending", "created_at": now() - timedelta(hours=1, minutes=40)},
            {"email_id": "email_004", "requester": "Quote Agent", "request_type": "high_amount", "amount": 52000.00, "currency": "USD", "reason": "High value quote - Brazil market", "details": {"products": ["Amoxicillin 500mg"], "customer": "carlos.silva@pharmabrasil.com.br", "discount": 0.05}, "status": "pending", "created_at": now() - timedelta(hours=11, minutes=20)},
        ]
        for approval_data in approval_requests:
            approval = ApprovalRequest(**approval_data)
            session.add(approval)
            print(f"  ✓ {approval_data['request_type']} - ${approval_data['amount']}")
        await session.commit()

    print("\n" + "=" * 60)
    print("数据注入完成!")
    print("=" * 60)
    print("\n现在可以访问:")
    print("  📬 收件箱 - 4 封邮件")
    print("  🏷️ 分类管理 - 4 条分类结果")
    print("  ✅ 审批管理 - 2 条待处理审批")
    print("  🤖 Agent 监控 - 6 条执行记录")
    print("  📊 数据指标 - 5 个 Prompt 版本")
    print()


async def main():
    db = get_database(settings)
    await db.init_tables()
    await inject_test_data(db)


if __name__ == "__main__":
    asyncio.run(main())
