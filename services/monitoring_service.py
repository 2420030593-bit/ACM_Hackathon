"""
Monitoring Service – Price tracking with periodic checks and WebSocket notifications.
"""
import logging
import asyncio
import json
from datetime import datetime
from typing import List, Callable, Optional

logger = logging.getLogger("aura.monitoring")

# Active monitors
_active_monitors: List[dict] = []
_ws_clients: List = []
_monitor_task: Optional[asyncio.Task] = None


def register_ws_client(ws):
    _ws_clients.append(ws)

def remove_ws_client(ws):
    if ws in _ws_clients:
        _ws_clients.remove(ws)


async def notify_clients(message: dict):
    """Send notification to all connected WebSocket clients."""
    disconnected = []
    for ws in _ws_clients:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    for ws in disconnected:
        _ws_clients.remove(ws)


async def add_monitor(watch_type: str, query: str, target_price: float):
    """Add a new price monitor."""
    monitor = {
        "id": len(_active_monitors) + 1,
        "type": watch_type,
        "query": query,
        "target_price": target_price,
        "current_price": None,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "checks": 0,
    }
    _active_monitors.append(monitor)
    logger.info(f"Added monitor: {watch_type} '{query}' target ₹{target_price}")

    # Start background task if not running
    global _monitor_task
    if _monitor_task is None or _monitor_task.done():
        _monitor_task = asyncio.create_task(_monitor_loop())

    return monitor


async def _monitor_loop():
    """Background loop that checks prices periodically."""
    while any(m["active"] for m in _active_monitors):
        for monitor in _active_monitors:
            if not monitor["active"]:
                continue

            monitor["checks"] += 1
            # Simulate price check (in production, would scrape actual prices)
            import random
            simulated_price = monitor["target_price"] * random.uniform(0.8, 1.3)
            monitor["current_price"] = round(simulated_price, 2)

            if simulated_price <= monitor["target_price"]:
                monitor["active"] = False
                await notify_clients({
                    "type": "price_alert",
                    "monitor_id": monitor["id"],
                    "message": f"🎯 Price dropped! {monitor['query']} is now ₹{monitor['current_price']} (target: ₹{monitor['target_price']})",
                    "data": monitor,
                })
                logger.info(f"Price target hit for monitor {monitor['id']}")
            else:
                await notify_clients({
                    "type": "price_update",
                    "monitor_id": monitor["id"],
                    "message": f"Current price: ₹{monitor['current_price']}",
                    "data": monitor,
                })

        await asyncio.sleep(60)  # Check every 60 seconds


def get_active_monitors():
    return [m for m in _active_monitors if m["active"]]

def get_all_monitors():
    return _active_monitors

def cancel_monitor(monitor_id: int):
    for m in _active_monitors:
        if m["id"] == monitor_id:
            m["active"] = False
            return True
    return False
