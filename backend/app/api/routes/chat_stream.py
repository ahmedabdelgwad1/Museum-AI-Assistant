"""
Streaming chat endpoint — POST /chat/stream (SSE token streaming).
Fast transcription endpoint — POST /transcribe (STT only).
"""

import asyncio
import base64
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.graph.nodes import rewrite_query, retrieve_and_grade, generate_answer_stream
from app.graph.state import GraphState
from app.models import ChatRequest
from app.voice.stt import transcribe_audio
from app.voice.tts import text_to_speech
from app.utils.language import detect_language

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


# ---------------------------------------------------------------------------
# Helper: run the RAG pipeline up to (not including) the generator
# ---------------------------------------------------------------------------

def _run_rag_pre_generate(
    query: str,
    language: str = "en",
    conversation_history: list[dict] | None = None,
) -> GraphState:
    """
    Runs the rewriter and retriever nodes synchronously and returns the
    state ready for streaming generation.  These two steps are fast
    (< 1 s combined) so blocking is acceptable.
    """
    state: GraphState = {
        "original_query": query,
        "rewritten_query": "",
        "language": language,
        "retrieved_docs": [],
        "relevance_score": 0.0,
        "generation": "",
        "rewrite_count": 0,
        "conversation_history": conversation_history or [],
    }

    # Node 1 — rewrite query (may retry up to max_rewrite_attempts times)
    state = rewrite_query(state)

    # Node 2 — retrieve + grade relevance
    state = retrieve_and_grade(state)

    # If relevance is too low and rewrites remain, do one more cycle
    from app.config import settings
    if state["relevance_score"] < settings.relevance_threshold and state["rewrite_count"] < settings.max_rewrite_attempts:
        state = rewrite_query(state)
        state = retrieve_and_grade(state)

    return state


# ---------------------------------------------------------------------------
# SSE token stream generator
# ---------------------------------------------------------------------------

async def _sse_stream(
    query: str,
    language: str,
    conversation_history: list[dict] | None,
    artifact_hint: str | None,
) -> AsyncGenerator[str, None]:
    """
    Full SSE generator:
      1. Run rewriter + retriever (blocking but fast)
      2. Stream LLM tokens → send as SSE token events
      3. Generate TTS on accumulated text → send as SSE done event
    """
    full_query = f"{query}\n\n{artifact_hint}" if artifact_hint else query

    # Step 1 — rewrite + retrieve (run in thread to avoid blocking the event loop)
    loop = asyncio.get_event_loop()
    try:
        state = await loop.run_in_executor(
            None,
            lambda: _run_rag_pre_generate(full_query, language, conversation_history),
        )
    except Exception as exc:
        logger.exception("Pre-generate RAG failed: %s", exc)
        error_msg = "عذرًا، حدث خطأ أثناء البحث." if language == "ar" else "Sorry, an error occurred during retrieval."
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        return

    # Step 2 — stream LLM tokens
    accumulated = ""
    try:
        token_gen = generate_answer_stream(state)
        for token in token_gen:
            if token:
                accumulated += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                # Tiny sleep to let the event loop breathe and flush to client
                await asyncio.sleep(0)
    except Exception as exc:
        logger.exception("Streaming generation failed: %s", exc)
        error_token = "عذرًا، حدث خطأ." if language == "ar" else "Sorry, an error occurred."
        yield f"data: {json.dumps({'type': 'error', 'content': error_token})}\n\n"
        return

    # Step 3 — TTS on the full accumulated text
    audio_b64: str | None = None
    if accumulated.strip():
        try:
            audio_bytes = await text_to_speech(accumulated, language)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as exc:
            logger.error("TTS failed in stream: %s", exc)

    yield f"data: {json.dumps({'type': 'done', 'audio_base64': audio_b64})}\n\n"


# ---------------------------------------------------------------------------
# POST /chat/stream
# ---------------------------------------------------------------------------

@router.post("/chat/stream", summary="Streaming text chat (SSE) — LLM tokens pushed in real-time")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Accepts the same ``ChatRequest`` body as ``POST /chat`` but responds with
    **Server-Sent Events** so LLM tokens arrive at the browser as they are
    generated.

    SSE event format:
    ``data: {"type": "token",  "content": "..."}``  — one per LLM token
    ``data: {"type": "done",   "audio_base64": "..."}``  — final event
    ``data: {"type": "error",  "content": "..."}``  — on failure
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty.",
        )

    # Detect language — fallback to request.language if detection is uncertain
    detected = detect_language(request.query)
    lang = detected if detected in {"ar", "en"} else (request.language or "en")

    return StreamingResponse(
        _sse_stream(
            query=request.query,
            language=lang,
            conversation_history=request.conversation_history,
            artifact_hint=None,  # artifact hint is baked into query by the frontend
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
        },
    )


# ---------------------------------------------------------------------------
# POST /transcribe  — STT only, returns transcript immediately
# ---------------------------------------------------------------------------

ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mpeg", "audio/mp3", "audio/webm",
    "audio/ogg", "application/octet-stream",
}


@router.post("/transcribe", summary="Speech-to-Text only — returns transcript without RAG/TTS")
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = Form(None),
):
    """
    Accept an audio file and return the Whisper transcript immediately.
    Use this as the first step of the two-step voice flow:
    1. ``POST /transcribe`` → transcript (fast)
    2. ``POST /chat/stream`` → SSE token stream
    """
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES and not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type: {content_type}.",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    logger.info("Transcribe request: filename=%s, size=%d bytes", file.filename, len(audio_bytes))

    try:
        transcript = await transcribe_audio(
            audio_bytes,
            filename=file.filename or "audio.wav",
            language=language,  # Pass the language from the UI to prevent Whisper hallucination
        )
    except Exception as exc:
        logger.exception("STT failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech transcription failed: {str(exc)}",
        )

    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not transcribe audio. Please speak clearly.",
        )

    # Detect language from transcript
    detected = detect_language(transcript)
    lang = detected if detected in {"ar", "en"} else (language or "ar")

    logger.info("Transcript: %s | lang=%s", transcript[:120], lang)

    return {"transcript": transcript, "language": lang}
