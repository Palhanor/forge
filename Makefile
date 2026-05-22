.PHONY: setup install test help

help:
	@echo "Targets:"
	@echo "  setup    Create .venv and install cli + server (editable)"
	@echo "  install  Install cli + server into existing .venv"
	@echo "  test     Run basic import/smoke checks"

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e cli/ -e server/

install:
	.venv/bin/pip install -e cli/ -e server/

test:
	.venv/bin/python -c "from forge_cli.main import app; from forge_server.main import app as api"
	@echo "OK: cli and server import successfully"
