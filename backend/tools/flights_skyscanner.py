# backend/tools/flights_skyscanner.py
import os
import time
import json
import hashlib
from typing import Any, Dict, Optional

import httpx

# ---- Config (env-driven) -----------------------------------------------------

RAPIDAPI_KEY   = os.getenv("RAPIDAPI_KEY", "")
# Match exactly what your RapidAPI subscription shows as "X-RapidAPI-Host"
RAPIDAPI_HOST  = os.getenv("RAPIDAPI_HOST", "skyscanner80.p.rapidapi.com")
# Match the sample path from your vendor page
ENDPOINT       = os.getenv("FLIGHTS_SKY_ENDPOINT", "/api/v1/flights/search-one-way")
# "fromId" (IATA) or "fromEntityId" (entity IDs), depends on vendor
PARAM_STYLE    = os.getenv("FLIGHTS_SKY_PARAM_STYLE", "fromId")  # or "fromEntityId"

# Caching (seconds) — avoids hammering the API for identical queries
CACHE_TTL_SEC  = int(os.getenv("FLIGHTS_CACHE_TTL_SEC", "900"))  # 15 min default
ERROR_TTL_SEC  = int(os.getenv("FLIGHTS_ERROR_TTL_SEC", "60"))   # cache errors for 1 min

# Market / locale settings (tweak if needed)
DEFAULT_MARKET   = os.getenv("FLIGHTS_MARKET", "FR")
DEFAULT_LOCALE   = os.getenv("FLIGHTS_LOCALE", "en-GB")
DEFAULT_CURRENCY = os.getenv("FLIGHTS_CURRENCY", "EUR")

# ---- Optional Redis cache (reuses your deps.redis). Falls back to local dict. ----

_redis = None
try:
    from backend.deps import redis as _redis  # if Redis is running per your project
except Exception:
    _redis = None

_LOCAL_CACHE: Dict[str, tuple[float, dict]] = {}

def _cache_get(key: str) -> Optional[dict]:
    if _redis:
        val = _redis.get(key)
        return json.loads(val) if val else None
    # in-proc fallback
    item = _LOCAL_CACHE.get(key)
    if not item:
        return None
    ts, payload = item
    if time.time() - ts <= CACHE_TTL_SEC:
        return payload
    return None

def _cache_set(key: str, value: dict, ttl: int = CACHE_TTL_SEC) -> None:
    if _redis:
        _redis.setex(key, ttl, json.dumps(value))
        return
    _LOCAL_CACHE[key] = (time.time(), value)

def _cache_key(origin: str, dest: str, date_iso: str) -> str:
    raw = f"{origin}|{dest}|{date_iso}|{RAPIDAPI_HOST}|{ENDPOINT}|{PARAM_STYLE}|{DEFAULT_MARKET}|{DEFAULT_LOCALE}|{DEFAULT_CURRENCY}"
    return "sky:" + hashlib.sha1(raw.encode()).hexdigest()

# ---- Helpers -----------------------------------------------------------------

def _params(origin: str, dest: str, depart_date: str) -> Dict[str, Any]:
    base = {
        "adults": 1,
        "currency": DEFAULT_CURRENCY,
        "market": DEFAULT_MARKET,
        "locale": DEFAULT_LOCALE,
        "departDate": depart_date,
    }
    if PARAM_STYLE == "fromEntityId":
        base.update({"fromEntityId": origin, "toEntityId": dest})
    else:  # default: fromId/toId (IATA)
        base.update({"fromId": origin, "toId": dest})
    return base

def _extract_price(js: Dict[str, Any]) -> float:
    """
    Vendors on RapidAPI expose slightly different shapes.
    Try common patterns in order; return 0.0 if none match.
    """
    try:
        return float(js["data"]["itineraries"][0]["price"]["amount"])
    except Exception:
        pass
    try:
        return float(js["price"]["amount"])
    except Exception:
        pass
    try:
        return float(js["results"][0]["price"])
    except Exception:
        pass
    return 0.0

# ---- Public API --------------------------------------------------------------

def flight_eur(origin: str, dest_city_or_code: str, depart_date: str) -> dict:
    """
    Returns a dict:
      {
        "provider": "skyscanner",
        "price_eur": float,
        "currency": "EUR",
        "url": "https://www.skyscanner.net/",
        "ttl_min": 15,
        # optional "error": "...",
        # optional "cached": True
      }
    """
    if not RAPIDAPI_KEY:
        raise RuntimeError("RAPIDAPI_KEY missing for Skyscanner (RapidAPI)")

    # cache check
    ck = _cache_key(origin, dest_city_or_code, depart_date)
    cached = _cache_get(ck)
    if cached:
        out = dict(cached)
        out["cached"] = True
        return out

    url = f"https://{RAPIDAPI_HOST}{ENDPOINT}"
    headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}
    params  = _params(origin, dest_city_or_code, depart_date)

    # Retry w/ exponential backoff on 429/5xx to tame rate limits
    attempt = 0
    last_err = ""
    with httpx.Client(timeout=20.0) as client:
        while attempt < 4:
            try:
                resp = client.get(url, headers=headers, params=params)
                status = resp.status_code

                if status == 200:
                    js = resp.json()
                    price = _extract_price(js)
                    if price > 0:
                        out = {
                            "provider": "skyscanner",
                            "price_eur": round(price, 2),
                            "currency": DEFAULT_CURRENCY,
                            "url": "https://www.skyscanner.net/",
                            "ttl_min": 15,
                        }
                        _cache_set(ck, out, ttl=CACHE_TTL_SEC)
                        return out
                    # 200 OK but schema not recognized
                    last_err = "200 OK but price not found in response"
                    break

                if status in (429, 500, 502, 503, 504):
                    # Exponential backoff with a touch of jitter
                    wait = (2 ** attempt) + (attempt * 0.25)
                    last_err = f"{status}: {resp.text[:200]}"
                    time.sleep(wait)
                    attempt += 1
                    continue

                # Other non-retryable errors
                last_err = f"{status}: {resp.text[:200]}"
                break

            except httpx.HTTPError as e:
                last_err = f"HTTPError {type(e).__name__}: {e}"
                wait = (2 ** attempt) + 0.5
                time.sleep(wait)
                attempt += 1

    # Return non-fatal result; your planner will fall back to mock if needed
    out = {
        "provider": "skyscanner",
        "price_eur": 0.0,
        "currency": DEFAULT_CURRENCY,
        "url": "https://www.skyscanner.net/",
        "error": last_err or "unknown error",
    }
    # Cache the error briefly to avoid hammering on repeated queries
    _cache_set(ck, out, ttl=ERROR_TTL_SEC)
    return out