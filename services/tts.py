"""
AURA – Text-to-Speech Service
Uses Google TTS (gTTS) for natural-sounding voice output.
Strips emojis and cleans text before generating speech.
"""

import logging
import re
import base64
import pyttsx3
import tempfile
import os

logger = logging.getLogger("aura.tts")

# Initialize pyttsx3 engine
try:
    _engine = pyttsx3.init()
except Exception as e:
    logger.error("Failed to initialize pyttsx3: %s", e)
    _engine = None

# ── Emoji & special character stripper ─────────
# Matches most emoji Unicode ranges
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0000200D"             # zero width joiner
    "\U00000023\U0000FE0F\U000020E3"  # keycap
    "]+",
    flags=re.UNICODE,
)

# gTTS language code mapping (some codes need adjustment for gTTS)
_GTTS_LANG_MAP = {
    "zh-CN": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-TW": "zh-TW",
    "en": "en",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "hi": "hi",
    "ja": "ja",
    "ko": "ko",
    "ar": "ar",
    "pt": "pt",
    "ru": "ru",
    "it": "it",
    "ta": "ta",
    "te": "te",
    "bn": "bn",
    "nl": "nl",
    "tr": "tr",
    "th": "th",
    "vi": "vi",
    "pl": "pl",
}


def clean_text_for_speech(text: str) -> str:
    """
    Remove emojis, special symbols, and excessive punctuation
    from text to produce clean spoken output.
    """
    # Remove emojis
    cleaned = _EMOJI_PATTERN.sub("", text)

    # Remove leftover pipe separators
    cleaned = cleaned.replace(" | ", ". ")

    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove leading/trailing punctuation noise
    cleaned = cleaned.strip("·•|—–- ")

    return cleaned


def generate_speech_audio(text: str, lang_code: str = "en") -> str | None:
    """
    Generate speech audio from text using pyttsx3 (Offline).
    """
    cleaned = clean_text_for_speech(text)

    if not cleaned or _engine is None:
        return None

    try:
        logger.info("Generating offline TTS audio: '%s'", cleaned[:80])

        # pyttsx3 saves to file. We read it back as base64.
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        _engine.save_to_file(cleaned, tmp_path)
        _engine.runAndWait()

        with open(tmp_path, "rb") as audio_file:
            audio_b64 = base64.b64encode(audio_file.read()).decode("utf-8")

        os.remove(tmp_path)
        logger.info("Offline TTS audio generated successfully")
        return audio_b64

    except Exception as e:
        logger.warning("Offline TTS generation failed (%s).", e)
        return None
