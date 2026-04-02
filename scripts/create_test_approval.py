#!/usr/bin/env python3
"""创建测试审批请求"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database

async def create():
    db = get_database(settings)

    # 创建测试审批请求
    request = await db.create_approval_request(
        email_id="email_001",
        requester="price_agent",
        request_type="high_amount",
        reason="Quote amount exceeds threshold ($50,000)",
        amount=50000,
        currency="USD",
        details={"quote_id": "QT-001", "threshold": 10000}
    )

    print(f"测试审批请求创建成功：{request}")

    # 创建通知
    notification = await db.create_notification(
        type="approval_request",
        title="新的审批请求 | New Approval Request",
        message="高金额审批待处理 | High amount approval pending",
        level="warning",
        related_id=str(request["id"]),
        extra_data={"email_id": "email_001", "amount": 50000}
    )

    print(f"测试通知创建成功：{notification}")

if __name__ == "__main__":
    asyncio.run(create())
