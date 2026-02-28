import requests
import io

def generate_speech_direct(text: str, lang_code: str = "en"):
    print(f"Generating TTS for: {text} ({lang_code})")
    url = "https://translate.google.com/translate_tts"
    params = {
        "ie": "UTF-8",
        "q": text,
        "tl": lang_code,
        "client": "tw-ob"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200:
        print(f"Success! Audio size: {len(resp.content)} bytes")
        return resp.content
    else:
        print(f"Failed: {resp.status_code} - {resp.text}")
        return None

if __name__ == "__main__":
    generate_speech_direct("Hello, I am booking your cab.", "en")
    generate_speech_direct("నమస్కారం, నేను మీ క్యాబ్ బుక్ చేస్తున్నాను.", "te")
