"""
Embedding Service — handles vector generation with in-memory caching.
Uses sentence-transformers currently, future-proofed for arbitrary models.
"""
from __future__ import annotations
import os
from functools import lru_cache

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# LRU Cache for frequently repeated small texts (like skills or job descriptions)
# Bound to 5000 strings to keep memory footprint light.
@lru_cache(maxsize=5000)
def _cached_embedding(text: str) -> list[float] | None:
    model = _get_sentence_model()
    if model is None:
        return None
    try:
        emb = model.encode([text], normalize_embeddings=True)[0]
        return emb.tolist()
    except Exception as exc:
        logger.error("Failed to generate embedding: %s", exc)
        return None


# Global model reference
_sentence_model = None
_model_loaded = False


def _get_sentence_model():
    global _sentence_model, _model_loaded
    if _model_loaded:
        return _sentence_model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Initializing SentenceTransformer: %s", settings.SENTENCE_MODEL_NAME)
        # Force CPU or GPU explicitly if needed, omitting for auto
        _sentence_model = SentenceTransformer(settings.SENTENCE_MODEL_NAME)
    except Exception as exc:
        logger.error("Could not load sentence transformer: %s", exc)
        _sentence_model = None
    finally:
        _model_loaded = True
    return _sentence_model


class EmbeddingService:
    @staticmethod
    def get_embedding(text: str) -> list[float] | None:
        """Get an embedding for a text string, utilizing LRU cache."""
        if not text:
            return None
        # Cache key is case-sensitive, optionally lower() here if semantic isn't sensitive
        return _cached_embedding(text)

    @staticmethod
    def semantic_similarity(text_a: str, text_b: str) -> float:
        """Calculate cosine similarity (0-100) between two text strings."""
        emb_a = EmbeddingService.get_embedding(text_a)
        emb_b = EmbeddingService.get_embedding(text_b)
        
        if emb_a is None or emb_b is None:
            # Fallback to TF-IDF
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity as cos_sim
            try:
                vect = TfidfVectorizer(stop_words="english", max_features=1000)
                matrix = vect.fit_transform([text_a.lower(), text_b.lower()])
                score = float(cos_sim(matrix[0:1], matrix[1:2])[0][0]) * 100.0
                return score
            except Exception:
                return 0.0

        # Cosine similarity of normalized vectors is dot product
        import numpy as np
        score = float(np.dot(emb_a, emb_b)) * 100.0
        return max(0.0, min(score, 100.0))

embedding_service = EmbeddingService()
