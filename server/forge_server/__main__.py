import uvicorn


def main():
    uvicorn.run(
        "forge_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["server/data/*", "*/data/deployments/*"],
    )


if __name__ == "__main__":
    main()
