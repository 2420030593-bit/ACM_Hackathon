"""
AURA – LLM-Driven Browser Automation Agent
Uses Groq (free cloud, sub-second) or local Ollama to navigate booking websites.
The LLM reads interactive page elements and decides what to click/type next.
Stops at the payment page so the user can complete the booking manually.
"""

import logging
import threading
import time
import json
import re
import os
import requests
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, GROQ_API_KEY, GROQ_MODEL
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

logger = logging.getLogger("aura.automation")

# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────
DEFAULT_LAT = 17.3850
DEFAULT_LNG = 78.4867
DEFAULT_PICKUP = "my current location"
DEFAULT_CITY = "my current location"
BROWSER_KEEP_ALIVE = 600  # 10 minutes
MAX_LLM_STEPS = 20  # Maximum number of LLM-guided actions per session

# Website mapping for each intent
SITE_MAP = {
    "taxi_booking": {"url": "https://m.uber.com/go/pickup", "name": "Uber"},
    "bus_booking": {"url": "https://www.redbus.in/", "name": "RedBus"},
    "hotel_booking": {"url": "https://www.booking.com/", "name": "Booking.com"},
    "flight_booking": {"url": "https://www.google.com/travel/flights", "name": "Google Flights"},
    "restaurant_booking": {"url": "https://www.zomato.com/", "name": "Zomato"},
    "tour_booking": {"url": "https://www.google.com/maps", "name": "Google Maps"},
}


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def trigger_automation(intent: str, destination: str, pickup: str = None, **kwargs):
    """Launch LLM-driven browser automation in a background thread."""
    pickup = pickup or DEFAULT_PICKUP
    logger.info("🤖 Launching LLM automation: %s → '%s' from '%s'", intent, destination, pickup)
    thread = threading.Thread(
        target=_safe_run, args=(intent, destination, pickup),
        kwargs=kwargs, daemon=True,
    )
    thread.start()


def _safe_run(intent, destination, pickup, **kwargs):
    try:
        _automate_with_llm(intent, destination, pickup, **kwargs)
    except Exception as e:
        logger.error("LLM Automation failed: %s", e, exc_info=True)


# ──────────────────────────────────────────────
#  LLM Call — Groq (fast cloud) with Ollama fallback
# ──────────────────────────────────────────────

def _call_llm(prompt: str) -> str:
    """
    Call the LLM for a browser agent decision.
    Priority: Groq Cloud (free, sub-second) → Ollama (local fallback).
    """
    # Try Groq first (fast cloud)
    if GROQ_API_KEY:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 150,
                    "response_format": {"type": "json_object"},
                },
                timeout=10,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                logger.info("Groq responded (%d chars)", len(content))
                return content.strip()
            else:
                logger.warning("Groq HTTP %d: %s", resp.status_code, resp.text[:100])
        except Exception as e:
            logger.warning("Groq call failed: %s — falling back to Ollama", e)

    # Fallback: local Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.0, "num_predict": 150},
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.error("Ollama call also failed: %s", e)

    return '{"action": "wait", "reason": "LLM unavailable"}'


# ──────────────────────────────────────────────
#  Browser Helpers
# ──────────────────────────────────────────────

def _launch_browser(pw):
    browser = pw.chromium.launch(
        headless=False,
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        geolocation={"latitude": DEFAULT_LAT, "longitude": DEFAULT_LNG},
        permissions=["geolocation"],
    )
    page = context.new_page()
    return browser, context, page


def _keep_alive(page, browser):
    try:
        start = time.time()
        while time.time() - start < BROWSER_KEEP_ALIVE:
            try:
                page.title()
                time.sleep(2)
            except Exception:
                logger.info("Browser closed by user.")
                break
    except Exception:
        pass
    finally:
        try:
            browser.close()
        except Exception:
            pass


# ──────────────────────────────────────────────
#  DOM Element Extraction (compact for LLM)
# ──────────────────────────────────────────────

def _get_page_elements(page):
    """Extract interactive elements into a compact numbered list for the LLM."""
    try:
        elements = page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const selectors = [
                'input:not([type="hidden"])', 'button', 'a[href]', 'select',
                'textarea', '[role="button"]', '[role="link"]', '[role="option"]',
                '[role="combobox"]', '[role="listbox"]', '[role="tab"]',
                '[contenteditable="true"]',
            ];
            for (const selector of selectors) {
                for (const el of document.querySelectorAll(selector)) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
                    
                    const tag = el.tagName.toLowerCase();
                    const id = el.getAttribute('id') || '';
                    const text = (el.textContent || '').trim().substring(0, 50);
                    const placeholder = el.getAttribute('placeholder') || '';
                    const ariaLabel = el.getAttribute('aria-label') || '';
                    const name = el.getAttribute('name') || '';
                    const type = el.getAttribute('type') || '';
                    const role = el.getAttribute('role') || '';
                    const value = el.value || '';
                    
                    const key = `${tag}|${id}|${text}|${placeholder}`;
                    if (seen.has(key)) continue;
                    seen.add(key);
                    
                    let desc = tag.toUpperCase();
                    if (type) desc += `[${type}]`;
                    let label = ariaLabel || placeholder || text || name || id || '';
                    label = label.substring(0, 60);
                    
                    results.push({
                        index: results.length, tag, type, role, id, name,
                        placeholder, ariaLabel, text: text.substring(0, 50),
                        value: value.substring(0, 30), desc, label,
                    });
                    if (results.length >= 35) break;
                }
                if (results.length >= 35) break;
            }
            return results;
        }""")

        lines = []
        for el in elements:
            line = f"[{el['index']}] {el['desc']}"
            if el['label']:
                line += f' "{el["label"]}"'
            if el['value']:
                line += f' (value: "{el["value"]}")'
            lines.append(line)

        return elements, "\n".join(lines)
    except Exception as e:
        logger.warning("Failed to extract elements: %s", e)
        return [], ""


# ──────────────────────────────────────────────
#  LLM Decision Engine
# ──────────────────────────────────────────────

def _ask_llm_action(elements_text, goal, page_url, page_title, history):
    """Ask the LLM what the next browser action should be. Returns a dict."""
    history_text = "\n".join(history[-5:]) if history else "None yet"

    prompt = f"""You are a browser automation agent. Goal: {goal}

Page: {page_title} ({page_url})
Previous actions: {history_text}

Interactive elements:
{elements_text}

Reply with ONLY a JSON object for the NEXT action:
- Click: {{"action":"click","element":<num>,"reason":"why"}}
- Type: {{"action":"type","element":<num>,"text":"value","reason":"why"}}
- Press Enter: {{"action":"press_enter","reason":"why"}}
- Scroll: {{"action":"scroll","reason":"why"}}
- Done (at payment): {{"action":"done","reason":"At payment page"}}
- Wait: {{"action":"wait","reason":"why"}}

Rules: Fill origin/destination inputs first, then search. If the pickup/origin is "my current location", look for a "Current location" button or type "Current location" to let the site use geolocation. If you see payment/checkout/card fields, respond done. Pick ONE action."""

    response = _call_llm(prompt)

    try:
        action = json.loads(response)
        logger.info("LLM action: %s", action)
        return action
    except json.JSONDecodeError:
        match = re.search(r'\{[^}]+\}', response)
        if match:
            try:
                action = json.loads(match.group(0))
                logger.info("LLM action (extracted): %s", action)
                return action
            except:
                pass
        logger.warning("Could not parse LLM response: %s", response[:100])
        return {"action": "wait", "reason": "Parse error"}


# ──────────────────────────────────────────────
#  Action Executor
# ──────────────────────────────────────────────

def _execute_action(page, action, elements):
    """Execute the LLM's action on the page. Returns False to stop."""
    action_type = action.get("action", "wait")

    if action_type == "done":
        return False
    if action_type == "wait":
        time.sleep(2)
        return True
    if action_type == "scroll":
        page.mouse.wheel(0, 400)
        time.sleep(1)
        return True
    if action_type == "press_enter":
        page.keyboard.press("Enter")
        time.sleep(2)
        return True

    idx = action.get("element", -1)
    if idx < 0 or idx >= len(elements):
        logger.warning("Invalid element index: %d (max %d)", idx, len(elements) - 1)
        time.sleep(1)
        return True

    el_info = elements[idx]

    try:
        locator = _build_locator(page, el_info)
        if action_type == "click":
            locator.click(timeout=5000)
            logger.info("Clicked: %s", el_info.get('label', '?')[:40])
            time.sleep(2)
        elif action_type == "type":
            text = action.get("text", "")
            locator.click(timeout=5000)
            time.sleep(0.3)
            locator.fill("")
            time.sleep(0.2)
            page.keyboard.type(text, delay=50)
            logger.info("Typed '%s' into: %s", text, el_info.get('label', '?')[:40])
            time.sleep(2)
    except Exception as e:
        logger.warning("Action failed on [%d]: %s", idx, e)
        try:
            page.keyboard.press("Tab")
            time.sleep(0.5)
        except:
            pass

    return True


def _build_locator(page, el_info):
    """Build a Playwright locator from element info."""
    strategies = []
    if el_info.get('id'):
        strategies.append(lambda: page.locator(f"#{el_info['id']}").first)
    if el_info.get('ariaLabel'):
        strategies.append(lambda: page.get_by_label(el_info['ariaLabel']).first)
    if el_info.get('placeholder'):
        strategies.append(lambda: page.get_by_placeholder(el_info['placeholder']).first)
    if el_info.get('text') and el_info['tag'] in ('button', 'a'):
        strategies.append(lambda: page.get_by_text(el_info['text'], exact=False).first)
    if el_info.get('name'):
        strategies.append(lambda: page.locator(f"{el_info['tag']}[name=\"{el_info['name']}\"]").first)

    for strategy in strategies:
        try:
            loc = strategy()
            loc.wait_for(state="visible", timeout=2000)
            return loc
        except:
            continue

    return page.locator(el_info.get('tag', 'div')).first


# ──────────────────────────────────────────────
#  Main LLM Automation Loop
# ──────────────────────────────────────────────

def _automate_with_llm(intent, destination, pickup, **kwargs):
    """
    Main LLM-driven browser automation:
    1. Opens the right website
    2. Reads page elements
    3. Asks LLM (Groq/Ollama) what to click/type
    4. Executes action
    5. Repeats until payment page
    """
    site = SITE_MAP.get(intent, {
        "url": f"https://www.google.com/search?q={destination}+booking",
        "name": "Google",
    })
    goal = _build_goal(intent, destination, pickup)

    using = "Groq Cloud" if GROQ_API_KEY else "Local Ollama"
    logger.info("🤖 LLM Agent starting on %s [using %s]: %s", site['name'], using, goal)

    with sync_playwright() as pw:
        browser, context, page = _launch_browser(pw)
        try:
            page.goto(site['url'], wait_until="domcontentloaded", timeout=30000)
            logger.info("Loaded %s", site['name'])
            time.sleep(4)

            _dismiss_popups(page)

            history = []
            waits = 0

            for step in range(MAX_LLM_STEPS):
                logger.info("── Step %d/%d ──", step + 1, MAX_LLM_STEPS)

                elements, elements_text = _get_page_elements(page)
                if not elements_text:
                    time.sleep(2)
                    continue

                try:
                    url = page.url
                    title = page.title()
                except:
                    url = title = "unknown"

                if _is_payment_page(url, title):
                    logger.info("✅ Payment page detected! Stopping.")
                    break

                llm_action = _ask_llm_action(elements_text, goal, url, title, history)
                history.append(f"Step {step+1}: {llm_action.get('action','?')} - {llm_action.get('reason','?')}")

                if not _execute_action(page, llm_action, elements):
                    logger.info("✅ LLM signaled done. Automation complete.")
                    break

                if llm_action.get("action") == "wait":
                    waits += 1
                    if waits >= 3:
                        logger.warning("Too many waits. Stopping.")
                        break
                else:
                    waits = 0

            logger.info("✅ Automation finished (%d steps). Browser stays open.", len(history))
            _keep_alive(page, browser)

        except Exception as e:
            logger.error("Automation error: %s", e, exc_info=True)
            _keep_alive(page, browser)


def _build_goal(intent, destination, pickup):
    goals = {
        "taxi_booking": f"Book a cab from '{pickup}' to '{destination}'. Enter pickup, destination, select ride, proceed to payment.",
        "bus_booking": f"Book a bus from '{pickup}' to '{destination}'. Enter origin, destination, select date, search, select bus, proceed to payment.",
        "hotel_booking": f"Book a hotel in '{destination}'. Enter city, dates, search, pick hotel, proceed to payment.",
        "flight_booking": f"Search flights from '{pickup}' to '{destination}'. Enter origin, destination, search, select flight, proceed to booking.",
        "restaurant_booking": f"Find '{destination}' restaurant, add items to cart, proceed to checkout.",
        "tour_booking": f"Search for tours in '{destination}'.",
    }
    return goals.get(intent, f"Complete a booking for '{destination}' from '{pickup}'.")


def _dismiss_popups(page):
    for selector in [
        'button:has-text("Accept")', 'button:has-text("Accept all")',
        'button:has-text("Got it")', 'button:has-text("OK")',
        'button:has-text("Close")', 'button:has-text("No thanks")',
        'i.icon-close', '[aria-label="Close"]', '[aria-label="Dismiss"]',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=800):
                el.click()
                time.sleep(0.3)
        except:
            pass


def _is_payment_page(url, title):
    keywords = [
        "payment", "checkout", "pay now", "card details", "billing",
        "credit card", "debit card", "upi", "razorpay", "stripe",
        "paytm", "phonepe", "confirm booking", "proceed to pay",
    ]
    combined = (url + " " + title).lower()
    return any(kw in combined for kw in keywords)
