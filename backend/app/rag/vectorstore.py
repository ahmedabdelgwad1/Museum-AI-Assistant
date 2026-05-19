"""Supabase pgvector store operations (replaces ChromaDB)."""

import logging
import json
from typing import List, Dict, Any, Optional

from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level Supabase client singleton
_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return or create the Supabase client."""
    global _client
    if _client is None:
        logger.info("Connecting to Supabase: %s", settings.supabase_url)
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client created successfully.")
    return _client


def query_collection(
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Query Supabase using pgvector similarity search.

    Returns a dict with ids, documents, metadatas, distances
    (compatible with the old ChromaDB interface).
    """
    client = get_supabase_client()

    try:
        response = client.rpc(
            settings.supabase_function,
            {
                "query_embedding": query_embedding,
                "match_count": n_results,
            },
        ).execute()

        rows = response.data or []

        ids = []
        documents = []
        metadatas = []
        distances = []

        for row in rows:
            ids.append(str(row.get("id", "")))
            documents.append(row.get("content", ""))

            # Parse metadata (stored as JSON string or dict)
            meta = row.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            metadatas.append(meta)

            # similarity → distance (1 - similarity)
            similarity = row.get("similarity", 0.0)
            distances.append(1.0 - similarity)

        return {
            "ids": [ids],
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    except Exception as e:
        logger.error("Supabase query failed: %s", e)
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


def get_by_id(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single artifact by its Supabase row ID."""
    client = get_supabase_client()
    try:
        response = (
            client.table(settings.supabase_table)
            .select("id, content, metadata")
            .eq("id", artifact_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if rows:
            row = rows[0]
            meta = row.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            return {
                "id": str(row["id"]),
                "document": row.get("content", ""),
                "metadata": meta,
            }
    except Exception as e:
        logger.error("Supabase get_by_id failed: %s", e)
    return None


def collection_count() -> int:
    """Return total number of documents in the Supabase table."""
    client = get_supabase_client()
    try:
        response = (
            client.table(settings.supabase_table)
            .select("id", count="exact")
            .execute()
        )
        return response.count or 0
    except Exception as e:
        logger.error("Supabase count failed: %s", e)
        return 0


def list_all(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List all artifacts with pagination."""
    client = get_supabase_client()
    try:
        response = (
            client.table(settings.supabase_table)
            .select("id, metadata")
            .range(offset, offset + limit - 1)
            .execute()
        )
        rows = response.data or []
        metadatas = []
        ids = []
        for row in rows:
            ids.append(str(row["id"]))
            meta = row.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            metadatas.append(meta)
        return {"ids": ids, "metadatas": metadatas}
    except Exception as e:
        logger.error("Supabase list_all failed: %s", e)
        return {"ids": [], "metadatas": []}
