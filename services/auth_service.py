"""
Auth Service – Google OAuth + JWT token authentication.
Supports Google Sign-In and local registration as fallback.
"""
import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

logger = logging.getLogger("aura.auth")

# ── Config ──
SECRET_KEY = os.getenv("AURA_JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# ── In-memory user store (SQLite in production) ──
_users_file = os.path.join(os.path.dirname(__file__), "users.json")

def _load_users() -> dict:
    if os.path.exists(_users_file):
        with open(_users_file, "r") as f:
            return json.load(f)
    return {}

def _save_users(users: dict):
    with open(_users_file, "w") as f:
        json.dump(users, f, indent=2)


# ── JWT Token ──
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── Security scheme ──
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency: extract and verify user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
        "picture": payload.get("picture", ""),
        "provider": payload.get("provider", "local"),
    }


# ── Google OAuth verification ──
async def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token and extract user info."""
    try:
        # Verify with Google's tokeninfo endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )
            if resp.status_code == 200:
                data = resp.json()
                # Verify audience if GOOGLE_CLIENT_ID is set
                if GOOGLE_CLIENT_ID and data.get("aud") != GOOGLE_CLIENT_ID:
                    return None
                return {
                    "email": data.get("email", ""),
                    "name": data.get("name", ""),
                    "picture": data.get("picture", ""),
                    "email_verified": data.get("email_verified", "false") == "true",
                }
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
    return None


# ── Local Auth ──
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(email: str, password: str, name: str = "") -> dict:
    """Register a new local user."""
    users = _load_users()
    if email in users:
        return None  # Already exists
    
    users[email] = {
        "email": email,
        "name": name or email.split("@")[0],
        "password_hash": hash_password(password),
        "provider": "local",
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_users(users)
    return users[email]


def authenticate_user(email: str, password: str) -> dict:
    """Authenticate a local user."""
    users = _load_users()
    user = users.get(email)
    if not user:
        return None
    if user.get("password_hash") != hash_password(password):
        return None
    return user


def get_or_create_google_user(email: str, name: str, picture: str) -> dict:
    """Get or create a user from Google OAuth."""
    users = _load_users()
    if email not in users:
        users[email] = {
            "email": email,
            "name": name,
            "picture": picture,
            "provider": "google",
            "created_at": datetime.utcnow().isoformat(),
        }
        _save_users(users)
    return users[email]
