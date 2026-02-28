"""
Voice Service – Optional Vosk STT + pyttsx3 TTS
STT is handled by browser Web Speech API; Vosk is optional fallback.
"""
import os, json, wave, tempfile, base64, logging, struct

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

import pyttsx3
from config import VOSK_MODEL_LARGE, VOSK_MODEL_SMALL, TTS_PERSONAS, DEFAULT_PERSONA

logger = logging.getLogger("aura.voice")

# ── Load Vosk Model (optional – STT is done in browser now) ──
_model = None
if VOSK_AVAILABLE:
    for path in [VOSK_MODEL_LARGE, VOSK_MODEL_SMALL]:
        if os.path.exists(path):
            try:
                _model = Model(path)
                logger.info(f"Loaded Vosk model from {path}")
                break
            except Exception as e:
                logger.warning(f"Failed to load Vosk model {path}: {e}")

if not _model:
    logger.info("Vosk STT not available – using browser Web Speech API instead")


def get_recognizer(sample_rate: int = 16000):
    """Create a new KaldiRecognizer for streaming STT."""
    if not _model:
        return None
    return KaldiRecognizer(_model, sample_rate)


def transcribe_audio_file(audio_path: str) -> str:
    """Transcribe a WAV file to text."""
    if not _model:
        return ""
    try:
        wf = wave.open(audio_path, "rb")
    except Exception as e:
        logger.error(f"Failed to open audio: {e}")
        return ""

    rec = KaldiRecognizer(_model, wf.getframerate())
    rec.SetWords(True)
    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(json.loads(rec.Result()))
    results.append(json.loads(rec.FinalResult()))
    wf.close()
import io
import requests
from config import GROQ_API_KEY

def transcribe_pcm_bytes(pcm_data: bytes, sample_rate: int = 16000) -> str:
    """Transcribe raw PCM Int16 bytes to text.
    First tries Groq Whisper (ultra-fast, multi-lingual).
    Falls back to offline Vosk if Groq fails or is unavailable.
    """
    if GROQ_API_KEY:
        try:
            # Convert raw PCM to a valid WAV file in memory
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_data)
            
            wav_bytes = wav_io.getvalue()
            
            resp = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": ("audio.wav", wav_bytes, "audio/wav")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "response_format": "json"
                },
                timeout=10
            )
            if resp.status_code == 200:
                text = resp.json().get("text", "").strip()
                logger.info(f"Groq Whisper transcribed: {text}")
                return text
            else:
                logger.warning(f"Groq Whisper failed (HTTP {resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            logger.error(f"Groq Whisper exception: {e}")
            logger.info("Falling back to local offline Vosk STT...")

    # Fallback to local offline Vosk
    if not _model:
        return ""
    rec = KaldiRecognizer(_model, sample_rate)
    rec.SetWords(True)
    chunk_size = 8000
    for i in range(0, len(pcm_data), chunk_size):
        # type hint ignore for the slice, standard python bytes slicing works fine at runtime
        rec.AcceptWaveform(pcm_data[i:i+chunk_size])
    result = json.loads(rec.FinalResult())
    text = result.get("text", "").strip()
    logger.info(f"Vosk STT transcribed: {text}")
    return text


def generate_speech(text: str, persona: str = DEFAULT_PERSONA, lang_code: str = "en") -> str:
    """Generate TTS audio and return as base64-encoded WAV/MP3 string.
    First tries Google TTS (dependency-free API) for high-quality multi-lingual support (all Indian languages).
    Falls back to local pyttsx3.
    """
    if not text:
        return ""
    
    # Try online Google TTS first (high-quality, multi-lingual, dependency-free)
    try:
        url = "https://translate.google.com/translate_tts"
        params = {"ie": "UTF-8", "q": text, "tl": lang_code, "client": "tw-ob"}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            audio_data = resp.content
            # We can safely return MP3 base64 to frontend
            return base64.b64encode(audio_data).decode("utf-8")
        else:
            logger.warning(f"Online TTS failed (HTTP {resp.status_code}). Falling back to local pyttsx3.")
    except Exception as e:
        logger.warning(f"Online TTS exception: {e}. Falling back to local pyttsx3.")

    # Fallback to local offline pyttsx3
    try:
        engine = pyttsx3.init()
        settings = TTS_PERSONAS.get(persona, TTS_PERSONAS[DEFAULT_PERSONA])
        engine.setProperty("rate", settings["rate"])
        engine.setProperty("volume", settings["volume"])

        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        engine.stop()

        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        os.unlink(tmp_path)

        return base64.b64encode(audio_data).decode("utf-8")
    except Exception as e:
        logger.error(f"Local TTS error: {e}")
        return ""


def detect_emotion_from_pcm(pcm_data: bytes) -> str:
    """Basic emotion detection from audio energy levels."""
    if len(pcm_data) < 100:
        return "neutral"
    try:
        samples = struct.unpack(f"<{len(pcm_data)//2}h", pcm_data)
        rms = (sum(s*s for s in samples) / len(samples)) ** 0.5
        if rms > 8000:
            return "stressed"
        elif rms > 4000:
            return "energetic"
        elif rms < 500:
            return "calm"
        return "neutral"
    except:
        return "neutral"
