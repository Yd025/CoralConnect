.PHONY: up api web test

up:
	docker compose up --build

api:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

web:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && python -m pytest -q
