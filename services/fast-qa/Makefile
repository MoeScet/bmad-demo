# Fast Q&A Service Makefile

.PHONY: help install test lint format run dev docker-build docker-run clean seed

# Default target
help:
	@echo "Fast Q&A Service - Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  run         - Run service in production mode"
	@echo "  dev         - Run service in development mode"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with docker-compose"
	@echo "  seed        - Seed database with sample data"
	@echo "  clean       - Clean temporary files"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	PYTHONPATH=src pytest tests/ -v

# Run linting
lint:
	PYTHONPATH=src ruff check src/ tests/
	PYTHONPATH=src ruff format --check src/ tests/

# Format code  
format:
	PYTHONPATH=src ruff format src/ tests/

# Run service in production mode
run:
	cd src && python main.py

# Run service in development mode with reload
dev:
	cd src && uvicorn main:app --reload --host 0.0.0.0 --port 8003

# Build Docker image
docker-build:
	docker build -t fast-qa:latest .

# Run with docker-compose
docker-run:
	docker-compose up -d

# Stop docker-compose services
docker-stop:
	docker-compose down

# Seed database with sample data
seed:
	PYTHONPATH=src python scripts/seed_data.py

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Run health check
health:
	curl -f http://localhost:8003/health || exit 1

# Quick development setup
setup-dev: install
	@echo "Development environment ready!"
	@echo "Run 'make dev' to start the service"