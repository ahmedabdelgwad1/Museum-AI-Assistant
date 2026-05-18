"""Utility for injecting artifact names into STT models to improve accuracy."""

import difflib
import logging
from typing import List, Optional

from app.rag.vectorstore import get_collection
from app.config import settings
from groq import Groq

logger = logging.getLogger(__name__)

# Cache for artifact keywords
_KEYWORDS_EN: Optional[str] = None
_KEYWORDS_AR: Optional[str] = None
_ALL_NAMES_EN: List[str] = []
_ALL_NAMES_AR: List[str] = []


def _load_names() -> None:
    """Load all artifact names from ChromaDB into memory."""
    global _KEYWORDS_EN, _KEYWORDS_AR, _ALL_NAMES_EN, _ALL_NAMES_AR
    if _KEYWORDS_EN is not None:
        return

    try:
        collection = get_collection()
        # Fetch all metadata
        result = collection.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])
        
        en_names = set()
        ar_names = set()
        
        for meta in metadatas:
            if not meta:
                continue
            name_en = meta.get("artifact_name_en")
            name_ar = meta.get("artifact_name_ar")
            
            if name_en:
                en_names.add(str(name_en).strip())
            if name_ar:
                ar_names.add(str(name_ar).strip())
                
        _ALL_NAMES_EN = list(en_names)
        _ALL_NAMES_AR = list(ar_names)
        
        # Create comma-separated strings for Whisper prompt (max ~200 chars is usually good, but we can pass more)
        # Whisper prompt is limited to 224 tokens, so we'll just pass a joined string.
        _KEYWORDS_EN = ", ".join(_ALL_NAMES_EN)
        _KEYWORDS_AR = ", ".join(_ALL_NAMES_AR)
        
        logger.info("Loaded %d English and %d Arabic artifact names for STT hints.", len(en_names), len(ar_names))
    except Exception as exc:
        logger.error("Failed to load artifact names from ChromaDB: %s", exc)
        _KEYWORDS_EN = ""
        _KEYWORDS_AR = ""


def get_artifact_keywords(language: Optional[str] = None) -> str:
    """Get a comma-separated string of artifact names for the specified language."""
    _load_names()
    
    # Whisper works best when the prompt matches the language
    if language == "ar":
        return _KEYWORDS_AR or ""
    elif language == "en":
        return _KEYWORDS_EN or ""
    else:
        # If language is unknown, return a mix of both
        return f"{_KEYWORDS_AR}, {_KEYWORDS_EN}"


def find_closest_artifact_name(text: str, language: str, threshold: float = 0.7) -> str:
    """
    Find the closest artifact name in the text and potentially replace it.
    This is a simplistic approach; for full correction, LLM is better.
    """
    _load_names()
    names = _ALL_NAMES_AR if language == "ar" else _ALL_NAMES_EN
    
    # Very basic string replacement if a highly similar string exists in the text.
    # In a real scenario, this would tokenize the text and find close matches.
    # For now, we'll just return the text as-is unless we want to do complex n-gram matching.
    return text


def correct_artifact_names_with_llm(text: str, language: str) -> str:
    """
    Use an LLM to correct potentially misspelled artifact names in the transcript.
    """
    if not text.strip():
        return text
        
    try:
        client = Groq(api_key=settings.groq_api_key)
        
        system_prompt = (
            "You are a spell checker for a museum transcription system. "
            "Your ONLY job is to correct misspellings of ancient Egyptian and Greco-Roman artifact names in the text. "
            "Do NOT answer the question. Do NOT add extra words. Just output the corrected text.\n"
        )
        
        if language == "ar":
            system_prompt += f"Known artifact names:\n{get_artifact_keywords('ar')}"
        else:
            system_prompt += f"Known artifact names:\n{get_artifact_keywords('en')}"
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.0,
            max_tokens=200,
        )
        
        corrected = completion.choices[0].message.content or text
        return corrected.strip()
    except Exception as exc:
        logger.error("LLM STT correction failed: %s", exc)
        return text
