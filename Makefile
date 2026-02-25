.PHONY: help install dev backend frontend worker beat migrate seed clean docker-up docker-down

## ── Help ──────────────────────────────────────────────────────────────────────
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

## ── Setup ─────────────────────────────────────────────────────────────────────
install:  ## Install all dependencies (backend + frontend)
	cd backend && pip install -r requirements.txt
	cd frontend && npm install --legacy-peer-deps

## ── Dev Servers ───────────────────────────────────────────────────────────────
dev:  ## Start everything concurrently (requires concurrently: npx concurrently)
	npx concurrently \
		"make backend" \
		"make worker" \
		"make frontend" \
		--names "API,Worker,Frontend" \
		--prefix-colors "blue,yellow,green"

backend:  ## Start FastAPI backend
	PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

worker:  ## Start Celery worker
	PYTHONPATH=. celery -A backend.workers.celery_app worker --loglevel=info --concurrency=2

beat:  ## Start Celery Beat (scheduler)
	PYTHONPATH=. celery -A backend.workers.celery_app beat --loglevel=info

frontend:  ## Start Next.js dev server
	cd frontend && npm run dev

## ── Database ──────────────────────────────────────────────────────────────────
migrate:  ## Run Alembic migrations
	PYTHONPATH=. alembic upgrade head

migrate-down:  ## Rollback last migration
	PYTHONPATH=. alembic downgrade -1

migrate-history:  ## Show migration history
	PYTHONPATH=. alembic history

## ── Docker ────────────────────────────────────────────────────────────────────
docker-up:  ## Start all services with Docker Compose
	docker compose up -d

docker-up-build:  ## Build and start all services
	docker compose up -d --build

docker-down:  ## Stop all Docker services
	docker compose down

docker-logs:  ## Tail Docker logs
	docker compose logs -f

## ── Utilities ─────────────────────────────────────────────────────────────────
clean:  ## Remove __pycache__, .next, etc.
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null; true

format:  ## Format Python code with black + isort
	black backend/
	isort backend/

lint:  ## Lint Python (ruff) + TypeScript
	ruff check backend/
	cd frontend && npm run lint
