import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def _get_expected_api_key() -> str | None:
    key = os.environ.get("FORGE_API_KEY", "").strip()
    return key or None


def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> None:
    expected = _get_expected_api_key()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Builder API key not configured. Set FORGE_API_KEY environment variable.",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header. Use: Bearer <api_key>",
        )

    if not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
