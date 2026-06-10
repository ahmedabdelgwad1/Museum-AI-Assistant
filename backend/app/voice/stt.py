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
    """Return singleton Groq client using the first configured API key."""
    global _groq_client
    if _groq_client is None:
        keys = settings.groq_api_keys
        _groq_client = Groq(api_key=keys[0] if keys else settings.groq_api_key)
    return _groq_client


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: Optional[str] = None,
    use_correction: bool = False,
) -> str:
    """
    Transcribe audio bytes using Groq Whisper.

    Args:
        audio_bytes:    Raw audio bytes (WebM / WAV / MP3 / OGG / MP4).
        filename:       Original filename — determines the file extension sent
                        to the Groq API (must match the actual audio format).
        language:       Language hint ('ar' or 'en'). Passed to Whisper so it
                        doesn't have to auto-detect, which saves ~0.5 s.
        use_correction: Whether to run an extra LLM call to fix artifact name
                        spellings. Disabled by default — adds ~2 s latency and
                        was the root cause of Whisper hallucinations because the
                        correction prompt contained all 96 artifact names, which
                        Whisper used as a text seed when audio was unclear.

    Returns:
        Transcribed text string.
    """
    client = get_groq_client()

    # Use the original file extension so Groq knows the codec.
    suffix = Path(filename).suffix.lower() or ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        kwargs: dict = {
            "model": settings.stt_model,
            "response_format": "text",
            "temperature": 0.0,
        }

        # ── Language & short domain prompt ──────────────────────────────────
        # We provide a SHORT prompt (5-7 words) so Whisper knows the domain.
        # IMPORTANT: Long prompts (e.g. 96 artifact names) cause Whisper to
        # hallucinate that text when audio is unclear or silent.  Never use
        # get_artifact_keywords() as a Whisper prompt.
        if language == "ar":
            kwargs["language"] = "ar"
            # Add specific keywords to guide Whisper away from misspellings
            # e.g., 'الصالة' instead of 'الأصالة'
            kwargs["prompt"] = "متحف، قطعة أثرية، الصالة الإسلامية، مصرية قديمة"
        elif language == "en":
            kwargs["language"] = "en"
            kwargs["prompt"] = "museum, artifact, ancient Egyptian, Islamic"

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(file=f, **kwargs)

        transcribed_text = str(transcription).strip()
        logger.info(
            "Whisper transcription: %d chars | preview: %s",
            len(transcribed_text),
            transcribed_text[:100],
        )

        # Optional LLM correction (disabled by default — see docstring)
        if use_correction and transcribed_text:
            from app.voice.artifact_names import correct_artifact_names_with_llm
            detected_lang = language or detect_language(transcribed_text)
            logger.info("Applying LLM artifact name correction (lang=%s)...", detected_lang)
            return correct_artifact_names_with_llm(transcribed_text, detected_lang)

        return transcribed_text

    except Exception as exc:
        logger.error("STT (Whisper) error: %s", exc)
        raise
    finally:
        os.unlink(tmp_path)
