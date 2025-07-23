.PHONY: verify lint format type test frontend install clean help

# Default target when just running 'make'
all: verify

# Main verification pipeline - what agents should run
verify: install lint type test
	@echo "✅ All checks passed - ready to commit"

# Individual components
install:
	@echo "📦 Installing dependencies..."
	poetry install --no-interaction --no-root

lint:
	@echo "🔍 Linting and formatting..."
	poetry run ruff check . --fix
	poetry run ruff format .

type:
	@echo "🔧 Type checking..."
	poetry run pip install types-pyyaml || true
	poetry run mypy . --show-error-codes

test:
	@echo "🧪 Running tests..."
	poetry run pytest -q --tb=short

format: lint
	@echo "✨ Code formatted"

# Frontend checks (run separately or as part of full verification)
frontend:
	@echo "🌐 Checking frontend..."
	@if [ -d "frontend" ]; then \
		cd frontend && \
		npm install --no-fund --no-audit && \
		npm run lint; \
	else \
		echo "⚠️  No frontend directory found"; \
	fi

# Full verification including frontend
verify-all: verify frontend
	@echo "✅ All checks (including frontend) passed"

# Development helpers
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage .ruff_cache
	@if [ -d "frontend/node_modules" ]; then rm -rf frontend/node_modules; fi

# Quick checks for rapid iteration
quick: install
	poetry run ruff check . --fix
	poetry run ruff format .
	poetry run pytest -x --tb=short

# Help target
help:
	@echo "Available targets:"
	@echo "  verify      - Run all Python checks (default for agents)"
	@echo "  verify-all  - Run all checks including frontend"
	@echo "  install     - Install Python dependencies"
	@echo "  lint        - Run ruff linter and formatter"
	@echo "  type        - Run mypy type checker"
	@echo "  test        - Run pytest suite"
	@echo "  frontend    - Run frontend linting"
	@echo "  quick       - Fast iteration: format + first test failure"
	@echo "  clean       - Remove cache files and node_modules"
	@echo "  help        - Show this help message"

# Debugging helpers
debug-deps:
	@echo "📋 Dependency information:"
	poetry show --outdated || echo "All dependencies up to date"
	poetry check

debug-env:
	@echo "🔍 Environment information:"
	@echo "Python: $$(poetry run python --version)"
	@echo "Poetry: $$(poetry --version)"
	@echo "Node: $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "NPM: $$(npm --version 2>/dev/null || echo 'Not installed')"