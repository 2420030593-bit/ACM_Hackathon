import time
from services.automation import trigger_automation

print("Testing Redbus...")
trigger_automation("bus_booking", "Bangalore", pickup="Hyderabad")

time.sleep(10)

print("Testing Ola...")
trigger_automation("taxi_booking", "Airport", pickup="Banjara Hills")

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Test finished.")
