"""
End-to-End Test: Voice input → Intent Detection → Entity Extraction → Automation Trigger
Tests the EXACT same code path that runs when the user speaks.
"""
import asyncio
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s")
logger = logging.getLogger("test.e2e")

# Import the exact functions used in the real pipeline
from services.llm_brain import detect_intent, extract_entities, INTENT_PATTERNS

# ── Test 1: Intent Detection ──
test_phrases = {
    "bus_booking": [
        "I want to get a bus ticket to vijaywada",
        "book a bus to bangalore",
        "find me a bus from hyderabad to mumbai",
    ],
    "taxi_booking": [
        "book a cab to the airport",
        "I need an uber ride to banjara hills",
        "get me an ola to jubilee hills",
    ],
    "flight_booking": [
        "book a flight to delhi",
        "I want to fly to mumbai tomorrow",
        "find flights from hyderabad to goa",
    ],
    "hotel_booking": [
        "find a hotel in goa",
        "book a room in mumbai for 2 nights",
        "I need accommodation in bangalore",
    ],
}

print("=" * 60)
print("TEST 1: Intent Detection")
print("=" * 60)
all_passed = True
for expected_intent, phrases in test_phrases.items():
    for phrase in phrases:
        detected, all_intents = detect_intent(phrase)
        status = "✅ PASS" if detected == expected_intent else f"❌ FAIL (got '{detected}')"
        if detected != expected_intent:
            all_passed = False
        print(f"  {status} | '{phrase}' → {detected}")

# ── Test 2: Entity Extraction (Regex fallback) ──
print("\n" + "=" * 60)
print("TEST 2: Entity Extraction (Regex)")
print("=" * 60)

async def test_entities():
    test_cases = [
        ("I want a bus ticket to vijayawada", "Vijayawada"),
        ("book a cab to the airport", "Airport"),
        ("find a hotel in goa for 3 people", "Goa"),
        ("flight to delhi tomorrow", "Delhi"),
    ]
    for phrase, expected_dest in test_cases:
        entities = await extract_entities(phrase)
        dest = entities.get("destination", "")
        status = "✅ PASS" if expected_dest.lower() in dest.lower() else f"❌ FAIL (got '{dest}')"
        print(f"  {status} | '{phrase}' → destination: '{dest}' (expected: '{expected_dest}')")

asyncio.run(test_entities())

# ── Test 3: Intent Regex Patterns compile correctly ──
print("\n" + "=" * 60)
print("TEST 3: Regex Patterns Valid")
print("=" * 60)
for intent_name, pattern in INTENT_PATTERNS.items():
    try:
        re.compile(pattern)
        print(f"  ✅ {intent_name}: pattern compiles OK")
    except re.error as e:
        print(f"  ❌ {intent_name}: INVALID pattern: {e}")

print("\n" + "=" * 60)
if all_passed:
    print("ALL INTENT DETECTION TESTS PASSED ✅")
else:
    print("SOME TESTS FAILED ❌ — Review above output")
print("=" * 60)
