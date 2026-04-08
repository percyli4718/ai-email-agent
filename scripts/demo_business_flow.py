#!/usr/bin/env python3
"""
业务流程演示脚本

模拟完整的 AI Email Agent 业务流程，包括：
1. 导入测试邮件
2. Layer 1 分类
3. Layer 2 检索
4. Layer 3 报价生成
5. 审批流程
6. Agent 执行记录
7. Trace 追踪
8. Prompt 进化记录
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
from email_agent.layer1.classifier import EmailClassifier
from sqlalchemy import select


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
        "status": "pending",
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
        "status": "pending",
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
        "status": "pending",
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
        "status": "pending",
        "priority": "high"
    }
]


async def create_test_emails(db):
    """创建测试邮件"""
    print("\n" + "=" * 60)
    print("步骤 1: 创建测试邮件")
    print("=" * 60)

    async with db.session() as session:
        for email_data in TEST_EMAILS:
            email = Email(**email_data)
            session.add(email)
            print(f"  ✓ 创建邮件：{email_data['subject'][:50]}...")
        await session.commit()

    print(f"\n已创建 {len(TEST_EMAILS)} 封测试邮件")
    return [email_data["id"] for email_data in TEST_EMAILS]


async def run_layer1_classification(db, email_ids):
    """执行 Layer 1 分类"""
    print("\n" + "=" * 60)
    print("步骤 2: Layer 1 - 邮件分类")
    print("=" * 60)

    classifier = EmailClassifier(settings)
    classified_count = 0

    async with db.session() as session:
        # 先清理现有的分析数据
        from sqlalchemy import delete
        await session.execute(delete(EmailAnalysis))
        print("  已清理现有分析数据")

        for email_id in email_ids:
            stmt = select(Email).where(Email.id == email_id)
            result = await session.execute(stmt)
            email = result.scalars().first()

            if email:
                print(f"\n  处理邮件：{email.subject}")
                try:
                    # 先更新邮件状态为 pending，避免分类器跳过
                    email.status = "pending"
                    await session.flush()

                    result = await classifier.classify(
                        email_id=email_id,
                        email_body=email.body or email.preview,
                        subject=email.subject
                    )

                    if result:
                        analysis = EmailAnalysis(
                            email_id=email_id,
                            layer1_classification=json.dumps(result)
                        )
                        session.add(analysis)
                        print(f"    ✓ 分类完成：{result.get('type')} - {result.get('suggested_route')}")
                        classified_count += 1
                    else:
                        print(f"    ✗ 分类返回空结果")

                except Exception as e:
                    print(f"    ✗ 分类失败：{e}")

        await session.commit()

    print(f"\nLayer 1 完成：{classified_count}/{len(email_ids)} 邮件已分类")


async def create_agent_execution_records(db):
    """创建 Agent 执行记录"""
    print("\n" + "=" * 60)
    print("步骤 3: 创建 Agent 执行记录")
    print("=" * 60)

    agent_executions = [
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_001",
            "agent_name": "classification_agent",
            "status": "completed",
            "budget_allocated": 0.10,
            "actual_cost": 0.0823,
            "started_at": now() - timedelta(hours=1, minutes=55),
            "completed_at": now() - timedelta(hours=1, minutes=53)
        },
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_001",
            "agent_name": "retrieval_agent",
            "status": "completed",
            "budget_allocated": 0.15,
            "actual_cost": 0.1247,
            "started_at": now() - timedelta(hours=1, minutes=52),
            "completed_at": now() - timedelta(hours=1, minutes=50)
        },
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_001",
            "agent_name": "quote_generation_agent",
            "status": "completed",
            "budget_allocated": 0.20,
            "actual_cost": 0.1856,
            "started_at": now() - timedelta(hours=1, minutes=48),
            "completed_at": now() - timedelta(hours=1, minutes=45)
        },
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_004",
            "agent_name": "classification_agent",
            "status": "completed",
            "budget_allocated": 0.10,
            "actual_cost": 0.0789,
            "started_at": now() - timedelta(hours=11, minutes=30),
            "completed_at": now() - timedelta(hours=11, minutes=28)
        },
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_004",
            "agent_name": "compliance_check_agent",
            "status": "completed",
            "budget_allocated": 0.12,
            "actual_cost": 0.0956,
            "started_at": now() - timedelta(hours=11, minutes=25),
            "completed_at": now() - timedelta(hours=11, minutes=23)
        },
        {
            "task_id": str(uuid.uuid4()),
            "email_id": "email_002",
            "agent_name": "complaint_handler_agent",
            "status": "running",
            "budget_allocated": 0.25,
            "actual_cost": 0.1200,
            "started_at": now() - timedelta(hours=4, minutes=30),
            "completed_at": None
        },
    ]

    async with db.session() as session:
        for exec_data in agent_executions:
            execution = AgentExecution(**exec_data)
            session.add(execution)
            print(f"  ✓ 创建执行记录：{exec_data['agent_name']} - {exec_data['status']}")
        await session.commit()

    print(f"\n已创建 {len(agent_executions)} 条 Agent 执行记录")


async def create_prompt_versions(db):
    """创建 Prompt 进化版本记录"""
    print("\n" + "=" * 60)
    print("步骤 4: 创建 Prompt 版本进化记录")
    print("=" * 60)

    prompt_versions = [
        {
            "name": "classifier_prompt",
            "version": "v1.0.0",
            "layer": "layer1",
            "template": """You are an email classifier for pharmaceutical trade.
Classify the email into one of these categories: inquiry, complaint, question, contract, status_check, other.

Email: {email_body}

Output JSON format:
{
    "type": "<category>",
    "urgency": "<high|medium|low>",
    "suggested_route": "<quote_flow|complaint_flow|auto_reply|manual|status_flow>"
}
""",
            "accuracy_score": 0.85,
            "changes": "Initial version",
            "diff": "N/A"
        },
        {
            "name": "classifier_prompt",
            "version": "v1.1.0",
            "layer": "layer1",
            "template": """You are an expert email classifier for pharmaceutical trade with 10 years experience.
Classify the email into one of these categories: inquiry, complaint, question, contract, status_check, other.

Consider these factors:
- Product mentions (Paracetamol, Ibuprofen, Amoxicillin, etc.)
- Customer region and timezone
- Urgency indicators

Email: {email_body}

Output JSON format:
{
    "type": "<category>",
    "urgency": "<high|medium|low>",
    "priority_score": <0.0-1.0>,
    "suggested_route": "<quote_flow|complaint_flow|auto_reply|manual|status_flow>",
    "products_mentioned": ["<product1>", "<product2>"],
    "customer_region": "<region>"
}
""",
            "accuracy_score": 0.92,
            "changes": "Added product extraction and priority scoring",
            "diff": """+ Added product extraction
+ Added priority_score (0.0-1.0)
+ Enhanced region detection
+ Improved category definitions"""
        },
        {
            "name": "classifier_prompt",
            "version": "v1.2.0",
            "layer": "layer1",
            "template": """You are a world-class email classifier for pharmaceutical trade.

## Classification Categories
- inquiry: Requests for quotes, product information, pricing
- complaint: Quality issues, delivery problems, service complaints
- question: General inquiries, non-urgent questions
- contract: Contract discussions, legal terms, agreements
- status_check: Order status, shipment tracking, delivery updates
- other: Everything else

## Instructions
1. Read the email carefully
2. Identify the PRIMARY intent
3. Assess urgency based on language and context
4. Extract all mentioned products
5. Determine customer region if possible

Email: {email_body}
Subject: {subject}

Output in JSON format.
""",
            "accuracy_score": 0.96,
            "changes": "Structured prompt with clear categories and instructions",
            "diff": """+ Added detailed category definitions
+ Added step-by-step instructions
+ Improved structure and formatting
+ Added subject field for context"""
        },
        {
            "name": "quote_generator_prompt",
            "version": "v1.0.0",
            "layer": "layer3",
            "template": """You are a quote generation assistant.
Generate a professional quote email based on:
- Customer email: {customer_email}
- Products: {products}
- Pricing: {pricing}

Quote format:
- Greeting
- Product list with prices
- Terms and conditions
- Closing
""",
            "accuracy_score": 0.88,
            "changes": "Initial version",
            "diff": "N/A"
        },
        {
            "name": "quote_generator_prompt",
            "version": "v2.0.0",
            "layer": "layer3",
            "template": """You are an expert quote generation specialist for pharmaceutical products.

## Context
- Customer: {customer_name} ({customer_tier})
- Region: {customer_region}
- Email: {customer_email}

## Products Requested
{products_list}

## Pricing Policy
{pricing_policy}

## Compliance Requirements
{compliance_requirements}

## Task
Generate a professional, comprehensive quote email that includes:

1. **Personalized greeting** - Address the customer by name
2. **Product listing** - Clear table with:
   - Product name and specifications
   - Unit price (with currency)
   - Quantity
   - Line total
3. **Order summary** - Subtotal, discounts, shipping, total
4. **Key terms**:
   - Payment terms (based on customer tier)
   - Delivery timeline
   - Validity period
5. **Compliance notes** - Any required certifications or documentation
6. **Call to action** - Next steps for the customer
7. **Professional closing**

Tone: Professional, warm, and confident
Language: Match the customer's email language
""",
            "accuracy_score": 0.94,
            "changes": "Complete rewrite with structured sections and comprehensive guidance",
            "diff": """+ Added structured context section
+ Added pricing policy integration
+ Added compliance requirements
+ Detailed 7-section output format
+ Specified tone and language matching"""
        },
    ]

    async with db.session() as session:
        for pv_data in prompt_versions:
            prompt_version = PromptVersion(**pv_data)
            session.add(prompt_version)
            print(f"  ✓ 创建 Prompt 版本：{pv_data['name']} - {pv_data['version']} (准确率：{pv_data['accuracy_score']})")
        await session.commit()

    print(f"\n已创建 {len(prompt_versions)} 条 Prompt 版本记录")


async def create_approval_requests(db, email_ids):
    """创建审批请求"""
    print("\n" + "=" * 60)
    print("步骤 5: 创建审批请求")
    print("=" * 60)

    approval_requests = [
        {
            "email_id": email_ids[0],
            "request_type": "quote_approval",
            "requester_name": "Quote Generation Agent",
            "requester_email": "agent@ourcompany.com",
            "status": "pending",
            "request_data": json.dumps({
                "quote_amount": 2800.00,
                "products": ["Paracetamol 500mg", "Ibuprofen 400mg"],
                "customer": "john.smith@pharmacom.co.uk",
                "discount": 0.0
            }),
            "created_at": now() - timedelta(hours=1, minutes=40)
        },
        {
            "email_id": email_ids[3],
            "request_type": "quote_approval",
            "requester_name": "Quote Generation Agent",
            "requester_email": "agent@ourcompany.com",
            "status": "pending",
            "request_data": json.dumps({
                "quote_amount": 52000.00,
                "products": ["Amoxicillin 500mg"],
                "customer": "carlos.silva@pharmabrasil.com.br",
                "discount": 0.05
            }),
            "created_at": now() - timedelta(hours=11, minutes=20)
        },
    ]

    async with db.session() as session:
        for approval_data in approval_requests:
            approval = ApprovalRequest(**approval_data)
            session.add(approval)
            print(f"  ✓ 创建审批请求：{approval_data['request_type']} - 金额：${json.loads(approval_data['request_data'])['quote_amount']}")
        await session.commit()

    print(f"\n已创建 {len(approval_requests)} 条审批请求")


async def main():
    """主流程"""
    print("\n" + "=" * 70)
    print(" "*20 + "AI Email Agent - 完整业务流程演示")
    print("=" * 70)

    db = get_database(settings)
    await db.init_tables()

    # 步骤 1: 创建测试邮件
    email_ids = await create_test_emails(db)

    # 步骤 2: Layer 1 分类
    await run_layer1_classification(db, email_ids)

    # 步骤 3: Agent 执行记录
    await create_agent_execution_records(db)

    # 步骤 4: Prompt 版本进化
    await create_prompt_versions(db)

    # 步骤 5: 审批请求
    await create_approval_requests(db, email_ids)

    # 完成
    print("\n" + "=" * 70)
    print(" "*25 + "业务流程演示完成!")
    print("=" * 70)
    print("\n现在可以访问以下页面查看数据:")
    print(f"  1. 📬 收件箱 - 查看 {len(TEST_EMAILS)} 封新邮件")
    print("  2. 🏷️ 分类管理 - 查看 AI 分类结果")
    print("  3. ✅ 审批管理 - 查看待处理审批")
    print("  4. 🤖 Agent 监控 - 查看执行历史和性能指标")
    print("  5. 📊 数据指标 - 查看 Trace 和 Prompt 版本")
    print("  6. 💰 报价管理 - 查看生成的报价")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
