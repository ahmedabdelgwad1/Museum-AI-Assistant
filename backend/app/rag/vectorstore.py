"""Supabase pgvector store operations."""

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

    Returns a dict with ids, documents, metadatas, distances.
    """
    client = get_supabase_client()

    try:
        response = client.rpc(
            settings.supabase_function,
            {
                "query_embedding": query_embedding,
                "match_count": n_results * 4 if where else n_results,
            },
        ).execute()

        rows = response.data or []

        ids = []
        documents = []
        metadatas = []
        distances = []

        for row in rows:
            # Parse metadata (stored as JSON string or dict)
            meta = row.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if where and not _metadata_matches(meta, where):
                continue

            ids.append(str(row.get("id", "")))
            documents.append(row.get("content", ""))
            metadatas.append(meta)

            # similarity → distance (1 - similarity)
            similarity = row.get("similarity", 0.0)
            distances.append(1.0 - similarity)

            if len(metadatas) >= n_results:
                break

        return {
            "ids": [ids],
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances],
        }

    except Exception as e:
        logger.error("Supabase query failed: %s", e)
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


def _metadata_matches(meta: Dict[str, Any], filters: Dict[str, str]) -> bool:
    """Return whether metadata contains all requested filter values."""
    for key, expected in filters.items():
        value = str(meta.get(key, "")).lower()
        if str(expected).lower() not in value:
            return False
    return True


def add_documents(
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """Upsert embedded artifacts into the Supabase table."""
    client = get_supabase_client()
    records = [
        {
            "id": artifact_id,
            "content": document,
            "metadata": metadata,
            "embedding": embedding,
        }
        for artifact_id, document, metadata, embedding in zip(
            ids, documents, metadatas, embeddings
        )
    ]
    if not records:
        return
    client.table(settings.supabase_table).upsert(records).execute()


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


def delete_by_id(artifact_id: str) -> None:
    """Delete a single artifact by its Supabase row ID."""
    client = get_supabase_client()
    client.table(settings.supabase_table).delete().eq("id", artifact_id).execute()


def collection_count() -> int:
    """Return total number of documents in the Supabase table."""
    client = get_supabase_client()
    response = (
        client.table(settings.supabase_table)
        .select("id", count="exact")
        .execute()
    )
    return response.count or 0


def list_records(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List raw artifact records for admin views."""
    client = get_supabase_client()
    try:
        response = (
            client.table(settings.supabase_table)
            .select("id, content, metadata, created_at")
            .order("id")
            .range(offset, offset + limit - 1)
            .execute()
        )
    except Exception:
        response = (
            client.table(settings.supabase_table)
            .select("id, content, metadata")
            .order("id")
            .range(offset, offset + limit - 1)
            .execute()
        )
    rows = response.data or []
    for row in rows:
        meta = row.get("metadata", {})
        if isinstance(meta, str):
            try:
                row["metadata"] = json.loads(meta)
            except Exception:
                row["metadata"] = {}
    return {"total": collection_count(), "records": rows}


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
