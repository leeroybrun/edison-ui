# Edison UI Makefile

PYTHON ?= python3.13
NPM_CACHE ?= $(CURDIR)/.npm-cache

.PHONY: help
help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-18s %s\n", $$1, $$2}'

# --- Install ---

.PHONY: install
install: ## Install backend+frontend deps
	@echo "Backend deps (venv in backend/.venv)..."
	@$(PYTHON) -m venv backend/.venv
	@. backend/.venv/bin/activate && pip install -U pip >/dev/null && pip install -r backend/requirements.txt
	@echo "Frontend deps..."
	@cd frontend && npm_config_cache="$(NPM_CACHE)" npm install

.PHONY: install-edison
install-edison: ## Install Edison editable (EDISON_PATH=../edison)
	@if [ -z "$(EDISON_PATH)" ]; then echo "EDISON_PATH is required (e.g. make install-edison EDISON_PATH=../edison)"; exit 1; fi
	@. backend/.venv/bin/activate && pip install -e "$(EDISON_PATH)"

# --- Dev ---

.PHONY: dev-backend
dev-backend: ## Run backend (http://localhost:8000)
	@cd backend && . .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run frontend (http://localhost:3000)
	@cd frontend && npm run dev

# --- Quality ---

.PHONY: backend-test
backend-test: ## Run backend tests
	@cd backend && . .venv/bin/activate && pytest -q

.PHONY: backend-lint
backend-lint: ## Lint backend (ruff + mypy)
	@cd backend && . .venv/bin/activate && ruff check . && mypy .

.PHONY: backend-format
backend-format: ## Format backend (ruff)
	@cd backend && . .venv/bin/activate && ruff format .

.PHONY: frontend-test
frontend-test: ## Run frontend tests (vitest)
	@cd frontend && npm test

.PHONY: frontend-lint
frontend-lint: ## Lint frontend
	@cd frontend && npm run lint

.PHONY: frontend-format
frontend-format: ## Format frontend (prettier)
	@cd frontend && npm run format

.PHONY: frontend-type-check
frontend-type-check: ## Typecheck frontend (tsc)
	@cd frontend && npm run type-check

.PHONY: test
test: backend-test frontend-test ## Run all tests

.PHONY: test-coverage
test-coverage: ## Run coverage (backend + frontend)
	@cd backend && . .venv/bin/activate && pytest --cov=. --cov-report=term-missing
	@cd frontend && npm run test:coverage

.PHONY: lint
lint: backend-lint frontend-lint ## Lint all

.PHONY: format
format: backend-format frontend-format ## Format all

.PHONY: type-check
type-check: backend-lint frontend-type-check ## Type check (backend via mypy)

.DEFAULT_GOAL := help
