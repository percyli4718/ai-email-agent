#!/usr/bin/env python3
"""创建测试通知"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database

async def create():
    db = get_database(settings)

    # 创建测试通知
    notification = await db.create_notification(
        type="system",
        title="测试通知 | Test Notification",
        message="通知系统工作正常！Notification system is working correctly!",
        level="success",
        related_id="test_001"
    )

    print(f"测试通知创建成功：{notification}")

if __name__ == "__main__":
    asyncio.run(create())
