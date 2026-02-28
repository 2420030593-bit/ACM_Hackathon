"""
Itinerary Service – Trip timeline generation, PDF export, voice summary.
"""
import logging
import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger("aura.itinerary")

# ── Activity Database ──
ACTIVITIES = {
    "hyderabad": {
        "morning": [
            {"name": "Charminar Visit", "duration": "2h", "cost": 200, "type": "monument"},
            {"name": "Golconda Fort Tour", "duration": "3h", "cost": 500, "type": "monument"},
            {"name": "Salar Jung Museum", "duration": "2.5h", "cost": 300, "type": "museum"},
        ],
        "afternoon": [
            {"name": "Birla Mandir", "duration": "1.5h", "cost": 0, "type": "temple"},
            {"name": "Hussain Sagar Lake", "duration": "2h", "cost": 400, "type": "leisure"},
            {"name": "Street Food Tour", "duration": "2h", "cost": 800, "type": "food"},
        ],
        "evening": [
            {"name": "Laad Bazaar Shopping", "duration": "2h", "cost": 1000, "type": "shopping"},
            {"name": "Paradise Biryani Dinner", "duration": "1.5h", "cost": 600, "type": "food"},
            {"name": "Necklace Road Walk", "duration": "1h", "cost": 0, "type": "leisure"},
        ],
        "hotels": [
            {"name": "Taj Deccan", "price_per_night": 5000, "rating": 4.5},
            {"name": "ITC Kohenur", "price_per_night": 8000, "rating": 4.8},
            {"name": "OYO Rooms", "price_per_night": 1500, "rating": 3.8},
        ],
    },
    "dubai": {
        "morning": [
            {"name": "Burj Khalifa Observation", "duration": "2h", "cost": 3000, "type": "landmark"},
            {"name": "Dubai Mall Exploration", "duration": "3h", "cost": 0, "type": "shopping"},
            {"name": "Desert Safari", "duration": "4h", "cost": 5000, "type": "adventure"},
        ],
        "afternoon": [
            {"name": "Sky Views Observation", "duration": "2h", "cost": 2500, "type": "landmark"},
            {"name": "Dubai Marina Walk", "duration": "2h", "cost": 0, "type": "leisure"},
            {"name": "Gold Souk Visit", "duration": "1.5h", "cost": 0, "type": "shopping"},
        ],
        "evening": [
            {"name": "Dinner Cruise", "duration": "2h", "cost": 4000, "type": "food"},
            {"name": "Fountain Show", "duration": "1h", "cost": 0, "type": "entertainment"},
            {"name": "La Mer Beach", "duration": "2h", "cost": 500, "type": "leisure"},
        ],
        "hotels": [
            {"name": "Armani Hotel", "price_per_night": 50000, "rating": 4.9},
            {"name": "JW Marriott", "price_per_night": 15000, "rating": 4.6},
            {"name": "Rove Downtown", "price_per_night": 5000, "rating": 4.2},
        ],
    },
    "default": {
        "morning": [
            {"name": "City Landmark Tour", "duration": "3h", "cost": 500, "type": "sightseeing"},
            {"name": "Local Market Visit", "duration": "2h", "cost": 200, "type": "shopping"},
        ],
        "afternoon": [
            {"name": "Local Cuisine Experience", "duration": "2h", "cost": 800, "type": "food"},
            {"name": "Museum Visit", "duration": "2h", "cost": 400, "type": "culture"},
        ],
        "evening": [
            {"name": "Sunset Point", "duration": "1.5h", "cost": 0, "type": "leisure"},
            {"name": "Traditional Dinner", "duration": "2h", "cost": 600, "type": "food"},
        ],
        "hotels": [
            {"name": "Premium Hotel", "price_per_night": 5000, "rating": 4.5},
            {"name": "Budget Hotel", "price_per_night": 1500, "rating": 3.8},
        ],
    },
}


def generate_itinerary(destination: str, days: int, budget: float = None, preferences: list = []) -> dict:
    """Generate a complete trip itinerary."""
    dest_lower = destination.lower()
    city_data = ACTIVITIES.get(dest_lower, ACTIVITIES["default"])

    itinerary = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "timeline": [],
        "budget_breakdown": {"travel": 0, "stay": 0, "activities": 0, "food": 0, "service_fee": 500},
        "total_estimated": 0,
    }

    # Select hotel based on budget
    hotels = city_data["hotels"]
    if budget:
        per_night_budget = budget / (days + 1)  # Leave room for activities
        hotels = sorted(hotels, key=lambda h: abs(h["price_per_night"] - per_night_budget * 0.4))
    selected_hotel = hotels[0]
    itinerary["hotel"] = selected_hotel
    itinerary["budget_breakdown"]["stay"] = selected_hotel["price_per_night"] * days

    # Build daily timeline
    start_date = datetime.now() + timedelta(days=7)
    for day in range(1, days + 1):
        day_date = start_date + timedelta(days=day - 1)
        day_plan = {
            "day": day,
            "date": day_date.strftime("%Y-%m-%d"),
            "activities": [],
        }

        for time_of_day in ["morning", "afternoon", "evening"]:
            activities = city_data.get(time_of_day, [])
            if activities:
                # Pick one activity per time slot
                idx = (day - 1) % len(activities)
                activity = activities[idx].copy()
                activity["time_of_day"] = time_of_day
                activity["start_time"] = {
                    "morning": "09:00 AM",
                    "afternoon": "02:00 PM",
                    "evening": "06:00 PM",
                }[time_of_day]
                day_plan["activities"].append(activity)
                itinerary["budget_breakdown"]["activities"] += activity.get("cost", 0)

        itinerary["timeline"].append(day_plan)

    # Calculate totals
    itinerary["budget_breakdown"]["travel"] = 2000  # Estimate local transport
    itinerary["total_estimated"] = sum(itinerary["budget_breakdown"].values())

    return itinerary


def generate_voice_summary(itinerary: dict) -> str:
    """Generate a voice-friendly summary of the itinerary."""
    dest = itinerary["destination"]
    days = itinerary["days"]
    total = itinerary["total_estimated"]
    hotel = itinerary.get("hotel", {}).get("name", "a hotel")

    summary = f"Here's your {days}-day trip to {dest}. "
    summary += f"You'll be staying at {hotel}. "

    for day in itinerary["timeline"]:
        day_num = day["day"]
        acts = [a["name"] for a in day["activities"]]
        summary += f"Day {day_num}: {', '.join(acts)}. "

    summary += f"Total estimated cost is {total} rupees."
    return summary


def generate_pdf_itinerary(itinerary: dict) -> str:
    """Generate a PDF of the itinerary and return the file path."""
    try:
        from fpdf import FPDF
    except ImportError:
        logger.warning("fpdf2 not installed, cannot generate PDF")
        return ""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, f"AURA Itinerary: {itinerary['destination']}", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"{itinerary['days']} Days | Budget: {itinerary.get('budget', 'Flexible')}", ln=True, align="C")
    pdf.ln(10)

    # Hotel
    hotel = itinerary.get("hotel", {})
    if hotel:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Hotel: {hotel.get('name', 'TBD')}", ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Price: {hotel.get('price_per_night', 'N/A')}/night | Rating: {hotel.get('rating', 'N/A')}", ln=True)
        pdf.ln(5)

    # Timeline
    for day in itinerary["timeline"]:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Day {day['day']} - {day['date']}", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for act in day["activities"]:
            time_label = act.get("start_time", "")
            pdf.cell(0, 8, f"  {time_label} - {act['name']} ({act.get('duration', 'N/A')}) - Cost: {act.get('cost', 0)}", ln=True)
        pdf.ln(3)

    # Budget breakdown
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Budget Breakdown", ln=True)
    pdf.set_font("Helvetica", "", 11)
    for category, amount in itinerary["budget_breakdown"].items():
        pdf.cell(0, 8, f"  {category.title()}: {amount}", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Total Estimated: {itinerary['total_estimated']}", ln=True)

    # Save
    output_path = os.path.join(tempfile.gettempdir(), f"aura_itinerary_{itinerary['destination'].lower().replace(' ', '_')}.pdf")
    pdf.output(output_path)
    logger.info(f"PDF saved to {output_path}")
    return output_path
