"""Quick test: trigger LLM-driven bus booking automation."""
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s")

from services.automation import trigger_automation, BROWSER_KEEP_ALIVE
import services.automation
services.automation.BROWSER_KEEP_ALIVE = 10  # Short timeout for testing
services.automation.MAX_LLM_STEPS = 8  # Fewer steps for a quick test

import time

print("Testing LLM-driven Bus Booking...")
trigger_automation("bus_booking", "Vijayawada", pickup="Hyderabad")

# Wait for the thread to finish (automation runs in background)
time.sleep(60)
print("Test complete.")
