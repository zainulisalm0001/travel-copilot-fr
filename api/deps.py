from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from redis import Redis
from qdrant_client import QdrantClient
from api.config import settings

_pg_dsn = f"postgresql+psycopg://{settings.PG_USER}:{settings.PG_PASSWORD}@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
engine: Engine = create_engine(_pg_dsn, pool_pre_ping=True)

redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email TEXT,
  locale TEXT,
  home_airport TEXT,
  currency TEXT DEFAULT 'EUR',
  preferences_json JSONB DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS trips (
  id SERIAL PRIMARY KEY,
  user_id INT,
  origin TEXT,
  start_date DATE,
  end_date DATE,
  budget_eur INT,
  party_size INT,
  style TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS feedback (
  id SERIAL PRIMARY KEY,
  trip_id INT,
  rating NUMERIC,
  comments TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
"""

def init_db():
    with engine.begin() as conn:
        conn.execute(text(SCHEMA_SQL))