"""Groq Whisper Speech-to-Text module."""

import logging
import os
import tempfile
from pathlib import Path

from typing import Optional
from groq import Groq
from app.config import settings
from app.utils.language import detect_language

logger = logging.getLogger(__name__)

_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """Return singleton Groq client."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


from app.voice.artifact_names import get_artifact_keywords, correct_artifact_names_with_llm

async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language: Optional[str] = None,
    use_correction: bool = True
) -> str:
    """
    Transcribe audio bytes using Groq Whisper.

    Args:
        audio_bytes: Raw audio file bytes (WAV or MP3).
        filename: Original filename (used for MIME type detection).
        language: Language code ('ar' or 'en') to improve transcription.
        use_correction: Whether to apply LLM artifact name correction.

    Returns:
        Transcribed text string.
    """
    client = get_groq_client()
    suffix = Path(filename).suffix or ".wav"

    # Write to a temp file — Groq SDK needs a file-like object
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Build prompt hint
        prompt_hint = ""
        if language:
            prompt_hint = get_artifact_keywords(language)

        # Prepare kwargs
        kwargs = {
            "model": settings.stt_model,
            "response_format": "text",
            "temperature": 0.0,
        }
        
        if language:
            kwargs["language"] = language
        if prompt_hint:
            # Whisper prompt should be relatively short (usually < 224 tokens)
            # We truncate to ~1000 chars to be safe.
            kwargs["prompt"] = prompt_hint[:1000]

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=f,
                **kwargs
            )
            
        transcribed_text = str(transcription).strip()
        logger.info("Transcription successful: %s chars", len(transcribed_text))
        
        if use_correction and transcribed_text:
            detected_lang = language or detect_language(transcribed_text)
            logger.info("Applying LLM artifact name correction (lang: %s)...", detected_lang)
            corrected_text = correct_artifact_names_with_llm(transcribed_text, detected_lang)
            return corrected_text
            
        return transcribed_text
    except Exception as exc:
        logger.error("STT error: %s", exc)
        raise
    finally:
        os.unlink(tmp_path)
