"""
AURA – Booking Simulation & Response Generation
Produces realistic-looking booking confirmations without any real APIs.
Now extracts actual destinations/places from user input.
"""

import logging
import re
import random
from datetime import datetime, timedelta

logger = logging.getLogger("aura.booking")

# ──────────────────────────────────────────────
#  Simulated Data Pools
# ──────────────────────────────────────────────
TAXI_DRIVERS = ["Ravi K.", "Priya S.", "Ahmed Z.", "Carlos M.", "Yuki T."]
TAXI_VEHICLES = ["Toyota Camry (White)", "Honda City (Silver)", "Hyundai Creta (Black)", "Maruti Swift (Blue)"]

TOUR_GUIDES = ["Ananya", "Marco", "Kenji", "Fatima", "Luis"]

RESTAURANT_NAMES = ["The Spice Garden", "Moonlight Bistro", "Saffron & Sage", "The Olive Branch", "Royal Tandoor"]
CUISINE_TYPES = ["North Indian", "Italian", "Pan-Asian", "Continental", "South Indian"]

HOTEL_NAMES = ["The Grand Oasis", "Skyline Suites", "Harbour View Inn", "Palm Crest Resort", "Velvet Stay"]
ROOM_TYPES = ["Deluxe King", "Executive Suite", "Premium Twin", "Studio Apartment"]

SPA_NAMES = ["Tranquil Touch Spa", "Zenith Wellness Center", "Lotus Serenity Spa"]
SPA_TREATMENTS = ["Swedish Massage", "Aromatherapy", "Deep Tissue Therapy", "Hot Stone Massage", "Ayurvedic Abhyanga"]

# Fallback destinations (only used when nothing is extracted)
FALLBACK_DESTINATIONS = ["Airport", "Railway Station", "City Center", "Bus Terminal"]


def _future_time(min_minutes=20, max_minutes=90) -> str:
    """Generate a realistic near-future time string."""
    delta = timedelta(minutes=random.randint(min_minutes, max_minutes))
    future = datetime.now() + delta
    return future.strftime("%I:%M %p")


def _tomorrow() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%A, %d %B %Y")


# ──────────────────────────────────────────────
#  Entity Extraction from User Text
# ──────────────────────────────────────────────

# Words to ignore when extracting locations (common verbs, articles, etc.)
_STOP_WORDS = {
    "i", "me", "my", "need", "want", "book", "get", "please", "can", "you",
    "a", "an", "the", "to", "for", "at", "in", "from", "and", "also",
    "reserve", "find", "take", "give", "make", "do", "go", "going",
    "taxi", "cab", "ride", "car", "uber", "pickup", "drop",
    "tour", "sightseeing", "travel", "explore", "trip", "city",
    "restaurant", "food", "dinner", "lunch", "breakfast", "table", "eat", "dining", "cuisine",
    "hotel", "room", "stay", "check-in", "accommodation", "suite",
    "spa", "massage", "wellness", "relaxation", "sauna",
    "tomorrow", "today", "tonight", "morning", "evening", "afternoon",
    "nice", "good", "best", "nearby", "local", "cheap", "expensive",
    "with", "near", "around", "some", "one", "two", "three", "four", "five",
    "of", "is", "it", "this", "that", "there", "here",
    "would", "like", "could", "should", "will",
    # Price / budget words
    "price", "range", "budget", "rupees", "rs", "inr", "per", "night",
    "rated", "rating", "ratings", "star", "stars", "review", "reviews",
    "under", "below", "above", "between", "less", "more", "than",
    "recommend", "recommended", "top", "highest",
}


def _extract_destination(text: str) -> str | None:
    """
    Extract a destination/place name from the user's English text.
    Uses preposition patterns like 'to X', 'at X', 'near X', 'in X'.

    Examples:
        'I need a taxi to Charminar'          → 'Charminar'
        'Book a taxi to the airport'          → 'the airport'
        'Take me to Golconda Fort'            → 'Golconda Fort'
        'I want a ride to Hitech City'        → 'Hitech City'
        'Restaurant near Tank Bund'           → 'Tank Bund'
        'Hotel in Banjara Hills'              → 'Banjara Hills'
    """
    text_clean = text.strip()

    # Pattern 1: "to <destination>" — most common for taxi/travel
    # Captures everything after "to" until end of clause
    patterns = [
        r'\bto\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
        r'\bnear\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
        r'\bat\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
        r'\bin\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
        r'\bfrom\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
        r'\bfor\s+(.+?)(?:\s*[,.]|\s+and\s+|\s+also\s+|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()

            # Clean up: remove leading stop words
            words = candidate.split()
            cleaned_words = []
            for w in words:
                w_lower = w.lower().strip(".,!?;:")
                if w_lower not in _STOP_WORDS or len(cleaned_words) > 0:
                    if w_lower in _STOP_WORDS and len(cleaned_words) == 0:
                        continue
                    cleaned_words.append(w)

            # Also strip trailing stop words (e.g., "Sitara Grand hotel" → "Sitara Grand")
            while cleaned_words and cleaned_words[-1].lower().strip(".,!?;:") in _STOP_WORDS:
                cleaned_words.pop()

            if cleaned_words:
                result = " ".join(cleaned_words).strip(".,!?;: ")
                # Only return if it looks like a real place (not just "me" or "a")
                # Also skip pure numbers (e.g., "3000" from "price range 2000 to 3000")
                if (len(result) > 1
                        and result.lower() not in _STOP_WORDS
                        and not result.replace(" ", "").isdigit()):
                    logger.info("Extracted destination: '%s'", result)
                    return _title_case(result)

    # Pattern 2: Look for capitalized proper nouns not in stop words
    # This catches cases like "taxi Charminar" without a preposition
    words = text_clean.split()
    proper_nouns = []
    for w in words:
        w_clean = w.strip(".,!?;:")
        if (w_clean and w_clean[0].isupper() and
                w_clean.lower() not in _STOP_WORDS and
                len(w_clean) > 1):
            proper_nouns.append(w_clean)

    # Group consecutive proper nouns (e.g., "Golconda Fort")
    if proper_nouns:
        result = " ".join(proper_nouns)
        logger.info("Extracted destination (proper noun): '%s'", result)
        return result

    return None


def _extract_place_for_intent(text: str, intent: str) -> str | None:
    """
    Extract a relevant place based on the intent type.
    """
    destination = _extract_destination(text)

    if destination:
        return destination

    # For restaurant: try to find cuisine type mentioned
    if intent == "restaurant_booking":
        text_lower = text.lower()
        cuisines_mentioned = {
            "italian": "Italian", "chinese": "Chinese", "indian": "Indian",
            "japanese": "Japanese", "thai": "Thai", "mexican": "Mexican",
            "french": "French", "korean": "Korean", "biryani": "Hyderabadi",
            "pizza": "Italian", "sushi": "Japanese", "dosa": "South Indian",
        }
        for keyword, cuisine in cuisines_mentioned.items():
            if keyword in text_lower:
                return cuisine

    return None


def _title_case(text: str) -> str:
    """Smart title case that preserves already-capitalized words."""
    words = text.split()
    return " ".join(w if w[0].isupper() else w.capitalize() for w in words if w)


# ──────────────────────────────────────────────
#  Response Generators (text-aware)
# ──────────────────────────────────────────────

def _taxi_response(text: str) -> dict:
    dest = _extract_place_for_intent(text, "taxi_booking") or random.choice(FALLBACK_DESTINATIONS)
    driver = random.choice(TAXI_DRIVERS)
    vehicle = random.choice(TAXI_VEHICLES)
    pickup_time = _future_time(15, 45)
    cost = random.randint(250, 900)
    eta = random.randint(5, 15)

    return {
        "intent": "taxi_booking",
        "status": "confirmed",
        "details": {
            "destination": dest,
            "driver": driver,
            "vehicle": vehicle,
            "pickup_time": pickup_time,
            "estimated_cost": f"₹{cost}",
            "driver_eta": f"{eta} minutes",
        },
        "message": (
            f"🚕 Opening Uber to book your taxi to {dest}. "
            f"Your pickup is being set to your current location. "
            f"Estimated fare: ₹{cost}. I'll stop at the payment screen for you to confirm."
        ),
    }


def _tour_response(text: str) -> dict:
    place = _extract_place_for_intent(text, "tour_booking")
    tour = f"{place} Tour" if place else random.choice([
        "Heritage City Walk", "Sunset Lake Cruise", "Hill Station Day Trip",
        "Old Town Food Trail", "Temple & Culture Tour",
    ])
    guide = random.choice(TOUR_GUIDES)
    date = _tomorrow()
    cost = random.choice([800, 1200, 1500, 2000, 2500])
    duration = random.choice(["3 hours", "4 hours", "Half day", "Full day"])

    return {
        "intent": "tour_booking",
        "status": "confirmed",
        "details": {
            "tour_name": tour,
            "guide": guide,
            "date": date,
            "duration": duration,
            "cost": f"₹{cost}",
        },
        "message": (
            f"🗺️ Tour booked! '{tour}' with guide {guide} on {date}. "
            f"Duration: {duration}. Cost: ₹{cost}. Have a wonderful trip!"
        ),
    }


def _restaurant_response(text: str) -> dict:
    place = _extract_place_for_intent(text, "restaurant_booking")
    # If a specific restaurant/cuisine was mentioned, use it
    if place and any(c in place.lower() for c in ["indian", "italian", "chinese", "thai", "japanese", "korean", "french", "mexican", "hyderabadi", "south"]):
        cuisine = place
        name = random.choice(RESTAURANT_NAMES)
    elif place:
        name = place
        cuisine = random.choice(CUISINE_TYPES)
    else:
        name = random.choice(RESTAURANT_NAMES)
        cuisine = random.choice(CUISINE_TYPES)

    time = _future_time(30, 120)
    guests = random.randint(2, 6)
    table = random.choice(["Window Seat", "Garden Area", "Private Dining", "Terrace"])

    return {
        "intent": "restaurant_booking",
        "status": "confirmed",
        "details": {
            "restaurant": name,
            "cuisine": cuisine,
            "reservation_time": time,
            "guests": guests,
            "seating": table,
        },
        "message": (
            f"🍽️ Opening Zomato to find {name}. "
            f"Looking for {cuisine} cuisine options near you. "
            f"I'll help you book a table!"
        ),
    }


def _hotel_response(text: str) -> dict:
    place = _extract_place_for_intent(text, "hotel_booking")
    hotel = place if place else ""
    room = random.choice(ROOM_TYPES)
    checkin = _tomorrow()
    nights = random.randint(1, 5)
    cost_per_night = random.choice([2500, 3500, 5000, 7500])

    return {
        "intent": "hotel_booking",
        "status": "confirmed",
        "details": {
            "hotel": hotel,
            "room_type": room,
            "check_in": checkin,
            "nights": nights,
            "total_cost": f"₹{cost_per_night * nights}",
        },
        "message": (
            f"🏨 Opening Booking.com to find {hotel} near your location. "
            f"I'll search in your area so you get the right one. "
            f"I'll stop at payment for you to confirm."
        ),
    }


def _spa_response(text: str) -> dict:
    spa = random.choice(SPA_NAMES)
    treatment = random.choice(SPA_TREATMENTS)
    time = _future_time(60, 180)
    duration = random.choice(["45 min", "60 min", "90 min"])
    cost = random.choice([1000, 1500, 2000, 2800])

    return {
        "intent": "spa_booking",
        "status": "confirmed",
        "details": {
            "spa": spa,
            "treatment": treatment,
            "appointment_time": time,
            "duration": duration,
            "cost": f"₹{cost}",
        },
        "message": (
            f"🧖 Spa appointment booked! {treatment} at {spa}. "
            f"Time: {time}, Duration: {duration}. Cost: ₹{cost}. Relax and enjoy!"
        ),
    }


def _general_help_response(text: str) -> dict:
    return {
        "intent": "general_help",
        "status": "info",
        "details": {},
        "message": (
            "👋 Hello! I'm AURA, your personal reservation assistant. "
            "I can help you book: 🚕 Taxis · 🗺️ Tours · 🍽️ Restaurants · 🏨 Hotels · 🧖 Spa sessions. "
            "Just tell me what you need!"
        ),
    }


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────
_GENERATORS = {
    "taxi_booking": _taxi_response,
    "tour_booking": _tour_response,
    "restaurant_booking": _restaurant_response,
    "hotel_booking": _hotel_response,
    "spa_booking": _spa_response,
    "general_help": _general_help_response,
}


def generate_response(intents: list[dict], user_text: str = "") -> list[dict]:
    """
    Generate realistic booking responses for each detected intent.
    Now extracts actual destinations/places from the user's text.

    Args:
        intents: list of intent dicts from detect_intent().
        user_text: the user's input in English (after translation).

    Returns:
        list of response dicts, one per intent.
    """
    responses = []
    for intent_info in intents:
        tag = intent_info["intent"]
        generator = _GENERATORS.get(tag, _general_help_response)
        resp = generator(user_text)
        logger.info("Generated response for intent '%s'", tag)
        responses.append(resp)

    return responses
