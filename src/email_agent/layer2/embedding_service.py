from typing import List

import ollama
from ollama import Client

from email_agent.config import Settings
from email_agent.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Ollama."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = Client(host=f"http://{settings.ollama_host}")
        self.model = "mxb3embed-base"

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = self.client.embeddings(
                model=self.model,
                prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise EmbeddingError(f"Failed to generate embedding: {e}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass
