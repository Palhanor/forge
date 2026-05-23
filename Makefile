.PHONY: setup install test help builder-up builder-down builder-logs

help:
	@echo "Targets:"
	@echo "  setup         Create .venv and install cli + server (editable)"
	@echo "  install       Install cli + server into existing .venv"
	@echo "  test          Run basic import/smoke checks"
	@echo "  builder-up    Build and start forge-builder (docker compose)"
	@echo "  builder-down  Stop forge-builder"
	@echo "  builder-logs  Tail forge-builder logs"

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e cli/ -e server/

install:
	.venv/bin/pip install -e cli/ -e server/

test:
	.venv/bin/python -c "from forge_cli.main import app; from forge_server.main import app as api"
	@echo "OK: cli and server import successfully"

COMPOSE_ENV_FILE := --env-file server/.env

builder-up:
	docker compose $(COMPOSE_ENV_FILE) up -d --build

builder-down:
	docker compose $(COMPOSE_ENV_FILE) down

builder-logs:
	docker compose $(COMPOSE_ENV_FILE) logs -f forge-builder
