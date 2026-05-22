import json
import re
import shutil
import socket
import subprocess
from pathlib import Path

DEFAULT_CONTAINER_PORT = 8000
DEFAULT_REACT_PORT = 3000
DEFAULT_NODEJS_PORT = 3000
HOST_PORT_START = 18000
HOST_PORT_END = 19000

FASTAPI_DOCKERFILE_TEMPLATE = Path(__file__).parent / "templates" / "fastapi" / "Dockerfile"
REACT_DOCKERFILE_TEMPLATE = Path(__file__).parent / "templates" / "react" / "Dockerfile"
NODEJS_DOCKERFILE_TEMPLATE = Path(__file__).parent / "templates" / "nodejs" / "Dockerfile"


def _safe_container_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", name.lower())
    return f"forge-{safe}"


def image_tag_for_name(name: str) -> str:
    return f"forge/{_safe_container_name(name)}:latest"


def find_free_host_port() -> int:
    for port in range(HOST_PORT_START, HOST_PORT_END):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port between {HOST_PORT_START} and {HOST_PORT_END}")


def _run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(stderr or f"Command failed: {' '.join(cmd)}")
    return result


def container_status(container_name: str) -> str | None:
    """Return docker state (running, exited, ...) or None if container does not exist."""
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", container_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def stop_existing_container(name: str) -> None:
    """Stop and remove container (used before redeploy)."""
    container = _safe_container_name(name)
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)


def stop_container(name: str) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    container = _safe_container_name(name)
    status = container_status(container)
    if status is None:
        raise RuntimeError(f"Container '{container}' not found")
    if status == "running":
        _run(["docker", "stop", container])


def _docker_run_args(
    container_name: str,
    host_port: int,
    container_port: int,
    image: str,
    env_file: Path | None = None,
) -> list[str]:
    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "-p",
        f"{host_port}:{container_port}",
    ]
    if env_file is not None:
        cmd.extend(["--env-file", str(env_file)])
    cmd.append(image)
    return cmd


def start_container(
    name: str,
    *,
    image: str,
    host_port: int,
    container_port: int,
    env_file: Path | None = None,
) -> dict:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    container = _safe_container_name(name)
    status = container_status(container)

    if status == "running":
        return _runtime_info(name, host_port, container_port)

    if status in ("exited", "created", "paused"):
        _run(["docker", "start", container])
        return _runtime_info(name, host_port, container_port)

    port_mapping = host_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", host_port)) == 0:
            port_mapping = find_free_host_port()

    _run(
        _docker_run_args(
            container,
            port_mapping,
            container_port,
            image,
            env_file,
        ),
    )
    return _runtime_info(name, port_mapping, container_port)


def remove_container_and_image(name: str) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    container = _safe_container_name(name)
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    subprocess.run(["docker", "rmi", "-f", image_tag_for_name(name)], capture_output=True)


def _runtime_info(name: str, host_port: int, container_port: int) -> dict:
    return {
        "container_id": _safe_container_name(name),
        "host_port": host_port,
        "container_port": container_port,
        "url": f"http://localhost:{host_port}",
        "image": image_tag_for_name(name),
    }


def ensure_requirements(source_dir: Path) -> None:
    req = source_dir / "requirements.txt"
    if req.exists():
        return
    req.write_text("fastapi>=0.115\nuvicorn[standard]>=0.32\n")


def write_fastapi_dockerfile(source_dir: Path, start_cmd: str) -> None:
    template = FASTAPI_DOCKERFILE_TEMPLATE.read_text()
    cmd_json = json.dumps(["sh", "-c", start_cmd])
    dockerfile = template.replace("__FORGE_START_CMD__", cmd_json)
    (source_dir / "Dockerfile").write_text(dockerfile)


def write_react_dockerfile(
    source_dir: Path,
    container_port: int,
    build_cmd: str = "npm run build",
) -> None:
    template = REACT_DOCKERFILE_TEMPLATE.read_text()
    dockerfile = (
        template.replace("__FORGE_PORT__", str(container_port))
        .replace("__FORGE_BUILD_CMD__", build_cmd)
    )
    (source_dir / "Dockerfile").write_text(dockerfile)
    dockerignore = source_dir / ".dockerignore"
    if not dockerignore.exists():
        dockerignore.write_text("node_modules\ndist\n.git\n")


def write_nodejs_dockerfile(
    source_dir: Path,
    container_port: int,
    start_cmd: str,
    build_cmd: str,
    runtime_copy: str,
) -> None:
    template = NODEJS_DOCKERFILE_TEMPLATE.read_text()
    cmd_json = json.dumps(["sh", "-c", start_cmd])
    dockerfile = (
        template.replace("__FORGE_PORT__", str(container_port))
        .replace("__FORGE_BUILD_CMD__", build_cmd)
        .replace("__FORGE_RUNTIME_COPY__", runtime_copy)
        .replace("__FORGE_START_CMD__", cmd_json)
    )
    (source_dir / "Dockerfile").write_text(dockerfile)
    # Always refresh — must not list src/ (TS needs it in the build stage).
    (source_dir / ".dockerignore").write_text(
        "node_modules\ndist\n.git\n.venv\n"
    )


def _docker_build_and_run(
    *,
    name: str,
    source_dir: Path,
    container_port: int,
    env_file: Path | None = None,
) -> dict:
    image_tag = image_tag_for_name(name)
    stop_existing_container(name)

    _run(["docker", "build", "-t", image_tag, "."], cwd=source_dir, timeout=600)

    host_port = find_free_host_port()
    container_name = _safe_container_name(name)

    _run(
        _docker_run_args(
            container_name,
            host_port,
            container_port,
            image_tag,
            env_file,
        ),
    )

    return _runtime_info(name, host_port, container_port)


def build_and_run(
    *,
    name: str,
    source_dir: Path,
    start_cmd: str,
    container_port: int = DEFAULT_CONTAINER_PORT,
    env_file: Path | None = None,
) -> dict:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    ensure_requirements(source_dir)
    write_fastapi_dockerfile(source_dir, start_cmd)
    return _docker_build_and_run(
        name=name,
        source_dir=source_dir,
        container_port=container_port,
        env_file=env_file,
    )


def build_and_run_react(
    *,
    name: str,
    source_dir: Path,
    container_port: int = DEFAULT_REACT_PORT,
    build_cmd: str = "npm run build",
    env_file: Path | None = None,
) -> dict:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    if not (source_dir / "package.json").exists():
        raise RuntimeError("package.json is required for React deploys")

    write_react_dockerfile(source_dir, container_port, build_cmd)
    return _docker_build_and_run(
        name=name,
        source_dir=source_dir,
        container_port=container_port,
        env_file=env_file,
    )


def build_and_run_nodejs(
    *,
    name: str,
    source_dir: Path,
    manifest: dict,
    container_port: int = DEFAULT_NODEJS_PORT,
    env_file: Path | None = None,
) -> dict:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is not installed or not in PATH")

    if not (source_dir / "package.json").exists():
        raise RuntimeError("package.json is required for Node.js deploys")

    from forge_server.nodejs_deploy import resolve_nodejs_commands

    build_cmd, start_cmd, runtime_copy = resolve_nodejs_commands(source_dir, manifest)
    write_nodejs_dockerfile(
        source_dir,
        container_port,
        start_cmd,
        build_cmd,
        runtime_copy,
    )
    return _docker_build_and_run(
        name=name,
        source_dir=source_dir,
        container_port=container_port,
        env_file=env_file,
    )
