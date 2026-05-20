"""Pydantic request/response models."""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Artifact models
# ---------------------------------------------------------------------------

class ArtifactBase(BaseModel):
    artifact_id: str
    artifact_name_en: str
    artifact_name_ar: str
    category_en: Optional[str] = None
    category_ar: Optional[str] = None
    hall_en: Optional[str] = None
    hall_ar: Optional[str] = None
    discovery_site_en: Optional[str] = None
    discovery_site_ar: Optional[str] = None
    section_name_en: Optional[str] = None
    section_name_ar: Optional[str] = None
    section_number: Optional[str] = None
    link: Optional[str] = None


class ArtifactDetail(ArtifactBase):
    description_en: Optional[str] = None
    description_ar: Optional[str] = None


class ArtifactCreateRequest(BaseModel):
    artifact_name_en: str
    artifact_name_ar: Optional[str] = None
    description_en: Optional[str] = None
    description_ar: Optional[str] = None
    category_en: Optional[str] = None
    category_ar: Optional[str] = None
    hall_en: Optional[str] = None
    hall_ar: Optional[str] = None
    discovery_site_en: Optional[str] = None
    discovery_site_ar: Optional[str] = None
    section_name_en: Optional[str] = None
    section_name_ar: Optional[str] = None
    section_number: Optional[str] = None
    link: Optional[str] = None
    image_url: Optional[str] = None


class ArtifactListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    artifacts: List[ArtifactBase]


# ---------------------------------------------------------------------------
# Chat models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query in Arabic or English")
    language: Optional[str] = Field(
        default="ar",
        description="Language override ('ar' or 'en'). Auto-detected if not provided.",
    )
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation turns for context",
    )


class ArtifactReference(BaseModel):
    artifact_name_en: str
    artifact_name_ar: str
    hall_en: Optional[str] = None
    link: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    language: str
    artifact_references: List[ArtifactReference] = Field(default_factory=list)
    pipeline: str = "corrective_rag"
    rewrite_count: int = 0
    audio_base64: Optional[str] = None


# ---------------------------------------------------------------------------
# Voice models
# ---------------------------------------------------------------------------

class VoiceResponse(BaseModel):
    transcript: str
    response_text: str
    language: str
    audio_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Search models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    hall_filter: Optional[str] = None
    category_filter: Optional[str] = None
    discovery_site_filter: Optional[str] = None


class SearchResult(ArtifactBase):
    relevance_score: float
    description_excerpt: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_found: int


# ---------------------------------------------------------------------------
# Health check model
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]
