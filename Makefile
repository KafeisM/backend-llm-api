.PHONY: run test lint docker-up docker-down seed

run:
	.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

test:
	.\venv\Scripts\python.exe -m pytest tests/ -v

lint:
	.\venv\Scripts\python.exe -m ruff check .

seed:
	.\venv\Scripts\python.exe -m app.db.seed

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
