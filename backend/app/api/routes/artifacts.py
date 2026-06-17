"""Artifacts endpoints — GET /artifacts, GET /artifacts/{id}, GET /search."""

import logging
from uuid import uuid4
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, status
import io
import httpx
from PIL import Image

from app.models import (
    ArtifactDetail,
    ArtifactCreateRequest,
    ArtifactUpdateRequest,
    ArtifactBase,
    ArtifactListResponse,
    SearchResponse,
    SearchResult,
)
from app.rag.embedder import embed_query
from app.rag.vectorstore import (
    add_documents,
    delete_by_id,
    update_metadata,
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

    metadata = {
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
        # 1. Insert into artifacts_raw to get the relational ID
        from app.rag.vectorstore import get_supabase_client
        client = get_supabase_client()
        raw_data = {
            "artifact_name_en": name_en,
            "artifact_name_ar": metadata["artifact_name_ar"],
            "description_en": metadata["description_en"],
            "description_ar": metadata["description_ar"],
            "category_en": metadata["category_en"],
            "url": metadata["image_url"] or metadata["link"],
        }
        
        # We wrap in try-except in case artifacts_raw doesn't exist yet in some environments
        try:
            raw_response = client.table("artifacts_raw").insert(raw_data).execute()
            final_id = str(raw_response.data[0]["artifact_id"])
        except Exception as e:
            logger.error("Failed to insert into artifacts_raw: %s", e)
            final_id = "new" # Fallback if table doesn't exist

        visual_embedding = None
        if metadata.get("image_url"):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(metadata["image_url"], timeout=10.0)
                    if resp.status_code == 200:
                        from app.dinov2 import DinoV2Encoder
                        encoder = DinoV2Encoder.get_instance()
                        visual_embedding = encoder.embed(Image.open(io.BytesIO(resp.content)))
            except Exception as e:
                logger.error("Failed to generate visual embedding on create: %s", e)

        # 2. Insert into museum_artifacts with the retrieved ID
        inserted_ids = add_documents(
            ids=[final_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
            visual_embeddings=[visual_embedding] if visual_embedding else None,
        )
        if final_id == "new" and inserted_ids:
            final_id = inserted_ids[0]
            
    except Exception as exc:
        logger.exception("Failed to create artifact in Supabase")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to save artifact: {exc}",
        ) from exc

    return _metadata_to_detail(final_id, metadata)


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = Field(..., description="'ar' or 'en'")

@router.post("/translate", summary="Translate text for admin panel")
async def translate_text(request: TranslateRequest):
    """
    Translates text between Arabic and English using the configured LLM.
    Used by the Admin Dashboard for quick artifact data entry.
    """
    if not request.text.strip():
        return {"translated_text": ""}
        
    from app.graph.nodes import _llm_call
    
    if request.target_lang == "ar":
        prompt = f"Translate the following artifact name/description into formal Arabic accurately without adding any extra conversational text or notes. Just output the translation:\n\n{request.text}"
    else:
        prompt = f"Translate the following artifact name/description into formal English accurately without adding any extra conversational text or notes. Just output the translation:\n\n{request.text}"
        
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # Use llama-3.1-8b-instant for lightning fast translation (~1 sec)
        translated = _llm_call(messages, max_tokens=1000, temperature=0.1, model="llama-3.1-8b-instant")
        return {"translated_text": translated.strip()}
    except Exception as exc:
        logger.error(f"Translation failed: {exc}")
        raise HTTPException(status_code=500, detail="Translation failed")

from app.models import BatchTranslateRequest, BatchTranslateResponse
import json

@router.post("/translate-batch", response_model=BatchTranslateResponse, summary="Batch translate text for admin panel")
async def translate_batch(request: BatchTranslateRequest):
    """
    Translates multiple fields between Arabic and English simultaneously using structured JSON output.
    Used by the Admin Dashboard for auto-filling all missing translations in one go.
    """
    if not request.fields_to_translate:
        return BatchTranslateResponse(translations={})
        
    from app.graph.nodes import _llm_call
    
    # Construct a structured prompt
    items_str = ""
    for item in request.fields_to_translate:
        lang_name = "Arabic" if item.target_lang == "ar" else "English"
        items_str += f"- Field ID: {item.field_id}\n  Source Text: {item.source_text}\n  Target Language: {lang_name}\n\n"
        
    prompt = f"""You are a professional museum translator. Translate the following text fields to their requested target languages.
Return ONLY a valid JSON object where the keys are the exact 'Field ID's provided, and the values are the translated text. Do not include any explanations or markdown wrappers outside the JSON object.

Fields to translate:
{items_str}

Respond with a JSON object containing the translations."""
        
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # We must use response_format={"type": "json_object"} and a model that supports it
        raw_response = _llm_call(
            messages, 
            max_tokens=2000, 
            temperature=0.1, 
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(raw_response)
        return BatchTranslateResponse(translations=parsed)
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse LLM JSON output: {exc}. Raw response: {raw_response}")
        raise HTTPException(status_code=502, detail="Invalid JSON from translation model")
    except Exception as exc:
        logger.error(f"Batch translation failed: {exc}")
        raise HTTPException(status_code=500, detail="Batch translation failed")
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


@router.patch("/{artifact_id}", response_model=ArtifactDetail, summary="Patch artifact metadata and re-embed")
async def patch_artifact(artifact_id: str, request: ArtifactUpdateRequest) -> ArtifactDetail:
    """Update selected metadata fields of an artifact and re-generate its semantic embedding."""
    fields = {k: v for k, v in request.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided to update.",
        )
        
    # 1. Fetch current artifact
    current = get_by_id(artifact_id)
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{artifact_id}' not found.")
        
    current_meta = current.get("metadata", {})
    
    # 2. Merge new fields (cleaning text values)
    for k, v in fields.items():
        current_meta[k] = clean_text(v) if isinstance(v, str) else v
        
    # 3. Build new document text for embedding
    document = _build_document_text(current_meta) or current_meta.get("artifact_name_en", "Unknown Artifact")
    
    # 4. Re-embed the updated text
    embedding = embed_query(document)
    
    # 5. Upsert back to database
    try:
        # Also update artifacts_raw if applicable
        from app.rag.vectorstore import get_supabase_client
        client = get_supabase_client()
        raw_update_data = {}
        if "artifact_name_en" in fields: raw_update_data["artifact_name_en"] = fields["artifact_name_en"]
        if "artifact_name_ar" in fields: raw_update_data["artifact_name_ar"] = fields["artifact_name_ar"]
        if "description_en" in fields: raw_update_data["description_en"] = fields["description_en"]
        if "description_ar" in fields: raw_update_data["description_ar"] = fields["description_ar"]
        if "image_url" in fields: raw_update_data["url"] = fields["image_url"]
        
        if raw_update_data:
            try:
                client.table("artifacts_raw").update(raw_update_data).eq("artifact_id", artifact_id).execute()
            except Exception as e:
                logger.error("Failed to update artifacts_raw: %s", e)

        visual_embedding = None
        if "image_url" in fields and fields["image_url"]:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(fields["image_url"], timeout=10.0)
                    if resp.status_code == 200:
                        from app.dinov2 import DinoV2Encoder
                        encoder = DinoV2Encoder.get_instance()
                        visual_embedding = encoder.embed(Image.open(io.BytesIO(resp.content)))
            except Exception as e:
                logger.error("Failed to generate visual embedding on patch: %s", e)

        add_documents(
            ids=[artifact_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[current_meta],
            visual_embeddings=[visual_embedding] if visual_embedding else None,
        )
    except Exception as exc:
        logger.exception("Failed to patch and re-embed artifact %s", artifact_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to update artifact: {exc}",
        ) from exc

    return _metadata_to_detail(artifact_id, current_meta)


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
