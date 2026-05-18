"""Edge TTS Text-to-Speech module."""

import logging
import asyncio
import io

import edge_tts

logger = logging.getLogger(__name__)

# Voice mapping by language
VOICE_MAP = {
    "ar": "ar-EG-SalmaNeural",
    "en": "en-US-JennyNeural",
}


async def text_to_speech(text: str, language: str) -> bytes:
    """
    Convert text to speech using Edge TTS.

    Args:
        text: The text to synthesize.
        language: Language code ('ar' or 'en').

    Returns:
        MP3 audio bytes.
    """
    voice = VOICE_MAP.get(language, VOICE_MAP["en"])
    logger.info("TTS: voice=%s, text_length=%d", voice, len(text))

    communicate = edge_tts.Communicate(text, voice)
    audio_chunks: list[bytes] = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("TTS produced no audio output.")

    audio_bytes = b"".join(audio_chunks)
    logger.info("TTS complete: %d bytes of audio generated.", len(audio_bytes))
    return audio_bytes


def run_tts_sync(text: str, language: str) -> bytes:
    """Synchronous wrapper for text_to_speech (useful in non-async contexts)."""
    return asyncio.run(text_to_speech(text, language))
