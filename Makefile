.PHONY: setup dev test lint eval seed demo check-models purge
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

seed:
	cd backend && $(PY) scripts/seed_demo.py

demo: seed

purge:
	cd backend && $(PY) scripts/purge.py
