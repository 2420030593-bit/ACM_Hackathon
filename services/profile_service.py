"""
Profile Service – Encrypted storage for personal data, auto-fill support.
"""
import logging
import json
import base64
import hashlib
from config import ENCRYPTION_KEY

logger = logging.getLogger("aura.profile")

# Simple encryption using XOR with key (for demo; use Fernet in production)
def _get_key_bytes(key: str) -> bytes:
    return hashlib.sha256(key.encode()).digest()

def encrypt_value(value: str) -> str:
    key_bytes = _get_key_bytes(ENCRYPTION_KEY)
    value_bytes = value.encode('utf-8')
    encrypted = bytes([v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(value_bytes)])
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_value(encrypted: str) -> str:
    key_bytes = _get_key_bytes(ENCRYPTION_KEY)
    encrypted_bytes = base64.b64decode(encrypted.encode('utf-8'))
    decrypted = bytes([v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(encrypted_bytes)])
    return decrypted.decode('utf-8')

# Fields that should be encrypted
SENSITIVE_FIELDS = {"passport_number", "credit_card", "phone", "email", "date_of_birth"}

def should_encrypt(field_name: str) -> bool:
    return field_name.lower() in SENSITIVE_FIELDS

def prepare_for_storage(field_name: str, value: str) -> tuple:
    """Return (stored_value, is_encrypted)."""
    if should_encrypt(field_name):
        return encrypt_value(value), True
    return value, False

def prepare_for_display(field_name: str, value: str, is_encrypted: bool) -> str:
    """Decrypt if needed for display."""
    if is_encrypted:
        try:
            return decrypt_value(value)
        except:
            return "***encrypted***"
    return value

def get_autofill_data(profile: dict) -> dict:
    """Prepare profile data for auto-filling booking forms."""
    autofill = {}
    field_mapping = {
        "first_name": "firstName",
        "last_name": "lastName",
        "email": "email",
        "phone": "phone",
        "passport_number": "passport",
        "nationality": "nationality",
        "date_of_birth": "dob",
    }
    for db_field, form_field in field_mapping.items():
        if db_field in profile:
            autofill[form_field] = profile[db_field]
    return autofill
