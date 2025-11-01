import httpx
from api.config import settings

async def forecast(city_lat: float, city_lon: float, date: str) -> dict:
    params = {
        "latitude": city_lat,
        "longitude": city_lon,
        "daily": ["weathercode","temperature_2m_max","temperature_2m_min","precipitation_probability_max"],
        "timezone": "Europe/Paris",
        "start_date": date,
        "end_date": date,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(settings.OPEN_METEO_BASE, params=params)
        r.raise_for_status()
        js = r.json()
    try:
        idx = 0
        return {
            "summary": int(js["daily"]["weathercode"][idx]),
            "high_c": float(js["daily"]["temperature_2m_max"][idx]),
            "low_c": float(js["daily"]["temperature_2m_min"][idx]),
            "rain_risk": float(js["daily"]["precipitation_probability_max"][idx]) / 100.0,
        }
    except Exception:
        return {"summary": 0, "high_c": 18.0, "low_c": 10.0, "rain_risk": 0.2}