from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ping_returns_pong():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


def test_db_ping_without_database_url():
    response = client.get("/db-ping")
    assert response.status_code == 503
