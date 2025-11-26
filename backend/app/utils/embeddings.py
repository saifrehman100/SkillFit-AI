"""
Embeddings service for vector search functionality.
Supports OpenAI embeddings and sentence-transformers.
"""
from typing import List, Optional
import numpy as np

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingsProvider:
    """Base class for embeddings providers."""

    def __init__(self):
        self.dimensions = settings.embeddings_dimensions

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        raise NotImplementedError

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


class OpenAIEmbeddings(EmbeddingsProvider):
    """OpenAI embeddings provider."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = settings.embeddings_model

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            logger.debug("Generating OpenAI embedding", text_length=len(text))

            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding

            logger.debug("OpenAI embedding generated", dimensions=len(embedding))

            return embedding

        except Exception as e:
            logger.error("OpenAI embedding failed", error=str(e))
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            logger.info("Generating OpenAI embeddings", num_texts=len(texts))

            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]

            logger.info("OpenAI embeddings generated", count=len(embeddings))

            return embeddings

        except Exception as e:
            logger.error("OpenAI batch embedding failed", error=str(e))
            raise


class SentenceTransformerEmbeddings(EmbeddingsProvider):
    """Sentence-Transformers embeddings provider (local, no API required)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        logger.info("Loading SentenceTransformer model", model=model_name)
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers."""
        try:
            logger.debug("Generating sentence embedding", text_length=len(text))

            embedding = self.model.encode(text, convert_to_numpy=True)

            return embedding.tolist()

        except Exception as e:
            logger.error("Sentence embedding failed", error=str(e))
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            logger.info("Generating sentence embeddings", num_texts=len(texts))

            embeddings = self.model.encode(texts, convert_to_numpy=True)

            return embeddings.tolist()

        except Exception as e:
            logger.error("Batch sentence embedding failed", error=str(e))
            raise


class EmbeddingsFactory:
    """Factory for creating embeddings providers."""

    _instances = {}

    @classmethod
    def get_provider(
        cls,
        provider: str = None,
        api_key: Optional[str] = None
    ) -> EmbeddingsProvider:
        """
        Get or create an embeddings provider.
        Uses singleton pattern to cache providers.
        """
        provider = provider or settings.embeddings_provider

        cache_key = f"{provider}:{api_key or 'default'}"

        if cache_key not in cls._instances:
            logger.info("Creating embeddings provider", provider=provider)

            if provider == "openai":
                cls._instances[cache_key] = OpenAIEmbeddings(api_key=api_key)
            elif provider == "sentence_transformers":
                model_name = settings.embeddings_model if hasattr(settings, 'embeddings_model') else "all-MiniLM-L6-v2"
                cls._instances[cache_key] = SentenceTransformerEmbeddings(model_name=model_name)
            else:
                raise ValueError(f"Unsupported embeddings provider: {provider}")

        return cls._instances[cache_key]
