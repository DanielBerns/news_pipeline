# --- Environment / Shell ---
.DEFAULT_GOAL := help
SHELL := /bin/bash
.PHONY: help install setup ci lint test typecheck format run db-start db-upgrade db-migrate db-revision docker-db-up docker-db-down docker-db-rm docker-db-logs clean

# --- Docker DB Configuration ---
# Customize these variables for your local setup
DB_CONTAINER_NAME := news_pipeline_db
DB_PASSWORD := mysecretpassword
DB_USER := news_user
DB_NAME := news_pipeline
DB_PORT := 5432
DB_VOLUME := pgdata

# Database URL for Alembic (reads from .env file or uses default)
# Note: We export this so it's available to alembic
export DATABASE_URL ?= postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}

# --- Commands ---
help:
	@echo "Available commands:"
	@echo "  install          Install dependencies using uv"
	@echo "  setup            Alias for install"
	@echo "  ci               Run all checks (lint, typecheck, test)"
	@echo "  lint             Run ruff linter"
	@echo "  typecheck        Run mypy type checker"
	@echo "  format           Run ruff formatter"
	@echo "  test             Run pytest"
	@echo "  run              Run the FastAPI server with uvicorn"
	@echo ""
	@echo "Database (Docker):"
	@echo "  docker-db-up     Start the local PostgreSQL Docker container"
	@echo "  docker-db-down   Stop the local PostgreSQL Docker container"
	@echo "  docker-db-rm     Remove the local PostgreSQL Docker container and volume"
	@echo "  docker-db-logs   Follow the logs of the Docker container"
	@echo ""
	@echo "Database (Alembic):"
	@echo "  db-start         Initialize alembic directory (with editable env.py)"
	@echo "  db-migrate       Create a new database migration file"
	@echo "  db-upgrade       Run database migrations (depends on docker-db-up)"
	@echo "  db-revision      Create a new empty database migration file"
	@echo ""
	@echo "Cleaning repo:"
	@echo "  clean    - Remove Python cache files and build artifacts"

# --- Environment Setup ---
install:
	@echo "Syncing dependencies with uv..."
	# Assuming you have pyproject.toml set up for uv
	uv sync pyproject.toml --all-extras

setup: install

# --- CI/Checks ---
ci: lint typecheck test

lint:
	@echo "Running linter..."
	uv run -- ruff check .

typecheck:
	@echo "Running type checker..."
	uv run -- mypy src

format:
	@echo "Running formatter..."
	uv run -- ruff format .

test:
	@echo "Running tests..."
	uv run -- pytest

# --- Application ---
run:
	@echo "Starting server..."
	uv run -- uvicorn src.news_pipeline.main:app --reload

# --- Docker Database Management ---
docker-db-up:
	@echo "Starting local PostgreSQL container..."
	@if [ $$(docker ps -q -f name=^/${DB_CONTAINER_NAME}$$) ]; then \
		echo "Container '${DB_CONTAINER_NAME}' is already running."; \
	elif [ $$(docker ps -aq -f name=^/${DB_CONTAINER_NAME}$$) ]; then \
		echo "Starting existing container '${DB_CONTAINER_NAME}'..."; \
		docker start ${DB_CONTAINER_NAME}; \
	else \
		echo "Creating and starting new container '${DB_CONTAINER_NAME}'..."; \
		docker run -d \
			--name ${DB_CONTAINER_NAME} \
			-e POSTGRES_USER=${DB_USER} \
			-e POSTGRES_PASSWORD=${DB_PASSWORD} \
			-e POSTGRES_DB=${DB_NAME} \
			-v ${DB_VOLUME}:/var/lib/postgresql/data \
			-p ${DB_PORT}:5432 \
			postgres:16; \
		echo "Waiting for database to be ready..."; \
		sleep 5; \
	fi

docker-db-down:
	@echo "Stopping local PostgreSQL container..."
	@docker stop ${DB_CONTAINER_NAME}

docker-db-rm:
	@echo "Stopping and removing local PostgreSQL container..."
	@docker rm -f ${DB_CONTAINER_NAME}
	@echo "Removing data volume '${DB_VOLUME}'..."
	@docker volume rm ${DB_VOLUME} || true

docker-db-logs:
	@echo "Following database logs (Press Ctrl+C to stop)..."
	@docker logs -f ${DB_CONTAINER_NAME}

# --- Database Migrations (Alembic) ---

db-start:
	@echo "Initializing alembic..."
	uv run alembic init alembic

# Note: db-upgrade now depends on docker-db-up
db-upgrade: docker-db-up
	@echo "Running database migrations..."
	@echo "Using database URL: ${DATABASE_URL}"
	uv run -- alembic upgrade head

db-migrate:
	@echo "Creating new migration..."
	@uv run -- bash -c 'read -p "Enter migration message: " msg; alembic revision --autogenerate -m "$$msg"'

db-revision:
	@echo "Creating new empty revision..."
	@uv run -- bash -c 'read -p "Enter migration message: " msg; alembic revision -m "$$msg"'

clean:
	@echo "Cleaning Python cache files and build artifacts..."
	# Find and remove all .pyc files
	find . -type f -name "*.pyc" -delete

	# Find and remove all __pycache__ directories
	# Using -exec rm -rf instead of -delete for non-empty directories
	find . -type d -name "__pycache__" -exec rm -rf {} +

	# Find and remove pytest cache
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

	# Find and remove tox directories
	find . -type d -name ".tox" -exec rm -rf {} +

	# Find and remove .egg-info directories
	find . -type d -name "*.egg-info" -exec rm -rf {} +

	# Remove build and dist directories
	rm -rf build/
	rm -rf dist/

	@echo "Cleaning complete."
