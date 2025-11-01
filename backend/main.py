# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import PlanRequest
from backend.agents.planner import plan_itinerary
from backend.agents.critic import validate
from backend.deps import init_db
from backend.config import settings


app = FastAPI(title="Travel Copilot FR", version="1.0.0")

# CORS (open for local dev; restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Don’t crash the server if DB isn’t available in dev
    try:
        init_db()
    except Exception as e:
        print(f"[deps.init_db] Skipped DB init due to: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    """Lightweight diagnostics so you can verify providers & keys are detected."""
    return {
        "providers": {
            "weather": getattr(settings, "PROVIDER_WEATHER", "unknown"),
            "flights": getattr(settings, "PROVIDER_FLIGHTS", "unknown"),
            "maps": getattr(settings, "PROVIDER_MAPS", "unknown"),
        },
        "keys_present": {
            "OPENWEATHER_API_KEY": bool(getattr(settings, "OPENWEATHER_API_KEY", "")),
            "RAPIDAPI_KEY": bool(getattr(settings, "RAPIDAPI_KEY", "")),
            "AMADEUS_CLIENT_ID": bool(getattr(settings, "AMADEUS_CLIENT_ID", "")),
            "AMADEUS_CLIENT_SECRET": bool(getattr(settings, "AMADEUS_CLIENT_SECRET", "")),
            "GOOGLE_MAPS_API_KEY": bool(getattr(settings, "GOOGLE_MAPS_API_KEY", "")),
        },
        "app": {
            "title": app.title,
            "version": app.version,
            "env": getattr(settings, "APP_ENV", "dev"),
        },
    }


@app.post("/plan")
async def plan(req: PlanRequest):
    """
    Create an itinerary. The planner internally calls weather / flights / hotels tools
    based on provider flags and uses graceful fallbacks where configured.
    """
    try:
        result = await plan_itinerary(req)
        issues = validate(result)
        return {"result": result.model_dump(), "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))