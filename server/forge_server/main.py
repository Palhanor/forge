import json

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from forge_server.auth import verify_api_key
from forge_server.app_lifecycle import delete_app_full, start_app, stop_app
from forge_server.deploy_runner import run_deploy
from forge_server.storage import list_apps, save_deploy

app = FastAPI(
    title="Forge Builder",
    version="0.1.0",
    dependencies=[Depends(verify_api_key)],
)


@app.get("/ping")
def ping():
    return {"message": "Pong!"}


@app.post("/deploy")
async def deploy(
    archive: UploadFile = File(...),
    name: str = Form(...),
    source_path: str = Form(...),
    manifest: str | None = Form(None),
):
    content = await archive.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty archive")

    manifest_data = None
    if manifest:
        try:
            manifest_data = json.loads(manifest)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid manifest JSON: {exc}",
            ) from exc
        if not isinstance(manifest_data, dict):
            raise HTTPException(status_code=400, detail="Manifest must be a JSON object")
        if manifest_data.get("name") and manifest_data["name"] != name.strip():
            raise HTTPException(
                status_code=400,
                detail="Manifest name does not match deploy name",
            )

    if not manifest_data:
        raise HTTPException(status_code=400, detail="Manifest is required for deploy")

    metadata = save_deploy(
        name=name.strip(),
        source_path=source_path,
        archive_bytes=content,
        filename=archive.filename or f"{name}.tar.gz",
        manifest=manifest_data,
    )

    try:
        result = run_deploy(metadata["id"], metadata)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": f"Deploy '{result['name']}' is running at {result.get('url')}",
        "id": result["id"],
        "status": result.get("status", "running"),
        "url": result.get("url"),
        "host_port": result.get("host_port"),
    }


@app.get("/apps")
def apps():
    return {"apps": list_apps()}


@app.post("/apps/{name}/stop")
def stop_app_route(name: str):
    try:
        result = stop_app(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "message": result.get("message"),
        "name": name,
        "status": result.get("status", "stopped"),
    }


@app.post("/apps/{name}/start")
def start_app_route(name: str):
    try:
        result = start_app(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "message": result.get("message"),
        "name": name,
        "status": result.get("status", "running"),
        "url": result.get("url"),
        "host_port": result.get("host_port"),
    }


@app.delete("/apps/{name}")
def delete_app_route(name: str):
    try:
        result = delete_app_full(name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result
