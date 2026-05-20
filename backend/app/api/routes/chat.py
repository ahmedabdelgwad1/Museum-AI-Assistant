"""Chat endpoint — POST /chat (powered by LangGraph Corrective RAG)."""

import logging
import base64
from fastapi import APIRouter, HTTPException, status

from app.models import ChatRequest, ChatResponse, ArtifactReference
from app.graph.graph import rag_graph
from app.graph.state import GraphState
from app.voice.tts import text_to_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def run_rag(
    query: str,
    language: str | None = None,
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Invoke the LangGraph Corrective RAG graph.

    Initialises the GraphState, calls ``rag_graph.ainvoke``, and returns
    a normalised dict with the answer, language, rewrite count, and docs.
    """
    initial_state: GraphState = {
        "original_query": query,
        "rewritten_query": "",
        "language": language or "en",
        "retrieved_docs": [],
        "relevance_score": 0.0,
        "generation": "",
        "rewrite_count": 0,
        "conversation_history": conversation_history or [],
    }
    result = await rag_graph.ainvoke(initial_state)
    return {
        "answer": result["generation"],
        "language": result["language"],
        "rewrite_count": result["rewrite_count"],
        "retrieved_docs": result["retrieved_docs"],
        "relevance_score": result.get("relevance_score", 0.0),
    }


@router.post("", response_model=ChatResponse, summary="Text chat with Corrective RAG agent")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a text query (Arabic or English) to the museum Corrective RAG pipeline.

    The pipeline:
    1. **Rewriter** — rewrites the query for semantic search & detects language
    2. **Retriever + Grader** — fetches artifacts from Supabase pgvector, LLM-grades relevance
    3. **Generator** — synthesises a bilingual answer citing names, halls, and links

    If relevance is below 0.5 the rewriter is called again (up to 2 retries).
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty.",
        )

    try:
        result = await run_rag(
            query=request.query,
            language=request.language,
            conversation_history=request.conversation_history,
        )
    except Exception as exc:
        logger.exception("Corrective RAG graph error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline failed: {str(exc)}",
        )

    # Convert retrieved docs to ArtifactReference models
    refs = [
        ArtifactReference(
            artifact_name_en=doc.get("artifact_name_en", ""),
            artifact_name_ar=doc.get("artifact_name_ar", ""),
            hall_en=doc.get("hall_en"),
            link=doc.get("link"),
            relevance_score=doc.get("relevance_score"),
        )
        for doc in result["retrieved_docs"]
    ]

    # Generate audio for the response
    audio_base64 = None
    try:
        audio_bytes = await text_to_speech(result["answer"], result["language"])
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        logger.error("TTS generation failed in chat endpoint: %s", exc)
        # We don't fail the request if TTS fails, just return text without audio

    return ChatResponse(
        response=result["answer"],
        language=result["language"],
        artifact_references=refs,
        pipeline="corrective_rag",
        rewrite_count=result["rewrite_count"],
        audio_base64=audio_base64,
    )
