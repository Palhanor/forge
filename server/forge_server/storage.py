import json
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from forge_server.config import DEPLOYMENTS_DIR, REGISTRY_FILE


def ensure_data_dirs() -> None:
    DEPLOYMENTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> list[dict]:
    if not REGISTRY_FILE.exists():
        return []
    with open(REGISTRY_FILE) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _save_registry(apps: list[dict]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(apps, f, indent=2)


def get_app_by_name(name: str) -> dict | None:
    for app in _load_registry():
        if app.get("name") == name:
            return app
    return None


def get_deploy_metadata(deploy_id: str) -> dict:
    metadata_path = DEPLOYMENTS_DIR / deploy_id / "metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text())


def save_deploy(
    name: str,
    source_path: str,
    archive_bytes: bytes,
    filename: str,
    manifest: dict | None = None,
) -> dict:
    ensure_data_dirs()

    deploy_id = uuid.uuid4().hex[:12]
    deploy_dir = DEPLOYMENTS_DIR / deploy_id
    deploy_dir.mkdir(parents=True)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    archive_name = filename or f"{safe_name}.tar.gz"
    archive_path = deploy_dir / archive_name
    archive_path.write_bytes(archive_bytes)

    created_at = datetime.now(UTC).isoformat()
    metadata = {
        "id": deploy_id,
        "name": name,
        "source_path": source_path,
        "archive": str(archive_path),
        "archive_size": len(archive_bytes),
        "created_at": created_at,
        "status": "stored",
        "manifest": manifest,
    }
    (deploy_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    apps = _load_registry()
    apps = [app for app in apps if app.get("name") != name]
    entry = {
        "name": name,
        "status": "stored",
        "id": deploy_id,
        "source_path": source_path,
        "archive_path": str(archive_path),
        "created_at": created_at,
    }
    if manifest:
        entry["runtime"] = manifest.get("runtime")
        entry["framework"] = manifest.get("framework")
        if manifest.get("subdomain"):
            entry["subdomain"] = manifest["subdomain"]
        if manifest.get("database"):
            entry["database"] = True
    apps.append(entry)
    _save_registry(apps)

    return metadata


def list_apps() -> list[dict]:
    return _load_registry()


def update_deploy_status(deploy_id: str, name: str, **updates) -> None:
    """Update metadata.json and apps.json registry entry."""
    deploy_dir = DEPLOYMENTS_DIR / deploy_id
    metadata_path = deploy_dir / "metadata.json"

    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
    metadata.update(updates)
    metadata_path.write_text(json.dumps(metadata, indent=2))

    apps = _load_registry()
    for app in apps:
        if app.get("name") == name:
            app.update(updates)
            break
    _save_registry(apps)


def delete_app(name: str) -> None:
    """Remove app from registry and delete its deployment directory."""
    app = get_app_by_name(name)
    if not app:
        raise ValueError(f"App '{name}' not found")

    deploy_id = app.get("id")
    if deploy_id:
        deploy_dir = DEPLOYMENTS_DIR / deploy_id
        if deploy_dir.exists():
            shutil.rmtree(deploy_dir)

    apps = [a for a in _load_registry() if a.get("name") != name]
    _save_registry(apps)
