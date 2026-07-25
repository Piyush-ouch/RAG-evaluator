.PHONY: help dev dev-up dev-down dev-build backend frontend test lint migrate seed clean logs

# =========================================================
# Enterprise RAG Sandbox & Guardrail Evaluator
# Developer Makefile
# =========================================================

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------
# Development
# ---------------------------------------------------------
dev: ## Start all services for local development
	docker compose up -d postgres redis minio
	@echo "Waiting for services to be ready..."
	@sleep 3
	@$(MAKE) migrate
	@echo "Starting backend and frontend..."
	@cd backend && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000 &
	@cd frontend && pnpm dev &
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "MinIO Console: http://localhost:9001"

dev-up: ## Start all services via Docker Compose
	docker compose up -d --build

dev-down: ## Stop all services
	docker compose down

dev-build: ## Rebuild all Docker images
	docker compose build --no-cache

# ---------------------------------------------------------
# Backend
# ---------------------------------------------------------
backend: ## Start backend server (dev mode)
	cd backend && uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

backend-install: ## Install backend dependencies
	cd backend && pip install -e ".[dev]"

worker: ## Start Celery worker
	cd backend && celery -A app.workers.celery_app worker -l info -Q evaluation,reports,notifications,data,scheduled,maintenance

worker-beat: ## Start Celery beat scheduler
	cd backend && celery -A app.workers.celery_app beat -l info

flower: ## Start Flower (Celery monitoring)
	cd backend && celery -A app.workers.celery_app flower --port=5555

# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------
frontend: ## Start frontend dev server
	cd frontend && pnpm dev

frontend-install: ## Install frontend dependencies
	cd frontend && pnpm install

frontend-build: ## Build frontend for production
	cd frontend && pnpm build

# ---------------------------------------------------------
# Database
# ---------------------------------------------------------
migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

migrate-history: ## Show migration history
	cd backend && alembic history

seed: ## Seed database with sample data
	cd backend && python -m app.database.seed

# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------
test: ## Run all tests
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests with coverage
	cd backend && pytest --cov=app --cov-report=html --cov-report=term-missing -v

test-frontend: ## Run frontend tests
	cd frontend && pnpm test

test-e2e: ## Run end-to-end tests
	cd frontend && pnpm exec playwright test

test-integration: ## Run integration tests only
	cd backend && pytest tests/integration -v

test-load: ## Run load tests
	cd backend && locust -f tests/load/locustfile.py

# ---------------------------------------------------------
# Code Quality
# ---------------------------------------------------------
lint: ## Run all linters
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend: ## Lint backend code
	cd backend && ruff check app/ tests/
	cd backend && ruff format --check app/ tests/
	cd backend && mypy app/

lint-frontend: ## Lint frontend code
	cd frontend && pnpm lint
	cd frontend && pnpm type-check

format: ## Format all code
	cd backend && ruff format app/ tests/
	cd frontend && pnpm format

# ---------------------------------------------------------
# Docker
# ---------------------------------------------------------
docker-build: ## Build production Docker images
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

docker-push: ## Push images to registry
	docker compose -f docker-compose.yml -f docker-compose.prod.yml push

# ---------------------------------------------------------
# Observability
# ---------------------------------------------------------
logs: ## Tail all service logs
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-worker: ## Tail worker logs
	docker compose logs -f worker

# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------
clean: ## Remove all build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .turbo -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage
	rm -rf frontend/coverage

shell: ## Open Python shell with app context
	cd backend && python -c "from app.main import create_app; app = create_app()" 

generate-key: ## Generate a new encryption key
	python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

generate-secret: ## Generate a new secret key
	python -c "import secrets; print(secrets.token_urlsafe(64))"
