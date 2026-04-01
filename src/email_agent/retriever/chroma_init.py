"""
ChromaDB 初始化模块

模块作用:
    本模块负责初始化和配置 ChromaDB 向量数据库，提供持久化存储和向量相似度搜索功能。
    用于存储和检索历史邮件的 embedding 向量，支持邮件相似性搜索和上下文检索。

使用场景:
    - 应用启动时初始化 ChromaDB 客户端
    - 创建或获取 email_embeddings 集合
    - 为其他模块提供 ChromaDB 客户端实例

在项目中的位置:
    位于 src/email_agent/retriever/chroma_init.py，属于检索层基础设施。
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.models.Collection import Collection
from chromadb.api import ClientAPI
import os
from pathlib import Path
from src.email_agent.logging_config import get_logger
import subprocess
import numpy as np

logger = get_logger(__name__)

from src.email_agent.config import settings
from typing import List


class CustomOllamaEmbeddingFunction:
    """
    自定义 Ollama Embedding 函数

    作用:
        使用 subprocess 调用 curl 直接访问 Ollama API，绕过 httpx 的代理配置问题。
        实现 ChromaDB embedding function 接口。

    使用场景:
        - 当系统代理配置导致 httpx 无法正常工作时
        - 需要直接使用 Ollama 本地 embedding 服务时
    """

    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/embeddings"

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        生成 embedding 向量

        参数:
            input: 文本字符串列表

        返回值:
            embedding 向量列表，每个向量是 float 列表
        """
        embeddings = []
        for text in input:
            result = subprocess.run(
                [
                    "curl", "-s", "-X", "POST",
                    "http://localhost:11434/api/embeddings",
                    "-H", "Content-Type: application/json",
                    "-d", f'{{"model": "{self.model_name}", "prompt": {repr(text)}}}'
                ],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Ollama API 调用失败：{result.stderr}")

            import json
            response = json.loads(result.stdout)
            embeddings.append(response.get("embedding", []))

        return embeddings


class ChromaDBInitializer:
    """
    ChromaDB 初始化器

    作用:
        负责初始化 ChromaDB 客户端，创建或获取集合，并提供客户端实例。
        使用持久化存储确保数据在应用重启后仍然可用。

    属性:
        client: ChromaDB 客户端实例
        collection: email_embeddings 集合

    使用场景:
        - 应用启动时调用 initialize() 方法初始化 ChromaDB
        - 通过 get_client() 获取客户端实例
        - 通过 get_collection() 获取集合实例
    """

    def __init__(self):
        """
        初始化 ChromaDBInitializer

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        self._client: ClientAPI = None
        self._collection: Collection = None

    def initialize(self) -> None:
        """
        初始化 ChromaDB 客户端和集合

        功能描述:
            1. 从配置中读取持久化目录
            2. 创建持久化目录（如果不存在）
            3. 初始化 ChromaDB 持久化客户端
            4. 创建或获取 email_embeddings 集合

        参数:
            无

        返回值:
            无

        异常:
            无
        """
        # 获取持久化目录
        persist_dir = Path(settings.chroma_persist_dir)

        # 创建持久化目录（如果不存在）
        persist_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ChromaDB 持久化目录：{persist_dir.absolute()}")

        # 初始化 ChromaDB 持久化客户端
        logger.info("正在初始化 ChromaDB 客户端...")
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

        # 创建或获取 email_embeddings 集合
        # 使用余弦相似度作为距离度量
        # 注意：不使用 embedding_function，由调用者手动提供 embedding 向量
        # 这样可以避免 Ollama 客户端库的代理问题
        self._collection = self._client.get_or_create_collection(
            name="email_embeddings",
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"ChromaDB 集合 'email_embeddings' 已创建/获取")
        logger.info(f"集合中当前有 {self._collection.count()} 个文档")

    def get_client(self) -> ClientAPI:
        """
        获取 ChromaDB 客户端实例

        功能描述:
            返回已初始化的 ChromaDB 客户端。
            如果尚未初始化，抛出异常。

        参数:
            无

        返回值:
            ClientAPI: ChromaDB 客户端实例

        异常:
            RuntimeError: 如果尚未调用 initialize() 方法
        """
        if self._client is None:
            raise RuntimeError("ChromaDB 尚未初始化，请先调用 initialize() 方法")
        return self._client

    def get_collection(self) -> Collection:
        """
        获取 email_embeddings 集合

        功能描述:
            返回已创建的 email_embeddings 集合。
            如果尚未初始化，抛出异常。

        参数:
            无

        返回值:
            Collection: email_embeddings 集合实例

        异常:
            RuntimeError: 如果尚未调用 initialize() 方法
        """
        if self._collection is None:
            raise RuntimeError("ChromaDB 尚未初始化，请先调用 initialize() 方法")
        return self._collection

    def is_initialized(self) -> bool:
        """
        检查 ChromaDB 是否已初始化

        功能描述:
            返回 ChromaDB 客户端是否已成功初始化。

        参数:
            无

        返回值:
            bool: 如果已初始化返回 True，否则返回 False

        异常:
            无
        """
        return self._client is not None


# 全局初始化器实例
_initializer: ChromaDBInitializer = None


def initialize_chromadb() -> None:
    """
    初始化 ChromaDB（全局函数）

    功能描述:
        创建全局 ChromaDBInitializer 实例并调用 initialize() 方法。
        此函数应在应用启动时调用。

    参数:
        无

    返回值:
        无

    异常:
        无
    """
    global _initializer
    _initializer = ChromaDBInitializer()
    _initializer.initialize()


def get_chromadb_client() -> ClientAPI:
    """
    获取 ChromaDB 客户端（全局函数）

    功能描述:
        返回已初始化的 ChromaDB 客户端实例。
        如果尚未初始化，抛出异常。

    参数:
        无

    返回值:
        ClientAPI: ChromaDB 客户端实例

    异常:
        RuntimeError: 如果尚未调用 initialize_chromadb() 方法
    """
    if _initializer is None:
        raise RuntimeError("ChromaDB 尚未初始化，请先调用 initialize_chromadb() 方法")
    return _initializer.get_client()


def get_email_embeddings_collection() -> Collection:
    """
    获取 email_embeddings 集合（全局函数）

    功能描述:
        返回已创建的 email_embeddings 集合实例。
        如果尚未初始化，抛出异常。

    参数:
        无

    返回值:
        Collection: email_embeddings 集合实例

    异常:
        RuntimeError: 如果尚未调用 initialize_chromadb() 方法
    """
    if _initializer is None:
        raise RuntimeError("ChromaDB 尚未初始化，请先调用 initialize_chromadb() 方法")
    return _initializer.get_collection()


def is_chromadb_initialized() -> bool:
    """
    检查 ChromaDB 是否已初始化（全局函数）

    功能描述:
        返回 ChromaDB 是否已成功初始化。

    参数:
        无

    返回值:
        bool: 如果已初始化返回 True，否则返回 False

    异常:
        无
    """
    global _initializer
    return _initializer is not None and _initializer.is_initialized()


if __name__ == "__main__":
    # 测试脚本：验证 ChromaDB 初始化是否成功

    import sys
    import logging
    from src.email_agent.logging_config import setup_logging

    # 配置日志
    setup_logging("INFO")

    print("=" * 60)
    print("ChromaDB 初始化测试")
    print("=" * 60)

    # 初始化 ChromaDB
    print("\n1. 初始化 ChromaDB...")
    try:
        initialize_chromadb()
        print("   ChromaDB 初始化成功!")
    except Exception as e:
        print(f"   ChromaDB 初始化失败：{e}")
        sys.exit(1)

    # 获取客户端
    print("\n2. 获取 ChromaDB 客户端...")
    try:
        client = get_chromadb_client()
        print(f"   客户端类型：{type(client).__name__}")
        print("   客户端获取成功!")
    except Exception as e:
        print(f"   客户端获取失败：{e}")
        sys.exit(1)

    # 获取集合
    print("\n3. 获取 email_embeddings 集合...")
    try:
        collection = get_email_embeddings_collection()
        print(f"   集合名称：{collection.name}")
        print(f"   集合元数据：{collection.metadata}")
        print(f"   当前文档数：{collection.count()}")
        print("   集合获取成功!")
    except Exception as e:
        print(f"   集合获取失败：{e}")
        sys.exit(1)

    # 测试添加和查询文档
    print("\n4. 测试添加文档...")
    try:
        collection.add(
            ids=["test-1"],
            embeddings=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadatas=[{"source": "test"}],
            documents=["这是一封测试邮件"]
        )
        print("   测试文档添加成功!")
    except Exception as e:
        print(f"   测试文档添加失败：{e}")
        sys.exit(1)

    print("\n5. 测试查询文档...")
    try:
        result = collection.query(
            query_embeddings=[[0.1, 0.2, 0.3, 0.4, 0.5]],
            n_results=1
        )
        print(f"   查询结果数量：{len(result['ids'][0])}")
        print(f"   查询结果文档：{result['documents'][0]}")
        print("   查询测试成功!")
    except Exception as e:
        print(f"   查询测试失败：{e}")
        sys.exit(1)

    # 清理测试数据
    print("\n6. 清理测试数据...")
    try:
        collection.delete(ids=["test-1"])
        print("   测试数据清理成功!")
    except Exception as e:
        print(f"   测试数据清理失败：{e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("所有测试通过！ChromaDB 工作正常。")
    print("=" * 60)
