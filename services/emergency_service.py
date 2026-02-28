"""
Emergency Service – Embassy lookup, police info, translated messages.
"""
import logging
from config import SUPPORTED_LANGUAGES

logger = logging.getLogger("aura.emergency")

# ── Emergency Database ──
EMBASSY_DATA = {
    "us": {
        "country": "United States",
        "embassies": {
            "in": {"name": "US Embassy New Delhi", "phone": "+91-11-2419-8000", "address": "Shantipath, Chanakyapuri"},
            "jp": {"name": "US Embassy Tokyo", "phone": "+81-3-3224-5000", "address": "1-10-5 Akasaka, Minato-ku"},
            "fr": {"name": "US Embassy Paris", "phone": "+33-1-43-12-22-22", "address": "2 Avenue Gabriel"},
        }
    },
    "in": {
        "country": "India",
        "embassies": {
            "us": {"name": "Indian Embassy Washington", "phone": "+1-202-939-7000", "address": "2107 Massachusetts Ave"},
            "jp": {"name": "Indian Embassy Tokyo", "phone": "+81-3-3262-2391", "address": "2-2-11 Kudan-Minami"},
        }
    },
}

EMERGENCY_NUMBERS = {
    "us": {"police": "911", "medical": "911", "fire": "911"},
    "in": {"police": "100", "medical": "108", "fire": "101"},
    "jp": {"police": "110", "medical": "119", "fire": "119"},
    "fr": {"police": "17", "medical": "15", "fire": "18"},
    "default": {"police": "112", "medical": "112", "fire": "112"},
}

EMERGENCY_PHRASES = {
    "en": {
        "help": "I need help! Please assist me.",
        "lost_passport": "I have lost my passport. I need to contact my embassy.",
        "medical": "I need medical attention. Please call an ambulance.",
        "police": "I need police assistance.",
    },
    "hi": {
        "help": "मुझे मदद चाहिए! कृपया मेरी सहायता करें।",
        "lost_passport": "मेरा पासपोर्ट खो गया है। मुझे अपने दूतावास से संपर्क करना है।",
        "medical": "मुझे चिकित्सा सहायता चाहिए। कृपया एम्बुलेंस बुलाएं।",
        "police": "मुझे पुलिस सहायता चाहिए।",
    },
    "ja": {
        "help": "助けてください！",
        "lost_passport": "パスポートを紛失しました。大使館に連絡する必要があります。",
        "medical": "医療の助けが必要です。救急車を呼んでください。",
        "police": "警察の助けが必要です。",
    },
    "fr": {
        "help": "J'ai besoin d'aide ! Aidez-moi s'il vous plaît.",
        "lost_passport": "J'ai perdu mon passeport. Je dois contacter mon ambassade.",
        "medical": "J'ai besoin de soins médicaux. Appelez une ambulance.",
        "police": "J'ai besoin de l'aide de la police.",
    },
    "te": {
        "help": "నాకు సహాయం కావాలి! దయచేసి నాకు సహాయం చేయండి.",
        "lost_passport": "నా పాస్‌పోర్ట్ పోయింది. నేను నా రాయబార కార్యాలయాన్ని సంప్రదించాలి.",
        "medical": "నాకు వైద్య సహాయం కావాలి. దయచేసి అంబులెన్స్‌ను పిలవండి.",
        "police": "నాకు పోలీసు సహాయం కావాలి.",
    },
}


def get_emergency_info(country_code: str = "in", situation: str = "general") -> dict:
    """Get emergency information for a country."""
    country_code = country_code.lower()
    numbers = EMERGENCY_NUMBERS.get(country_code, EMERGENCY_NUMBERS["default"])

    # Get embassy info
    embassy_info = {}
    for nationality, data in EMBASSY_DATA.items():
        if country_code in data.get("embassies", {}):
            embassy_info[nationality] = data["embassies"][country_code]

    # Get translated phrases for common emergency situations
    phrases = {}
    for lang_code in SUPPORTED_LANGUAGES:
        lang_phrases = EMERGENCY_PHRASES.get(lang_code, EMERGENCY_PHRASES["en"])
        phrases[lang_code] = lang_phrases

    return {
        "country": country_code,
        "emergency_numbers": numbers,
        "embassies": embassy_info,
        "phrases": phrases.get(country_code, phrases.get("en")),
        "all_phrases": phrases,
        "situation": situation,
        "advice": _get_situation_advice(situation),
    }


def _get_situation_advice(situation: str) -> str:
    advice_map = {
        "lost_passport": "1. Contact your embassy immediately\n2. File a police report\n3. Keep copies of your ID\n4. Contact your airline if you have a return flight",
        "medical": "1. Call the local emergency number\n2. Go to the nearest hospital\n3. Keep your insurance information ready\n4. Contact your embassy for assistance",
        "police": "1. Call the local police number\n2. Note down the officer's name and badge number\n3. Keep calm and cooperate\n4. Contact your embassy if needed",
        "general": "1. Stay calm\n2. Contact local emergency services\n3. Reach out to your embassy\n4. Keep important documents safe",
    }
    return advice_map.get(situation, advice_map["general"])
