import os
import urllib.parse
import httpx
from backend.config import settings

def nightly_hotel(city: str, date: str, guests: int, max_price: int) -> dict:
    """
    Look up a hotel in a city using Google Places Text Search.
    Returns a simple dict consistent with the mock hotels tool.
    Synchronous (planner calls this without await).
    Falls back to a bounded mock price if API key is missing or API fails.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        # Graceful offline fallback
        return {
            "provider": "google-places(fallback)",
            "city": city,
            "checkin": date,
            "nights": 1,
            "guests": guests,
            "price_eur": min(max_price, 150),
            "rating": 4.2,
            "url": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus('hotel '+city+' France')}",
        }

    try:
        params = {
            "query": f"best hotel in {city}, France",
            "type": "lodging",
            "key": api_key,
        }
        r = httpx.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params=params,
            timeout=10.0,
        )
        r.raise_for_status()
        js = r.json()
        results = js.get("results") or []
        top = results[0] if results else {}
        name = top.get("name", f"Hotel in {city}")
        rating = float(top.get("rating", 4.2))
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(name+' '+city)}"
        est = min(max_price, 150)  # Google Places doesn't return price here; keep estimate bounded
        return {
            "provider": "google-places",
            "city": city,
            "checkin": date,
            "nights": 1,
            "guests": guests,
            "price_eur": est,
            "rating": rating,
            "url": maps_url,
        }
    except Exception:
        # Any error -> graceful fallback
        return {
            "provider": "google-places(error-fallback)",
            "city": city,
            "checkin": date,
            "nights": 1,
            "guests": guests,
            "price_eur": min(max_price, 150),
            "rating": 4.2,
            "url": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus('hotel '+city+' France')}",
        }
