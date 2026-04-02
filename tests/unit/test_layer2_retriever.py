"""
Layer 2 检索器单元测试

测试模块:
- src/email_agent/layer2/retriever.py - ContextRetriever 类
- src/email_agent/layer2/chroma_client.py - ChromaClient 类
- src/email_agent/layer2/embedding_service.py - EmbeddingService 类

覆盖范围:
- ContextRetriever 完整上下文检索
- ChromaClient 向量数据库操作
- EmbeddingService 嵌入生成服务
- 所有私有方法和边界情况
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from email_agent.layer2.retriever import ContextRetriever
from email_agent.layer2.chroma_client import ChromaClient, _generate_embedding_with_ollama
from email_agent.layer2.embedding_service import EmbeddingService, EmbeddingError
from email_agent.config import Settings


# ============================================================================
# ContextRetriever 测试
# ============================================================================

class TestContextRetriever:
    """ContextRetriever 检索器测试"""

    @pytest.fixture
    def settings(self):
        """创建设置对象"""
        settings = Settings()
        settings.anthropic_api_key = "test-key"
        settings.database_url = "sqlite+aiosqlite:///./test.db"
        settings.chroma_persist_dir = "./test_chroma"
        settings.ollama_host = "localhost:11434"
        return settings

    @pytest.fixture
    def retriever(self, settings):
        """创建检索器实例"""
        return ContextRetriever(settings)

    def test_init(self, settings):
        """测试检索器初始化"""
        retriever = ContextRetriever(settings)

        assert retriever.settings == settings
        assert isinstance(retriever.chroma_client, ChromaClient)
        assert isinstance(retriever.embedding_service, EmbeddingService)
        assert retriever.db is not None

    @pytest.mark.asyncio
    async def test_retrieve_returns_all_context(self, retriever):
        """测试检索器返回完整上下文"""
        mock_similar_emails = {
            "documents": [["Previous email content"]],
            "metadatas": [[{"email_id": "123", "type": "inquiry"}]]
        }

        mock_customer = {"name": "Test Customer", "tier": "B", "region": "brazil"}
        mock_pricing = {"policies": [{"product": "Paracetamol", "base_price": 2.0}], "region": "brazil"}
        mock_compliance = {"requirements": [{"type": "ANVISA", "mandatory": True}], "region": "brazil"}

        with patch.object(retriever.chroma_client, 'search_similar', return_value=mock_similar_emails):
            with patch.object(retriever.db, 'query_customer', return_value=mock_customer):
                with patch.object(retriever.db, 'query_pricing_policy', return_value=mock_pricing):
                    with patch.object(retriever.db, 'query_compliance_requirements', return_value=mock_compliance):

                        result = await retriever.retrieve(
                            email_id="test-123",
                            email_body="We want to order Paracetamol",
                            classification={
                                "type": "inquiry",
                                "customer_region": "brazil",
                                "products_mentioned": ["Paracetamol"]
                            }
                        )

                        assert "similar_emails" in result
                        assert "customer_history" in result
                        assert "pricing_policy" in result
                        assert "compliance" in result
                        assert result["customer_history"] == mock_customer
                        assert result["pricing_policy"] == mock_pricing

    @pytest.mark.asyncio
    async def test_retrieve_with_empty_products(self, retriever):
        """测试检索器 - 产品列表为空"""
        mock_similar_emails = {"documents": [[]], "metadatas": [[]]}

        with patch.object(retriever.chroma_client, 'search_similar', return_value=mock_similar_emails):
            with patch.object(retriever.db, 'query_customer', return_value=None):
                with patch.object(retriever.db, 'query_pricing_policy', return_value={"policies": [], "region": "eu"}):
                    with patch.object(retriever.db, 'query_compliance_requirements', return_value={"requirements": [], "region": "eu"}):

                        result = await retriever.retrieve(
                            email_id="test-456",
                            email_body="General inquiry",
                            classification={
                                "type": "inquiry",
                                "customer_region": "eu",
                                "products_mentioned": []
                            }
                        )

                        assert result["pricing_policy"]["policies"] == []
                        assert result["compliance"]["requirements"] == []

    @pytest.mark.asyncio
    async def test_retrieve_without_region(self, retriever):
        """测试检索器 - 没有指定区域"""
        mock_similar_emails = {"documents": [[]], "metadatas": [[]]}

        with patch.object(retriever.chroma_client, 'search_similar', return_value=mock_similar_emails):
            with patch.object(retriever.db, 'query_customer', return_value=None):
                with patch.object(retriever.db, 'query_pricing_policy', return_value={"policies": [], "region": None}):
                    with patch.object(retriever.db, 'query_compliance_requirements', return_value={"requirements": [], "region": None}):

                        result = await retriever.retrieve(
                            email_id="test-789",
                            email_body="Inquiry without region",
                            classification={
                                "type": "inquiry",
                                "customer_region": None,
                                "products_mentioned": []
                            }
                        )

                        assert result["pricing_policy"]["region"] is None

    @pytest.mark.asyncio
    async def test_search_similar_emails(self, retriever):
        """测试搜索相似邮件方法"""
        mock_result = {
            "documents": [["Similar email 1", "Similar email 2"]],
            "metadatas": [[{"region": "brazil"}, {"region": "brazil"}]],
            "ids": [["email-1", "email-2"]]
        }

        with patch.object(retriever.chroma_client, 'search_similar', return_value=mock_result) as mock_search:
            result = await retriever._search_similar_emails(
                email_body="Test email content",
                region="brazil"
            )

            mock_search.assert_called_once_with(
                query_text="Test email content",
                n_results=3,
                filter_metadata={"region": "brazil"}
            )
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_search_similar_emails_without_region(self, retriever):
        """测试搜索相似邮件 - 不指定区域"""
        with patch.object(retriever.chroma_client, 'search_similar', return_value={"documents": [[]]}) as mock_search:
            await retriever._search_similar_emails(
                email_body="Test content",
                region=None
            )

            # 验证 filter_metadata 为 None
            mock_search.assert_called_once_with(
                query_text="Test content",
                n_results=3,
                filter_metadata=None
            )

    @pytest.mark.asyncio
    async def test_search_similar_emails_truncates_body(self, retriever):
        """测试搜索相似邮件 - 截断长文本"""
        long_text = "A" * 3000  # 超过 2000 字符

        with patch.object(retriever.chroma_client, 'search_similar', return_value={"documents": [[]]}) as mock_search:
            await retriever._search_similar_emails(
                email_body=long_text,
                region=None
            )

            # 验证文本被截断到 2000 字符
            call_args = mock_search.call_args
            assert len(call_args[1]["query_text"]) == 2000

    @pytest.mark.asyncio
    async def test_get_customer_history(self, retriever):
        """测试获取客户历史"""
        mock_customer = {"name": "Test Customer", "tier": "A", "region": "eu"}

        with patch.object(retriever.db, 'query_customer', return_value=mock_customer) as mock_query:
            result = await retriever._get_customer_history({
                "customer_email": "test@example.com",
                "customer_region": "eu"
            })

            mock_query.assert_called_once_with(
                email="test@example.com",
                region="eu"
            )
            assert result == mock_customer

    @pytest.mark.asyncio
    async def test_get_customer_history_without_email(self, retriever):
        """测试获取客户历史 - 没有邮箱"""
        with patch.object(retriever.db, 'query_customer', return_value=None) as mock_query:
            result = await retriever._get_customer_history({
                "customer_region": "asia"
            })

            mock_query.assert_called_once_with(
                email=None,
                region="asia"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_get_pricing_policy(self, retriever):
        """测试获取定价政策"""
        mock_pricing = {
            "policies": [
                {"product": "Paracetamol", "base_price": 2.5, "discount_rate": 0.1}
            ],
            "region": "brazil"
        }

        with patch.object(retriever.db, 'query_pricing_policy', return_value=mock_pricing) as mock_query:
            result = await retriever._get_pricing_policy(
                products=["Paracetamol"],
                region="brazil"
            )

            mock_query.assert_called_once_with(
                products=["Paracetamol"],
                region="brazil"
            )
            assert result == mock_pricing

    @pytest.mark.asyncio
    async def test_get_pricing_policy_empty_products(self, retriever):
        """测试获取定价政策 - 空产品列表"""
        with patch.object(retriever.db, 'query_pricing_policy', return_value={"policies": [], "region": "eu"}) as mock_query:
            result = await retriever._get_pricing_policy(
                products=[],
                region="eu"
            )

            mock_query.assert_called_once_with(
                products=[],
                region="eu"
            )
            assert result["policies"] == []

    @pytest.mark.asyncio
    async def test_get_compliance_requirements(self, retriever):
        """测试获取合规要求"""
        mock_compliance = {
            "requirements": [
                {"type": "certification", "name": "ANVISA", "mandatory": True, "description": "Brazil approval"}
            ],
            "region": "brazil"
        }

        with patch.object(retriever.db, 'query_compliance_requirements', return_value=mock_compliance) as mock_query:
            result = await retriever._get_compliance_requirements(
                products=["Paracetamol"],
                region="brazil"
            )

            mock_query.assert_called_once_with(
                products=["Paracetamol"],
                destination="brazil"
            )
            assert result == mock_compliance

    @pytest.mark.asyncio
    async def test_get_compliance_requirements_empty(self, retriever):
        """测试获取合规要求 - 无要求"""
        with patch.object(retriever.db, 'query_compliance_requirements', return_value={"requirements": [], "region": "unknown"}) as mock_query:
            result = await retriever._get_compliance_requirements(
                products=["UnknownProduct"],
                region="unknown"
            )

            assert result["requirements"] == []


# ============================================================================
# ChromaClient 测试
# ============================================================================

class TestChromaClient:
    """ChromaDB 客户端测试"""

    @pytest.fixture
    def settings(self):
        """创建设置对象"""
        settings = Settings()
        settings.chroma_persist_dir = "./test_chroma"
        return settings

    @pytest.fixture
    def chroma_client(self, settings):
        """创建 ChromaClient 实例"""
        return ChromaClient(settings)

    def test_init(self, settings):
        """测试 ChromaClient 初始化"""
        client = ChromaClient(settings)

        assert client.settings == settings
        assert client._client is None
        assert client._collection is None

    def test_client_lazy_loading(self, settings):
        """测试客户端懒加载"""
        client = ChromaClient(settings)

        assert client._client is None

        with patch('email_agent.layer2.chroma_client.chromadb.PersistentClient') as mock_persistent:
            mock_client = MagicMock()
            mock_persistent.return_value = mock_client

            result = client.client

            assert client._client is not None
            mock_persistent.assert_called_once_with(path="./test_chroma")

    def test_collection_lazy_loading(self, settings, chroma_client):
        """测试集合懒加载"""
        with patch.object(chroma_client, 'client', MagicMock()) as mock_chroma_client:
            mock_collection = MagicMock()
            mock_chroma_client.get_or_create_collection.return_value = mock_collection

            result = chroma_client.collection

            mock_chroma_client.get_or_create_collection.assert_called_once_with(
                name="email_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            assert result == mock_collection

    @pytest.mark.asyncio
    async def test_add_email(self, settings):
        """测试添加邮件到向量存储"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()
        mock_collection.add = MagicMock()

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[0.1, 0.2, 0.3]) as mock_embed:
                await client.add_email(
                    email_id="test-email-123",
                    content="Test email content",
                    metadata={"region": "brazil", "type": "inquiry"}
                )

                mock_embed.assert_called_once_with("Test email content")
                mock_collection.add.assert_called_once_with(
                    embeddings=[[0.1, 0.2, 0.3]],
                    metadatas=[{"region": "brazil", "type": "inquiry"}],
                    ids=["test-email-123"]
                )

    @pytest.mark.asyncio
    async def test_add_email_embedding_failure(self, settings):
        """测试添加邮件 - embedding 生成失败"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[]) as mock_embed:
                await client.add_email(
                    email_id="test-email-456",
                    content="Failed content",
                    metadata={"region": "eu"}
                )

                mock_embed.assert_called_once()
                mock_collection.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_similar(self, settings):
        """测试搜索相似邮件"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()
        mock_result = {
            "documents": [["Similar email 1"]],
            "metadatas": [[{"region": "brazil"}]],
            "ids": [["email-1"]],
            "distances": [0.15]
        }
        mock_collection.query.return_value = mock_result

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[0.1, 0.2, 0.3]) as mock_embed:
                result = await client.search_similar(
                    query_text="Test query",
                    n_results=3,
                    filter_metadata={"region": "brazil"}
                )

                mock_embed.assert_called_once_with("Test query")
                mock_collection.query.assert_called_once_with(
                    query_embeddings=[[0.1, 0.2, 0.3]],
                    n_results=3,
                    where={"region": "brazil"}
                )
                assert result == mock_result

    @pytest.mark.asyncio
    async def test_search_similar_without_filter(self, settings):
        """测试搜索相似邮件 - 无过滤条件"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()
        mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": []}

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[0.1, 0.2, 0.3]):
                await client.search_similar(
                    query_text="Test query",
                    n_results=5,
                    filter_metadata=None
                )

                mock_collection.query.assert_called_once_with(
                    query_embeddings=[[0.1, 0.2, 0.3]],
                    n_results=5,
                    where=None
                )

    @pytest.mark.asyncio
    async def test_search_similar_embedding_failure(self, settings):
        """测试搜索相似邮件 - embedding 生成失败"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[]) as mock_embed:
                from chromadb.api.types import QueryResult
                result = await client.search_similar(
                    query_text="Failed query",
                    n_results=3
                )

                mock_embed.assert_called_once()
                mock_collection.query.assert_not_called()
                assert isinstance(result, QueryResult)
                assert result["documents"] == []

    @pytest.mark.asyncio
    async def test_search_similar_default_n_results(self, settings):
        """测试搜索相似邮件 - 默认结果数量"""
        client = ChromaClient(settings)

        mock_collection = MagicMock()
        mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": []}

        with patch.object(client, 'collection', mock_collection):
            with patch('email_agent.layer2.chroma_client._generate_embedding_with_ollama', return_value=[0.1, 0.2, 0.3]):
                await client.search_similar(query_text="Test")

                # 验证默认 n_results=3
                call_args = mock_collection.query.call_args
                assert call_args[1]["n_results"] == 3


# ============================================================================
# EmbeddingService 测试
# ============================================================================

class TestEmbeddingService:
    """Embedding 服务测试"""

    @pytest.fixture
    def settings(self):
        """创建设置对象"""
        settings = Settings()
        settings.ollama_host = "localhost:11434"
        return settings

    @pytest.fixture
    def embedding_service(self, settings):
        """创建 EmbeddingService 实例"""
        return EmbeddingService(settings)

    def test_init(self, settings):
        """测试 EmbeddingService 初始化"""
        service = EmbeddingService(settings)

        assert service.settings == settings
        assert service._client is None
        assert service.model == "mxb3embed-base"

    def test_client_lazy_loading(self, settings):
        """测试客户端懒加载"""
        service = EmbeddingService(settings)

        assert service._client is None

        with patch('email_agent.layer2.embedding_service.ollama') as mock_ollama:
            mock_client = MagicMock()
            mock_ollama.Client.return_value = mock_client

            result = service.client

            assert service._client is not None
            mock_ollama.Client.assert_called_once_with(host="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_generate_embedding(self, embedding_service):
        """测试生成单个 embedding"""
        mock_response = {"embedding": [0.1, 0.2, 0.3, 0.4]}

        with patch.object(embedding_service, 'client', MagicMock()) as mock_client:
            mock_client.embeddings.return_value = mock_response

            result = await embedding_service.generate_embedding("Test text")

            mock_client.embeddings.assert_called_once_with(
                model="mxb3embed-base",
                prompt="Test text"
            )
            assert result == [0.1, 0.2, 0.3, 0.4]

    @pytest.mark.asyncio
    async def test_generate_embedding_failure(self, embedding_service):
        """测试生成 embedding 失败"""
        with patch.object(embedding_service, 'client', MagicMock()) as mock_client:
            mock_client.embeddings.side_effect = Exception("Connection failed")

            with pytest.raises(EmbeddingError) as exc_info:
                await embedding_service.generate_embedding("Test text")

            assert "Failed to generate embedding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, embedding_service):
        """测试批量生成 embeddings"""
        mock_response = {"embedding": [0.1, 0.2, 0.3]}

        with patch.object(embedding_service, 'client', MagicMock()) as mock_client:
            mock_client.embeddings.return_value = mock_response

            result = await embedding_service.generate_embeddings(["Text 1", "Text 2", "Text 3"])

            assert len(result) == 3
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.1, 0.2, 0.3]
            assert result[2] == [0.1, 0.2, 0.3]
            # 验证调用了 3 次
            assert mock_client.embeddings.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_input(self, embedding_service):
        """测试批量生成 embeddings - 空输入"""
        result = await embedding_service.generate_embeddings([])

        assert result == []


# ============================================================================
# _generate_embedding_with_ollama 函数测试
# ============================================================================

class TestGenerateEmbeddingWithOllama:
    """_generate_embedding_with_ollama 函数测试"""

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_success(self, mock_run):
        """测试成功生成 embedding"""
        import json
        mock_response = {"embedding": [0.1, 0.2, 0.3]}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response),
            stderr=""
        )

        result = _generate_embedding_with_ollama("Test text")

        assert result == [0.1, 0.2, 0.3]
        mock_run.assert_called_once()

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_subprocess_failure(self, mock_run):
        """测试 subprocess 执行失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error message"
        )

        result = _generate_embedding_with_ollama("Test text")

        assert result == []

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_json_parse_failure(self, mock_run):
        """测试 JSON 解析失败"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Invalid JSON",
            stderr=""
        )

        # 应该会抛出 JSONDecodeError 并被捕获，返回空列表
        import json
        with pytest.raises(json.JSONDecodeError):
            _generate_embedding_with_ollama("Test text")

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_missing_embedding_field(self, mock_run):
        """测试响应缺少 embedding 字段"""
        import json
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"other_field": "value"}),
            stderr=""
        )

        result = _generate_embedding_with_ollama("Test text")

        assert result == []

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_timeout(self, mock_run):
        """测试超时异常"""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=60)

        result = _generate_embedding_with_ollama("Test text")

        assert result == []

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_general_exception(self, mock_run):
        """测试一般异常"""
        mock_run.side_effect = Exception("Unexpected error")

        result = _generate_embedding_with_ollama("Test text")

        assert result == []

    @patch('email_agent.layer2.chroma_client.subprocess.run')
    def test_generate_embedding_with_custom_model(self, mock_run):
        """测试使用自定义模型"""
        import json
        mock_response = {"embedding": [0.1, 0.2, 0.3]}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_response),
            stderr=""
        )

        result = _generate_embedding_with_ollama("Test text", model="custom-model")

        assert result == [0.1, 0.2, 0.3]
        # 验证使用了自定义模型
        call_args = mock_run.call_args[0][0]
        assert "custom-model" in call_args
