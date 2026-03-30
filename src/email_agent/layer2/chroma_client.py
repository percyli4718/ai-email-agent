"""
Layer 2: ChromaDB 向量数据库客户端模块

模块作用:
    本模块封装 ChromaDB 向量数据库的操作，提供邮件嵌入的存储和检索功能。
    支持持久化存储，便于历史邮件向量的长期保存和相似性搜索。

使用场景:
    - 将处理过的邮件及其嵌入向量存储到向量数据库
    - 根据查询文本搜索相似的历史邮件 (RAG 检索增强生成)
    - 按元数据 (如区域) 过滤搜索结果

在项目中的位置:
    位于 src/email_agent/layer2/chroma_client.py，
    是 Layer 2 检索模块的底层存储组件，
    被 retriever.py 调用进行相似邮件搜索。
"""
from typing import TYPE_CHECKING, List, Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult

from email_agent.config import Settings
from email_agent.logging_config import get_logger

# TYPE_CHECKING 用于类型检查时导入，避免运行时依赖
if TYPE_CHECKING:
    from chromadb import Collection

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class ChromaClient:
    """
    ChromaDB 向量数据库客户端

    作用:
        封装 ChromaDB 的操作接口，提供邮件嵌入的添加和搜索功能。
        使用懒加载初始化客户端和集合，避免不必要的资源占用。

    使用场景:
        - 存储新处理邮件的嵌入向量
        - 搜索与当前邮件相似的历史邮件
        - 按区域等元数据过滤搜索结果

    主要方法:
        add_email: 添加邮件到向量存储
        search_similar: 搜索相似邮件

    属性:
        settings: Settings 类型，应用配置
        _client: ChromaDB 客户端，懒加载初始化
        _collection: 邮件嵌入集合，懒加载初始化
    """

    def __init__(self, settings: Settings):
        """
        初始化 ChromaDB 客户端

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._client: Optional[ClientAPI] = None
        self._collection: Optional["Collection"] = None

    @property
    def client(self) -> ClientAPI:
        """
        ChromaDB 客户端属性 (懒加载)

        功能描述:
            按需创建 ChromaDB 持久化客户端。
            使用配置中的持久化目录，确保向量数据持久存储。

        参数:
            无

        返回值:
            ClientAPI: ChromaDB 客户端实例

        异常:
            无
        """
        if self._client is None:
            # 首次访问时创建持久化客户端
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir
            )
            logger.info(
                "chromadb_initialized",
                persist_dir=self.settings.chroma_persist_dir
            )
        return self._client

    @property
    def collection(self) -> "Collection":
        """
        邮件嵌入集合属性 (懒加载)

        功能描述:
            获取或创建 email_embeddings 集合。
            集合用于存储历史邮件的嵌入向量和元数据。

        参数:
            无

        返回值:
            Collection: ChromaDB 集合实例

        异常:
            无
        """
        if self._collection is None:
            # 首次访问时获取或创建集合
            self._collection = self.client.get_or_create_collection(
                name="email_embeddings",
                metadata={"description": "Historical email embeddings for RAG"}
            )
            logger.info("chromadb_collection_ready")
        return self._collection

    async def add_email(
        self,
        email_id: str,
        content: str,
        metadata: dict
    ) -> None:
        """
        添加邮件到向量存储

        功能描述:
            将邮件内容及其元数据添加到 ChromaDB 集合中。
            邮件 ID 作为唯一标识符用于后续检索。

        参数:
            email_id: str 类型，邮件唯一标识符
            content: str 类型，邮件文本内容 (用于生成嵌入)
            metadata: dict 类型，邮件元数据
                - region: 客户区域
                - type: 邮件类型
                - timestamp: 时间戳等

        返回值:
            无

        异常:
            无

        使用场景:
            - 邮件处理完成后，将邮件存入向量库供后续检索
            - 批量导入历史邮件数据
        """
        # 将邮件添加到集合中
        # documents: 文档内容列表 (此处仅一封邮件)
        # metadatas: 元数据列表，与 documents 一一对应
        # ids: 文档 ID 列表，必须唯一
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[email_id]
        )
        logger.info(
            "email_added_to_vector_store",
            email_id=email_id,
            metadata=metadata
        )

    async def search_similar(
        self,
        query_text: str,
        n_results: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> QueryResult:
        """
        搜索相似的邮件

        功能描述:
            使用查询文本在向量数据库中搜索最相似的邮件。
            支持通过元数据进行过滤，例如只搜索特定区域的邮件。

        参数:
            query_text: str 类型，查询文本 (用于生成查询嵌入)
            n_results: int 类型，返回结果数量，默认为 3
            filter_metadata: Optional[dict] 类型，过滤条件 (可选)
                例如：{"region": "Brazil"} 只搜索巴西区域的邮件

        返回值:
            QueryResult: 查询结果，包含:
                - documents: 相似邮件内容列表
                - metadatas: 相似邮件元数据列表
                - ids: 相似邮件 ID 列表
                - distances: 距离分数列表

        异常:
            无

        使用场景:
            - 为新邮件查找相似的历史处理案例
            - RAG 检索增强生成，提供上下文参考
        """
        # 使用 ChromaDB 的 query 方法进行相似性搜索
        # query_texts: 查询文本列表 (自动内部生成嵌入)
        # n_results: 返回最相似的 N 个结果
        # where: 元数据过滤条件 (可选)
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )
