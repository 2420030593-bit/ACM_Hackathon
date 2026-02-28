# 🌟 AURA – Autonomous Universal Reservation Assistant

A multilingual voice-first AI concierge backend built with Flask.

AURA can understand spoken text in **any language**, detect the user's intent, simulate a realistic booking, and respond back **in the user's original language**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **Multilingual** | Detects language automatically and translates input/output |
| 🧠 **Intent Detection** | Keyword-based with multi-intent support in a single sentence |
| 🚕 **Taxi Booking** | Simulated with driver, vehicle, ETA, and fare |
| 🗺️ **Tour Booking** | City tours with guide, date, and duration |
| 🍽️ **Restaurant Booking** | Table reservations with cuisine type and seating |
| 🏨 **Hotel Booking** | Room booking with type, dates, and cost |
| 🧖 **Spa Booking** | Wellness appointments with treatment details |
| 📝 **Logging** | Structured request/response logging |
| ⚠️ **Error Handling** | Graceful validation for empty/missing input |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
python app.py
```

The server starts at `http://127.0.0.1:5000`.

### 3. Test with curl

**English:**
```bash
curl -X POST http://127.0.0.1:5000/process -H "Content-Type: application/json" -d "{\"text\": \"I need a taxi to the airport\"}"
```

**Spanish:**
```bash
curl -X POST http://127.0.0.1:5000/process -H "Content-Type: application/json" -d "{\"text\": \"Necesito un taxi al aeropuerto\"}"
```

**Hindi:**
```bash
curl -X POST http://127.0.0.1:5000/process -H "Content-Type: application/json" -d "{\"text\": \"मुझे एक टैक्सी चाहिए\"}"
```

**Multi-intent (English):**
```bash
curl -X POST http://127.0.0.1:5000/process -H "Content-Type: application/json" -d "{\"text\": \"Book me a taxi and reserve a restaurant table\"}"
```

---

## 📦 Project Structure

```
AURALAVDA/
├── app.py               # Flask server & /process endpoint
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── services/
    ├── __init__.py
    ├── language.py      # detect_language(), translate_to_english(), translate_back()
    ├── intent.py        # detect_intent()  — keyword-based, multi-intent support
    └── booking.py       # generate_response()  — realistic booking simulation
```

---

## 📡 API Reference

### `POST /process`

**Request:**
```json
{
  "text": "Necesito un taxi al aeropuerto"
}
```

**Response:**
```json
{
  "detected_language": "es",
  "detected_language_name": "Spanish",
  "original_text": "Necesito un taxi al aeropuerto",
  "translated_text": "I need a taxi to the airport",
  "intents": ["Taxi Booking"],
  "response": "🚕 Taxi confirmado! Su Toyota Camry (Blanco) llegará en 8 min...",
  "bookings": [
    {
      "intent": "taxi_booking",
      "status": "confirmed",
      "details": {
        "destination": "Airport",
        "driver": "Ravi K.",
        "vehicle": "Toyota Camry (White)",
        "pickup_time": "02:15 PM",
        "estimated_cost": "₹550",
        "driver_eta": "8 minutes"
      },
      "message": "🚕 Taxi confirmed! ...",
      "message_translated": "🚕 ¡Taxi confirmado! ..."
    }
  ]
}
```

### `GET /health`

Returns `{"status": "healthy", "service": "AURA"}`.

### `GET /`

Returns API info and usage examples.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Flask** — lightweight web framework
- **googletrans** — Google Translate API wrapper (no API key needed)

---

## 📝 Notes

- All bookings are **simulated** — no real APIs or charges.
- `googletrans` uses an unofficial Google Translate API. If it fails, the system falls back gracefully to English.
- Designed to be **hackathon-ready**: simple, modular, and easy to extend.
