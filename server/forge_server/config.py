import os
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent
_DATA_DEFAULT = SERVER_ROOT / "data"
DATA_DIR = Path(os.environ.get("FORGE_DATA_DIR", _DATA_DEFAULT)).resolve()
DEPLOYMENTS_DIR = DATA_DIR / "deployments"
REGISTRY_FILE = DATA_DIR / "apps.json"

FORGE_DOCKER_NETWORK = os.environ.get("FORGE_DOCKER_NETWORK", "forge-net")
FORGE_POSTGRES_HOST = os.environ.get("FORGE_POSTGRES_HOST", "forge-postgres")
FORGE_POSTGRES_PORT = int(os.environ.get("FORGE_POSTGRES_PORT", "5432"))
FORGE_POSTGRES_USER = os.environ.get("FORGE_POSTGRES_USER", "forge")
FORGE_POSTGRES_PASSWORD = os.environ.get("FORGE_POSTGRES_PASSWORD", "")
FORGE_POSTGRES_DB = os.environ.get("FORGE_POSTGRES_DB", "forge")

POSTGRES_CONTAINER_NAME = "forge-postgres"
FORGE_DATA_VOLUME = os.environ.get("FORGE_DATA_VOLUME", "forge_forge-data")
