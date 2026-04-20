"""
Tests for gateway/auth.py - JWT authentication management.
"""

import os

# Set required env vars before any gateway imports
os.environ.setdefault("SME_GATEWAY_SECRET", "test-secret-key-12345678901234567890")
os.environ.setdefault("SME_ADMIN_PASSWORD", "admin-pass-xyz")

import datetime
from unittest.mock import patch

import jwt
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from gateway.auth import AuthManager, get_auth_manager, SECRET_KEY, ALGORITHM, TOKEN_EXPIRY_HOURS


@pytest.fixture(autouse=True)
def reset_auth_manager():
    """Reset global auth manager state between tests."""
    import gateway.auth as auth_mod

    original_manager = auth_mod._auth_manager
    original_lock = auth_mod._auth_lock
    auth_mod._auth_manager = None
    auth_mod._auth_lock = None
    yield
    # Restore previous state (optional, not needed)
    auth_mod._auth_manager = original_manager
    auth_mod._auth_lock = original_lock


@pytest.fixture
def secrets():
    """Set required environment variables for auth tests."""
    env = {
        "SME_GATEWAY_SECRET": "test-secret-key-12345678901234567890",
        "SME_ADMIN_PASSWORD": "admin-pass-xyz",
    }
    with patch.dict(os.environ, env, clear=False):
        yield


def test_auth_manager_initialization(secrets):
    """AuthManager initializes with env password."""
    am = AuthManager()
    assert am.admin_password == "admin-pass-xyz"


def test_login_success(secrets):
    """Successful login returns a valid JWT token."""
    am = AuthManager()
    token = am.login("admin", "admin-pass-xyz")
    assert token is not None
    assert isinstance(token, str)
    # Decode to verify payload
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_login_wrong_password(secrets):
    """Login with wrong password returns None."""
    am = AuthManager()
    token = am.login("admin", "wrong-pass")
    assert token is None


def test_login_user_role(secrets):
    """Non-admin user gets 'user' role."""
    am = AuthManager()
    token = am.login("user1", "admin-pass-xyz")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["role"] == "user"


def test_verify_token_success(secrets):
    """verify_token decodes a valid token."""
    am = AuthManager()
    token = am.login("admin", "admin-pass-xyz")
    payload = am.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"


def test_verify_token_expired(secrets):
    """verify_token returns None for expired token."""
    # Create an expired token manually
    now = datetime.datetime.now(datetime.UTC)
    exp = now - datetime.timedelta(hours=1)
    payload = {
        "sub": "admin",
        "role": "admin",
        "exp": exp,
        "iat": now,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    am = AuthManager()
    result = am.verify_token(token)
    assert result is None


def test_verify_token_invalid(secrets):
    """verify_token returns None for tampered token."""
    am = AuthManager()
    result = am.verify_token("invalid.token.here")
    assert result is None


def test_get_auth_manager_singleton(secrets):
    """get_auth_manager returns a singleton instance."""
    a = get_auth_manager()
    b = get_auth_manager()
    assert a is b
