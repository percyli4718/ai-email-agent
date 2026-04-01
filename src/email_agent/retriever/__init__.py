"""
检索器模块

提供向量数据库检索功能，支持邮件相似度搜索和上下文检索。
"""
from src.email_agent.retriever.chroma_init import (
    initialize_chromadb,
    get_chromadb_client,
    get_email_embeddings_collection,
    is_chromadb_initialized,
    ChromaDBInitializer
)

__all__ = [
    "initialize_chromadb",
    "get_chromadb_client",
    "get_email_embeddings_collection",
    "is_chromadb_initialized",
    "ChromaDBInitializer"
]
