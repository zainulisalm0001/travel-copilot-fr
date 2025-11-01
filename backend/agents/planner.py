# backend/agents/planner.py
from datetime import datetime, timedelta
from typing import List

from backend.models import PlanRequest, PlanResponse, DayPlan, Activity
from backend.config import settings

# --------------------------
# Provider switches (imports)
# --------------------------

# Weather provider
if getattr(settings, "PROVIDER_WEATHER", "openmeteo") == "openweather":
    from backend.tools.weather_openweather import forecast  # OpenWeather (requires key)
else:
    from backend.tools.weather import forecast  # Open-Meteo (no key)

# Flights provider (live or mock)
if getattr(settings, "PROVIDER_FLIGHTS", "mock") == "skyscanner":
    from backend.tools.flights_skyscanner import flight_eur  # RapidAPI Skyscanner
elif getattr(settings, "PROVIDER_FLIGHTS", "mock") == "amadeus":
    from backend.tools.flights_amadeus import flight_eur     # Amadeus
else:
    from backend.tools.pricing import flight_eur             # mock fallback (always available)

# Always keep mock flight for fallback in case live provider fails at runtime
from backend.tools.pricing import flight_eur as mock_flight_eur

# Hotels / Places
if getattr(settings, "PROVIDER_MAPS", "google") == "google":
    # Your Google Places-based hotel stub (replace with real Places later)
    from backend.tools.hotels_google import nightly_hotel
else:
    from backend.tools.hotels import nightly_hotel  # mock hotels

# Optional routing helper (not yet used in naive plan)
from backend.tools.routing import estimate_minutes


# --------------------------
# Static data / Coordinates
# --------------------------
CITY_COORDS = {
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Nice": (43.7102, 7.2620),
    "Marseille": (43.2965, 5.3698),
    "Bordeaux": (44.8378, -0.5792),
}

# Helpful IATA mapping for French cities — many flight providers expect IATA
CITY_IATA = {
    "Paris": "PAR",
    "Lyon": "LYS",
    "Nice": "NCE",
    "Marseille": "MRS",
    "Bordeaux": "BOD",
}


# --------------------------
# Planner
# --------------------------
async def plan_itinerary(req: PlanRequest) -> PlanResponse:
    start = datetime.fromisoformat(req.start_date)
    end = datetime.fromisoformat(req.end_date)
    days_n = (end - start).days
    if days_n <= 0:
        raise ValueError("end_date must be after start_date")

    per_day_budget = req.budget_eur / max(1, days_n)

    total_cost: float = 0.0
    plans: List[DayPlan] = []
    citations: List[str] = []

    # ----- Flight estimate to first city -----
    first_city = req.cities[0]
    dest_code = CITY_IATA.get(first_city, first_city)  # prefer IATA if we know it

    # Try live provider; if bad or zero, fall back to mock to keep UX smooth
    try:
        flight_quote = flight_eur(req.origin, dest_code, req.start_date)
        price = float(flight_quote.get("price_eur", 0.0))
        if price <= 0.0:
            # surface provider error text if present and fall back
            err = flight_quote.get("error", "")
            raise ValueError(f"no price from provider: {err}")
    except Exception as e:
        flight_quote = mock_flight_eur(req.origin, dest_code, req.start_date)
        citations.append(f"skyscanner-fallback:{type(e).__name__}:{str(e)[:120]}")

    total_cost += float(flight_quote.get("price_eur", 0.0))
    if flight_quote.get("url"):
        citations.append(flight_quote["url"])
    if flight_quote.get("error"):
        citations.append(f"skyscanner-error:{flight_quote['error'][:140]}")

    # ----- Per-day planning -----
    for i in range(days_n):
        date = (start + timedelta(days=i)).date().isoformat()
        # simple: stick in first city for day 1, second city for day 2+, etc.
        city = req.cities[min(i, len(req.cities) - 1)]
        lat, lon = CITY_COORDS.get(city, CITY_COORDS.get(first_city))

        # Weather (provider-selected above)
        w = await forecast(lat, lon, date)

        # Hotel estimate — cap ~60% of daily budget
        hotel = nightly_hotel(city, date, req.party_size, max_price=int(per_day_budget * 0.6))
        total_cost += float(hotel.get("price_eur", 0.0))
        if hotel.get("url"):
            citations.append(hotel["url"])

        # Naive daily schedule (replace with optimizer later)
        acts: List[Activity] = [
            Activity(
                title=f"Morning stroll in {city}",
                city=city,
                start_time=f"{date} 09:30",
                end_time=f"{date} 11:30",
                cost_eur=0.0,
                transport_mode="walk",
            ),
            Activity(
                title="Lunch: local specialty",
                city=city,
                start_time=f"{date} 12:30",
                end_time=f"{date} 14:00",
                cost_eur=25.0,
                transport_mode="walk",
            ),
            Activity(
                title=f"Museum/landmark (rain risk {int(w.get('rain_risk', 0.2) * 100)}%)",
                city=city,
                start_time=f"{date} 14:30",
                end_time=f"{date} 17:00",
                cost_eur=18.0,
                transport_mode="metro",
            ),
            Activity(
                title="Dinner neighborhood tour",
                city=city,
                start_time=f"{date} 19:00",
                end_time=f"{date} 21:00",
                cost_eur=45.0,
                transport_mode="walk",
            ),
        ]
        total_cost += 25 + 18 + 45
        plans.append(DayPlan(date=date, city=city, activities=acts))

    # ----- Summary -----
    summary = (
        f"{days_n} days across {', '.join(req.cities)}. "
        f"Flight estimate to {first_city}: €{float(flight_quote.get('price_eur', 0.0)):.2f}. "
        f"Daily budget ~€{per_day_budget:.0f}."
    )

    return PlanResponse(
        summary=summary,
        total_cost_estimate_eur=round(total_cost, 2),
        days=plans,
        citations=citations,
    )