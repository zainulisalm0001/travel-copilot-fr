up:
	docker compose up --build

down:
	docker compose down -v

api:
	uvicorn api.main:app --reload --port 8000

ui:
	streamlit run app/streamlit_app.py