import random

def flight_eur(origin: str, dest_airport: str, depart_date: str) -> dict:
    """Return a mock flight quote (EUR). Replace with real API later."""
    return {
        "provider": "mock-skyscanner",
        "price_eur": round(random.uniform(60, 180), 2),
        "currency": "EUR",
        "url": f"https://example.com/flights?o={origin}&d={dest_airport}&dt={depart_date}",
        "ttl_min": 30,
    }
