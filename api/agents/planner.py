from datetime import datetime, timedelta
from typing import List
from api.models import PlanRequest, PlanResponse, DayPlan, Activity
from api.tools import weather, routing, pricing, hotels

CITY_COORDS = {
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Nice": (43.7102, 7.2620),
    "Marseille": (43.2965, 5.3698),
    "Bordeaux": (44.8378, -0.5792),
}

async def plan_itinerary(req: PlanRequest) -> PlanResponse:
    start = datetime.fromisoformat(req.start_date)
    end = datetime.fromisoformat(req.end_date)
    days_n = (end - start).days
    if days_n <= 0:
        raise ValueError("end_date must be after start_date")

    per_day_budget = req.budget_eur / max(1, days_n)

    total_cost = 0.0
    plans: List[DayPlan] = []
    citations = []

    first_city = req.cities[0]
    flight = pricing.flight_eur(req.origin, first_city, req.start_date)
    total_cost += flight["price_eur"]
    citations.append(flight["url"])

    for i in range(days_n):
        date = (start + timedelta(days=i)).date().isoformat()
        city = req.cities[min(i, len(req.cities)-1)]
        lat, lon = CITY_COORDS.get(city, CITY_COORDS[first_city])
        w = await weather.forecast(lat, lon, date)

        hotel = hotels.nightly_hotel(city, date, req.party_size, max_price=int(per_day_budget*0.6))
        total_cost += hotel["price_eur"]
        citations.append(hotel["url"])

        acts: List[Activity] = [
            Activity(title=f"Morning stroll in {city}", city=city, start_time=f"{date} 09:30", end_time=f"{date} 11:30", cost_eur=0.0, transport_mode="walk"),
            Activity(title=f"Lunch: local specialty", city=city, start_time=f"{date} 12:30", end_time=f"{date} 14:00", cost_eur=25.0, transport_mode="walk"),
            Activity(title=f"Museum/landmark (rain risk {int(w['rain_risk']*100)}%)", city=city, start_time=f"{date} 14:30", end_time=f"{date} 17:00", cost_eur=18.0, transport_mode="metro"),
            Activity(title=f"Dinner neighborhood tour", city=city, start_time=f"{date} 19:00", end_time=f"{date} 21:00", cost_eur=45.0, transport_mode="walk"),
        ]
        total_cost += 25 + 18 + 45
        plans.append(DayPlan(date=date, city=city, activities=acts))

    summary = (
        f"{days_n} days across {', '.join(req.cities)}. "
        f"Flight estimate to {first_city}: €{flight['price_eur']}. "
        f"Daily budget ~€{per_day_budget:.0f}."
    )

    return PlanResponse(summary=summary, total_cost_estimate_eur=round(total_cost, 2), days=plans, citations=citations)