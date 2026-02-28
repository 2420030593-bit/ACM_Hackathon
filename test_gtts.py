import asyncio
from services.voice_service import generate_speech

def test_gtts():
    print("Testing gTTS generation for English...")
    b64_en = generate_speech("Hello, I am ready to book your cab.", lang_code="en")
    print(f"English base64 len: {len(b64_en)}")

    print("Testing gTTS generation for Telugu...")
    b64_te = generate_speech("నమస్కారం, నేను మీ కోసం క్యాబ్ బుక్ చేస్తున్నాను.", lang_code="te")
    print(f"Telugu base64 len: {len(b64_te)}")

    print("Testing gTTS generation for Hindi...")
    b64_hi = generate_speech("नमस्ते, मैं आपकी कैब बुक कर रही हूँ।", lang_code="hi")
    print(f"Hindi base64 len: {len(b64_hi)}")

if __name__ == "__main__":
    test_gtts()
