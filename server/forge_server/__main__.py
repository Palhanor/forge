import os

import uvicorn

from forge_server.config import DATA_DIR


def main():
    reload = os.environ.get("FORGE_RELOAD", "true").lower() in ("1", "true", "yes")
    kwargs = {
        "host": "0.0.0.0",
        "port": 8000,
        "reload": reload,
    }
    if reload:
        data_glob = str(DATA_DIR / "**" / "*")
        kwargs["reload_excludes"] = [data_glob, "*/data/deployments/*"]
    uvicorn.run("forge_server.main:app", **kwargs)


if __name__ == "__main__":
    main()
