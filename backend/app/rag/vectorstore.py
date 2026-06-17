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
    visual_embeddings: Optional[List[List[float]]] = None,
) -> List[str]:
    """Upsert embedded artifacts into the Supabase table and return assigned IDs."""
    client = get_supabase_client()
    records = []
    for i, (artifact_id, document, metadata, embedding) in enumerate(zip(
        ids, documents, metadatas, embeddings
    )):
        record = {
            "content": document,
            "metadata": metadata,
            "embedding": embedding,
        }
        if visual_embeddings and i < len(visual_embeddings) and visual_embeddings[i]:
            record["visual_embedding"] = visual_embeddings[i]
            
        # If ID is a number, we are updating an existing row
        try:
            record["id"] = int(artifact_id)
        except (ValueError, TypeError):
            pass  # New row, let Supabase auto-increment

        records.append(record)

    if not records:
        return []
        
    response = client.table(settings.supabase_table).upsert(records).execute()
    
    returned_ids = []
    if response.data:
        for row in response.data:
            returned_ids.append(str(row.get("id")))
    return returned_ids


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
    """Delete a single artifact by its Supabase row ID and its associated image."""
    client = get_supabase_client()
    
    # First, fetch the artifact to get its image_url
    artifact = get_by_id(artifact_id)
    if artifact:
        metadata = artifact.get("metadata", {})
        image_url = metadata.get("image_url")
        if image_url and "supabase.co" in image_url and "artifact-images" in image_url:
            try:
                from urllib.parse import urlparse
                path = urlparse(image_url).path
                filename = path.split("/")[-1]
                if filename:
                    client.storage.from_("artifact-images").remove([filename])
            except Exception as e:
                logger.error("Failed to delete image from Supabase Storage: %s", e)

    # Finally, delete the row from the database
    client.table(settings.supabase_table).delete().eq("id", artifact_id).execute()


def update_metadata(artifact_id: str, fields: Dict[str, Any]) -> None:
    """Patch specific metadata fields of an artifact without re-embedding.

    Fetches the current metadata, merges the provided fields, then writes back.
    The embedding and content columns are left untouched.
    """
    client = get_supabase_client()

    # Fetch current metadata
    current = get_by_id(artifact_id)
    if current is None:
        raise ValueError(f"Artifact '{artifact_id}' not found.")

    meta = dict(current.get("metadata", {}))
    # Merge only the provided (non-None) fields
    for key, value in fields.items():
        if value is not None:
            meta[key] = value

    client.table(settings.supabase_table).update({"metadata": meta}).eq("id", artifact_id).execute()


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
