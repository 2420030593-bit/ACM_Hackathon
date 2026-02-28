"""
Translation Service – Language detection and translation.
Supports: English, Hindi, Telugu, Japanese, French.
Uses Ollama for translation when available, offline dictionary fallback.
"""
import re
import logging
import httpx
from config import SUPPORTED_LANGUAGES, OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("aura.translation")

# ── Language Detection Patterns ──
LANG_PATTERNS = {
    "hi": re.compile(r"[\u0900-\u097F]"),  # Devanagari
    "te": re.compile(r"[\u0C00-\u0C7F]"),  # Telugu
    "ja": re.compile(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]"),  # Japanese
    "fr": re.compile(r"\b(bonjour|merci|oui|non|s'il vous plaît|je|nous|très)\b", re.I),
}

# ── Offline Translation Dictionary ──
OFFLINE_TRANSLATIONS = {
    "en_ja": {
        "hello": "こんにちは",
        "hi": "こんにちは",
        "good morning": "おはようございます",
        "good evening": "こんばんは",
        "thank you": "ありがとうございます",
        "thanks": "ありがとう",
        "yes": "はい",
        "no": "いいえ",
        "please": "お願いします",
        "sorry": "ごめんなさい",
        "excuse me": "すみません",
        "goodbye": "さようなら",
        "how are you": "お元気ですか",
        "how are you today": "今日はお元気ですか",
        "hello, how are you today?": "こんにちは、今日はお元気ですか？",
        "i need help": "助けが必要です",
        "where is the hotel": "ホテルはどこですか",
        "where is the airport": "空港はどこですか",
        "how much": "いくらですか",
        "i don't understand": "わかりません",
        "do you speak english": "英語を話しますか",
        "water": "水",
        "food": "食べ物",
        "taxi": "タクシー",
        "train": "電車",
        "hotel": "ホテル",
        "airport": "空港",
        "restaurant": "レストラン",
        "hospital": "病院",
        "police": "警察",
        "help": "助けて",
        "emergency": "緊急",
        "one": "一",
        "two": "二",
        "three": "三",
        "book a flight": "フライトを予約する",
        "book a hotel": "ホテルを予約する",
    },
    "en_hi": {
        "hello": "नमस्ते",
        "hi": "नमस्ते",
        "good morning": "सुप्रभात",
        "good evening": "शुभ संध्या",
        "thank you": "धन्यवाद",
        "thanks": "शुक्रिया",
        "yes": "हाँ",
        "no": "नहीं",
        "please": "कृपया",
        "sorry": "माफ़ कीजिए",
        "goodbye": "अलविदा",
        "how are you": "आप कैसे हैं",
        "how are you today": "आज आप कैसे हैं",
        "hello, how are you today?": "नमस्ते, आज आप कैसे हैं?",
        "i need help": "मुझे मदद चाहिए",
        "where is the hotel": "होटल कहाँ है",
        "how much": "कितना है",
        "water": "पानी",
        "food": "खाना",
        "taxi": "टैक्सी",
        "hotel": "होटल",
        "airport": "हवाई अड्डा",
        "restaurant": "रेस्तरां",
        "hospital": "अस्पताल",
        "police": "पुलिस",
        "help": "मदद",
        "emergency": "आपातकाल",
        "book a flight": "उड़ान बुक करें",
        "book a hotel": "होटल बुक करें",
    },
    "en_fr": {
        "hello": "Bonjour",
        "hi": "Salut",
        "good morning": "Bonjour",
        "good evening": "Bonsoir",
        "thank you": "Merci",
        "thanks": "Merci",
        "yes": "Oui",
        "no": "Non",
        "please": "S'il vous plaît",
        "sorry": "Pardon",
        "goodbye": "Au revoir",
        "how are you": "Comment allez-vous",
        "how are you today": "Comment allez-vous aujourd'hui",
        "hello, how are you today?": "Bonjour, comment allez-vous aujourd'hui ?",
        "i need help": "J'ai besoin d'aide",
        "where is the hotel": "Où est l'hôtel",
        "how much": "Combien",
        "water": "Eau",
        "food": "Nourriture",
        "taxi": "Taxi",
        "hotel": "Hôtel",
        "airport": "Aéroport",
        "restaurant": "Restaurant",
        "hospital": "Hôpital",
        "police": "Police",
        "help": "Aide",
        "emergency": "Urgence",
        "book a flight": "Réserver un vol",
        "book a hotel": "Réserver un hôtel",
    },
    "en_te": {
        "hello": "హలో",
        "hi": "హాయ్",
        "good morning": "శుభోదయం",
        "thank you": "ధన్యవాదాలు",
        "yes": "అవును",
        "no": "కాదు",
        "please": "దయచేసి",
        "sorry": "క్షమించండి",
        "goodbye": "వీడ్కోలు",
        "how are you": "మీరు ఎలా ఉన్నారు",
        "hello, how are you today?": "హలో, మీరు ఈ రోజు ఎలా ఉన్నారు?",
        "help": "సహాయం",
        "water": "నీరు",
        "food": "ఆహారం",
        "hotel": "హోటల్",
        "airport": "విమానాశ్రయం",
        "hospital": "ఆసుపత్రి",
        "police": "పోలీసు",
        "emergency": "అత్యవసరం",
        "book a flight": "ఫ్లైట్ బుక్ చేయండి",
    },
}


def detect_language(text: str) -> dict:
    """Detect the language of input text."""
    for lang_code, pattern in LANG_PATTERNS.items():
        if pattern.search(text):
            return {
                "lang_code": lang_code,
                "lang_name": SUPPORTED_LANGUAGES.get(lang_code, "Unknown"),
                "confidence": 0.8
            }
    return {"lang_code": "en", "lang_name": "English", "confidence": 0.9}


def _offline_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Try to translate using the offline dictionary."""
    key = f"{source_lang}_{target_lang}"
    reverse_key = f"{target_lang}_{source_lang}"

    # Direct lookup - normalize text
    dictionary = OFFLINE_TRANSLATIONS.get(key, {})
    lower_text = text.lower().strip().strip('"\'').rstrip("?!.,;: ").lstrip()
    if lower_text in dictionary:
        return dictionary[lower_text]
    # Try with punctuation
    if (lower_text + "?") in dictionary:
        return dictionary[lower_text + "?"]

    # Reverse lookup (e.g. ja→en)
    reverse_dict = OFFLINE_TRANSLATIONS.get(reverse_key, {})
    for eng, translated in reverse_dict.items():
        if translated == text.strip() or eng == lower_text:
            return eng if key.startswith(target_lang) else translated

    # Token-by-token fallback
    words = lower_text.split()
    translated_words = []
    any_translated = False
    for w in words:
        clean = w.strip(",.!?;:")
        if clean in dictionary:
            translated_words.append(dictionary[clean])
            any_translated = True
        else:
            translated_words.append(w)

    if any_translated:
        return " ".join(translated_words)

    return ""


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text using Ollama LLM with offline dictionary fallback."""
    if source_lang == target_lang:
        return text

    source_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)

    # 1. Try offline dictionary first for fast, exact matches (bypasses LLM hallucination for basic phrases)
    offline = _offline_translate(text, source_lang, target_lang)
    if offline:
        logger.info(f"Offline translation {source_lang}->{target_lang}: {offline[:40]}")
        return offline

    # 2. Try Ollama for complex sentences
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"Translate the following from {source_name} to {target_name}. Return ONLY the translation, nothing else:\n\n{text}",
                    "stream": False,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("response", "").strip()
                if translated:
                    logger.info(f"Ollama translation {source_lang}->{target_lang}: {text[:30]}...")
                    return translated
    except Exception as e:
        logger.warning(f"Translation via Ollama failed: {e}")

    # Final fallback: return original with note
    logger.info("No translation available, returning original")
    return f"[{target_name}] {text}"


async def translate_to_english(text: str, source_lang: str) -> str:
    """Convenience: translate any language to English."""
    return await translate_text(text, source_lang, "en")


async def translate_from_english(text: str, target_lang: str) -> str:
    """Convenience: translate English to target language."""
    return await translate_text(text, "en", target_lang)
