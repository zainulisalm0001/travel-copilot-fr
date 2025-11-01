import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_ENV = os.getenv("APP_ENV", "dev")
    APP_PORT = int(os.getenv("APP_PORT", 8000))

    OPEN_METEO_BASE = os.getenv("OPEN_METEO_BASE", "https://api.open-meteo.com/v1/forecast")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    OSRM_BASE = os.getenv("OSRM_BASE", "http://router.project-osrm.org")

    PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
    PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    PG_DB = os.getenv("POSTGRES_DB", "tcopilot")
    PG_USER = os.getenv("POSTGRES_USER", "tcopilot")
    PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "tcopilot")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

    EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

settings = Settings()