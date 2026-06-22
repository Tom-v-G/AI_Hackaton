DOCKER_COMPOSE ?= docker compose

.PHONY: help setup backend-setup frontend-setup db-up db-wait migrate

help:
	@printf "Available targets:\n"
	@printf "  setup          Install dependencies, start Postgres, wait, and run migrations\n"
	@printf "  backend-setup  Synchronize backend dependencies with uv\n"
	@printf "  frontend-setup Install frontend dependencies with npm ci\n"
	@printf "  db-up          Start local Postgres with Docker Compose\n"
	@printf "  db-wait        Wait until local Postgres accepts connections\n"
	@printf "  migrate        Apply Alembic migrations to the local database\n"

setup:
	$(MAKE) backend-setup
	$(MAKE) frontend-setup
	$(MAKE) db-up
	$(MAKE) db-wait
	$(MAKE) migrate

backend-setup:
	cd backend && uv sync --all-extras --dev

frontend-setup:
	cd frontend && npm ci

db-up:
	$(DOCKER_COMPOSE) up -d postgres

db-wait:
	@printf "Waiting for de_lekbak Postgres to be ready"
	@until $(DOCKER_COMPOSE) exec -T postgres pg_isready -U de_lekbak -d de_lekbak >/dev/null 2>&1; do \
		printf "."; \
		sleep 1; \
	done
	@printf " ready\n"

migrate:
	cd backend && uv run alembic upgrade head
