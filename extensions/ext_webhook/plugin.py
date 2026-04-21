import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Webhook")

WEBHOOKS_DIR = Path(__file__).parent / "webhooks"
WEBHOOKS_FILE = WEBHOOKS_DIR / "registered.json"


class WebhookManager:
    def __init__(self):
        self.webhooks: dict[str, dict[str, Any]] = {}
        self.event_history: list[dict[str, Any]] = []
        self._load_webhooks()

    def _load_webhooks(self):
        if WEBHOOKS_FILE.exists():
            try:
                with open(WEBHOOKS_FILE) as f:
                    self.webhooks = json.load(f)
                logger.info(f"Loaded {len(self.webhooks)} webhooks")
            except Exception as e:
                logger.exception(f"Failed to load webhooks: {e}")

    def _save_webhooks(self):
        WEBHOOKS_DIR.mkdir(parents=True, exist_ok=True)
        with open(WEBHOOKS_FILE, "w") as f:
            json.dump(self.webhooks, f, indent=2)

    def register(
        self,
        name: str,
        url: str,
        events: list[str],
        secret: str | None = None,
        enabled: bool = True,
    ) -> str:
        webhook_id = hashlib.sha256(f"{name}{url}".encode()).hexdigest()[:12]
        self.webhooks[webhook_id] = {
            "id": webhook_id,
            "name": name,
            "url": url,
            "events": events,
            "secret": secret or "",
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "failure_count": 0,
        }
        self._save_webhooks()
        logger.info(f"Registered webhook: {name} ({webhook_id})")
        return webhook_id

    def unregister(self, webhook_id: str) -> bool:
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._save_webhooks()
            logger.info(f"Unregistered webhook: {webhook_id}")
            return True
        return False

    def list_webhooks(self) -> list[dict[str, Any]]:
        return list(self.webhooks.values())

    async def trigger(self, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        for webhook_id, webhook in self.webhooks.items():
            if not webhook.get("enabled", True):
                continue
            if event not in webhook.get("events", []):
                continue

            result = await self._send_webhook(webhook, event, payload)
            results.append(result)
            self.event_history.append(
                {
                    "webhook_id": webhook_id,
                    "event": event,
                    "timestamp": datetime.now().isoformat(),
                    "success": result.get("success", False),
                }
            )
            if len(self.event_history) > 1000:
                self.event_history = self.event_history[-1000:]
        return results

    async def _send_webhook(
        self, webhook: dict[str, Any], event: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event,
            "X-Webhook-ID": webhook["id"],
        }
        if webhook.get("secret"):
            import hmac

            signature = hmac.new(
                webhook["secret"].encode(), json.dumps(payload).encode(), "sha256"
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature

        payload_with_meta = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": payload,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook["url"], json=payload_with_meta, headers=headers
                )
                self.webhooks[webhook["id"]]["last_triggered"] = datetime.now().isoformat()
                self.webhooks[webhook["id"]]["failure_count"] = 0
                self._save_webhooks()
                return {
                    "webhook_id": webhook["id"],
                    "success": True,
                    "status": response.status_code,
                }
        except Exception as e:
            self.webhooks[webhook["id"]]["failure_count"] = (
                self.webhooks[webhook["id"]].get("failure_count", 0) + 1
            )
            self._save_webhooks()
            logger.exception(f"Webhook {webhook['id']} failed: {e}")
            return {"webhook_id": webhook["id"], "success": False, "error": str(e)}

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.event_history[-limit:]


class WebhookExtension(BasePlugin):
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.manager = WebhookManager()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Webhook Manager extension activated")

    async def on_shutdown(self):
        logger.info(f"[{self.plugin_id}] Webhook Manager shutting down")

    async def on_event(self, event: str, data: dict[str, Any]):
        await self.manager.trigger(event, data)

    def get_tools(self):
        return [
            self.register_webhook,
            self.unregister_webhook,
            self.list_webhooks,
            self.trigger_event,
            self.get_webhook_history,
        ]

    async def register_webhook(
        self, name: str, url: str, events: str, secret: str = "", enabled: bool = True
    ) -> str:
        """Register a new webhook."""
        events_list = [e.strip() for e in events.split(",")]
        webhook_id = self.manager.register(name, url, events_list, secret, enabled)
        return json.dumps({"webhook_id": webhook_id, "status": "registered"})

    async def unregister_webhook(self, webhook_id: str) -> str:
        """Unregister an existing webhook."""
        success = self.manager.unregister(webhook_id)
        return json.dumps(
            {"webhook_id": webhook_id, "status": "unregistered" if success else "not_found"}
        )

    async def list_webhooks(self) -> str:
        """List all registered webhooks."""
        return json.dumps({"webhooks": self.manager.list_webhooks()})

    async def trigger_event(self, event: str, payload: str) -> str:
        """Manually trigger an event to all matching webhooks."""
        try:
            payload_data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            payload_data = {"raw": payload}
        results = await self.manager.trigger(event, payload_data)
        return json.dumps({"event": event, "results": results})

    async def get_webhook_history(self, limit: int = 100) -> str:
        """Get webhook trigger history."""
        return json.dumps({"history": self.manager.get_history(limit)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return WebhookExtension(manifest, nexus_api)
