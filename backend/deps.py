# backend/deps.py
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from backend.config import settings

DB_URL = settings.db_url()
engine: Engine = create_engine(DB_URL, pool_pre_ping=True, future=True)

def _schema_sql_postgres() -> str:
    return """
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

def _schema_sql_sqlite() -> str:
    return """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT,
  locale TEXT,
  home_airport TEXT,
  currency TEXT DEFAULT 'EUR',
  preferences_json TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS trips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  origin TEXT,
  start_date TEXT,
  end_date TEXT,
  budget_eur INTEGER,
  party_size INTEGER,
  style TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id INTEGER,
  rating REAL,
  comments TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
"""

def init_db() -> None:
    try:
        dialect = engine.url.get_backend_name()
        schema = _schema_sql_postgres() if dialect.startswith("postgres") else _schema_sql_sqlite()
        with engine.begin() as conn:
            # Execute each statement separately to appease SQLite
            for stmt in [s.strip() for s in schema.strip().split(";\n") if s.strip()]:
                conn.execute(text(stmt))
    except Exception as e:
        print(f"[deps.init_db] Skipped DB init due to: {e}")