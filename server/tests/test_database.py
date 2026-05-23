from forge_server.database import build_database_url, database_name_for_app


def test_database_name_for_app():
    assert database_name_for_app("ping-api") == "forge_ping_api"
    assert database_name_for_app("My-App") == "forge_my_app"


def test_build_database_url():
    url = build_database_url(
        {
            "user": "forge_ping_api",
            "password": "s3cret/p@ss",
            "database": "forge_ping_api",
            "host": "forge-postgres",
            "port": 5432,
        }
    )
    assert url.startswith("postgresql://")
    assert "forge-postgres" in url
    assert "forge_ping_api" in url
