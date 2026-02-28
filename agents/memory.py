"""
Memory Agent – Personal memory system.
Stores preferences: seat, budget, language, frequent routes.
Uses memory to influence decisions.
"""
import logging
from database.db import save_memory, get_memories

logger = logging.getLogger("aura.memory")


async def remember(category: str, key: str, value: str):
    """Store a memory."""
    await save_memory(category, key, value)
    logger.info(f"Remembered: [{category}] {key}={value}")


async def recall(category: str = None) -> list:
    """Recall memories, optionally filtered by category."""
    return await get_memories(category)


async def recall_preference(key: str) -> str:
    """Get a specific preference value."""
    memories = await get_memories("preference")
    for m in memories:
        if m["key"] == key:
            return m["value"]
    return None


async def learn_from_interaction(intent: str, entities: dict, text: str):
    """Extract and store preferences from user interactions."""
    # Learn preferred budget range
    if "budget" in entities:
        await remember("preference", "budget_range", entities["budget"])

    # Learn destination frequency
    dest = entities.get("destination", "")
    if dest:
        await remember("route", dest, f"searched_{intent}")

    # Learn language preference
    if entities.get("language"):
        await remember("preference", "language", entities["language"])

    # Learn seat preference
    if "business" in text.lower():
        await remember("preference", "seat_class", "business")
    elif "economy" in text.lower():
        await remember("preference", "seat_class", "economy")
    elif "first" in text.lower() and "class" in text.lower():
        await remember("preference", "seat_class", "first")


async def get_context_for_llm() -> str:
    """Build a context string from memories for the LLM."""
    memories = await get_memories()
    if not memories:
        return ""

    context_parts = ["User preferences:"]
    for m in memories[:10]:  # Top 10 by frequency
        context_parts.append(f"- {m['key']}: {m['value']} (used {m['frequency']}x)")
    return "\n".join(context_parts)
