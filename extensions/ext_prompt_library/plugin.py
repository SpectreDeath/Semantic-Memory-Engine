from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.PromptLibrary")

PROMPTS_FILE = Path(__file__).parent / "prompts.json"


class Prompt:
    def __init__(
        self,
        prompt_id: str,
        name: str,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
        variables: list[str] | None = None,
    ):
        self.prompt_id = prompt_id
        self.name = name
        self.content = content
        self.category = category
        self.tags = tags or []
        self.variables = variables or []
        self.version = 1
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.version_history = [
            {"version": 1, "content": content, "timestamp": datetime.now().isoformat()}
        ]

    def update(self, new_content: str) -> int:
        self.version += 1
        self.content = new_content
        self.updated_at = datetime.now().isoformat()
        self.version_history.append(
            {
                "version": self.version,
                "content": new_content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._extract_variables()
        return self.version

    def _extract_variables(self):
        self.variables = re.findall(r"\{\{(\w+)\}\}", self.content)

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "name": self.name,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "variables": self.variables,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version_history": self.version_history[-5:],  # Keep last 5 versions
        }

    @staticmethod
    def from_dict(data: dict) -> "Prompt":
        prompt = Prompt(
            data["prompt_id"],
            data["name"],
            data["content"],
            data.get("category", "general"),
            data.get("tags", []),
        )
        prompt.version = data.get("version", 1)
        prompt.created_at = data.get("created_at", datetime.now().isoformat())
        prompt.updated_at = data.get("updated_at", datetime.now().isoformat())
        prompt.version_history = data.get(
            "version_history",
            [{"version": 1, "content": data["content"], "timestamp": datetime.now().isoformat()}],
        )
        prompt._extract_variables()
        return prompt


class PromptLibrary:
    def __init__(self):
        self.prompts: dict[str, Prompt] = {}
        self._load_prompts()

    def _load_prompts(self):
        if PROMPTS_FILE.exists():
            try:
                with open(PROMPTS_FILE) as f:
                    data = json.load(f)
                    for prompt_data in data.values():
                        self.prompts[prompt_data["prompt_id"]] = Prompt.from_dict(prompt_data)
                logger.info(f"Loaded {len(self.prompts)} prompts")
            except Exception as e:
                logger.exception(f"Failed to load prompts: {e}")

    def _save_prompts(self):
        data = {prompt_id: prompt.to_dict() for prompt_id, prompt in self.prompts.items()}
        with open(PROMPTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def add(
        self, name: str, content: str, category: str = "general", tags: list[str] | None = None
    ) -> str:
        prompt_id = f"prompt_{len(self.prompts) + 1}"
        prompt = Prompt(prompt_id, name, content, category, tags)
        self.prompts[prompt_id] = prompt
        self._save_prompts()
        logger.info(f"Added prompt: {name}")
        return prompt_id

    def get(self, prompt_id: str) -> Prompt | None:
        return self.prompts.get(prompt_id)

    def update(self, prompt_id: str, new_content: str) -> int | None:
        if prompt_id in self.prompts:
            version = self.prompts[prompt_id].update(new_content)
            self._save_prompts()
            return version
        return None

    def delete(self, prompt_id: str) -> bool:
        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            self._save_prompts()
            return True
        return False

    def list(self, category: str | None = None, tags: list[str] | None = None) -> list[dict]:
        results = []
        for prompt in self.prompts.values():
            if category and prompt.category != category:
                continue
            if tags and not any(tag in prompt.tags for tag in tags):
                continue
            results.append(prompt.to_dict())
        return results

    def search(self, query: str) -> list[dict]:
        results = []
        query_lower = query.lower()
        for prompt in self.prompts.values():
            if query_lower in prompt.name.lower() or query_lower in prompt.content.lower():
                results.append(prompt.to_dict())
        return results

    def render(self, prompt_id: str, variables: dict[str, str]) -> str | None:
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            return None
        content = prompt.content
        for var, value in variables.items():
            content = content.replace(f"{{{{{var}}}}}", value)
        return content

    def get_versions(self, prompt_id: str) -> list[dict] | None:
        prompt = self.prompts.get(prompt_id)
        if prompt:
            return prompt.version_history
        return None

    def restore_version(self, prompt_id: str, version: int) -> bool:
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            return False
        for v in prompt.version_history:
            if v["version"] == version:
                prompt.update(v["content"])
                self._save_prompts()
                return True
        return False


class PromptLibraryExtension(BasePlugin):
    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.library = PromptLibrary()

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] Prompt Library extension activated")

    def get_tools(self):
        return [
            self.add_prompt,
            self.get_prompt,
            self.update_prompt,
            self.delete_prompt,
            self.list_prompts,
            self.search_prompts,
            self.render_prompt,
            self.get_prompt_versions,
            self.restore_prompt_version,
        ]

    async def add_prompt(
        self, name: str, content: str, category: str = "general", tags: str = ""
    ) -> str:
        """Add a new prompt."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        prompt_id = self.library.add(name, content, category, tag_list)
        return json.dumps({"prompt_id": prompt_id, "status": "added"})

    async def get_prompt(self, prompt_id: str) -> str:
        """Get a prompt by ID."""
        prompt = self.library.get(prompt_id)
        if prompt:
            return json.dumps(prompt.to_dict())
        return json.dumps({"error": "Prompt not found"})

    async def update_prompt(self, prompt_id: str, content: str) -> str:
        """Update prompt content."""
        version = self.library.update(prompt_id, content)
        if version:
            return json.dumps({"prompt_id": prompt_id, "version": version, "status": "updated"})
        return json.dumps({"error": "Prompt not found"})

    async def delete_prompt(self, prompt_id: str) -> str:
        """Delete a prompt."""
        success = self.library.delete(prompt_id)
        return json.dumps({"prompt_id": prompt_id, "status": "deleted" if success else "not_found"})

    async def list_prompts(self, category: str = "", tags: str = "") -> str:
        """List all prompts with optional filtering."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
        return json.dumps({"prompts": self.library.list(category or None, tag_list)})

    async def search_prompts(self, query: str) -> str:
        """Search prompts by name or content."""
        return json.dumps({"results": self.library.search(query)})

    async def render_prompt(self, prompt_id: str, variables: str) -> str:
        """Render a prompt with variable substitution."""
        try:
            vars_dict = json.loads(variables) if variables else {}
        except json.JSONDecodeError:
            vars_dict = {}
        rendered = self.library.render(prompt_id, vars_dict)
        if rendered:
            return json.dumps({"prompt_id": prompt_id, "rendered": rendered})
        return json.dumps({"error": "Prompt not found"})

    async def get_prompt_versions(self, prompt_id: str) -> str:
        """Get version history for a prompt."""
        versions = self.library.get_versions(prompt_id)
        if versions:
            return json.dumps({"prompt_id": prompt_id, "versions": versions})
        return json.dumps({"error": "Prompt not found"})

    async def restore_prompt_version(self, prompt_id: str, version: int) -> str:
        """Restore a prompt to a specific version."""
        success = self.library.restore_version(prompt_id, version)
        return json.dumps(
            {"prompt_id": prompt_id, "status": "restored" if success else "not_found"}
        )


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return PromptLibraryExtension(manifest, nexus_api)
