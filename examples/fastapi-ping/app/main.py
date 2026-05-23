import os

import psycopg
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.get("/db-ping")
def db_ping():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not configured",
        )
    try:
        with psycopg.connect(database_url, connect_timeout=5) as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {exc}",
        ) from exc
    return {"ok": True}
