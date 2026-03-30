"""
Layer 2: Embedding 服务模块

模块作用:
    本模块封装 Ollama embedding 生成服务，使用本地运行的 embedding 模型
    将文本转换为向量表示。支持批量生成 embeddings，用于 ChromaDB 向量存储。

使用场景:
    - 为邮件内容生成 embedding 向量并存入 ChromaDB
    - 为查询文本生成 embedding 用于相似性搜索
    - 批量处理历史邮件数据

在项目中的位置:
    位于 src/email_agent/layer2/embedding_service.py，
    是 Layer 2 检索模块的嵌入生成组件，
    被 retriever.py 调用生成查询嵌入。
"""
from typing import TYPE_CHECKING, List

from email_agent.config import Settings
from email_agent.logging_config import get_logger

# TYPE_CHECKING 用于类型检查时导入，避免运行时循环依赖
if TYPE_CHECKING:
    from ollama import Client

# 获取当前模块的日志记录器
logger = get_logger(__name__)


class EmbeddingService:
    """
    Embedding 生成服务

    作用:
        使用 Ollama 本地服务生成文本嵌入向量。
        支持单机运行，无需外部 API，降低成本。

    使用场景:
        - 为邮件内容生成 embedding 存入向量数据库
        - 为查询文本生成 embedding 进行相似性搜索
        - 批量处理历史邮件数据

    主要方法:
        generate_embedding: 为单个文本生成 embedding
        generate_embeddings: 为多个文本批量生成 embeddings

    属性:
        settings: Settings 类型，应用配置
        _client: Ollama 客户端，懒加载初始化
        model: str 类型，使用的 embedding 模型名称
    """

    def __init__(self, settings: Settings):
        """
        初始化 Embedding 服务

        参数:
            settings: Settings 类型，应用配置对象

        返回值:
            无

        异常:
            无
        """
        self.settings = settings
        self._client = None  # 懒加载客户端，避免初始化时的代理问题
        self.model = "mxb3embed-base"  # 使用 mxb3embed-base 模型

    @property
    def client(self) -> "Client":
        """
        Ollama 客户端属性 (懒加载)

        功能描述:
            按需创建 Ollama 客户端，避免在构造函数中初始化可能导致的代理问题。
            使用配置中的 Ollama 服务地址连接本地服务。

        参数:
            无

        返回值:
            Client: Ollama 客户端实例

        异常:
            无
        """
        if self._client is None:
            # 首次访问时创建 Ollama 客户端
            import ollama
            # 构建 Ollama 服务地址，默认 localhost:11434
            self._client = ollama.Client(host=f"http://{self.settings.ollama_host}")
        return self._client

    async def generate_embedding(self, text: str) -> List[float]:
        """
        为单个文本生成 embedding 向量

        功能描述:
            调用 Ollama API 将文本转换为固定维度的向量表示。
            生成的 embedding 可用于语义相似性比较。

        参数:
            text: str 类型，需要生成 embedding 的文本内容

        返回值:
            List[float]: embedding 向量，浮点数列表

        异常:
            EmbeddingError: 当 embedding 生成失败时抛出

        使用场景:
            - 单封邮件的 embedding 生成
            - 查询文本的 embedding 生成
        """
        try:
            # 调用 Ollama API 生成 embedding
            response = self.client.embeddings(
                model=self.model,  # 使用配置的 embedding 模型
                prompt=text  # 输入文本
            )
            # 从响应中提取 embedding 向量
            return response["embedding"]
        except Exception as e:
            # 记录错误日志并抛出 EmbeddingError
            logger.error("embedding_generation_failed", error=str(e))
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        为多个文本批量生成 embedding 向量

        功能描述:
            遍历文本列表，为每个文本生成 embedding。
            顺序处理，避免并发请求对 Ollama 服务造成压力。

        参数:
            texts: List[str] 类型，需要生成 embedding 的文本列表

        返回值:
            List[List[float]]: embedding 向量列表，每个元素是一个浮点数列表

        异常:
            EmbeddingError: 当任一文本的 embedding 生成失败时抛出

        使用场景:
            - 批量导入历史邮件数据
            - 一次性处理多封邮件
        """
        embeddings = []
        # 遍历文本列表，逐个生成 embedding
        for text in texts:
            # 调用单文本生成方法
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


class EmbeddingError(Exception):
    """
    Embedding 生成错误异常类

    作用:
        当 embedding 生成失败时抛出此异常。
        可能的失败原因包括:
        - Ollama 服务不可用
        - 模型加载失败
        - 输入文本过长或格式错误
        - 网络连接问题

    使用场景:
        - 捕获并处理 embedding 生成失败的情况
        - 向上层调用者传达失败原因
    """
    pass
