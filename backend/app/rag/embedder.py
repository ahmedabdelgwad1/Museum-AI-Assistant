"""Multilingual embedding logic using sentence-transformers."""

import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton so we only load the model once
_model: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    """Return the singleton embedding model, loading it on first call."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully.")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts.

    Returns a list of embedding vectors (list of floats).
    """
    model = get_embedder()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    model = get_embedder()
    embedding = model.encode(
        query,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embedding.tolist()
