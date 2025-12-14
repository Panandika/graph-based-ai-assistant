.PHONY: dev dev-backend dev-frontend install install-backend install-frontend lint lint-backend lint-frontend test test-backend test-frontend build docker-up docker-down clean

# Development
dev: ## Run both backend and frontend in development mode
	@make -j2 dev-backend dev-frontend

dev-backend: ## Run backend development server
	cd backend && uv run fastapi dev app/main.py

dev-frontend: ## Run frontend development server
	cd frontend && npm run dev

# Installation
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	cd backend && uv sync

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# Linting
lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	cd backend && uv run ruff check app && uv run ruff format --check app

fix-backend: ## Auto-fix backend code
	cd backend && uv run ruff check --fix app && uv run ruff format app

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

# Type checking
type-check: type-check-backend type-check-frontend ## Run all type checks

type-check-backend: ## Type check backend
	cd backend && uv run mypy app

type-check-frontend: ## Type check frontend
	cd frontend && npm run type-check

# Testing
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && uv run pytest tests/ -v

test-frontend: ## Run frontend tests
	cd frontend && npm run test -- --run

# Building
build: build-backend build-frontend ## Build all

build-backend: ## Build backend Docker image
	docker build -t graph-ai-backend:latest --target production ./backend

build-frontend: ## Build frontend for production
	cd frontend && npm run build

# Docker
docker-up: ## Start all services with Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## View Docker logs
	docker compose logs -f

# Utilities
clean: ## Clean generated files
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	rm -rf frontend/node_modules frontend/dist frontend/coverage
	docker compose down -v

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
