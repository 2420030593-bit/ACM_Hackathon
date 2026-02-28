"""
Booking Service – Generate responses for all booking intents.
Local experience database for tours, restaurants, etc.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aura.booking")

# ── Local Experience Database ──
LOCAL_EXPERIENCES = {
    "city_tours": [
        {"name": "Old City Heritage Walk", "duration": "3 hours", "price": "₹1500", "rating": 4.8},
        {"name": "Street Food Safari", "duration": "2.5 hours", "price": "₹1200", "rating": 4.9},
        {"name": "Temple & Monument Tour", "duration": "4 hours", "price": "₹2000", "rating": 4.7},
    ],
    "restaurants": [
        {"name": "Paradise Biryani", "cuisine": "Hyderabadi", "price_range": "₹₹", "rating": 4.6},
        {"name": "Barbeque Nation", "cuisine": "BBQ", "price_range": "₹₹₹", "rating": 4.4},
        {"name": "Ohri's Jalavihar", "cuisine": "Multi-cuisine", "price_range": "₹₹", "rating": 4.3},
    ],
    "airport_services": [
        {"name": "Airport Pickup (Sedan)", "price": "₹800", "wait_time": "15 min"},
        {"name": "Airport Pickup (SUV)", "price": "₹1200", "wait_time": "15 min"},
        {"name": "Airport Pickup (Luxury)", "price": "₹2500", "wait_time": "20 min"},
    ],
    "hotel_services": [
        {"name": "Room Service", "available": True},
        {"name": "Spa & Wellness", "available": True},
        {"name": "Laundry", "available": True},
        {"name": "Concierge", "available": True},
    ],
}


def generate_booking_response(intent: str, entities: dict, llm_response: str = "") -> Dict[str, Any]:
    """Generate a booking response based on intent and entities."""
    handlers = {
        "flight_booking": _handle_flight,
        "hotel_booking": _handle_hotel,
        "taxi_booking": _handle_taxi,
        "restaurant_booking": _handle_restaurant,
        "tour_booking": _handle_tour,
        "spa_booking": _handle_spa,
        "bus_booking": _handle_bus,
        "travel_planning": _handle_travel_plan,
        "general_help": _handle_general,
    }

    handler = handlers.get(intent)
    if not handler:
        if intent.endswith("_booking"):
            handler = _handle_dynamic_booking
        else:
            handler = _handle_general
            
    result = handler(entities, llm_response)
    result["intent"] = intent
    return result

def _handle_dynamic_booking(entities: dict, llm: str) -> dict:
    return {
        "status": "searching",
        "message": llm or "I will set that up for you right now.",
        "details": entities,
        "requires_automation": True,
    }


def _handle_flight(entities: dict, llm: str) -> dict:
    dest = entities.get("destination", "your destination")
    return {
        "status": "searching",
        "message": llm or f"I'll search for flights to {dest}. Let me find the best options for you.",
        "details": {
            "destination": dest,
            "date": entities.get("date", "flexible"),
            "class": entities.get("class", "economy"),
            "budget": entities.get("budget", "any"),
        },
        "requires_automation": True,
    }


def _handle_hotel(entities: dict, llm: str) -> dict:
    dest = entities.get("destination", entities.get("hotel", ""))
    return {
        "status": "searching",
        "message": llm or f"Looking for hotels in {dest}. I'll compare prices and amenities.",
        "details": {
            "location": dest,
            "check_in": entities.get("check_in", ""),
            "check_out": entities.get("check_out", ""),
            "guests": entities.get("guests", "2"),
            "budget": entities.get("budget", "any"),
        },
        "requires_automation": True,
    }


def _handle_taxi(entities: dict, llm: str) -> dict:
    dest = entities.get("destination", "")
    return {
        "status": "confirmed",
        "message": llm or f"Booking a cab to {dest}. Your ride will arrive shortly.",
        "details": {
            "destination": dest,
            "vehicle_type": entities.get("vehicle", "sedan"),
            "pickup": entities.get("pickup", "current location"),
        },
        "requires_automation": True,
    }


def _handle_restaurant(entities: dict, llm: str) -> dict:
    options = LOCAL_EXPERIENCES["restaurants"]
    return {
        "status": "suggestions",
        "message": llm or "Here are some great dining options nearby:",
        "details": {"options": options},
        "requires_automation": True,
    }


def _handle_tour(entities: dict, llm: str) -> dict:
    options = LOCAL_EXPERIENCES["city_tours"]
    return {
        "status": "suggestions",
        "message": llm or "Here are popular tours in the area:",
        "details": {"options": options},
        "requires_automation": True,
    }


def _handle_spa(entities: dict, llm: str) -> dict:
    return {
        "status": "confirmed",
        "message": llm or "I'll book a spa session for you. Any time preference?",
        "details": {"service": "spa", "time": entities.get("time", "flexible")},
        "requires_automation": False,
    }


def _handle_bus(entities: dict, llm: str) -> dict:
    dest = entities.get("destination", "")
    return {
        "status": "searching",
        "message": llm or f"Searching for buses to {dest}.",
        "details": {
            "destination": dest,
            "date": entities.get("date", "today"),
            "type": entities.get("bus_type", "AC sleeper"),
        },
        "requires_automation": True,
    }


def _handle_travel_plan(entities: dict, llm: str) -> dict:
    dest = entities.get("destination", "your chosen city")
    days = entities.get("days", "2")
    budget = entities.get("budget", "moderate")
    return {
        "status": "planning",
        "message": llm or f"Planning a {days}-day trip to {dest} within {budget} budget. Let me create a detailed itinerary.",
        "details": {
            "destination": dest,
            "days": days,
            "budget": budget,
        },
        "requires_automation": False,
    }


def _handle_general(entities: dict, llm: str) -> dict:
    return {
        "status": "info",
        "message": llm or "I'm AURA, your AI travel concierge. I can help with flights, hotels, taxis, tours, restaurants, translations, and emergency assistance. How can I help?",
        "details": {},
        "requires_automation": False,
    }
