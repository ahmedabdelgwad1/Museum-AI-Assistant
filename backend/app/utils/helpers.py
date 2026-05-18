"""Misc helper utilities."""

import re
import unicodedata
from typing import Optional


def clean_text(text: str) -> str:
    """Normalize and clean text for embedding or display."""
    if not text:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFC", text)
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate_text(text: str, max_chars: int = 1000) -> str:
    """Truncate text to max_chars, preserving word boundaries."""
    if not text or len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def build_artifact_id(row_index: int, artifact_name_en: str) -> str:
    """Build a stable artifact ID from index and name."""
    slug = re.sub(r"[^a-z0-9]+", "_", artifact_name_en.lower())[:40]
    return f"artifact_{row_index:04d}_{slug}"


def excerpt(text: str, max_chars: int = 200) -> Optional[str]:
    """Return a short excerpt of text."""
    if not text:
        return None
    cleaned = clean_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rsplit(" ", 1)[0] + "..."
