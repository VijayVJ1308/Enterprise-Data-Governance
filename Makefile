.PHONY: help setup test lint build clean docker-up docker-down docker-start run-backend run-frontend build-frontend seed healthcheck

help:
	@echo "🛡️  AegisData: Enterprise Data Quality & Governance Platform"
	@echo "================================================================="
	@echo "Local Execution Commands:"
	@echo "  make seed            Seed demo metadata & Medallion lakehouse tables"
	@echo "  make run-backend     Start FastAPI backend server (port 8000)"
	@echo "  make run-frontend    Start React Vite dashboard (port 5173)"
	@echo "  make build-frontend  Build production bundle for React frontend"
	@echo "  make healthcheck     Probe all platform service endpoints"
	@echo ""
	@echo "Docker Production Stack Commands:"
	@echo "  make docker-start    One-click bootstrap via ./scripts/start_platform.sh"
	@echo "  make docker-up       Start 8-service container stack with Docker Compose"
	@echo "  make docker-down     Stop container stack and prune local volumes"
	@echo ""
	@echo "Testing & Quality Assurance:"
	@echo "  make test            Run all 113 automated tests across 22 phases"
	@echo "  make lint            Run code linters (ruff, black, mypy)"
	@echo "  make clean           Remove temporary build, cache, and artifact files"
	@echo "================================================================="

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip -r requirements.txt
	@echo "Virtual environment created. Activate with 'source .venv/bin/activate'"

seed:
	python3 scripts/seed_demo_data.py

run-backend:
	python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

healthcheck:
	./scripts/healthcheck.sh

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m ruff check backend/ data-quality/ governance/
	python3 -m black --check backend/ data-quality/ governance/

docker-start:
	./scripts/start_platform.sh

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf dist/ build/ .coverage htmlcov/

