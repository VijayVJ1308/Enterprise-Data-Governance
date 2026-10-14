.PHONY: help setup test lint build clean docker-up docker-down

help:
	@echo "Enterprise Data Quality & Data Governance Platform Management Commands"
	@echo ""
	@echo "  setup       Initialize Python virtual environment & dependencies"
	@echo "  test        Run unit and integration test suites"
	@echo "  lint        Run code linters (ruff, black, mypy)"
	@echo "  docker-up   Start complete local stack with Docker Compose"
	@echo "  docker-down Stop local stack and clean containers"
	@echo "  clean       Remove temporary build, cache, and artifact files"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	@echo "Virtual environment created. Activate with 'source .venv/bin/activate'"

test:
	pytest tests/ -v

lint:
	python3 -m ruff check backend/ data-quality/ governance/
	python3 -m black --check backend/ data-quality/ governance/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf dist/ build/ .coverage htmlcov/
