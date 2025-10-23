# Use bash as the default shell
SHELL := /bin/bash

# --- Configuration ---
# venv directory is managed by uv (defaults to .venv)
VENV_DIR := .venv
SRC_DIR := src/news_pipeline
TESTS_DIR := tests

# Phony targets are ones that don't represent actual files.
.PHONY: all install-dev dev-services format lint lint-check test test-unit test-integration run db-upgrade db-migrate clean

# --- Main Targets ---

all: install-dev lint test-unit
# Default target when just typing 'make'.

install-dev: $(VENV_DIR)/touchfile
# This target creates the venv and syncs dependencies.
# It's idempotent: it only runs if the venv doesn't exist or pyproject.toml changed.

$(VENV_DIR)/touchfile: pyproject.toml .python-version
	@echo "--- 📦 Creating/updating virtual environment at $(VENV_DIR) ---"
	@echo "Using Python version from .python-version file..."
	@echo "--- 🔄 Syncing all dependencies (prod + dev) ---"
	# Syncs all main dependencies and all optional-dependencies (extras)
	uv sync --all-extras
	@touch $(VENV_DIR)/touchfile
	@echo "--- ✅ Sync complete ---"

dev-services:
	@echo "--- 🐳 Starting background services (Postgres, Redis) ---"
	docker-compose -f docker-compose.dev.yml up --build -d

# --- Code Quality & Formatting ---

format:
	@echo "--- 🎨 Formatting code with black ---"
	uv run black $(SRC_DIR) $(TESTS_DIR)

lint-check:
	@echo "--- 🧐 Checking formatting with black ---"
	uv run black --check $(SRC_DIR) $(TESTS_DIR)
	@echo "---  linting with flake8 ---"
	uv run flake8 $(SRC_DIR) $(TESTS_DIR)

lint: format lint-check
# 'lint' will auto-format first, then run the checks.

# --- Testing ---

test: test-unit
# Default 'make test' runs only the fast unit tests

test-unit:
	@echo "--- 🧪 Running unit tests ---"
	uv run pytest $(TESTS_DIR)/unit -q

test-integration:
	@echo "--- 🧪 Running integration tests (requires services) ---"
	uv run pytest $(TESTS_DIR)/integration -q

test-all: test-unit test-integration
	@echo "--- ✅ All tests passed ---"

# --- Running the App ---

run:
	@echo "--- 🚀 Starting FastAPI server (live reload) ---"
	uv run uvicorn news_pipeline.main:app --reload --host 0.0.0.0 --port 8000

# --- Database Migrations (Alembic) ---

db-start:
	@echo "--- 🗄️ Initializing alembic ---"
	uv run alembic init alembic

db-upgrade:
	@echo "--- 🗄️ Applying database migrations ---"
	uv run alembic upgrade head

db-migrate:
	@echo "--- 🗄️ Generating new migration file ---"
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

# --- Cleanup ---

clean:
	@echo "--- 🧹 Cleaning up ---"
	rm -rf $(VENV_DIR)
	rm -rf .pytest_cache
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
