import httpx
from collections import Counter
from datetime import datetime
from backend.config import settings

def _risk(v) -> float:
    try:
        x = float(v)
        return 0.0 if x < 0 else (1.0 if x > 1 else x)
    except Exception:
        return 0.2

def _date_of(ts_or_iso):
    if isinstance(ts_or_iso, (int, float)):
        return datetime.utcfromtimestamp(ts_or_iso).date().isoformat()
    try:
        return datetime.fromisoformat(str(ts_or_iso)).date().isoformat()
    except Exception:
        return str(ts_or_iso)[:10]

async def _onecall_3(lat: float, lon: float, date_iso: str, api_key: str) -> dict:
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,alerts",
        "units": "metric",
        "appid": api_key,
    }
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get("https://api.openweathermap.org/data/3.0/onecall", params=params)
        r.raise_for_status()
        js = r.json()

    # pick the matching day (or first)
    target = date_iso
    daily = js.get("daily") or []
    if not daily:
        raise RuntimeError("No daily data in One Call 3.0 response")
    bucket = None
    for d in daily:
        if _date_of(d.get("dt")) == target:
            bucket = d
            break
    bucket = bucket or daily[0]
    temp = bucket.get("temp") or {}
    weather = (bucket.get("weather") or [{"main": "Unknown"}])[0]
    pop = bucket.get("pop", 0.2)

    return {
        "summary": weather.get("main", "Unknown"),
        "high_c": float(temp.get("max", 18.0)),
        "low_c": float(temp.get("min", 10.0)),
        "rain_risk": _risk(pop),
    }

async def _aggregate_forecast_25(lat: float, lon: float, date_iso: str, api_key: str) -> dict:
    """
    Fallback using 5-day/3-hour forecast (free). Aggregate per target date.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "appid": api_key,
    }
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.get("https://api.openweathermap.org/data/2.5/forecast", params=params)
        r.raise_for_status()
        js = r.json()

    blocks = [x for x in (js.get("list") or []) if _date_of(x.get("dt")) == date_iso]
    if not blocks:
        # take nearest day if target missing
        blocks = (js.get("list") or [])[:8]

    highs, lows, pops, labels = [], [], [], []
    for b in blocks:
        main = b.get("main") or {}
        high = main.get("temp_max", main.get("temp"))
        low  = main.get("temp_min", main.get("temp"))
        pop  = b.get("pop", 0.2)
        w    = (b.get("weather") or [{"main": "Unknown"}])[0].get("main", "Unknown")
        if high is not None: highs.append(float(high))
        if low  is not None: lows.append(float(low))
        pops.append(float(pop))
        labels.append(w)

    if not highs:
        return {"summary": "Unknown", "high_c": 18.0, "low_c": 10.0, "rain_risk": 0.2}

    # Aggregate: max of highs, min of lows, max POP, most common label
    summary = Counter(labels).most_common(1)[0][0] if labels else "Unknown"
    return {
        "summary": summary,
        "high_c": max(highs),
        "low_c": min(lows),
        "rain_risk": _risk(max(pops) if pops else 0.2),
    }

async def forecast(lat: float, lon: float, date_iso: str) -> dict:
    """
    Try One Call 3.0 (paid/activated). On 401/403/404 or any error, fallback to
    free 5-day/3-hour forecast aggregation.
    """
    api_key = getattr(settings, "OPENWEATHER_API_KEY", "") or ""
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY missing")

    try:
        return await _onecall_3(lat, lon, date_iso, api_key)
    except httpx.HTTPStatusError as he:
        # Typical when One Call 3.0 isn't enabled: 401/403/404
        try:
            return await _aggregate_forecast_25(lat, lon, date_iso, api_key)
        except Exception:
            raise he
    except Exception:
        # Any other error -> try fallback
        return await _aggregate_forecast_25(lat, lon, date_iso, api_key)
