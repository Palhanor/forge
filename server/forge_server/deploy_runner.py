from pathlib import Path

from forge_server.config import FORGE_DOCKER_NETWORK
from forge_server.database import (
    ensure_app_database,
    validate_manifest_database,
)
from forge_server.docker_runner import (
    DEFAULT_CONTAINER_PORT,
    DEFAULT_NODEJS_PORT,
    DEFAULT_REACT_PORT,
    build_and_run,
    build_and_run_nodejs,
    build_and_run_react,
)
from forge_server.env_files import resolve_env_file
from forge_server.extract import safe_extract_archive
from forge_server.storage import update_deploy_status

SUPPORTED_FRAMEWORKS = {"fastapi", "react", "nodejs"}


def _default_fastapi_start(port: int) -> str:
    return f"uvicorn app.main:app --host 0.0.0.0 --port {port}"


def _resolve_database_runtime(app_name: str, deploy_id: str, manifest: dict) -> tuple[str | None, dict[str, str]]:
    if not manifest.get("database"):
        return None, {}

    validate_manifest_database(manifest)
    extra_env = ensure_app_database(app_name, deploy_id)
    return FORGE_DOCKER_NETWORK, extra_env


def run_deploy(deploy_id: str, metadata: dict) -> dict:
    manifest = metadata.get("manifest") or {}
    framework = manifest.get("framework")

    if framework not in SUPPORTED_FRAMEWORKS:
        raise ValueError(
            f"Framework '{framework}' is not supported yet. "
            f"Supported: {', '.join(sorted(SUPPORTED_FRAMEWORKS))}"
        )

    validate_manifest_database(manifest)

    deploy_dir = Path(metadata["archive"]).parent
    archive_path = Path(metadata["archive"])
    app_name = metadata["name"]

    update_deploy_status(deploy_id, app_name, status="building")

    try:
        source_dir = safe_extract_archive(archive_path, deploy_dir)
        env_file = resolve_env_file(source_dir, manifest)
        network, extra_env = _resolve_database_runtime(app_name, deploy_id, manifest)

        run_kwargs = {
            "name": app_name,
            "source_dir": source_dir,
            "env_file": env_file,
            "network": network,
            "extra_env": extra_env or None,
        }

        if framework == "fastapi":
            port = manifest.get("port") or DEFAULT_CONTAINER_PORT
            start_cmd = (
                (manifest.get("start") or "").strip() or _default_fastapi_start(port)
            )
            runtime_info = build_and_run(
                start_cmd=start_cmd,
                container_port=int(port),
                **run_kwargs,
            )
        elif framework == "react":
            port = manifest.get("port") or DEFAULT_REACT_PORT
            build_cmd = (manifest.get("build") or "").strip() or "npm run build"
            runtime_info = build_and_run_react(
                container_port=int(port),
                build_cmd=build_cmd,
                **run_kwargs,
            )
        else:
            port = manifest.get("port") or DEFAULT_NODEJS_PORT
            runtime_info = build_and_run_nodejs(
                manifest=manifest,
                container_port=int(port),
                **run_kwargs,
            )

        updates = {
            "status": "running",
            "host_port": runtime_info["host_port"],
            "container_port": runtime_info["container_port"],
            "url": runtime_info["url"],
            "container_id": runtime_info["container_id"],
            "image": runtime_info["image"],
            "error": None,
        }
        if manifest.get("database"):
            updates["database_enabled"] = True
        update_deploy_status(deploy_id, app_name, **updates)
        return {**metadata, **updates}

    except Exception as exc:
        update_deploy_status(
            deploy_id,
            app_name,
            status="failed",
            error=str(exc),
        )
        raise
