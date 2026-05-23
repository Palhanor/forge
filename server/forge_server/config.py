import os
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parent.parent
_DATA_DEFAULT = SERVER_ROOT / "data"
DATA_DIR = Path(os.environ.get("FORGE_DATA_DIR", _DATA_DEFAULT)).resolve()
DEPLOYMENTS_DIR = DATA_DIR / "deployments"
REGISTRY_FILE = DATA_DIR / "apps.json"
