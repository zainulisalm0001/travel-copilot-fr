import httpx
from backend.config import settings
from math import ceil

def _mins(seconds: float) -> int:
    try: return max(1, int(ceil(float(seconds)/60.0)))
    except: return 15

async def transit_minutes(origin_latlon: tuple[float,float], dest_latlon: tuple[float,float], mode: str="transit") -> int:
    """
    Uses Google Directions API to estimate travel minutes. mode: driving|walking|bicycling|transit
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY missing")
    params = {
        "origin": f"{origin_latlon[0]},{origin_latlon[1]}",
        "destination": f"{dest_latlon[0]},{dest_latlon[1]}",
        "mode": mode,
        "key": settings.GOOGLE_MAPS_API_KEY,
        "departure_time": "now" if mode=="transit" else None,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get("https://maps.googleapis.com/maps/api/directions/json", params={k:v for k,v in params.items() if v})
        r.raise_for_status()
        js = r.json()
    routes = js.get("routes") or []
    if not routes: return 15
    legs = (routes[0].get("legs") or [])
    secs = sum([(l.get("duration") or {}).get("value", 0) for l in legs])
    return _mins(secs)