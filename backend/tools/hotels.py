import random

def nightly_hotel(city: str, date: str, guests: int, max_price: int) -> dict:
    """Return a mock nightly hotel price (EUR)."""
    return {
        "provider": "mock-booking",
        "city": city,
        "checkin": date,
        "nights": 1,
        "guests": guests,
        "price_eur": min(max_price, round(random.uniform(80, 180), 2)),
        "rating": round(random.uniform(3.8, 4.8), 1),
        "url": f"https://example.com/hotels?c={city}&ci={date}",
    }
