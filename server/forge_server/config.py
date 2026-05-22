from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SERVER_ROOT / "data"
DEPLOYMENTS_DIR = DATA_DIR / "deployments"
REGISTRY_FILE = DATA_DIR / "apps.json"
