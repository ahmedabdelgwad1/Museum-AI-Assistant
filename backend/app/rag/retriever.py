"""Semantic search and retrieval over the Supabase pgvector artifact collection."""

import logging
from typing import List, Dict, Any, Optional

from app.rag.embedder import embed_query
from app.rag.vectorstore import query_collection, get_by_id, collection_count
from app.utils.helpers import excerpt
from app.config import settings

logger = logging.getLogger(__name__)


def _build_where_filter(
    hall: Optional[str] = None,
    category: Optional[str] = None,
    discovery_site: Optional[str] = None,
    section: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Build a metadata substring filter from optional fields."""
    filters = {}
    if hall:
        filters["hall_en"] = hall
    if category:
        filters["category_en"] = category
    if discovery_site:
        filters["discovery_site_en"] = discovery_site
    if section:
        filters["section_name_en"] = section

    return filters or None


def semantic_search(
    query: str,
    top_k: int | None = None,
    hall: Optional[str] = None,
    category: Optional[str] = None,
    discovery_site: Optional[str] = None,
    section: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search over artifacts.

    Returns a list of result dicts with metadata and relevance score.
    """
    if collection_count() == 0:
        logger.warning("Supabase artifact table is empty. Run the indexing script first.")
        return []

    k = top_k or settings.top_k_results
    query_emb = embed_query(query)
    where = _build_where_filter(hall, category, discovery_site, section)

    raw = query_collection(query_embedding=query_emb, n_results=k, where=where)

    results = []
    ids = raw.get("ids", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    documents = raw.get("documents", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    for i, (art_id, meta, doc, dist) in enumerate(
        zip(ids, metadatas, documents, distances)
    ):
        # Cosine distance → similarity score (0-1, higher is better)
        score = max(0.0, 1.0 - dist)
        results.append(
            {
                "artifact_id": art_id,
                "relevance_score": round(score, 4),
                "description_excerpt": excerpt(doc, 200),
                **meta,
            }
        )

    return results


def get_artifact_by_id(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full artifact details by ID."""
    result = get_by_id(artifact_id)
    if result:
        return {"artifact_id": result["id"], **result["metadata"]}
    return None


def get_artifact_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find an artifact by approximate name match using semantic search."""
    results = semantic_search(name, top_k=1)
    if results and results[0]["relevance_score"] >= 0.5:
        return results[0]
    return None
