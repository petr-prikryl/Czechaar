PYTHON ?= python
PIP ?= $(PYTHON) -m pip
NPM ?= npm

.PHONY: install dev backend-dev frontend-dev format lint typecheck test test-backend test-frontend migrate build docker-build docker-up docker-down

install:
	$(PIP) install -e "backend[dev]"
	cd frontend && $(NPM) install

dev:
	@echo "Run 'make backend-dev' and 'make frontend-dev' in separate shells."

backend-dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

frontend-dev:
	cd frontend && $(NPM) run dev

format:
	cd backend && $(PYTHON) -m ruff format app tests
	cd frontend && $(NPM) run format

lint:
	cd backend && $(PYTHON) -m ruff check app tests
	cd frontend && $(NPM) run lint

typecheck:
	cd backend && $(PYTHON) -m mypy app
	cd frontend && $(NPM) run typecheck

test: test-backend test-frontend

test-backend:
	cd backend && $(PYTHON) -m pytest

test-frontend:
	cd frontend && $(NPM) run test

migrate:
	cd backend && $(PYTHON) -m alembic upgrade head

build:
	cd frontend && $(NPM) run build

docker-build:
	docker build -t czecharr:local .

docker-up:
	docker compose up --build

docker-down:
	docker compose down
