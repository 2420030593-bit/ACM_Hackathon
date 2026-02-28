"""
╔═══════════════════════════════════════════════════════════════════╗
║   AURA – Autonomous Universal Reservation Assistant              ║
║   A multilingual voice-first AI concierge backend                ║
║                                                                   ║
║   Endpoints:                                                      ║
║     POST /process   →  Process spoken text & return booking info  ║
║     GET  /health    →  Health check                               ║
║     GET  /          →  Welcome message                            ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import logging
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sock import Sock

from services.language import detect_language, translate_to_english, translate_back
from services.intent import detect_intent
from services.booking import generate_response
from services.tts import generate_speech_audio
from services.automation import trigger_automation
from services.session import (
    get_session, clear_session, start_hotel_session, process_session_input
)
from services.stt_offline import transcribe_audio

# ──────────────────────────────────────────────
#  Logging Configuration
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("aura.app")

import time
from datetime import datetime

# ──────────────────────────────────────────────
#  Flask App
# ──────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)
sock = Sock(app)


@app.route("/", methods=["GET"])
def home():
    """Serve the frontend UI."""
    return send_from_directory("static", "index.html")


@app.route("/api/info", methods=["GET"])
def api_info():
    """API info endpoint."""
    return jsonify({
        "application": "AURA – Autonomous Universal Reservation Assistant",
        "version": "1.0.0",
        "description": "Multilingual voice-first AI concierge backend",
        "endpoints": {
            "POST /process": "Process spoken text and return booking confirmations",
            "GET  /health": "Health check",
        },
        "supported_intents": [
            "taxi_booking",
            "tour_booking",
            "restaurant_booking",
            "hotel_booking",
            "spa_booking",
        ],
        "example_request": {
            "url": "POST /process",
            "body": {"text": "Necesito un taxi al aeropuerto"},
        },
    })


@app.route("/health", methods=["GET"])
def health():
    """Simple health check."""
    return jsonify({"status": "healthy", "service": "AURA"}), 200


@app.route("/process", methods=["POST"])
def process():
    """
    Main processing pipeline:
      1. Validate input
      2. Detect language
      3. Translate to English
      4. Detect intent(s)
      5. Generate booking response(s)
      6. Translate response(s) back to original language
      7. Return structured JSON
    """
    # ── Step 0: Validate input ──────────────────
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        logger.warning("Request missing 'text' field.")
        return jsonify({
            "error": "Missing 'text' field in request body.",
            "hint": "Send JSON like: {\"text\": \"I need a taxi\"}",
        }), 400

    user_text = data["text"].strip()
    if not user_text:
        logger.warning("Empty text received.")
        return jsonify({
            "error": "The 'text' field is empty.",
            "hint": "Please provide a spoken sentence to process.",
        }), 400

    logger.info("═" * 50)
    logger.info("Incoming text: '%s'", user_text)

    # ── Check for active session (multi-turn) ──
    session = get_session()
    if session:
        logger.info("Active session: %s (step: %s)", session["type"], session["step"])

        # Detect language for the follow-up
        lang_info = detect_language(user_text)
        detected_lang = lang_info["lang_code"]
        english_text = translate_to_english(user_text, detected_lang)

        result = process_session_input(english_text)

        if result and result.get("complete"):
            # All info collected — trigger automation with full details
            sess = result["session"]
            message = result["question"]
            translated_msg = translate_back(message, detected_lang)
            audio_b64 = generate_speech_audio(translated_msg, detected_lang)

            # Save booking to persistent storage
            booking_entry = {
                "id": str(int(time.time())),
                "intent": "hotel_booking",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "hotel": sess["hotel"],
                    "check_in": sess["checkin"].strftime("%Y-%m-%d"),
                    "check_out": sess["checkout"].strftime("%Y-%m-%d"),
                    "adults": sess["adults"],
                    "children": sess["children"]
                }
            }
            save_booking(booking_entry)

            # Trigger Booking.com
            trigger_automation(
                "hotel_booking",
                sess["hotel"],
                checkin=sess["checkin"],
                checkout=sess["checkout"],
                adults=sess["adults"],
                children=sess["children"]
            )
            clear_session()

            return jsonify({
                "detected_language": detected_lang,
                "detected_language_name": lang_info["lang_name"],
                "original_text": user_text,
                "translated_text": english_text,
                "intents": ["Hotel Booking"],
                "response": translated_msg,
                "bookings": [{
                    "intent": "hotel_booking",
                    "status": "confirmed",
                    "details": {
                        "hotel": sess["hotel"],
                        "check_in": sess["checkin"].strftime("%B %d, %Y"),
                        "check_out": sess["checkout"].strftime("%B %d, %Y"),
                        "adults": sess["adults"],
                        "children": sess["children"],
                    },
                    "message": message,
                }],
                "audio": audio_b64,
                "automation_triggered": True,
            }), 200

        elif result:
            # Still collecting info — ask next question
            message = result["question"]
            translated_msg = translate_back(message, detected_lang)
            audio_b64 = generate_speech_audio(translated_msg, detected_lang)

            return jsonify({
                "detected_language": detected_lang,
                "detected_language_name": lang_info["lang_name"],
                "original_text": user_text,
                "translated_text": english_text,
                "intents": ["Hotel Booking"],
                "response": translated_msg,
                "bookings": [],
                "audio": audio_b64,
                "automation_triggered": False,
                "auto_listen": True,  # Frontend should start listening again
            }), 200

    # ── Normal pipeline (no active session) ────

    # ── Step 1: Detect language ─────────────────
    lang_info = detect_language(user_text)
    detected_lang = lang_info["lang_code"]
    detected_lang_name = lang_info["lang_name"]
    logger.info("Detected → %s (%s)", detected_lang_name, detected_lang)

    # ── Step 2: Translate to English ────────────
    english_text = translate_to_english(user_text, detected_lang)
    logger.info("English text → '%s'", english_text)

    # ── Step 3: Detect intent(s) ────────────────
    intents = detect_intent(english_text)
    intent_labels = [i["label"] for i in intents]
    logger.info("Intents → %s", intent_labels)

    # ── Step 4: Generate booking responses ──────
    responses = generate_response(intents, english_text)

    # ── Check if hotel intent → start session ───
    for resp in responses:
        if resp["intent"] == "hotel_booking":
            hotel_name = resp.get("details", {}).get("hotel", "")
            
            start_hotel_session(hotel_name, detected_lang)
            if hotel_name:
                # Hotel name known → ask budget next
                question = f"Sure! I'll find {hotel_name} for you. What's your budget per night? Say something like '2000 to 3000 rupees' or 'under 5000', or say 'any budget'."
            else:
                # No hotel name → ask for it first
                question = "Sure! Which hotel or area would you like to stay in?"

            translated_q = translate_back(question, detected_lang)
            audio_b64 = generate_speech_audio(translated_q, detected_lang)

            return jsonify({
                "detected_language": detected_lang,
                "detected_language_name": detected_lang_name,
                "original_text": user_text,
                "translated_text": english_text,
                "intents": intent_labels,
                "response": translated_q,
                "bookings": [],
                "audio": audio_b64,
                "automation_triggered": False,
                "auto_listen": True,
            }), 200

    # ── Step 5: Translate responses back ────────
    for resp in responses:
        resp["message_translated"] = translate_back(resp["message"], detected_lang)

    # ── Step 6: Build final output ──────────────
    combined_message = " | ".join(r["message_translated"] for r in responses)

    # ── Step 7: Generate speech audio (gTTS) ────
    audio_b64 = generate_speech_audio(combined_message, detected_lang)

    # ── Step 8: Trigger browser automation ─────
    for resp in responses:
        intent_tag = resp.get("intent", "")
        # Extract destination from details
        details = resp.get("details", {})
        destination = details.get("destination") \
                   or details.get("restaurant") \
                   or details.get("hotel") \
                   or details.get("tour_name", "").replace(" Tour", "") \
                   or ""

        if destination and intent_tag not in ("general_help", "hotel_booking"):
            trigger_automation(intent_tag, destination)
            # Save these as well
            booking_entry = {
                "id": str(int(time.time())),
                "intent": intent_tag,
                "timestamp": datetime.now().isoformat(),
                "details": details
            }
            save_booking(booking_entry)

    output = {
        "detected_language": detected_lang,
        "detected_language_name": detected_lang_name,
        "original_text": user_text,
        "translated_text": english_text,
        "intents": intent_labels,
        "response": combined_message,
        "bookings": responses,
        "audio": audio_b64,
        "automation_triggered": True,
    }

    logger.info("Response sent successfully.")
    logger.info("═" * 50)

    return jsonify(output), 200

def save_booking(entry):
    path = "bookings.json"
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(entry)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to save booking: %s", e)

@app.route("/bookings", methods=["GET"])
def bookings_page():
    return send_from_directory("static", "bookings.html")

@app.route("/api/bookings", methods=["GET"])
def get_bookings_api():
    try:
        if os.path.exists("bookings.json"):
            with open("bookings.json", "r") as f:
                return jsonify(json.load(f))
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sock.route('/ws/stt')
def stt_stream(ws):
    """
    WebSocket for live STT preview.
    Receives raw PCM audio chunks and returns JSON transcripts.
    """
    from services.stt_offline import get_recognizer
    rec = get_recognizer(16000)
    
    logger.info("New WebSocket connection for STT")
    while True:
        data = ws.receive()
        if not data:
            logger.info("WebSocket connection closed")
            break
        
        # logger.debug(f"Received {len(data)} bytes of audio")
        
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            if res.get("text"):
                logger.info(f"Final partial: {res['text']}")
                ws.send(json.dumps({"text": res["text"], "final": True}))
        else:
            res = json.loads(rec.PartialResult())
            if res.get("partial"):
                # logger.debug(f"Partial: {res['partial']}")
                ws.send(json.dumps({"text": res["partial"], "final": False}))

    # Send final result when socket closes
    res = json.loads(rec.FinalResult())
    if res.get("text"):
        logger.info(f"Final result: {res['text']}")
        ws.send(json.dumps({"text": res["text"], "final": True}))


# ──────────────────────────────────────────────
#  Error Handlers
# ──────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "hint": "Try POST /process"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "hint": "Use POST for /process"}), 405


@app.errorhandler(500)
def internal_error(e):
    logger.error("Internal server error: %s", e)
    return jsonify({"error": "Internal server error", "message": str(e)}), 500


# ──────────────────────────────────────────────
#  Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 Starting AURA – Autonomous Universal Reservation Assistant")
    logger.info("   Listening on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
