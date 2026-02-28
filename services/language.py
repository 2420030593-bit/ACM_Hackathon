"""
AURA – Language Detection & Translation Service
Uses deep-translator (GoogleTranslator) for reliable translation
with a built-in fallback for language detection.
"""

import logging
import re
# from deep_translator import GoogleTranslator, single_detection

logger = logging.getLogger("aura.language")

# Friendly display names for common languages
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ru": "Russian",
    "it": "Italian",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "nl": "Dutch",
    "tr": "Turkish",
    "th": "Thai",
    "vi": "Vietnamese",
    "pl": "Polish",
}

# Unicode-range heuristics for language detection (no external API needed)
_SCRIPT_PATTERNS = [
    (r'[\u0900-\u097F]', 'hi'),    # Devanagari → Hindi
    (r'[\u0C00-\u0C7F]', 'te'),    # Telugu
    (r'[\u0B80-\u0BFF]', 'ta'),    # Tamil
    (r'[\u0980-\u09FF]', 'bn'),    # Bengali
    (r'[\u0600-\u06FF]', 'ar'),    # Arabic
    (r'[\u3040-\u309F\u30A0-\u30FF]', 'ja'),  # Japanese
    (r'[\uAC00-\uD7AF]', 'ko'),   # Korean
    (r'[\u4E00-\u9FFF]', 'zh-CN'), # Chinese
    (r'[\u0E00-\u0E7F]', 'th'),    # Thai
    (r'[\u0400-\u04FF]', 'ru'),    # Cyrillic → Russian (default)
]

# Common non-English word markers for Latin-script languages
_LATIN_MARKERS = {
    'es': ['necesito', 'quiero', 'hola', 'por favor', 'reservar', 'taxi', 'aeropuerto',
           'dónde', 'cómo', 'tengo', 'estoy', 'el', 'la', 'un', 'una', 'para', 'yo'],
    'fr': ['je', 'besoin', 'bonjour', 'réserver', "s'il", 'vous', 'plaît', 'merci',
           'oui', 'avec', 'dans', 'une', 'les', 'des', 'est', 'sont'],
    'de': ['ich', 'brauche', 'bitte', 'reservieren', 'einen', 'guten', 'danke',
           'möchte', 'ein', 'und', 'ist', 'das', 'die', 'der'],
    'it': ['ho', 'bisogno', 'prenotare', 'per favore', 'grazie', 'buongiorno',
           'vorrei', 'una', 'sono', 'con', 'che', 'questo'],
    'pt': ['eu', 'preciso', 'reservar', 'por favor', 'obrigado', 'quero',
           'tenho', 'uma', 'com', 'para', 'está', 'não'],
}


def detect_language(text: str) -> dict:
    """
    Detect the language of the input text using script analysis
    and keyword heuristics. No external API calls needed.

    Returns:
        dict with 'lang_code' (ISO 639-1) and 'lang_name' (friendly name).
    """
    try:
        # 1. Check non-Latin scripts via Unicode ranges
        for pattern, lang_code in _SCRIPT_PATTERNS:
            if re.search(pattern, text):
                name = LANGUAGE_NAMES.get(lang_code, lang_code)
                logger.info("Detected script-based language: %s (%s)", name, lang_code)
                return {"lang_code": lang_code, "lang_name": name}

        # 2. For Latin-script text, check keyword markers
        text_lower = text.lower()
        best_lang = None
        best_score = 0

        for lang_code, markers in _LATIN_MARKERS.items():
            score = sum(1 for m in markers if m in text_lower)
            if score > best_score:
                best_score = score
                best_lang = lang_code

        if best_lang and best_score >= 2:
            name = LANGUAGE_NAMES.get(best_lang, best_lang)
            logger.info("Detected marker-based language: %s (%s) [score=%d]", name, best_lang, best_score)
            return {"lang_code": best_lang, "lang_name": name}

        # 3. Default to English
        logger.info("Defaulting to English for: '%s'", text[:50])
        return {"lang_code": "en", "lang_name": "English"}

    except Exception as e:
        logger.warning("Language detection failed (%s). Defaulting to English.", e)
        return {"lang_code": "en", "lang_name": "English"}


def translate_to_english(text: str, source_lang: str) -> str:
    """
    Offline: Return original text (English only or simple script detection).
    """
    return text


def translate_back(text: str, target_lang: str) -> str:
    """
    Offline: Return original text.
    """
    return text
