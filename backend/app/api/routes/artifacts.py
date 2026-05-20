"""Artifacts endpoints — GET /artifacts, GET /artifacts/{id}, GET /search."""

import logging
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models import (
    ArtifactDetail,
    ArtifactCreateRequest,
    ArtifactBase,
    ArtifactListResponse,
    SearchResponse,
    SearchResult,
)
from app.rag.embedder import embed_query
from app.rag.vectorstore import (
    add_documents,
    delete_by_id,
    list_all,
    list_records,
    get_by_id,
    collection_count,
)
from app.rag.retriever import semantic_search
from app.utils.helpers import clean_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _build_document_text(meta: dict) -> str:
    """Build the searchable text stored with an artifact embedding."""
    parts = [
        f"Name: {meta.get('artifact_name_en', '')} / {meta.get('artifact_name_ar', '')}",
        f"Category: {meta.get('category_en', '')} / {meta.get('category_ar', '')}",
        f"Hall: {meta.get('hall_en', '')} / {meta.get('hall_ar', '')}",
        f"Section: {meta.get('section_name_en', '')} / {meta.get('section_name_ar', '')}",
        f"Discovery Site: {meta.get('discovery_site_en', '')} / {meta.get('discovery_site_ar', '')}",
        f"Description: {meta.get('description_en', '')}",
        f"وصف: {meta.get('description_ar', '')}",
    ]
    return "\n".join(part for part in parts if part.split(": ", 1)[-1].strip(" /"))


def _metadata_to_base(art_id: str, meta: dict) -> ArtifactBase:
    """Convert an artifact metadata dict to an ArtifactBase model."""
    return ArtifactBase(
        artifact_id=art_id,
        artifact_name_en=meta.get("artifact_name_en", ""),
        artifact_name_ar=meta.get("artifact_name_ar", ""),
        category_en=meta.get("category_en"),
        category_ar=meta.get("category_ar"),
        hall_en=meta.get("hall_en"),
        hall_ar=meta.get("hall_ar"),
        discovery_site_en=meta.get("discovery_site_en"),
        discovery_site_ar=meta.get("discovery_site_ar"),
        section_name_en=meta.get("section_name_en"),
        section_name_ar=meta.get("section_name_ar"),
        section_number=meta.get("section_number"),
        link=meta.get("link"),
    )


def _metadata_to_detail(art_id: str, meta: dict) -> ArtifactDetail:
    """Convert an artifact metadata dict to an ArtifactDetail model."""
    return ArtifactDetail(
        artifact_id=art_id,
        artifact_name_en=meta.get("artifact_name_en", ""),
        artifact_name_ar=meta.get("artifact_name_ar", ""),
        category_en=meta.get("category_en"),
        category_ar=meta.get("category_ar"),
        hall_en=meta.get("hall_en"),
        hall_ar=meta.get("hall_ar"),
        discovery_site_en=meta.get("discovery_site_en"),
        discovery_site_ar=meta.get("discovery_site_ar"),
        section_name_en=meta.get("section_name_en"),
        section_name_ar=meta.get("section_name_ar"),
        section_number=meta.get("section_number"),
        link=meta.get("link"),
        description_en=meta.get("description_en"),
        description_ar=meta.get("description_ar"),
    )


@router.get("", response_model=ArtifactListResponse, summary="List all artifacts")
async def list_artifacts(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> ArtifactListResponse:
    """List all artifacts with pagination."""
    total = collection_count()
    offset = (page - 1) * page_size

    if offset >= total and total > 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page} exceeds total pages.",
        )

    result = list_all(limit=page_size, offset=offset)
    artifacts = [
        _metadata_to_base(art_id, meta)
        for art_id, meta in zip(result["ids"], result["metadatas"])
    ]

    return ArtifactListResponse(
        total=total,
        page=page,
        page_size=page_size,
        artifacts=artifacts,
    )


@router.post("", response_model=ArtifactDetail, status_code=status.HTTP_201_CREATED, summary="Create artifact")
async def create_artifact(request: ArtifactCreateRequest) -> ArtifactDetail:
    """Create an artifact and store its pgvector embedding in Supabase."""
    name_en = clean_text(request.artifact_name_en)
    if not name_en:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="artifact_name_en is required.",
        )

    artifact_id = f"artifact_{uuid4().hex[:12]}"
    metadata = {
        "artifact_id": artifact_id,
        "artifact_name_en": name_en,
        "artifact_name_ar": clean_text(request.artifact_name_ar or request.artifact_name_en),
        "description_en": clean_text(request.description_en or ""),
        "description_ar": clean_text(request.description_ar or request.description_en or ""),
        "category_en": clean_text(request.category_en or ""),
        "category_ar": clean_text(request.category_ar or ""),
        "hall_en": clean_text(request.hall_en or ""),
        "hall_ar": clean_text(request.hall_ar or ""),
        "discovery_site_en": clean_text(request.discovery_site_en or ""),
        "discovery_site_ar": clean_text(request.discovery_site_ar or ""),
        "section_name_en": clean_text(request.section_name_en or ""),
        "section_name_ar": clean_text(request.section_name_ar or ""),
        "section_number": clean_text(str(request.section_number or "")),
        "link": clean_text(request.link or ""),
        "image_url": clean_text(request.image_url or ""),
    }
    document = _build_document_text(metadata) or name_en
    embedding = embed_query(document)

    try:
        add_documents(
            ids=[artifact_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )
    except Exception as exc:
        logger.exception("Failed to create artifact in Supabase")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to save artifact: {exc}",
        ) from exc

    return _metadata_to_detail(artifact_id, metadata)


@router.get("/admin", summary="List raw artifacts for admin dashboard")
async def list_admin_artifacts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
) -> dict:
    """List raw artifact records through the backend service role."""
    offset = (page - 1) * page_size
    return list_records(limit=page_size, offset=offset)


@router.get("/search", response_model=SearchResponse, summary="Semantic search")
async def search_artifacts(
    q: str = Query(..., description="Search query (Arabic or English)"),
    top_k: int = Query(default=5, ge=1, le=20),
    hall: Optional[str] = Query(default=None, description="Filter by hall"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    discovery_site: Optional[str] = Query(default=None, description="Filter by discovery site"),
) -> SearchResponse:
    """Quick semantic search over museum artifacts."""
    results = semantic_search(
        query=q,
        top_k=top_k,
        hall=hall,
        category=category,
        discovery_site=discovery_site,
    )

    search_results = [
        SearchResult(
            artifact_id=r.get("artifact_id", ""),
            artifact_name_en=r.get("artifact_name_en", ""),
            artifact_name_ar=r.get("artifact_name_ar", ""),
            category_en=r.get("category_en"),
            category_ar=r.get("category_ar"),
            hall_en=r.get("hall_en"),
            hall_ar=r.get("hall_ar"),
            discovery_site_en=r.get("discovery_site_en"),
            discovery_site_ar=r.get("discovery_site_ar"),
            section_name_en=r.get("section_name_en"),
            section_name_ar=r.get("section_name_ar"),
            section_number=r.get("section_number"),
            link=r.get("link"),
            relevance_score=r.get("relevance_score", 0.0),
            description_excerpt=r.get("description_excerpt"),
        )
        for r in results
    ]

    return SearchResponse(
        query=q,
        results=search_results,
        total_found=len(search_results),
    )


@router.get("/{artifact_id}", response_model=ArtifactDetail, summary="Get artifact details")
async def get_artifact(artifact_id: str) -> ArtifactDetail:
    """Retrieve complete details for a single artifact by its ID."""
    result = get_by_id(artifact_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found.",
        )
    return _metadata_to_detail(result["id"], result["metadata"])


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete artifact")
async def delete_artifact(artifact_id: str) -> None:
    """Delete an artifact through the backend service role."""
    try:
        delete_by_id(artifact_id)
    except Exception as exc:
        logger.exception("Failed to delete artifact from Supabase")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to delete artifact: {exc}",
        ) from exc
