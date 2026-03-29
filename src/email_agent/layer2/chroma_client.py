from typing import Optional

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult

from email_agent.config import Settings
from email_agent.logging_config import get_logger

logger = get_logger(__name__)


class ChromaClient:
    """Client for ChromaDB vector store operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[ClientAPI] = None
        self._collection = None

    @property
    def client(self) -> ClientAPI:
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir
            )
            logger.info(
                "chromadb_initialized",
                persist_dir=self.settings.chroma_persist_dir
            )
        return self._client

    @property
    def collection(self):
        """Get or create email embeddings collection."""
        if self._collection is None:
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
        """Add an email to the vector store."""
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
        """Search for similar emails."""
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=filter_metadata
        )
