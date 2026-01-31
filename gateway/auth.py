import jwt
import datetime
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Security configuration - in production, these should be in env variables
SECRET_KEY = os.environ.get("SME_GATEWAY_SECRET", "super-secret-lawnmower-key")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

class AuthManager:
    """
    Handles JWT authentication for the Lawnmower Man gateway.
    """
    
    def __init__(self, admin_password: str = "admin"):
        self.admin_password = os.environ.get("SME_ADMIN_PASSWORD", admin_password)
        logger.info("AuthManager initialized")

    def login(self, username: str, password: str) -> Optional[str]:
        """Verify credentials and return a JWT token."""
        if password == self.admin_password:
            payload = {
                "sub": username,
                "role": "admin" if username == "admin" else "user",
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
                "iat": datetime.datetime.utcnow()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            logger.info(f"Successful login for user: {username}")
            return token
        
        logger.warning(f"Failed login attempt for user: {username}")
        return None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and return the payload."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

_auth_manager = None

def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
