#!/usr/bin/env python3
"""
数据清理脚本

清除所有测试数据，让系统回到初始状态，以便用户可以手动和自动跑完整业务流程
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from sqlalchemy import delete, select
from email_agent.storage.models import (
    Email, EmailAnalysis, Quote, QuoteItem,
    Notification, ApprovalRequest, Customer
)


async def clean_all_data():
    """清除所有测试数据"""
    print("\n" + "=" * 60)
    print("数据清理脚本")
    print("=" * 60)

    db = get_database(settings)
    await db.init_tables()

    async with db.session() as session:
        # 1. 清除所有审批请求
        result = await session.execute(delete(ApprovalRequest))
        approval_count = result.rowcount
        print(f"\n已删除审批请求：{approval_count} 条")

        # 2. 清除所有通知
        result = await session.execute(delete(Notification))
        notification_count = result.rowcount
        print(f"已删除通知：{notification_count} 条")

        # 3. 清除所有报价单项
        result = await session.execute(delete(QuoteItem))
        quote_item_count = result.rowcount
        print(f"已删除报价单项：{quote_item_count} 条")

        # 4. 清除所有报价
        result = await session.execute(delete(Quote))
        quote_count = result.rowcount
        print(f"已删除报价：{quote_count} 条")

        # 5. 清除所有邮件分析记录
        result = await session.execute(delete(EmailAnalysis))
        analysis_count = result.rowcount
        print(f"已删除邮件分析记录：{analysis_count} 条")

        # 6. 清除所有邮件 (保留客户数据)
        result = await session.execute(delete(Email))
        email_count = result.rowcount
        print(f"已删除邮件：{email_count} 条")

        await session.commit()

    print("\n" + "=" * 60)
    print("数据清理完成！系统已回到初始状态")
    print("=" * 60)
    print("\n接下来您可以:")
    print("1. 手动导入新邮件进行测试")
    print("2. 启动自动处理流程跑完整业务")
    print("3. 查看 Agent 监控页面的数据变化")
    print()


if __name__ == "__main__":
    asyncio.run(clean_all_data())
