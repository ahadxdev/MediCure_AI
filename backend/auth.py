from typing import Annotated

from fastapi import Header, HTTPException, status

from backend.config import settings


def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Require the configured operator API key for state-changing actions."""
    # Local development and the existing isolated unit-test clients remain
    # usable without headers. Any non-development deployment is fail-closed.
    if settings.APP_ENV == "development" and x_api_key is None:
        return "development-local"
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-API-Key header is required",
        )
    return x_api_key
