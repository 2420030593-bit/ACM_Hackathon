import time
import logging

logging.basicConfig(level=logging.INFO)

from services.automation import (
    _automate_uber,
    _automate_ola,
    _automate_redbus,
    _automate_booking_com,
    _automate_google_flights,
    _automate_zomato
)

# Monkeypatch keepalive so it doesn't wait 10 mins during test
import services.automation
services.automation.BROWSER_KEEP_ALIVE = 5

def run_tests():
    print("Testing Uber...")
    try:
        _automate_uber("Airport", "Banjara Hills")
        print("Uber TEST PASSED")
    except Exception as e:
        print(f"Uber TEST FAILED: {e}")

    print("\nTesting Ola...")
    try:
        _automate_ola("Airport", "Banjara Hills")
        print("Ola TEST PASSED")
    except Exception as e:
        print(f"Ola TEST FAILED: {e}")

    print("\nTesting Redbus...")
    try:
        _automate_redbus("Vijayawada", "Hyderabad")
        print("Redbus TEST PASSED")
    except Exception as e:
        print(f"Redbus TEST FAILED: {e}")

    print("\nTesting Google Flights...")
    try:
        _automate_google_flights("Delhi", "Hyderabad")
        print("Google Flights TEST PASSED")
    except Exception as e:
        print(f"Google Flights TEST FAILED: {e}")

    print("\nTesting Booking.com...")
    try:
        _automate_booking_com("Goa", "Hyderabad")
        print("Booking.com TEST PASSED")
    except Exception as e:
        print(f"Booking.com TEST FAILED: {e}")

    print("\nTesting Zomato...")
    try:
        _automate_zomato("Paradise Biryani", "Hyderabad")
        print("Zomato TEST PASSED")
    except Exception as e:
        print(f"Zomato TEST FAILED: {e}")

if __name__ == "__main__":
    run_tests()
