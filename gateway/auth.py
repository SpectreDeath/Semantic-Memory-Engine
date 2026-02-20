import jwt
import datetime
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Secret key — MUST be set via SME_GATEWAY_SECRET environment variable.
# If it is missing, we log a CRITICAL warning so the gap is visible in logs.
# There is intentionally no safe "default" — a hardcoded fallback lets anyone
# who reads the source code forge admin JWTs.
# --------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SME_GATEWAY_SECRET")
if not SECRET_KEY:
    logger.critical(
        "SME_GATEWAY_SECRET is not set. JWT tokens are being signed with a "
        "placeholder key — ALL TOKENS ARE FORGEABLE. Set this env var before "
        "running in any non-local environment."
    )
    SECRET_KEY = "INSECURE-PLACEHOLDER-SET-SME_GATEWAY_SECRET"

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


class AuthManager:
    """
    Handles JWT authentication for the Lawnmower Man gateway.
    """

    def __init__(self, admin_password: str = "admin"):
        self.admin_password = os.environ.get("SME_ADMIN_PASSWORD", admin_password)
        if self.admin_password == "admin":
            logger.warning(
                "SME_ADMIN_PASSWORD is using the insecure default 'admin'. "
                "Set the SME_ADMIN_PASSWORD environment variable."
            )
        logger.info("AuthManager initialized")

    def login(self, username: str, password: str) -> Optional[str]:
        """Verify credentials and return a JWT token."""
        if password == self.admin_password:
            now = datetime.datetime.now(datetime.timezone.utc)
            payload = {
                "sub": username,
                "role": "admin" if username == "admin" else "user",
                "exp": now + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
                "iat": now,
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
_auth_lock = None


def get_auth_manager() -> AuthManager:
    global _auth_manager, _auth_lock
    # Lazy-initialise the lock itself (avoids import-time threading overhead)
    if _auth_lock is None:
        import threading
        _auth_lock = threading.Lock()
    with _auth_lock:
        if _auth_manager is None:
            _auth_manager = AuthManager()
    return _auth_manager
