"""Voice endpoint — POST /voice (STT → Corrective RAG → TTS)."""

import io
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.graph.graph import rag_graph
from app.graph.state import GraphState
from app.voice.stt import transcribe_audio
from app.voice.tts import text_to_speech
from app.utils.language import detect_language

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/webm",
    "audio/ogg",
    "application/octet-stream",
}


async def run_rag(query: str, language: str = "ar", conversation_history: list[dict] | None = None) -> dict:
    """Invoke the LangGraph Corrective RAG graph and return normalised result."""
    initial_state: GraphState = {
        "original_query": query,
        "rewritten_query": "",
        "language": language,
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
    }


from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

@router.post("", summary="Voice query — STT → Corrective RAG → TTS")
async def voice_query(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    conversation_history: str = Form(None)
) -> JSONResponse:
    """
    Accept an audio file (WAV / MP3), run the full voice pipeline, and return
    an MP3 audio response.

    Pipeline:
    1. **Groq Whisper** — transcribes the audio
    2. **LangGraph Corrective RAG** — rewrite → retrieve+grade → generate
    3. **Edge TTS** — synthesises the answer in the detected language
    """
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES and not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type: {content_type}. Use WAV or MP3.",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    logger.info(
        "Voice request: filename=%s, size=%d bytes", file.filename, len(audio_bytes)
    )

    # Step 1 — Speech-to-Text
    try:
        transcript = await transcribe_audio(
            audio_bytes,
            filename=file.filename or "audio.wav",
            language=language,
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

    logger.info("Transcript: %s", transcript[:120])

    # Step 2 — Corrective RAG
    history_list = []
    if conversation_history:
        import json
        try:
            history_list = json.loads(conversation_history)
        except Exception as e:
            logger.warning("Failed to parse conversation history in voice query: %s", e)

    # Detect language from the transcript itself (most reliable signal)
    detected_lang = detect_language(transcript)
    if detected_lang not in {"ar", "en"} and language in {"ar", "en"}:
        detected_lang = language
    logger.info("Detected language from transcript: %s", detected_lang)

    try:
        rag_result = await run_rag(query=transcript, language=detected_lang, conversation_history=history_list)
    except Exception as exc:
        logger.exception("RAG graph failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG pipeline failed: {str(exc)}",
        )

    response_text = rag_result["answer"]
    language = rag_result["language"]

    # Step 3 — Text-to-Speech
    try:
        audio_response = await text_to_speech(response_text, language)
    except Exception as exc:
        logger.exception("TTS failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis failed: {str(exc)}",
        )

    import base64
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content={
            "transcript": transcript,
            "response": response_text,
            "language": language,
            "rewrite_count": rag_result.get("rewrite_count", 0),
            "audio_base64": base64.b64encode(audio_response).decode("utf-8"),
        }
    )
