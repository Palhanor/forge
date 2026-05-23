from forge_server.config import DEPLOYMENTS_DIR, FORGE_DOCKER_NETWORK
from forge_server.database import build_extra_env_for_credentials, drop_app_database
from forge_server.database_config import DatabaseConfig, parse_database_config
from forge_server.docker_runner import (
    DEFAULT_CONTAINER_PORT,
    remove_container_and_image,
    start_container,
    stop_container,
)
from forge_server.env_files import resolve_env_file
from forge_server.storage import (
    delete_app,
    get_app_by_name,
    get_deploy_metadata,
    update_deploy_status,
)


def _database_config_from_metadata(metadata: dict, manifest: dict) -> DatabaseConfig | None:
    config = parse_database_config(manifest)
    if config is None:
        return None

    stored = (metadata.get("database") or {}).get("config") or {}
    if stored.get("variable"):
        return DatabaseConfig(
            enabled=True,
            variable=stored["variable"],
            migration=stored.get("migration"),
        )
    return config


def _database_runtime_from_metadata(
    metadata: dict,
    manifest: dict,
) -> tuple[str | None, dict[str, str] | None]:
    config = _database_config_from_metadata(metadata, manifest)
    if config is None:
        return None, None

    database_meta = metadata.get("database") or {}
    credentials = database_meta.get("credentials")
    if not credentials:
        return FORGE_DOCKER_NETWORK, None

    return FORGE_DOCKER_NETWORK, build_extra_env_for_credentials(credentials, config)


def stop_app(name: str) -> dict:
    app = get_app_by_name(name)
    if not app:
        raise ValueError(f"App '{name}' not found")

    deploy_id = app.get("id")
    if not deploy_id:
        raise ValueError(f"App '{name}' has no deployment id")

    status = app.get("status")
    if status == "stopped":
        return {**app, "message": f"App '{name}' is already stopped"}

    if status not in ("running", "failed"):
        raise ValueError(
            f"App '{name}' cannot be stopped (status: {status}). Deploy it first."
        )

    stop_container(name)

    updates = {
        "status": "stopped",
        "url": None,
        "error": None,
    }
    update_deploy_status(deploy_id, name, **updates)
    return {**app, **updates, "message": f"App '{name}' stopped"}


def start_app(name: str) -> dict:
    app = get_app_by_name(name)
    if not app:
        raise ValueError(f"App '{name}' not found")

    deploy_id = app.get("id")
    if not deploy_id:
        raise ValueError(f"App '{name}' has no deployment id")

    metadata = get_deploy_metadata(deploy_id)
    image = app.get("image") or metadata.get("image")
    if not image:
        raise ValueError(
            f"App '{name}' has no Docker image. Run 'forge deploy' again."
        )

    host_port = app.get("host_port") or metadata.get("host_port")
    container_port = (
        app.get("container_port")
        or metadata.get("container_port")
        or DEFAULT_CONTAINER_PORT
    )
    if not host_port:
        raise ValueError(f"App '{name}' has no host port recorded")

    manifest = metadata.get("manifest") or {}
    source_dir = DEPLOYMENTS_DIR / deploy_id / "source"
    env_file = None
    if source_dir.is_dir():
        env_file = resolve_env_file(source_dir, manifest)

    network, extra_env = _database_runtime_from_metadata(metadata, manifest)
    if parse_database_config(manifest) and extra_env is None:
        raise ValueError(
            f"App '{name}' has database enabled but no credentials. Run 'forge deploy' again."
        )

    runtime_info = start_container(
        name,
        image=image,
        host_port=int(host_port),
        container_port=int(container_port),
        env_file=env_file,
        network=network,
        extra_env=extra_env,
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
    update_deploy_status(deploy_id, name, **updates)
    return {
        **app,
        **updates,
        "message": f"App '{name}' is running at {runtime_info['url']}",
    }


def delete_app_full(name: str) -> dict:
    app = get_app_by_name(name)
    if not app:
        raise ValueError(f"App '{name}' not found")

    deploy_id = app.get("id")
    metadata = get_deploy_metadata(deploy_id) if deploy_id else {}

    remove_container_and_image(name)
    drop_app_database(metadata)
    delete_app(name)
    return {"message": f"App '{name}' deleted permanently", "name": name}
