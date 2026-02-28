import asyncio
import os
import wave
from services.voice_service import transcribe_pcm_bytes

def test_groq_stt():
    print("Testing Groq Whisper STT...")
    
    # Generate 1 sec of dummy silence/noise PCM data (16kHz, 16-bit mono)
    # Just to see if Groq API accepts and processes it properly
    dummy_pcm = b'\x00' * (16000 * 2) 
    
    try:
        text = transcribe_pcm_bytes(dummy_pcm)
        print(f"Transcribed (should be empty/noise): '{text}'")
        print("API Call Succeeded!")
    except Exception as e:
        print(f"Failed to test STT: {e}")

if __name__ == "__main__":
    test_groq_stt()
