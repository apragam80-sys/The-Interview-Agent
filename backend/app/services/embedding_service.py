"""
Embedding Service Module.
Provides standardized text embedding generation supporting Google Generative AI
embeddings (models/text-embedding-004) with deterministic local vector fallback.
"""

import hashlib
import math
import numpy as np
from typing import List, Optional
from app.config import GEMINI_API_KEY, logger


class EmbeddingService:
    """
    Service for generating vector embeddings for text documents and search queries.
    """

    def __init__(self, model_name: str = "models/text-embedding-004", dimension: int = 768):
        """
        Initialize Embedding Service.

        Args:
            model_name (str): Embedding model identifier.
            dimension (int): Vector embedding dimension.
        """
        self.model_name = model_name
        self.dimension = dimension
        self._provider = None
        self._init_provider()

    def _init_provider(self):
        """Initialize Google Gemini embedding model if API key is configured."""
        if GEMINI_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._provider = GoogleGenerativeAIEmbeddings(
                    model=self.model_name,
                    google_api_key=GEMINI_API_KEY
                )
                logger.info(f"Initialized Google Generative AI Embeddings with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize GoogleGenerativeAIEmbeddings: {e}. Using local embedding fallback.")
                self._provider = None
        else:
            logger.info("No GEMINI_API_KEY provided; using deterministic normalized embedding fallback.")
            self._provider = None

    def _generate_fallback_vector(self, text: str) -> List[float]:
        """
        Deterministic, unit-normalized dense embedding generator for offline testing.
        Uses hashing and feature hashing across character and word n-grams.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        
        # Word hashing
        for i, word in enumerate(words):
            h = int(hashlib.md5(f"w_{word}".encode()).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 / math.sqrt(i + 1))
            
            # Sub-word 3-grams
            for j in range(len(word) - 2):
                tri = word[j:j+3]
                htri = int(hashlib.sha256(f"t_{tri}".encode()).hexdigest(), 16)
                idx_t = htri % self.dimension
                vec[idx_t] += 0.5 * (1.0 if ((htri >> 3) % 2 == 0) else -1.0)

        # Normalize to unit sphere
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a list of document strings.

        Args:
            texts (List[str]): List of texts to embed.

        Returns:
            List[List[float]]: List of float embedding vectors.
        """
        if not texts:
            return []

        if self._provider is not None:
            try:
                return self._provider.embed_documents(texts)
            except Exception as e:
                logger.warning(f"Embedding API call failed: {e}. Falling back to local vectors.")

        return [self._generate_fallback_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        """
        Generate a vector embedding for a single search query string.

        Args:
            text (str): Query text.

        Returns:
            List[float]: Query embedding vector.
        """
        if not text:
            return [0.0] * self.dimension

        if self._provider is not None:
            try:
                return self._provider.embed_query(text)
            except Exception as e:
                logger.warning(f"Embedding API query failed: {e}. Falling back to local vector.")

        return self._generate_fallback_vector(text)


# Global singleton instance
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Dependency injection helper returning singleton EmbeddingService."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
