#!/usr/bin/env python3
"""初始化数据库表"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database

async def init():
    db = get_database(settings)
    await db.init_tables()
    print("数据库表初始化完成！")

if __name__ == "__main__":
    asyncio.run(init())
