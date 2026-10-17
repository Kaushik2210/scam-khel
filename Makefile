.PHONY: setup dev test lint eval eval-live seed demo check-models purge e2e up
PY ?= python

setup:
	cd backend && $(PY) -m pip install -e ".[dev]"

dev:
	cd backend && $(PY) -m uvicorn app.main:create_app --factory --reload --port 8000

test:
	cd backend && $(PY) -m pytest -q

lint:
	cd backend && $(PY) -m ruff check . && $(PY) -m mypy app

check-models:
	cd backend && $(PY) scripts/check_models.py

eval:
	cd backend && $(PY) evals/run_eval.py

eval-live:
	cd backend && $(PY) evals/run_eval.py --live

e2e:
	cd frontend && npx playwright test

up:
	docker compose up --build

seed:
	cd backend && $(PY) scripts/seed_demo.py

demo:
	cd backend && $(PY) scripts/seed_demo.py --reset

purge:
	cd backend && $(PY) scripts/purge.py
