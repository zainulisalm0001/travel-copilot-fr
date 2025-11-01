# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

class Settings:
    APP_ENV = os.getenv("APP_ENV", "dev")
    APP_PORT = int(os.getenv("APP_PORT", 8000))

    # Provider switches
    PROVIDER_WEATHER = os.getenv("PROVIDER_WEATHER", "openmeteo")   # openmeteo|openweather
    PROVIDER_FLIGHTS = os.getenv("PROVIDER_FLIGHTS", "skyscanner")  # skyscanner|amadeus|mock
    PROVIDER_MAPS    = os.getenv("PROVIDER_MAPS", "google")         # google|mock

    # API keys
    OPENWEATHER_API_KEY   = os.getenv("OPENWEATHER_API_KEY", "")
    GOOGLE_MAPS_API_KEY   = os.getenv("GOOGLE_MAPS_API_KEY", "")
    RAPIDAPI_KEY          = os.getenv("RAPIDAPI_KEY", "")
    AMADEUS_CLIENT_ID     = os.getenv("AMADEUS_CLIENT_ID", "")
    AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET", "")

    # Database: either a single DATABASE_URL or build Postgres from parts
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB   = os.getenv("POSTGRES_DB", "tcopilot")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "tcopilot")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "tcopilot")

    def db_url(self) -> str:
        """Return a SQLAlchemy URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()