import logging
logging.basicConfig(level=logging.INFO)

from services.automation import trigger_automation
import time

def run_llm_tests():
    print("Testing Uber via LLM...")
    trigger_automation("taxi_booking", "Airport", pickup="Banjara Hills")
    time.sleep(30)
    
    print("\nTesting Redbus via LLM...")
    trigger_automation("bus_booking", "Vijayawada", pickup="Hyderabad")
    time.sleep(30)

    print("\nTesting Google Flights via LLM...")
    trigger_automation("flight_booking", "Delhi", pickup="Hyderabad")
    time.sleep(30)

if __name__ == "__main__":
    run_llm_tests()
