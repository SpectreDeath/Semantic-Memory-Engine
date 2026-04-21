"""
Tests for ext_api_key_manager extension
========================================
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestAPIKeyManager:
    """Tests for APIKeyManager class."""

    def test_manager_creation(self):
        """APIKeyManager should initialize."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()
            assert manager.keys == {}

    def test_add_key(self):
        """Should add new API key."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            key_id = manager.add_key(
                name="OpenAI Key",
                api_key="sk-test-key",
                provider="openai",
                expiry_days=90,
                notes="Test key",
            )

            assert key_id is not None
            assert "key_" in key_id
            assert manager.keys[key_id]["name"] == "OpenAI Key"

    def test_get_key(self):
        """Should retrieve and decrypt API key."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            key_id = manager.add_key(name="Test Key", api_key="secret-key-123", provider="openai")

            retrieved = manager.get_key(key_id)
            assert retrieved == "secret-key-123"

    def test_list_keys(self):
        """Should list all keys without exposing secrets."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            manager.add_key("Key 1", "value1", "openai")
            manager.add_key("Key 2", "value2", "anthropic")

            keys = manager.list_keys()
            assert len(keys) == 2
            # encrypted_key should be hidden
            assert all(k.get("encrypted_key") is None for k in keys)

    def test_delete_key(self):
        """Should delete key by ID."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            key_id = manager.add_key("Test Key", "value", "openai")
            result = manager.delete_key(key_id)

            assert result is True
            assert key_id not in manager.keys

    def test_get_expiring_keys(self):
        """Should identify keys expiring soon."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            manager.add_key("Expiring Key", "value", "openai", expiry_days=3)

            expiring = manager.get_expiring_keys(days=7)
            assert len(expiring) >= 1


class TestAPIKeyManagerExtension:
    """Tests for APIKeyManagerExtension class."""

    def test_extension_creation(self):
        """Should create extension with manager."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        assert extension.manager is not None

    def test_get_tools(self):
        """Should return list of tools."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        tools = extension.get_tools()
        tool_names = [t.__name__ for t in tools]

        assert "add_api_key" in tool_names
        assert "list_api_keys" in tool_names
        assert "delete_api_key" in tool_names
        assert "get_expiring_keys" in tool_names

    @pytest.mark.asyncio
    async def test_add_api_key_tool(self):
        """Should add key via tool."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        result = await extension.add_api_key(
            name="Test Key", api_key="sk-test-123", provider="openai", expiry_days=90, notes="Test"
        )

        result_data = json.loads(result)
        assert result_data["status"] == "added"
        assert "key_id" in result_data

    @pytest.mark.asyncio
    async def test_list_api_keys_tool(self):
        """Should list keys via tool."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        # Add a key first
        await extension.add_api_key("Test", "value", "openai")

        result = await extension.list_api_keys()
        result_data = json.loads(result)

        assert "keys" in result_data

    @pytest.mark.asyncio
    async def test_delete_api_key_tool(self):
        """Should delete key via tool."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        # Add a key
        result = await extension.add_api_key("Test", "value", "openai")
        key_id = json.loads(result)["key_id"]

        # Delete it
        result = await extension.delete_api_key(key_id)
        result_data = json.loads(result)

        assert result_data["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_get_expiring_keys_tool(self):
        """Should get expiring keys via tool."""
        from extensions.ext_api_key_manager.plugin import APIKeyManagerExtension

        manifest = {"plugin_id": "ext_api_key_manager", "name": "API Key Manager"}
        extension = APIKeyManagerExtension(manifest, None)

        result = await extension.get_expiring_keys(days=30)
        result_data = json.loads(result)

        assert "expiring" in result_data


class TestAPIKeyEncryption:
    """Tests for encryption functionality."""

    def test_encryption_key_generation(self):
        """Should generate encryption key on first run."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            # Should have generated a Fernet key
            assert manager._fernet is not None

    def test_key_encryption(self):
        """Should encrypt API key."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            key_id = manager.add_key("Test", "my-secret-key", "openai")

            # The stored key should be different (encrypted)
            stored_key = manager.keys[key_id]["encrypted_key"]
            assert stored_key != "my-secret-key"

    def test_key_persistency(self):
        """Should save and load keys."""
        with (
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.exists", return_value=True) as mock_exists,
            patch("builtins.open", create=True) as mock_open,
            patch("json.load", return_value={}),
            patch("json.dump"),
        ):
            from extensions.ext_api_key_manager.plugin import APIKeyManager

            manager = APIKeyManager()

            # Should have tried to load keys
            assert mock_exists.called or mock_mkdir.called
