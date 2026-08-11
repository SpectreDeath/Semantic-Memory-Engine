"""Authentication & Authorization Middleware for SME API Gateway.

Provides standardized JWT Bearer and API Key authentication schemes
with clean 401 JSON error payloads.
"""

from __future__ import annotations

import os

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

# Standard Header Security Definitions
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

JWT_SECRET = os.getenv("SME_JWT_SECRET", "sme-secret-key-change-in-production")
API_KEY = os.getenv("SME_API_KEY", "")


async def verify_jwt_or_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(api_key_scheme),
) -> dict:
    """Verify incoming request using Bearer JWT or X-API-Key.

    Returns:
        User/Agent identity dictionary.

    Raises:
        HTTPException(401) on missing or invalid credentials.
    """
    # 1. Check API Key header first
    if API_KEY and api_key == API_KEY:
        return {"sub": "api_key_agent", "role": "admin", "auth_method": "api_key"}

    # 2. Check JWT Bearer token
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "invalid_token", "message": "Signature verification failed"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 3. Fallback for unauthenticated requests when auth is enabled
    if os.getenv("SME_REQUIRE_AUTH", "false").lower() == "true":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "authentication_required", "message": "Bearer token or X-API-Key header required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"sub": "anonymous", "role": "guest", "auth_method": "none"}
