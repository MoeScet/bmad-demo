# BMAD Development Makefile
# Provides common development tasks and commands

.PHONY: help setup test test-unit test-integration lint type-check format clean docker-build docker-up docker-down deploy-staging deploy-prod

# Default target
help:
	@echo "BMAD Development Commands"
	@echo "========================="
	@echo ""
	@echo "Setup:"
	@echo "  setup          - Set up development environment"
	@echo "  clean          - Clean up temporary files and caches"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests (unit + integration)"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-service   - Run tests for specific service (SERVICE=name)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           - Run linting on all services"
	@echo "  type-check     - Run type checking on all services"
	@echo "  format         - Format code using ruff"
	@echo "  security-scan  - Run security checks"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   - Build all service containers"
	@echo "  docker-up      - Start development environment with Docker"
	@echo "  docker-down    - Stop Docker development environment"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod    - Deploy to production environment"

# Development setup
setup:
	@echo "Setting up BMAD development environment..."
	python scripts/setup-dev-env.py

# Testing targets
test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ] && [ -d "$$service/tests" ]; then \
			echo "Testing $$service..."; \
			cd "$$service" && \
			source venv/bin/activate && \
			pytest tests/ -v --cov=src --cov-report=term-missing && \
			cd - > /dev/null; \
		fi; \
	done

test-integration:
	@echo "Running integration tests..."
	@if [ -d "tests/integration" ]; then \
		cd tests/integration && \
		pytest . -v; \
	else \
		echo "No integration tests found"; \
	fi

test-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: Please specify SERVICE=<service-name>"; \
		exit 1; \
	fi
	@echo "Running tests for $(SERVICE)..."
	@cd services/$(SERVICE) && \
	source venv/bin/activate && \
	pytest tests/ -v --cov=src --cov-report=term-missing

# Code quality targets
lint:
	@echo "Running linting on all services..."
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ] && [ -d "$$service/src" ]; then \
			echo "Linting $$service..."; \
			cd "$$service" && \
			source venv/bin/activate && \
			ruff check src/ && \
			cd - > /dev/null; \
		fi; \
	done

type-check:
	@echo "Running type checking on all services..."
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ] && [ -d "$$service/src" ]; then \
			echo "Type checking $$service..."; \
			cd "$$service" && \
			source venv/bin/activate && \
			mypy src/ --ignore-missing-imports && \
			cd - > /dev/null; \
		fi; \
	done

format:
	@echo "Formatting code..."
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ] && [ -d "$$service/src" ]; then \
			echo "Formatting $$service..."; \
			cd "$$service" && \
			source venv/bin/activate && \
			ruff format src/ && \
			cd - > /dev/null; \
		fi; \
	done

security-scan:
	@echo "Running security scans..."
	@for service in services/*/; do \
		if [ -f "$$service/requirements.txt" ]; then \
			echo "Security scan for $$service..."; \
			cd "$$service" && \
			source venv/bin/activate && \
			safety check -r requirements.txt && \
			bandit -r src/ -f json || true && \
			cd - > /dev/null; \
		fi; \
	done

# Docker targets
docker-build:
	@echo "Building Docker containers for all services..."
	@for service in services/*/; do \
		if [ -f "$$service/Dockerfile" ]; then \
			service_name=$$(basename "$$service"); \
			echo "Building bmad-$$service_name..."; \
			docker build -t "bmad-$$service_name:latest" "$$service"; \
		fi; \
	done

docker-up:
	@echo "Starting development environment with Docker..."
	docker-compose up -d
	@echo "Services available at:"
	@echo "  Teams Bot API: http://localhost:8001"
	@echo "  Query Orchestration: http://localhost:8002"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  ChromaDB: http://localhost:8000"

docker-down:
	@echo "Stopping Docker development environment..."
	docker-compose down

# Database targets
db-migrate:
	@echo "Running database migrations..."
	@if [ -f ".env" ]; then \
		export $$(cat .env | xargs); \
	fi; \
	psql $$DATABASE_URL -f infrastructure/database/migrations/001_initial_schema.sql

db-reset:
	@echo "Resetting database..."
	@if [ -f ".env" ]; then \
		export $$(cat .env | xargs); \
	fi; \
	dropdb --if-exists bmad_dev && \
	createdb bmad_dev && \
	psql bmad_dev -f infrastructure/database/migrations/001_initial_schema.sql

# Deployment targets
deploy-staging:
	@echo "Deploying to staging environment..."
	gh workflow run deploy-staging.yml

deploy-prod:
	@echo "Deploying to production environment..."
	@read -p "Are you sure you want to deploy to production? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		gh workflow run deploy-production.yml; \
	else \
		echo "Deployment cancelled."; \
	fi

# Cleanup targets
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleanup complete."

# Install pre-commit hooks
install-hooks:
	@echo "Installing pre-commit hooks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
	else \
		echo "pre-commit not installed. Run: pip install pre-commit"; \
	fi