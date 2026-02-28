import os
import json
import wave
from vosk import Model, KaldiRecognizer

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "vosk-model-en-us-0.22-lgraph"))
print(f"LOADING VOSK MODEL FROM: {MODEL_PATH}")

_model = None
try:
    if os.path.exists(MODEL_PATH):
        print("Found large model folder. Contents:")
        try:
            print(os.listdir(MODEL_PATH))
        except:
            pass
        print("Initializing large model...")
        _model = Model(MODEL_PATH)
    else:
        print(f"CRITICAL: Large model not found at {MODEL_PATH}")
        SMALL_MODEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "vosk-model-small-en-us-0.15"))
        if os.path.exists(SMALL_MODEL):
            print("Falling back to small model...")
            _model = Model(SMALL_MODEL)
except Exception as e:
    print(f"Error loading Vosk model: {e}")

import logging

logger = logging.getLogger("aura.stt")

def get_recognizer(sample_rate: int = 16000):
    if not _model:
        return None
    return KaldiRecognizer(_model, sample_rate)

def transcribe_audio(audio_path: str) -> str:
    if not _model:
        logger.error("Vosk model not loaded.")
        return ""
    
    try:
        wf = wave.open(audio_path, "rb")
    except Exception as e:
        logger.error("Failed to open audio file %s: %s", audio_path, e)
        # Try to diagnose file type
        with open(audio_path, "rb") as f:
            header = f.read(12)
            logger.info("File header: %s", header)
        return ""

    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        logger.warning("Audio format mismatch: channels=%d, sampwidth=%d, comptype=%s",
                       wf.getnchannels(), wf.getsampwidth(), wf.getcomptype())
        
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
    
    transcript = " ".join([res.get("text", "") for res in results if res.get("text")])
    return transcript.strip()
