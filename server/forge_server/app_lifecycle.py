from forge_server.docker_runner import (
    DEFAULT_CONTAINER_PORT,
    remove_container_and_image,
    start_container,
    stop_container,
)
from forge_server.storage import (
    delete_app,
    get_app_by_name,
    get_deploy_metadata,
    update_deploy_status,
)


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

    runtime_info = start_container(
        name,
        image=image,
        host_port=int(host_port),
        container_port=int(container_port),
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

    remove_container_and_image(name)
    delete_app(name)
    return {"message": f"App '{name}' deleted permanently", "name": name}
