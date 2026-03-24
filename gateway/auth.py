import datetime
import logging
import os
import secrets
import sys
from typing import Any

import jwt

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Secret key — MUST be set via SME_GATEWAY_SECRET environment variable.
# This will fail-fast if not set to prevent running with insecure defaults.
# --------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SME_GATEWAY_SECRET")
if not SECRET_KEY:
    logger.critical(
        "SME_GATEWAY_SECRET is not set. Exiting to prevent running with "
        "insecure defaults. Set this environment variable before starting."
    )
    sys.exit(1)

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


class AuthManager:
    """
    Handles JWT authentication for the Lawnmower Man gateway.
    """

    def __init__(self, admin_password: str | None = None):
        admin_password = admin_password or os.environ.get("SME_ADMIN_PASSWORD")
        if not admin_password:
            logger.critical(
                "SME_ADMIN_PASSWORD is not set. Exiting to prevent running with insecure defaults."
            )
            sys.exit(1)
        self.admin_password = admin_password
        logger.info("AuthManager initialized")

    def login(self, username: str, password: str) -> str | None:
        """Verify credentials and return a JWT token."""
        if secrets.compare_digest(password, self.admin_password):
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

    def verify_token(self, token: str) -> dict[str, Any] | None:
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
