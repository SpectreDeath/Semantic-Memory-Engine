"""
Skills Loader for SME

Loads skill specifications from the registry and provides them as context
for AI agent consumption via the MCP Gateway.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillInfo:
    """Loaded skill information."""

    name: str
    domain: str
    version: str
    complexity: str
    type: str
    category: str
    source_file: str
    source_exists: bool
    spec_path: str
    purpose: str
    description: str
    workflow: list = field(default_factory=list)
    source: str | None = None
    implementation_status: str = "unknown"
    content: str = ""


class SkillsLoader:
    """Loads and queries SME skill specifications."""

    def __init__(self, skills_dir: str = "skills", registry_path: str | None = None):
        self.skills_dir = Path(skills_dir)
        self.registry_path = Path(registry_path or self.skills_dir / "registry.json")
        self._skills: dict[str, SkillInfo] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Lazy-load the registry on first access."""
        if self._loaded:
            return

        if self.registry_path.exists():
            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                skill = SkillInfo(**entry)
                self._skills[skill.name] = skill

        self._loaded = True

    def load_registry(self) -> list[SkillInfo]:
        """Load the full skill registry."""
        self._ensure_loaded()
        return list(self._skills.values())

    def get_skill(self, name: str) -> SkillInfo | None:
        """Get a skill by name."""
        self._ensure_loaded()
        return self._skills.get(name)

    def get_skill_context(self, name: str) -> str:
        """Load the full SKILL.md content for a skill."""
        skill = self.get_skill(name)
        if not skill:
            return ""

        spec_path = Path(skill.spec_path)
        if not spec_path.is_absolute():
            spec_path = Path.cwd() / spec_path

        if spec_path.exists():
            return spec_path.read_text(encoding="utf-8")
        return ""

    def search_skills(self, query: str) -> list[SkillInfo]:
        """Search skills by name, purpose, or description."""
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        for skill in self._skills.values():
            searchable = (
                f"{skill.name} {skill.purpose} {skill.description} {skill.category}".lower()
            )
            if query_lower in searchable:
                results.append(skill)
        return results

    def get_skills_by_category(self, category: str) -> list[SkillInfo]:
        """Get all skills in a category."""
        self._ensure_loaded()
        return [s for s in self._skills.values() if s.category == category]

    def get_skills_by_domain(self, domain: str) -> list[SkillInfo]:
        """Get all skills in a domain."""
        self._ensure_loaded()
        return [s for s in self._skills.values() if s.domain == domain]

    def get_skills_by_complexity(self, complexity: str) -> list[SkillInfo]:
        """Get all skills with a given complexity level."""
        self._ensure_loaded()
        return [s for s in self._skills.values() if s.complexity == complexity]

    def validate_source_files(self) -> dict[str, bool]:
        """Check which skill source files exist in the SME."""
        self._ensure_loaded()
        return {name: skill.source_exists for name, skill in self._skills.items()}

    def get_categories(self) -> dict[str, int]:
        """Get skill counts by category."""
        self._ensure_loaded()
        counts: dict[str, int] = {}
        for skill in self._skills.values():
            counts[skill.category] = counts.get(skill.category, 0) + 1
        return counts

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of loaded skills."""
        self._ensure_loaded()
        verified = sum(1 for s in self._skills.values() if s.source_exists)
        return {
            "total_skills": len(self._skills),
            "verified_sources": verified,
            "unverified_sources": len(self._skills) - verified,
            "categories": self.get_categories(),
            "domains": list({s.domain for s in self._skills.values()}),
        }

    def format_skill_for_agent(self, name: str) -> str:
        """Format a skill's information as context for an AI agent."""
        skill = self.get_skill(name)
        if not skill:
            return f"Skill '{name}' not found."

        lines = [
            f"# Skill: {skill.name}",
            f"Domain: {skill.domain} | Category: {skill.category}",
            f"Complexity: {skill.complexity} | Type: {skill.type}",
            f"Source: {skill.source_file} ({'verified' if skill.source_exists else 'not found'})",
            "",
            "## Purpose",
            skill.purpose,
            "",
            "## Description",
            skill.description,
        ]

        if skill.workflow:
            lines.append("")
            lines.append("## Workflow")
            for i, step in enumerate(skill.workflow, 1):
                lines.append(f"{i}. {step}")

        return "\n".join(lines)
