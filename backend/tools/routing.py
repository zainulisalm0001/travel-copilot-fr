from math import radians, sin, cos, asin, sqrt

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points (km)."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

def travel_minutes_km(distance_km: float, mode: str) -> int:
    """Rough travel time in minutes for a given mode."""
    speeds_kmh = {
        "walk": 4.5,
        "metro": 25.0,
        "bus": 18.0,
        "train": 120.0,
    }
    v = speeds_kmh.get(mode, 20.0)
    return max(1, int((distance_km / v) * 60))

def estimate_minutes(a: tuple[float, float], b: tuple[float, float], mode: str = "metro") -> int:
    """Estimate minutes between coords a and b using a simple speed model."""
    km = _haversine(a[0], a[1], b[0], b[1])
    return max(5, travel_minutes_km(km, mode))
