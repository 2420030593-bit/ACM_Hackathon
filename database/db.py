"""
Database layer – SQLite via aiosqlite for async operations.
Tables: bookings, profiles, memories, sessions, emergency_log
"""
import aiosqlite
import json
import os
from datetime import datetime
from config import DB_PATH

_db = None

async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _init_tables(_db)
    return _db

async def _init_tables(db):
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT UNIQUE NOT NULL,
            field_value TEXT NOT NULL,
            encrypted INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_used TEXT DEFAULT (datetime('now')),
            UNIQUE(category, key)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT NOT NULL,
            state TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS emergency_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS price_watches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            watch_type TEXT NOT NULL,
            query TEXT NOT NULL,
            target_price REAL,
            current_price REAL,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            last_checked TEXT
        );
    """)
    await db.commit()

# ── Booking CRUD ──
async def save_booking(intent: str, details: dict, status: str = "confirmed"):
    db = await get_db()
    await db.execute(
        "INSERT INTO bookings (intent, details, status) VALUES (?, ?, ?)",
        (intent, json.dumps(details), status)
    )
    await db.commit()

async def get_all_bookings():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM bookings ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "intent": row["intent"],
            "details": json.loads(row["details"]),
            "status": row["status"],
            "created_at": row["created_at"]
        })
    return result

# ── Memory CRUD ──
async def save_memory(category: str, key: str, value: str):
    db = await get_db()
    await db.execute("""
        INSERT INTO memories (category, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(category, key)
        DO UPDATE SET value=excluded.value, frequency=frequency+1, last_used=datetime('now')
    """, (category, key, value))
    await db.commit()

async def get_memories(category: str = None):
    db = await get_db()
    if category:
        cursor = await db.execute(
            "SELECT * FROM memories WHERE category=? ORDER BY frequency DESC", (category,)
        )
    else:
        cursor = await db.execute("SELECT * FROM memories ORDER BY frequency DESC")
    rows = await cursor.fetchall()
    return [{"category": r["category"], "key": r["key"], "value": r["value"],
             "frequency": r["frequency"]} for r in rows]

# ── Profile CRUD ──
async def save_profile(field_name: str, field_value: str, encrypted: bool = False):
    db = await get_db()
    await db.execute("""
        INSERT INTO profiles (field_name, field_value, encrypted)
        VALUES (?, ?, ?)
        ON CONFLICT(field_name)
        DO UPDATE SET field_value=excluded.field_value, updated_at=datetime('now')
    """, (field_name, field_value, 1 if encrypted else 0))
    await db.commit()

async def get_profile():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM profiles ORDER BY field_name")
    rows = await cursor.fetchall()
    return {r["field_name"]: r["field_value"] for r in rows}

# ── Price Watch CRUD ──
async def add_price_watch(watch_type: str, query: str, target_price: float):
    db = await get_db()
    await db.execute(
        "INSERT INTO price_watches (watch_type, query, target_price) VALUES (?, ?, ?)",
        (watch_type, query, target_price)
    )
    await db.commit()

async def get_active_watches():
    db = await get_db()
    cursor = await db.execute("SELECT * FROM price_watches WHERE active=1")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
