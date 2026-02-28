"""
AURA – Conversation Session Manager
Handles multi-turn conversations for bookings that need follow-up info.
For example: hotel bookings need check-in, check-out, adults, children.
"""

import logging
import re
from datetime import datetime, timedelta
from dateutil import parser as dateparser

logger = logging.getLogger("aura.session")


# ──────────────────────────────────────────────
#  Active booking session (single-user demo)
# ──────────────────────────────────────────────
_active_session = None


def get_session():
    """Get the current active session, or None."""
    return _active_session


def clear_session():
    """Clear the active session."""
    global _active_session
    _active_session = None
    logger.info("Session cleared.")


def start_hotel_session(hotel_name: str, detected_lang: str = "en", initial_text: str = ""):
    """Start a new hotel booking session."""
    global _active_session

    _active_session = {
        "type": "hotel_booking",
        "hotel": hotel_name,
        "lang": detected_lang,
        "step": "ask_budget" if hotel_name else "ask_hotel",
        "checkin": None,
        "checkout": None,
        "adults": 2,
        "children": 0,
        "price_min": None,
        "price_max": None,
        "sort_by_rating": True,       # Always sort by best ratings
    }
    logger.info("Hotel session started: %s (step: %s)",
                hotel_name or "Unknown", _active_session["step"])
    return _active_session


def process_session_input(text: str) -> dict | None:
    """
    Process user input in the context of an active session.

    Returns:
        dict with 'question' (next follow-up) or 'complete' (all info gathered).
        None if no active session.
    """
    global _active_session

    if not _active_session:
        return None

    session = _active_session
    step = session["step"]

    if step == "ask_hotel":
        # Clean the input: strip out common filler words so
        # "I want a hotel in Hyderabad" → "Hyderabad"
        # "Sitara Grand" → "Sitara Grand"
        # "suggest me" → "" (handled below)
        _noise = {
            "i", "want", "need", "book", "a", "an", "the", "hotel", "room",
            "stay", "in", "at", "to", "for", "please", "can", "you", "me",
            "find", "get", "search", "look", "near", "around", "would",
            "like", "some", "good", "nice", "cheap", "with", "lodge",
            "resort", "inn", "accommodation",
            "suggest", "suggestion", "recommend", "recommendation",
            "best", "top", "any", "something", "anything", "one",
            "show", "give", "tell", "nearby",
        }
        words = text.strip().split()
        cleaned = [w for w in words if w.lower().strip(".,!?;:") not in _noise
                   and not w.lower().strip(".,!?;:").isdigit()]
        # Also strip trailing noise
        while cleaned and cleaned[-1].lower().strip(".,!?;:") in _noise:
            cleaned.pop()
        while cleaned and cleaned[0].lower().strip(".,!?;:") in _noise:
            cleaned.pop(0)

        hotel_name = " ".join(cleaned).strip(".,!?;: ") if cleaned else ""

        if not hotel_name or len(hotel_name) < 2:
            # User said "suggest me" / "recommend" / "any" — default to their city
            hotel_name = "Hyderabad"
            session["hotel"] = hotel_name
            session["step"] = "ask_budget"
            logger.info("Hotel defaulted to city: %s", hotel_name)
            return {
                "question": f"I'll search for the best hotels in {hotel_name} for you! What's your budget per night? Say '2000 to 3000 rupees' or 'under 5000', or 'any budget'.",
                "step": "ask_budget",
            }

        session["hotel"] = hotel_name
        session["step"] = "ask_budget"
        logger.info("Hotel set: %s", hotel_name)
        return {
            "question": f"Got it, {hotel_name}! What's your budget per night? You can say something like '2000 to 3000 rupees' or 'under 5000'.",
            "step": "ask_budget",
        }

    elif step == "ask_budget":
        p_min, p_max = _parse_budget(text)
        if p_min or p_max:
            session["price_min"] = p_min
            session["price_max"] = p_max
            budget_msg = ""
            if p_min and p_max:
                budget_msg = f"{p_min} to {p_max} rupees"
            elif p_max:
                budget_msg = f"under {p_max} rupees"
            elif p_min:
                budget_msg = f"above {p_min} rupees"
            session["step"] = "ask_checkin"
            logger.info("Budget set: %s - %s", p_min, p_max)
            return {
                "question": f"Budget set to {budget_msg} per night. I'll sort by top ratings too! When would you like to check in?",
                "step": "ask_checkin",
            }
        else:
            # Check if they said "no budget" / "any" / "doesn't matter"
            skip_words = ["no", "any", "doesn't", "doesnt", "dont", "don't", "skip", "whatever", "flexible"]
            if any(w in text.lower() for w in skip_words):
                session["step"] = "ask_checkin"
                return {
                    "question": "No problem! I'll show you the best-rated options. When would you like to check in?",
                    "step": "ask_checkin",
                }
            return {
                "question": "I didn't catch your budget. You can say '2000 to 3000' or 'under 5000' or 'any budget'.",
                "step": "ask_budget",
            }

    elif step == "ask_checkin":
        date = _parse_date(text)
        if date:
            session["checkin"] = date
            session["step"] = "ask_checkout"
            logger.info("Check-in set: %s", date)
            return {
                "question": f"Check-in on {date.strftime('%B %d, %Y')}. And when would you like to check out?",
                "step": "ask_checkout",
            }
        else:
            return {
                "question": "I didn't catch the date. When would you like to check in? You can say something like 'March 5th' or 'tomorrow'.",
                "step": "ask_checkin",
            }

    elif step == "ask_checkout":
        date = _parse_date(text)
        if date:
            session["checkout"] = date
            session["step"] = "ask_guests"
            logger.info("Check-out set: %s", date)
            return {
                "question": f"Check-out on {date.strftime('%B %d, %Y')}. How many guests? Tell me the number of adults and children.",
                "step": "ask_guests",
            }
        else:
            return {
                "question": "I didn't catch the date. When would you like to check out?",
                "step": "ask_checkout",
            }

    elif step == "ask_guests":
        adults, children = _parse_guests(text)
        session["adults"] = adults
        session["children"] = children
        session["step"] = "done"
        logger.info("Guests set: %d adults, %d children", adults, children)

        checkin_str = session["checkin"].strftime("%B %d")
        checkout_str = session["checkout"].strftime("%B %d")
        hotel = session["hotel"]
        kids_text = f" and {children} {'child' if children == 1 else 'children'}" if children > 0 else ""

        # Budget info for message
        budget_text = ""
        if session.get("price_min") and session.get("price_max"):
            budget_text = f" Budget: {session['price_min']} to {session['price_max']} rupees per night."
        elif session.get("price_max"):
            budget_text = f" Budget: under {session['price_max']} rupees per night."

        return {
            "complete": True,
            "question": (
                f"Opening Booking.com to find the best rated hotels in {hotel} — "
                f"{checkin_str} to {checkout_str}, "
                f"{adults} {'adult' if adults == 1 else 'adults'}{kids_text}."
                f"{budget_text} "
                f"Sorted by top ratings! I'll fill everything in for you."
            ),
            "step": "done",
            "session": session,
        }

    return None


# ──────────────────────────────────────────────
#  Date Parsing
# ──────────────────────────────────────────────

def _parse_date(text: str) -> datetime | None:
    """
    Parse a date from natural language text.

    Supports:
      - "March 5th", "5 March", "March 5"
      - "tomorrow", "day after tomorrow"
      - "next Monday", "next Friday"
      - "in 3 days", "3 days from now"
      - "15th", "the 20th"  (assumes current/next month)
      - ISO-like: "2026-03-05", "03/05"
    """
    text_lower = text.lower().strip()

    # Relative dates
    if "tomorrow" in text_lower:
        if "day after" in text_lower:
            return datetime.now() + timedelta(days=2)
        return datetime.now() + timedelta(days=1)

    if "today" in text_lower or "tonight" in text_lower:
        return datetime.now()

    # "in X days" or "X days from now"
    m = re.search(r'(\d+)\s*days?\s*(from\s*now|later)?', text_lower)
    if m and ("in" in text_lower or "from" in text_lower or "later" in text_lower):
        return datetime.now() + timedelta(days=int(m.group(1)))

    # "next Monday", "next Friday", etc.
    days_of_week = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    for day_name, day_num in days_of_week.items():
        if day_name in text_lower:
            today = datetime.now()
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return today + timedelta(days=days_ahead)

    # Try dateutil parser for anything else (e.g., "March 5th", "5 March 2026")
    try:
        parsed = dateparser.parse(text, fuzzy=True, dayfirst=False)
        if parsed:
            # If the parsed date is in the past, assume next year
            if parsed < datetime.now():
                parsed = parsed.replace(year=parsed.year + 1)
            return parsed
    except (ValueError, OverflowError):
        pass

    # Last resort: just a number? Assume it's a day of current/next month
    m = re.search(r'\b(\d{1,2})(st|nd|rd|th)?\b', text_lower)
    if m:
        day = int(m.group(1))
        if 1 <= day <= 31:
            now = datetime.now()
            try:
                result = now.replace(day=day)
                if result < now:
                    # Move to next month
                    if now.month == 12:
                        result = result.replace(year=now.year + 1, month=1)
                    else:
                        result = result.replace(month=now.month + 1)
                return result
            except ValueError:
                pass

    return None


# ──────────────────────────────────────────────
#  Guest Parsing
# ──────────────────────────────────────────────

def _parse_guests(text: str) -> tuple[int, int]:
    """
    Parse number of adults and children from text.

    Examples:
      "2 adults and 1 child"  → (2, 1)
      "3 adults"              → (3, 0)
      "2"                     → (2, 0)
      "just me"               → (1, 0)
      "couple"                → (2, 0)
      "family of 4"           → (4, 0)
      "2 adults 2 kids"       → (2, 2)
    """
    text_lower = text.lower().strip()
    adults = 2  # default
    children = 0

    # "just me" / "only me" / "solo"
    if any(w in text_lower for w in ["just me", "only me", "solo", "myself", "alone"]):
        return (1, 0)

    # "couple"
    if "couple" in text_lower:
        return (2, 0)

    # "family of X"
    m = re.search(r'family\s*of\s*(\d+)', text_lower)
    if m:
        total = int(m.group(1))
        return (total, 0)

    # Look for "X adults"
    m = re.search(r'(\d+)\s*adults?', text_lower)
    if m:
        adults = int(m.group(1))

    # Look for "X children" / "X kids" / "X child"
    m = re.search(r'(\d+)\s*(children|childs?|kids?)', text_lower)
    if m:
        children = int(m.group(1))

    # If only a single number with no context, treat as adults
    if not re.search(r'adults?|children|childs?|kids?', text_lower):
        m = re.search(r'\b(\d+)\b', text_lower)
        if m:
            adults = int(m.group(1))

    # Clamp to reasonable values
    adults = max(1, min(adults, 10))
    children = max(0, min(children, 6))

    return (adults, children)


# ──────────────────────────────────────────────
#  Budget / Price Range Parsing
# ──────────────────────────────────────────────

def _parse_budget(text: str) -> tuple:
    """
    Parse price range from natural language.

    Examples:
      "2000-3000"               → (2000, 3000)
      "2000 to 3000"            → (2000, 3000)
      "between 2000 and 3000"   → (2000, 3000)
      "under 5000"              → (None, 5000)
      "less than 3000"          → (None, 3000)
      "below 4000"              → (None, 4000)
      "above 2000"              → (2000, None)
      "more than 2000"          → (2000, None)
      "around 3000"             → (2500, 3500)  ± ~15%
      "budget of 4000"          → (3000, 5000)
      "price range 2000 3000"   → (2000, 3000)

    Returns:
        (price_min, price_max) — either can be None if not detected.
    """
    text_lower = text.lower().strip()

    # "2000-3000" or "2000 - 3000"
    m = re.search(r'(\d{3,6})\s*[-–]\s*(\d{3,6})', text_lower)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    # "between 2000 and 3000" or "2000 to 3000" or "from 2000 to 3000"
    m = re.search(r'(?:between|from)?\s*(\d{3,6})\s*(?:to|and)\s*(\d{3,6})', text_lower)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    # "price range 2000 3000"
    m = re.search(r'(?:price|range|budget)\s*(?:range|of)?\s*(\d{3,6})\s*(\d{3,6})', text_lower)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    # "under / below / less than X"
    m = re.search(r'(?:under|below|less\s+than|max|maximum|upto|up\s+to)\s*(\d{3,6})', text_lower)
    if m:
        return (None, int(m.group(1)))

    # "above / more than / over / minimum X"
    m = re.search(r'(?:above|over|more\s+than|min|minimum|at\s+least)\s*(\d{3,6})', text_lower)
    if m:
        return (int(m.group(1)), None)

    # "around X" or "about X" → give ±15% range
    m = re.search(r'(?:around|about|approximately|roughly)\s*(\d{3,6})', text_lower)
    if m:
        price = int(m.group(1))
        margin = int(price * 0.15)
        return (price - margin, price + margin)

    # "budget of X" or "budget X"
    m = re.search(r'budget\s*(?:of|is)?\s*(\d{3,6})', text_lower)
    if m:
        price = int(m.group(1))
        return (int(price * 0.75), int(price * 1.25))

    return (None, None)
