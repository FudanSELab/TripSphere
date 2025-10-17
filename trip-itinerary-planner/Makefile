.PHONY: help install compile-proto run test lint format clean docker-build docker-run

# Load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

help:
	@echo "Trip Itinerary Planner - Available Commands"
	@echo "==========================================="
	@echo "install         Install dependencies"
	@echo "install-dev     Install with dev dependencies"
	@echo "compile-proto   Compile protobuf files"
	@echo "run            Run the service locally"
	@echo "test           Run tests (requires install-dev)"
	@echo "lint           Run linters (requires install-dev)"
	@echo "format         Format code (requires install-dev)"
	@echo "clean          Clean generated files"
	@echo "docker-build   Build Docker image"
	@echo "docker-run     Run Docker container"

install:
	uv sync

install-dev:
	uv sync --all-groups

compile-proto:
	uv run --with grpcio-tools -m grpc_tools.protoc \
		-Ilibs/proto \
		--python_out=libs/tripsphere/src \
		--pyi_out=libs/tripsphere/src \
		--grpc_python_out=libs/tripsphere/src \
		libs/proto/tripsphere/**/*.proto

run:
	@if [ -z "$$LLM__API_KEY" ]; then \
		echo "Error: LLM__API_KEY is not set"; \
		echo "Please set it via: export LLM__API_KEY='your-key'"; \
		echo "Or create a .env file: make setup-env"; \
		exit 1; \
	fi
	uv run python -m itinerary_planner.server

test:
	@if ! uv run --no-sync pytest --version > /dev/null 2>&1; then \
		echo "Error: pytest not found. Run 'make install-dev' first"; \
		exit 1; \
	fi
	uv run pytest -v

lint:
	@if ! uv run --no-sync ruff --version > /dev/null 2>&1; then \
		echo "Error: ruff not found. Run 'make install-dev' first"; \
		exit 1; \
	fi
	uv run mypy src/
	uv run ruff check src/

format:
	@if ! uv run --no-sync ruff --version > /dev/null 2>&1; then \
		echo "Error: ruff not found. Run 'make install-dev' first"; \
		exit 1; \
	fi
	uv run ruff format src/
	uv run ruff check --fix src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf libs/tripsphere/src/tripsphere/**/*_pb2.py
	rm -rf libs/tripsphere/src/tripsphere/**/*_pb2.pyi
	rm -rf libs/tripsphere/src/tripsphere/**/*_pb2_grpc.py

docker-build:
	docker build -t trip-itinerary-planner:latest .

docker-run:
	@echo "Make sure to set LLM__API_KEY environment variable"
	docker run -e LLM__API_KEY="${LLM__API_KEY}" \
		-e NACOS__SERVER_ADDRESS="host.docker.internal:8848" \
		-p 50059:50059 \
		trip-itinerary-planner:latest

example:
	cd examples && uv run python -m example_client

