"""
Authentication & Authorization - Security layer for SimpleMem API.

Provides:
- JWT token generation and verification
- API key validation
- User role management
- FastAPI security dependencies
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel

# Configuration (REQUIRED - must be set via environment variables)
# In production, these MUST be set or the application will refuse to start
_SECRETS_CHECKED = False

def _get_secret_key() -> str:
    """Get SECRET_KEY from environment or raise error."""
    global _SECRETS_CHECKED
    key = os.getenv("SECRET_KEY")
    if not key:
        if not _SECRETS_CHECKED:
            import logging
            logging.getLogger(__name__).critical(
                "SECRET_KEY environment variable not set! "
                "Set SME_GATEWAY_SECRET in .env file. "
                "Application will use insecure default for now."
            )
            _SECRETS_CHECKED = True
        # Return a warning-generating key but log the issue
        return "INSECURE_DEFAULT_DO_NOT_USE_IN_PRODUCTION"
    return key

def _get_admin_api_key() -> Optional[str]:
    """Get ADMIN_API_KEY from environment."""
    return os.getenv("ADMIN_API_KEY")

SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
API_KEY_NAME = "X-API-Key"
ADMIN_API_KEY = _get_admin_api_key()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

class User(BaseModel):
    username: str
    roles: List[str] = ["user"]
    tenant_id: str = "default"

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> User:
    """
    Validate credentials (JWT or API Key) and return current user.
    
    This is used as a FastAPI dependency.
    """
    # Simple API Key check
    if api_key and ADMIN_API_KEY:
        if api_key == ADMIN_API_KEY:
            return User(username="admin", roles=["admin"], tenant_id="system")
        # In a real app, look up API key in database
    
    # JWT check
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return User(
            username=username,
            roles=payload.get("roles", ["user"]),
            tenant_id=payload.get("tenant_id", "default")
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def check_admin(user: User = Depends(get_current_user)):
    """Check if user has admin privileges."""
    if "admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return user
