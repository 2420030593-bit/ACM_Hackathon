"""
Ollama LLM Brain – Real conversational AI using Ollama chat API.
Uses local LLM for natural language responses.
Intent detection done via keywords for routing.
Entity extraction uses fast regex (instant) with LLM fallback for complex cases.
"""
import logging
import re
import json
import asyncio
import httpx
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("aura.llm")

SYSTEM_PROMPT = """You are AURA, a premium AI travel concierge assistant. You help travelers with:
- Finding and recommending flights, hotels, restaurants, tours, and attractions
- Booking taxis, buses, and transportation
- Travel planning and itineraries with budget breakdowns
- Local recommendations (best food spots, hidden gems, cultural experiences)
- Translation and language help
- Emergency travel assistance

Be conversational, warm, specific, and helpful. Give real recommendations with details like prices, ratings, and tips.
Keep responses concise (2-4 sentences). Use emojis sparingly for warmth.
If a user asks about a specific place or food, give genuine local knowledge."""

# ── Conversation History ──
_messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
MAX_MESSAGES = 30


async def chat_with_llm(user_text: str) -> str:
    """Send message to Ollama and get a natural conversation response."""
    _messages.append({"role": "user", "content": user_text})

    # Keep history manageable
    if len(_messages) > MAX_MESSAGES:
        _messages[:] = [_messages[0]] + _messages[-(MAX_MESSAGES - 1):]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": _messages,
                    "stream": False,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("message", {}).get("content", "").strip()
                if reply:
                    _messages.append({"role": "assistant", "content": reply})
                    logger.info(f"Ollama replied: {reply[:80]}...")
                    return reply
                else:
                    logger.warning("Ollama returned empty response")
                    return ""
            else:
                logger.warning(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}")
                return ""
    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama. Is it running? (ollama serve)")
        return ""
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return ""


# ── Intent Detection (keyword-based, for routing only) ──
# Ordered by priority — first match wins
INTENT_PATTERNS = {
    "taxi_booking": r"\b(taxi|cab|ride|uber|ola|pickup|drop|driver|auto)\b",
    "bus_booking": r"\b(bus|coach|intercity|bus ticket|redbus)\b",
    "flight_booking": r"\b(flights?|fly|flying|plane|airline|boarding|air ticket)\b",
    "hotel_booking": r"\b(hotel|room|stay|accommodation|resort|hostel|lodge)\b",
    "restaurant_booking": r"\b(restaurant|food|dinner|lunch|breakfast|eat|dine|biryani|cuisine|cafe)\b",
    "tour_booking": r"\b(tour|sightseeing|visit|explore|attraction|temple|monument|museum|places)\b",
    "spa_booking": r"\b(spa|massage|wellness|relax)\b",
    "travel_planning": r"\b(plan|trip|itinerary|travel plan|budget trip|vacation)\b",
    "emergency": r"\b(emergency|sos|lost passport|police|embassy|hospital|ambulance)\b",
    "translation": r"\b(translate|translation|say in|how to say)\b",
    "price_check": r"\b(price|cost|cheap|expensive|compare|deal)\b",
    "movie_booking": r"\b(movie|tickets|cinema|film|show)\b",
}

INTENT_LABELS = {
    "flight_booking": "Flight Booking",
    "hotel_booking": "Hotel Booking",
    "taxi_booking": "Taxi Booking",
    "restaurant_booking": "Restaurant Booking",
    "tour_booking": "Tour Booking",
    "spa_booking": "Spa Booking",
    "bus_booking": "Bus Booking",
    "travel_planning": "Travel Planning",
    "emergency": "Emergency Assistance",
    "translation": "Translation",
    "price_check": "Price Intelligence",
    "movie_booking": "Movie Booking",
    "general_chat": "General Chat",
}

# Intents that should trigger browser automation
AUTOMATION_INTENTS = {
    "taxi_booking", "bus_booking", "flight_booking",
    "hotel_booking", "restaurant_booking", "tour_booking",
}


def detect_intent(text: str) -> tuple[str, list[str]]:
    """Detect intent from keywords. Returns (primary_intent, all_intents).
    Pattern dict is ordered by priority — first match wins."""
    text_lower = text.lower()
    detected = []
    for intent, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, text_lower):
            detected.append(intent)
    if not detected:
        return "general_chat", ["general_chat"]
    return detected[0], detected


def extract_entities_fast(text: str) -> dict:
    """
    FAST regex-based entity extraction. Runs instantly (no LLM call).
    Handles patterns like:
      - "from Hyderabad to Mumbai" → pickup=Hyderabad, destination=Mumbai
      - "to Vijayawada" → destination=Vijayawada
      - "in Goa" → destination=Goa
      - "hotel in goa for 2 people" → destination=Goa, guests=2
    """
    entities = {}

    # Pattern 1: "from X to Y" (captures both origin and destination)
    from_to = re.search(
        r"\bfrom\s+([A-Za-z][a-zA-Z\s]+?)\s+to\s+([A-Za-z][a-zA-Z\s]+?)(?:\s+(?:on|for|under|below|with|budget|tomorrow|today)|[?.,!]|$)",
        text, re.I
    )
    if from_to:
        entities["pickup"] = from_to.group(1).strip().title()
        entities["destination"] = from_to.group(2).strip().title()
    else:
        # Pattern 2: "to <destination>"
        to_match = re.search(
            r"\bto\s+(?:the\s+)?([A-Za-z][a-zA-Z\s]+?)(?:\s+(?:on|for|under|below|with|budget|tomorrow|today|from)|[?.,!]|$)",
            text, re.I
        )
        if to_match:
            entities["destination"] = to_match.group(1).strip().title()

        # Pattern 3: "in <place>" (for hotels)
        if "destination" not in entities:
            in_match = re.search(
                r"\bin\s+([A-Za-z][a-zA-Z\s]+?)(?:\s+(?:on|for|under|below|with|budget|tomorrow|today)|[?.,!]|$)",
                text, re.I
            )
            if in_match:
                entities["destination"] = in_match.group(1).strip().title()

    # Budget: "under 5000", "budget 2000"
    budget_match = re.search(r"(?:under|below|max|budget|within)\s*(?:[$₹]|rs\.?|inr|usd)?\s*(\d[\d,]*)", text, re.I)
    if budget_match:
        entities["budget"] = budget_match.group(1).replace(",", "")

    # Guests: "2 people", "3 adults"
    guest_match = re.search(r"(\d+)\s*(?:people|person|adults?|guests?|pax)", text, re.I)
    if guest_match:
        entities["guests"] = guest_match.group(1)

    # Days: "3 days", "2 nights"
    day_match = re.search(r"(\d+)\s*(?:days?|nights?)", text, re.I)
    if day_match:
        entities["days"] = day_match.group(1)

    # Date: "tomorrow", "today", specific date
    if re.search(r"\btomorrow\b", text, re.I):
        entities["date"] = "tomorrow"
    elif re.search(r"\btoday\b", text, re.I):
        entities["date"] = "today"

    logger.info("Fast entities: %s", entities)
    return entities


async def process_with_llm(text: str, context: str = "") -> dict:
    """
    Main processing pipeline. For booking intents:
    - Uses FAST regex for entity extraction (instant, no LLM call)
    - Fires automation trigger IMMEDIATELY
    - Gets LLM chat response concurrently (for voice reply)
    
    For non-booking intents:
    - Just gets the LLM chat response normally
    """
    # Step 1: Detect intent (instant, regex-based)
    intent, all_intents = detect_intent(text)
    explanation = f"Detected intent '{INTENT_LABELS.get(intent, intent)}' from keywords."
    
    # Step 2: Extract entities (instant regex — no slow LLM call)
    entities = extract_entities_fast(text)

    # Step 3: For booking intents, trigger automation IMMEDIATELY
    # Don't wait for the LLM chat response — do both at the same time
    is_booking = intent in AUTOMATION_INTENTS
    
    if is_booking and entities.get("destination"):
        # Fire automation in the background RIGHT NOW
        try:
            from services.automation import trigger_automation
            destination = entities.get("destination", "")
            pickup = entities.get("pickup", "my current location")
            logger.info("🚀 INSTANT automation trigger: %s → %s", intent, destination)
            trigger_automation(intent, destination, pickup)
        except Exception as e:
            logger.error("Automation trigger failed: %s", e)

    # Step 4: Generate response
    if is_booking and entities.get("destination"):
        # For booking intents → instant template response (no LLM wait!)
        # The browser automation is already launching — user just needs confirmation
        dest = entities.get("destination", "")
        site_names = {
            "taxi_booking": "Uber",
            "bus_booking": "RedBus",
            "flight_booking": "Google Flights",
            "hotel_booking": "Booking.com",
            "restaurant_booking": "Zomato",
            "tour_booking": "Google Maps",
        }
        site = site_names.get(intent, "the booking site")
        llm_response = f"Opening {site} now to book your {intent.replace('_booking', '')} to {dest}. The browser will open automatically — I'll handle the navigation for you! 🚀"
        source = "instant"
    else:
        # For non-booking intents → get full LLM chat response
        llm_response = await chat_with_llm(text)
        source = "ollama" if llm_response else "keyword"

    return {
        "intent": intent,
        "entities": entities,
        "response": llm_response,
        "explanation": explanation,
        "actions": [f"Process {intent}"],
        "requires_followup": False,
        "followup_question": "",
        "all_intents": all_intents,
        "source": source,
        # Tell the planner automation was already triggered from here
        "automation_fired": is_booking and bool(entities.get("destination")),
    }
