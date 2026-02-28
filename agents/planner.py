"""
Planner Agent – Orchestrates LLM responses with booking/automation routing.
The LLM provides the conversational response; intent detection routes to services.
"""
import logging
from services.llm_brain import process_with_llm
from services.booking_service import generate_booking_response
from services.itinerary_service import generate_itinerary, generate_voice_summary
from agents.memory import get_context_for_llm, learn_from_interaction

logger = logging.getLogger("aura.planner")


async def plan_and_execute(text: str, language: str = "en") -> dict:
    """
    Master orchestrator: takes user input and returns a complete response.
    1. Query Ollama for natural conversational response
    2. Detect intent for routing (booking, automation, etc.)
    3. If booking intent detected, generate booking record
    """
    # Get user context from memory
    context = await get_context_for_llm()

    # Process with LLM (Ollama chat + keyword intent)
    llm_result = await process_with_llm(text, context)
    intent = llm_result.get("intent", "general_chat")
    entities = llm_result.get("entities", {})
    explanation = llm_result.get("explanation", "")
    actions = llm_result.get("actions", [])
    llm_response = llm_result.get("response", "")

    # Learn from this interaction
    await learn_from_interaction(intent, entities, text)

    # Generate booking record for booking intents (for tracking, not for response text)
    booking = {}
    requires_automation = False
    if intent.endswith("_booking") or intent in ("travel_planning",):
        booking = generate_booking_response(intent, entities, llm_response)
        requires_automation = booking.get("requires_automation", False)

    # Automation was already triggered instantly from process_with_llm
    # (fires BEFORE the chat response — no duplicate trigger needed)
    automation_already_fired = llm_result.get("automation_fired", False)
    if automation_already_fired:
        requires_automation = True
        logger.info("Automation was already fired from LLM pipeline for '%s'", intent)

    # If it's a travel plan, generate full itinerary
    itinerary = None
    if intent == "travel_planning":
        dest = entities.get("destination", "Hyderabad")
        days = int(entities.get("days", "2"))
        budget = float(entities.get("budget", "0")) or None
        itinerary = generate_itinerary(dest, days, budget)

    # The LLM response IS the final response – no canned text
    final_response = llm_response
    if not final_response:
        # Only if Ollama is completely unreachable, use booking service message
        if booking:
            final_response = booking.get("message", "I'm processing your request...")
        else:
            final_response = "I'm AURA, your AI travel concierge. I can help with flights, hotels, cabs, restaurants, tours, translations, and more. What would you like to do?"

    if not explanation:
        explanation = f"Processed as '{intent}'"

    return {
        "intent": intent,
        "entities": entities,
        "response_text": final_response,
        "explanation": explanation,
        "actions": actions,
        "mode": booking.get("status", "chat"),
        "booking": booking,
        "itinerary": itinerary,
        "requires_automation": requires_automation,
        "requires_followup": llm_result.get("requires_followup", False),
        "followup_question": llm_result.get("followup_question", ""),
        "source": llm_result.get("source", "unknown"),
        "all_intents": llm_result.get("all_intents", [intent]),
    }
