.PHONY: help install dev test clean docker-up docker-down migrate

help:
	@echo "CloudCostly Development Commands"
	@echo "================================"
	@echo "install        - Install all dependencies"
	@echo "dev            - Start development servers"
	@echo "test           - Run all tests"
	@echo "clean          - Clean build artifacts"
	@echo "docker-up      - Start Docker containers"
	@echo "docker-down    - Stop Docker containers"
	@echo "migrate        - Run database migrations"
	@echo "format         - Format code"
	@echo "lint           - Run linters"

install:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	docker-compose up

test:
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest
	@echo "Running frontend tests..."
	cd frontend && npm test

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf backend/dist backend/build
	rm -rf frontend/dist frontend/build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	@echo "Running database migrations..."
	cd backend && . venv/bin/activate && alembic upgrade head

format:
	@echo "Formatting code..."
	cd backend && . venv/bin/activate && black app
	cd frontend && npm run format

lint:
	@echo "Running linters..."
	cd backend && . venv/bin/activate && flake8 app && mypy app
	cd frontend && npm run lint
