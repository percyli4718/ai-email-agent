#!/usr/bin/env python3
"""
真实 RAG 数据注入脚本

将数据库中的邮件注入到 ChromaDB 向量数据库
使用 Ollama nomic-embed-text 模型生成真实的 embedding 向量
"""
import asyncio
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from email_agent.config import settings
from email_agent.storage.database import get_database
from email_agent.storage.models import Email
from sqlalchemy import select
import chromadb


def generate_embedding(text: str) -> list:
    """使用 Ollama 生成 embedding 向量"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://localhost:11434/api/embeddings",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"model": "nomic-embed-text", "prompt": text[:2000]})],
            capture_output=True, text=True, timeout=60
        )
        response = json.loads(result.stdout)
        return response.get("embedding", [])
    except Exception as e:
        print(f"Embedding 生成失败：{e}")
        return []


async def inject_rag_data():
    """注入 RAG 向量数据"""
    print("\n" + "=" * 70)
    print(" " * 20 + "真实 RAG 数据注入脚本")
    print("=" * 70)

    db = get_database(settings)
    await db.init_tables()

    # 初始化 ChromaDB
    chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = chroma_client.get_or_create_collection(
        name="email_embeddings",
        metadata={"hnsw:space": "cosine"}
    )

    # 清空现有数据
    print("\n清空现有向量数据...")
    existing = collection.get()
    if existing['ids']:
        collection.delete(ids=existing['ids'])
    print("  ✓ 向量库已清空")

    # 从数据库获取邮件
    print("\n从数据库加载邮件...")
    async with db.session() as session:
        stmt = select(Email)
        result = await session.execute(stmt)
        emails = result.scalars().all()

    print(f"  找到 {len(emails)} 封邮件")

    # 注入向量数据
    print("\n生成 embedding 并注入向量库...")
    injected_count = 0
    for i, email in enumerate(emails, 1):
        # 构建邮件内容
        content = f"{email.subject}\n{email.body or ''}"
        metadata = {
            "region": email.region or "Unknown",
            "type": "email",
            "from_address": email.from_address,
            "timestamp": email.received_at.isoformat() if email.received_at else datetime.now(timezone.utc).isoformat()
        }

        print(f"  [{i}/{len(emails)}] {email.subject[:50]}...")

        # 生成 embedding
        embedding = generate_embedding(content)
        if not embedding:
            print(f"    ✗ Embedding 生成失败")
            continue

        # 添加到向量库
        collection.add(
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[email.id]
        )
        print(f"    ✓ 注入成功 (embedding dim: {len(embedding)})")
        injected_count += 1

    # 验证数据
    print("\n验证向量库...")
    count = collection.count()
    print(f"  向量库中邮件数量：{count}")

    # 测试检索
    print("\n测试检索功能...")
    test_query = "Request for Quote Paracetamol"
    test_embedding = generate_embedding(test_query)
    if test_embedding:
        results = collection.query(
            query_embeddings=[test_embedding],
            n_results=2
        )
        print(f"  查询：'{test_query}'")
        print(f"  找到 {len(results['ids'][0])} 条相似邮件")
        for i, doc_id in enumerate(results['ids'][0]):
            print(f"    - {doc_id}: {results['metadatas'][0][i].get('region', 'Unknown')}")

    print("\n" + "=" * 70)
    print(f"RAG 数据注入完成！共注入 {injected_count}/{len(emails)} 封邮件")
    print("=" * 70)
    print("\n现在可以访问邮件详情页，点击「检索结果」→「相似邮件」查看真实的 RAG 检索结果")
    print()


if __name__ == "__main__":
    asyncio.run(inject_rag_data())
