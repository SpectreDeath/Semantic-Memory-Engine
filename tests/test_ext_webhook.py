"""
Tests for ext_webhook extension
===============================
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWebhookManager:
    """Tests for WebhookManager class."""

    def test_manager_creation(self):
        """WebhookManager should initialize with empty webhooks."""
        # Patch the file operations
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()
            assert manager.webhooks == {}
            assert manager.event_history == []

    def test_register_webhook(self):
        """Should register a webhook with all required fields."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            webhook_id = manager.register(
                name="Test Webhook",
                url="https://example.com/webhook",
                events=["test.event"],
                secret="secret123",
                enabled=True,
            )

            assert webhook_id is not None
            assert len(webhook_id) == 12
            assert "Test Webhook" in manager.webhooks[webhook_id]["name"]

    def test_unregister_webhook(self):
        """Should remove webhook by ID."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            webhook_id = manager.register(
                name="Test Webhook", url="https://example.com/webhook", events=["test.event"]
            )

            result = manager.unregister(webhook_id)
            assert result is True
            assert webhook_id not in manager.webhooks

    def test_list_webhooks(self):
        """Should return list of registered webhooks."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            manager.register("Webhook 1", "https://example.com/1", ["event1"])
            manager.register("Webhook 2", "https://example.com/2", ["event2"])

            webhooks = manager.list_webhooks()
            assert len(webhooks) == 2
            assert any(w["name"] == "Webhook 1" for w in webhooks)

    def test_get_history(self):
        """Should return event trigger history."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            # Simulate some events
            manager.event_history = [
                {
                    "webhook_id": "test1",
                    "event": "event1",
                    "timestamp": "2024-01-01",
                    "success": True,
                },
                {
                    "webhook_id": "test2",
                    "event": "event2",
                    "timestamp": "2024-01-02",
                    "success": False,
                },
            ]

            history = manager.get_history(limit=10)
            assert len(history) == 2


class TestWebhookExtension:
    """Tests for WebhookExtension class."""

    def test_extension_creation(self):
        """Should create extension with manager."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        assert extension.manager is not None
        assert extension.plugin_id == "ext_webhook"

    def test_get_tools(self):
        """Should return list of available tools."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        tools = extension.get_tools()
        tool_names = [t.__name__ for t in tools]

        assert "register_webhook" in tool_names
        assert "unregister_webhook" in tool_names
        assert "list_webhooks" in tool_names

    @pytest.mark.asyncio
    async def test_on_startup(self):
        """Should log startup message."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        # Should not raise
        await extension.on_startup()

    @pytest.mark.asyncio
    async def test_register_webhook_tool(self):
        """Should register webhook via tool."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        result = await extension.register_webhook(
            name="Test",
            url="https://example.com",
            events="test.event",
            secret="secret",
            enabled=True,
        )

        result_data = json.loads(result)
        assert result_data["status"] == "registered"
        assert "webhook_id" in result_data

    @pytest.mark.asyncio
    async def test_list_webhooks_tool(self):
        """Should list webhooks via tool."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        # Add a webhook first
        await extension.register_webhook(
            name="Test", url="https://example.com", events="test.event"
        )

        result = await extension.list_webhooks()
        result_data = json.loads(result)

        assert "webhooks" in result_data
        assert len(result_data["webhooks"]) >= 1


class TestWebhookSecurity:
    """Security tests for webhooks."""

    def test_webhook_id_generation(self):
        """Should generate consistent webhook IDs."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            # Same name and URL should generate same ID
            id1 = manager.register("Test", "https://example.com", ["event"])
            manager.webhooks = {}  # Reset
            id2 = manager.register("Test", "https://example.com", ["event"])

            assert id1 == id2

    def test_secret_not_exposed(self):
        """Should not expose secret in list output."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            from extensions.ext_webhook.plugin import WebhookManager

            manager = WebhookManager()

            manager.register(
                name="Secret Webhook",
                url="https://example.com",
                events=["event"],
                secret="super-secret",
            )

            webhooks = manager.list_webhooks()
            # Secret should be in the webhook but not returned in list by default
            # The encrypted_key field contains the actual value
            assert webhooks[0].get("secret", "") == ""  # Empty in list


class TestWebhookEvents:
    """Tests for webhook event triggering."""

    @pytest.mark.asyncio
    async def test_trigger_event(self):
        """Should trigger event for matching webhooks."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        # Add webhook
        await extension.register_webhook(
            name="Test", url="https://example.com/webhook", events="test.event"
        )

        # Mock the HTTP call
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await extension.trigger_event("test.event", '{"data": "test"}')

            # Should not raise
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_webhook_history(self):
        """Should retrieve trigger history."""
        from extensions.ext_webhook.plugin import WebhookExtension

        manifest = {"plugin_id": "ext_webhook", "name": "Webhook"}
        extension = WebhookExtension(manifest, None)

        result = await extension.get_webhook_history(limit=10)
        result_data = json.loads(result)

        assert "history" in result_data
