"""
AURA – Intent Detection Service
Simple keyword-based intent detection with multi-intent support.
"""

import logging

logger = logging.getLogger("aura.intent")

# ──────────────────────────────────────────────
#  Intent Rules  (keyword → intent tag)
# ──────────────────────────────────────────────
INTENT_RULES = [
    {
        "intent": "taxi_booking",
        "keywords": ["taxi", "cab", "ride", "uber", "car", "pickup", "drop"],
        "label": "Taxi Booking",
    },
    {
        "intent": "tour_booking",
        "keywords": ["tour", "sightseeing", "city tour", "travel", "explore", "trip"],
        "label": "Tour Booking",
    },
    {
        "intent": "restaurant_booking",
        "keywords": ["restaurant", "food", "dinner", "lunch", "breakfast", "table", "eat", "dining", "cuisine"],
        "label": "Restaurant Booking",
    },
    {
        "intent": "hotel_booking",
        "keywords": ["hotel", "room", "stay", "check-in", "accommodation", "suite", "lodge", "resort", "inn"],
        "label": "Hotel Booking",
    },
    {
        "intent": "spa_booking",
        "keywords": ["spa", "massage", "wellness", "relaxation", "sauna"],
        "label": "Spa Booking",
    },
]


def detect_intent(text: str) -> list[dict]:
    """
    Detect one or more intents from the user's text (already in English).
    Supports multiple intents in a single sentence.

    Returns:
        A list of matched intent dicts. Each dict has 'intent' and 'label'.
        Falls back to a 'general_help' intent if nothing matches.
    """
    text_lower = text.lower()
    matched = []

    for rule in INTENT_RULES:
        for kw in rule["keywords"]:
            if kw in text_lower:
                matched.append({"intent": rule["intent"], "label": rule["label"]})
                logger.info("Matched intent: %s (keyword: '%s')", rule["intent"], kw)
                break  # avoid duplicate match from same rule

    if not matched:
        logger.info("No specific intent matched — returning general help.")
        matched.append({"intent": "general_help", "label": "General Help"})

    return matched
