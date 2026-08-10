.PHONY: install test lint format type-check clean build docker run

install:
	uv pip install -e ".[dev]"

test:
	pytest -v --cov=multicloud_mcp --cov-report=term-missing

lint:
	ruff check src tests

format:
	ruff format src tests

type-check:
	mypy src

check: lint type-check test

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

docker:
	docker build -t multicloud-mcp-server:latest .

run:
	multicloud-mcp-server --log-level DEBUG

run-http:
	multicloud-mcp-server --transport http --port 8080
