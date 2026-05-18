"""ChromaDB vector store operations."""

import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level client and collection singletons
_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[chromadb.Collection] = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        logger.info("Connecting to ChromaDB at: %s", settings.chroma_persist_dir)
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    """Return or create the artifacts collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Using ChromaDB collection '%s' with %d documents.",
            settings.chroma_collection_name,
            _collection.count(),
        )
    return _collection


def add_documents(
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """Add documents with embeddings to ChromaDB."""
    collection = get_collection()
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info("Added %d documents to ChromaDB.", len(ids))


def query_collection(
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query the collection with an embedding vector.

    Returns a ChromaDB result dict with ids, documents, metadatas, distances.
    """
    collection = get_collection()
    kwargs: Dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def get_by_id(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single artifact by its ChromaDB ID."""
    collection = get_collection()
    result = collection.get(
        ids=[artifact_id],
        include=["documents", "metadatas"],
    )
    if result["ids"] and result["ids"][0]:
        return {
            "id": result["ids"][0],
            "document": result["documents"][0],
            "metadata": result["metadatas"][0],
        }
    return None


def collection_count() -> int:
    """Return total number of documents in the collection."""
    return get_collection().count()


def list_all(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List all artifacts with pagination."""
    collection = get_collection()
    return collection.get(
        limit=limit,
        offset=offset,
        include=["metadatas"],
    )
