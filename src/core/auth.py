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

# Configuration (In production, move to environment variables/config file)
SECRET_KEY = os.getenv("SECRET_KEY", "simplemem-super-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
API_KEY_NAME = "X-API-Key"

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
    if api_key:
        if api_key == os.getenv("ADMIN_API_KEY", "admin-key-123"):
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
