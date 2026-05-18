"""Language detection utility."""

import logging
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    Detect language of the input text.

    Returns 'ar' for Arabic, 'en' for English, defaults to 'en' on failure.
    """
    if not text or not text.strip():
        return "en"

    # Quick heuristic: check for Arabic Unicode range (U+0600–U+06FF)
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    if arabic_chars > len(text) * 0.2:
        return "ar"

    try:
        lang = detect(text)
        if lang == "ar":
            return "ar"
        return "en"
    except LangDetectException:
        logger.warning("Language detection failed, defaulting to 'en'")
        return "en"
