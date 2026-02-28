"""Pydantic models for all AURA entities."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class VoiceInput(BaseModel):
    text: str


class AgentRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"


class AgentResponse(BaseModel):
    response_text: str
    explanation: str
    actions: List[str]
    mode: str
    intent: str
    language: str
    audio_b64: Optional[str] = None
    automation_triggered: bool = False
    auto_listen: bool = False
    bookings: List[Dict[str, Any]] = []


class BookingRecord(BaseModel):
    id: Optional[int] = None
    intent: str
    details: Dict[str, Any]
    status: str = "confirmed"
    created_at: Optional[str] = None


class ProfileField(BaseModel):
    field_name: str
    field_value: str
    encrypted: bool = False


class MemoryEntry(BaseModel):
    category: str
    key: str
    value: str


class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"


class EmergencyRequest(BaseModel):
    country_code: str = "us"
    situation: str = "general"


class PriceWatchRequest(BaseModel):
    watch_type: str  # flight, hotel, bus
    query: str
    target_price: float


class ItineraryRequest(BaseModel):
    destination: str
    days: int = 2
    budget: Optional[float] = None
    preferences: List[str] = []


class AutomationRequest(BaseModel):
    intent: str
    destination: str
    details: Dict[str, Any] = {}
