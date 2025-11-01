from math import radians, sin, cos, asin, sqrt

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2*asin(sqrt(a))
    return R*c

# Rough travel time in minutes by mode
SPEEDS = {"walk": 4.5, "metro": 25, "bus": 18, "train": 120}

def travel_minutes_km(distance_km: float, mode: str) -> int:
    v = SPEEDS.get(mode, 20)
    return max(5, int((distance_km / v) * 60))

def estimate_minutes(a: tuple[float,float], b: tuple[float,float], mode: str = "metro") -> int:
    km = _haversine(a[0], a[1], b[0], b[1])
    return travel_minutes_km(km, mode)