"""
╔═══════════════════════════════════════════════════════════════════╗
║   AURA v2 – Autonomous Universal Reservation Assistant            ║
║   FastAPI backend with full feature stack                         ║
╚═══════════════════════════════════════════════════════════════════╝
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars directly

# ── Paths ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
DB_PATH = os.path.join(BASE_DIR, "aura.db")
BOOKINGS_PATH = os.path.join(BASE_DIR, "bookings.json")

# ── Vosk STT ──
VOSK_MODEL_LARGE = os.path.join(MODEL_DIR, "vosk-model-en-us-0.22-lgraph")
VOSK_MODEL_SMALL = os.path.join(MODEL_DIR, "vosk-model-small-en-us-0.15")

# ── Ollama LLM ──
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

# ── Groq Cloud LLM (free, fast — used for browser automation agent) ──
# Get a free API key at https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ── Server ──
HOST = "0.0.0.0"
PORT = 8001
FRONTEND_URL = "http://localhost:5173"

# ── Encryption ──
ENCRYPTION_KEY = os.getenv("AURA_ENCRYPTION_KEY", "aura-default-key-change-in-production")

# ── TTS Personas ──
TTS_PERSONAS = {
    "elysia": {"rate": 160, "volume": 0.9},
    "atlas": {"rate": 180, "volume": 1.0},
    "nova": {"rate": 200, "volume": 0.95},
}
DEFAULT_PERSONA = "elysia"

# ── Supported Languages ──
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ja": "Japanese",
    "fr": "French",
}

# ── Emergency Data ──
EMBASSY_DATA = {
    "us": {"name": "US Embassy", "phone": "+1-202-501-4444"},
    "in": {"name": "Indian Embassy", "phone": "+91-11-2419-8000"},
    "jp": {"name": "Japan Embassy", "phone": "+81-3-3224-5000"},
    "fr": {"name": "French Embassy", "phone": "+33-1-43-12-22-22"},
}
