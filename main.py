"""
╔═══════════════════════════════════════════════════════════════════╗
║   AURA v2 – Autonomous Universal Reservation Assistant            ║
║   FastAPI Backend – All 19 Features                               ║
║                                                                   ║
║   Endpoints:                                                      ║
║     POST /agent/process     → Main voice/text processing          ║
║     WS   /ws/stt            → Live STT streaming                  ║
║     WS   /ws/monitor        → Price monitoring notifications      ║
║     POST /voice/speak       → TTS generation                      ║
║     POST /translate         → Translation                         ║
║     POST /automation/execute → Browser automation                 ║
║     GET  /bookings          → Booking history                     ║
║     GET  /emergency/:code   → Emergency info                     ║
║     POST /profile           → Save profile                        ║
║     GET  /profile           → Get profile                         ║
║     POST /itinerary         → Generate itinerary                  ║
║     POST /monitor/add       → Add price monitor                   ║
║     GET  /health            → Health check                        ║
╚═══════════════════════════════════════════════════════════════════╝
"""
import logging
import os
import json
import asyncio
import base64
import tempfile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

from config import HOST, PORT, FRONTEND_URL
from database.db import (
    get_db, close_db, save_booking, get_all_bookings,
    save_profile as db_save_profile, get_profile as db_get_profile,
)
from database.models import (
    AgentRequest, AgentResponse, TranslationRequest, EmergencyRequest,
    ProfileField, MemoryEntry, PriceWatchRequest, ItineraryRequest,
    AutomationRequest, VoiceInput,
)
from services.voice_service import (
    get_recognizer, generate_speech, transcribe_pcm_bytes,
    detect_emotion_from_pcm,
)
from services.llm_brain import process_with_llm
from services.translation_service import detect_language, translate_text, translate_to_english, translate_from_english
from services.booking_service import generate_booking_response
from services.emergency_service import get_emergency_info
from services.profile_service import prepare_for_storage, get_autofill_data
from services.monitoring_service import (
    add_monitor, get_all_monitors, cancel_monitor,
    register_ws_client, remove_ws_client,
)
from services.itinerary_service import (
    generate_itinerary, generate_voice_summary, generate_pdf_itinerary,
)
from agents.planner import plan_and_execute
from agents.memory import remember, recall, get_context_for_llm
from services.auth_service import (
    create_access_token, verify_google_token,
    register_user, authenticate_user, get_or_create_google_user,
    get_current_user,
)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.FileHandler("server.log"), logging.StreamHandler()]
)
logger = logging.getLogger("aura.app")


# ── App Lifecycle ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AURA v2 starting up...")
    await get_db()  # Initialize database
    yield
    await close_db()
    logger.info("AURA v2 shut down.")


app = FastAPI(title="AURA v2", lifespan=lifespan)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files (serve frontend build) ──
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ═══════════════════════════════════════════════
#  AUTH MODELS
# ═══════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str


# ═══════════════════════════════════════════════
#  AUTH ENDPOINTS (public)
# ═══════════════════════════════════════════════

@app.post("/auth/register")
async def auth_register(req: RegisterRequest):
    """Register a new user with email/password."""
    user = register_user(req.email, req.password, req.name)
    if not user:
        raise HTTPException(status_code=400, detail="Email already registered")
    token = create_access_token({"email": user["email"], "name": user["name"], "provider": "local"})
    return {"token": token, "user": {"email": user["email"], "name": user["name"], "provider": "local"}}


@app.post("/auth/login")
async def auth_login(req: LoginRequest):
    """Login with email/password."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"email": user["email"], "name": user["name"], "provider": "local"})
    return {"token": token, "user": {"email": user["email"], "name": user["name"], "provider": "local"}}


@app.post("/auth/google")
async def auth_google(req: GoogleLoginRequest):
    """Login via Google OAuth."""
    google_user = await verify_google_token(req.id_token)
    if not google_user:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    user = get_or_create_google_user(google_user["email"], google_user["name"], google_user.get("picture", ""))
    token = create_access_token({
        "email": user["email"], "name": user["name"],
        "picture": user.get("picture", ""), "provider": "google"
    })
    return {"token": token, "user": {"email": user["email"], "name": user["name"], "picture": user.get("picture", ""), "provider": "google"}}


@app.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    """Get current authenticated user."""
    return user


# ═══════════════════════════════════════════════
#  MAIN ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/")
async def root():
    """Serve the frontend index.html."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AURA v2 Backend Online", "status": "ready"}


@app.get("/health")
async def health():
    return {
        "status": "online",
        "version": "2.0.0",
        "services": {
            "stt": "vosk",
            "tts": "pyttsx3",
            "llm": "ollama",
            "automation": "playwright",
        }
    }


# ═══════════════════════════════════════════════
#  AGENT PROCESSING (Core Brain)
# ═══════════════════════════════════════════════

@app.post("/agent/process")
async def agent_process(req: AgentRequest, user=Depends(get_current_user)):
    """
    Main processing endpoint. Takes text, runs through:
    Language Detection → Translation → LLM Intent → Booking → Response → TTS
    """
    try:
        user_text = req.text.strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="Empty text")

        logger.info(f"═{'═'*49}")
        logger.info(f"Input: '{user_text}'")

        # 1. Detect language
        lang_info = detect_language(user_text)
        detected_lang = lang_info["lang_code"]
        logger.info(f"Language: {lang_info['lang_name']} ({detected_lang})")

        # 2. Translate to English if needed
        english_text = user_text
        if detected_lang != "en":
            english_text = await translate_to_english(user_text, detected_lang)
            logger.info(f"Translated: '{english_text}'")

        # 3. Plan and execute (LLM + booking + memory)
        result = await plan_and_execute(english_text, detected_lang)
        logger.info(f"Intent: {result['intent']} | Source: {result.get('source', '?')}")

        # 4. Translate response back if needed
        response_text = result["response_text"]
        if detected_lang != "en" and response_text:
            response_text = await translate_from_english(response_text, detected_lang)

        # 5. Generate TTS audio
        audio_b64 = generate_speech(response_text, lang_code=detected_lang)

        # 6. Save booking if applicable
        booking = result.get("booking", {})
        if booking.get("status") in ("confirmed", "searching"):
            await save_booking(
                result["intent"],
                booking.get("details", {}),
                booking.get("status", "confirmed")
            )

        # Build output
        output = {
            "detected_language": detected_lang,
            "detected_language_name": lang_info["lang_name"],
            "original_text": user_text,
            "translated_text": english_text,
            "intent": result["intent"],
            "intents": result.get("all_intents", [result["intent"]]),
            "response": response_text,
            "explanation": result["explanation"],
            "actions": result["actions"],
            "mode": result["mode"],
            "bookings": [booking] if booking.get("details") else [],
            "audio": audio_b64,
            "automation_triggered": result.get("requires_automation", False),
            "auto_listen": result.get("requires_followup", False),
            "itinerary": result.get("itinerary"),
            "source": result.get("source", "unknown"),
        }

        logger.info("Response sent successfully.")
        logger.info(f"═{'═'*49}")
        return JSONResponse(output)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════
#  VOICE ENDPOINTS
# ═══════════════════════════════════════════════

@app.post("/voice/speak")
async def voice_speak(req: VoiceInput, user=Depends(get_current_user)):
    """Generate TTS for given text."""
    audio_b64 = generate_speech(req.text)
    return {"audio": audio_b64, "text": req.text}

@app.post("/voice/transcribe")
async def voice_transcribe(request: Request, user=Depends(get_current_user)):
    """Transcribe raw 16kHz PCM Int16 audio bytes using offline Vosk."""
    pcm_data = await request.body()
    try:
        text = transcribe_pcm_bytes(pcm_data)
        logger.info(f"POST Transcription successful: {text}")
    except Exception as e:
        logger.error(f"POST Transcription error: {e}")
        text = ""
        
    return {"text": text}


# ── WebSocket: Live STT ──
@app.websocket("/ws/stt")
async def ws_stt(ws: WebSocket):
    """WebSocket for live speech-to-text streaming."""
    await ws.accept()
    logger.info("WebSocket STT connected")

    rec = get_recognizer(16000)
    if not rec:
        await ws.send_json({"error": "Vosk model not loaded"})
        await ws.close()
        return

    try:
        while True:
            data = await ws.receive_bytes()
            if not data:
                break

            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if res.get("text"):
                    logger.info(f"STT final: {res['text']}")
                    await ws.send_json({"text": res["text"], "final": True})
            else:
                res = json.loads(rec.PartialResult())
                if res.get("partial"):
                    await ws.send_json({"text": res["partial"], "final": False})

    except WebSocketDisconnect:
        logger.info("WebSocket STT disconnected")
    except Exception as e:
        logger.error(f"WebSocket STT error: {e}")
    finally:
        # Send final result
        try:
            res = json.loads(rec.FinalResult())
            if res.get("text"):
                await ws.send_json({"text": res["text"], "final": True})
        except:
            pass


# ═══════════════════════════════════════════════
#  TRANSLATION ENDPOINT
# ═══════════════════════════════════════════════

@app.post("/translate")
async def translate_endpoint(req: TranslationRequest, user=Depends(get_current_user)):
    """Bidirectional translation with TTS."""
    source = req.source_lang
    if source == "auto":
        lang_info = detect_language(req.text)
        source = lang_info["lang_code"]

    translated = await translate_text(req.text, source, req.target_lang)
    
    # Generate audio for the translated text
    audio_b64 = generate_speech(translated, lang_code=req.target_lang)
    
    return {
        "original": req.text,
        "translated": translated,
        "source_lang": source,
        "target_lang": req.target_lang,
        "audio": audio_b64,
    }


# ═══════════════════════════════════════════════
#  BOOKING ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/bookings")
async def get_bookings(user=Depends(get_current_user)):
    """Get all booking history."""
    return await get_all_bookings()


@app.get("/bookings/page")
async def bookings_page():
    """Serve the bookings HTML page."""
    path = os.path.join(static_dir, "bookings.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Page not found"}


# ═══════════════════════════════════════════════
#  EMERGENCY ENDPOINT
# ═══════════════════════════════════════════════

@app.get("/emergency/{country_code}")
async def emergency(country_code: str, situation: str = "general"):
    """Get emergency info for a country."""
    return get_emergency_info(country_code, situation)


# ═══════════════════════════════════════════════
#  PROFILE ENDPOINTS
# ═══════════════════════════════════════════════

@app.post("/profile")
async def save_profile_endpoint(field: ProfileField, user=Depends(get_current_user)):
    """Save a profile field (encrypted if sensitive)."""
    stored_value, is_encrypted = prepare_for_storage(field.field_name, field.field_value)
    await db_save_profile(field.field_name, stored_value, is_encrypted)
    return {"status": "saved", "field": field.field_name}


@app.get("/profile")
async def get_profile_endpoint(user=Depends(get_current_user)):
    """Get user profile."""
    profile = await db_get_profile()
    return {"profile": profile, "autofill": get_autofill_data(profile)}


# ═══════════════════════════════════════════════
#  MEMORY ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/memory")
async def get_memories_endpoint(category: str = None):
    """Get stored memories."""
    return await recall(category)


@app.post("/memory")
async def save_memory_endpoint(entry: MemoryEntry):
    """Save a memory entry."""
    await remember(entry.category, entry.key, entry.value)
    return {"status": "remembered"}


# ═══════════════════════════════════════════════
#  MONITORING ENDPOINTS
# ═══════════════════════════════════════════════

@app.post("/monitor/add")
async def add_monitor_endpoint(req: PriceWatchRequest):
    """Add a new price monitor."""
    monitor = await add_monitor(req.watch_type, req.query, req.target_price)
    return {"status": "monitoring", "monitor": monitor}


@app.get("/monitor/list")
async def list_monitors():
    """List all monitors."""
    return get_all_monitors()


@app.post("/monitor/cancel/{monitor_id}")
async def cancel_monitor_endpoint(monitor_id: int):
    success = cancel_monitor(monitor_id)
    return {"status": "cancelled" if success else "not_found"}


@app.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket):
    """WebSocket for price monitoring alerts."""
    await ws.accept()
    register_ws_client(ws)
    try:
        while True:
            await ws.receive_text()  # Keep alive
    except WebSocketDisconnect:
        remove_ws_client(ws)


# ═══════════════════════════════════════════════
#  ITINERARY ENDPOINTS
# ═══════════════════════════════════════════════

@app.post("/itinerary")
async def create_itinerary(req: ItineraryRequest, user=Depends(get_current_user)):
    """Generate a trip itinerary."""
    itinerary = generate_itinerary(
        req.destination, req.days, req.budget, req.preferences
    )
    voice_summary = generate_voice_summary(itinerary)
    audio_b64 = generate_speech(voice_summary)
    return {
        "itinerary": itinerary,
        "voice_summary": voice_summary,
        "audio": audio_b64,
    }


@app.post("/itinerary/pdf")
async def export_itinerary_pdf(req: ItineraryRequest):
    """Generate and return a PDF itinerary."""
    itinerary = generate_itinerary(
        req.destination, req.days, req.budget, req.preferences
    )
    pdf_path = generate_pdf_itinerary(itinerary)
    if pdf_path and os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf",
                          filename=f"aura_itinerary_{req.destination}.pdf")
    raise HTTPException(status_code=500, detail="PDF generation failed")


# ═══════════════════════════════════════════════
#  AUTOMATION ENDPOINT
# ═══════════════════════════════════════════════

@app.post("/automation/execute")
async def execute_automation(req: AutomationRequest):
    """Trigger browser automation for booking."""
    try:
        from services.automation import trigger_automation
        details = req.details.copy()
        details.pop("destination", None)  # Prevent multiple values for argument 'destination'
        result = trigger_automation(req.intent, req.destination, **details)
        return {"status": "executed", "result": result}
    except Exception as e:
        logger.error(f"Automation error: {e}")
        return {"status": "failed", "error": str(e), "recovery": "Will retry with alternative approach."}


# ═══════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.exception_handler(500)
async def internal_error(request, exc):
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# ═══════════════════════════════════════════════
#  RUN
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AURA v2 - Autonomous Universal Reservation Assistant")
    logger.info(f"   Listening on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
