import logging
from services.automation import _automate_with_llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-5s | %(message)s")

print("Starting LLM Agent Loop (Groq enabled)...")
print("Target: Bus booking to Vijayawada from Hyderabad")

_automate_with_llm("bus_booking", "Vijayawada", "Hyderabad")
print("Agent stopped. Check browser if it reached payment.")
