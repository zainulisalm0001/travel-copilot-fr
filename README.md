# Travel Planner Copilot — France

## Quick Start (Docker)
1) `cp .env.example .env`
2) `docker compose up --build`
3) Open http://localhost:8501

## Quick Start (Local)
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
streamlit run app/streamlit_app.py