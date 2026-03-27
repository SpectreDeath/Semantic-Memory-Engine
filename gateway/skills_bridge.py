"""
Skills MCP Bridge

Registers SME skills as MCP tools in the ToolRegistry, making them
discoverable and callable through the MCP Gateway.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def register_skills_with_registry(
    registry: Any,
    skills_dir: str = "skills",
) -> int:
    """
    Register all SME skills as tools in the ToolRegistry.

    Args:
        registry: The ToolRegistry instance from gateway.tool_registry
        skills_dir: Path to the skills directory containing SKILL.md files

    Returns:
        Number of skills registered
    """
    from src.sme.skills_loader import SkillsLoader

    loader = SkillsLoader(skills_dir)
    skills = loader.load_registry()

    registered = 0
    for skill in skills:
        if not skill.source_exists:
            logger.warning(f"Skipping skill '{skill.name}': source not found")
            continue

        tool_name = f"skill_{skill.name}"
        handler = _make_skill_handler(skill.name, loader)

        registry.add_tool(
            name=tool_name,
            instance=handler,
            description=f"[{skill.category}] {skill.purpose[:120]}",
            parameters={"action": "str", "query": "str"},
        )
        registered += 1

    logger.info(f"Registered {registered} skills with ToolRegistry")
    return registered


def _make_skill_handler(skill_name: str, loader: Any) -> Callable:
    """Create a handler function for a skill."""

    def handler(action: str = "info", query: str = "") -> dict[str, Any]:
        if action == "info":
            skill = loader.get_skill(skill_name)
            if not skill:
                return {"error": f"Skill '{skill_name}' not found"}
            return {
                "name": skill.name,
                "category": skill.category,
                "purpose": skill.purpose,
                "source_file": skill.source_file,
                "source_exists": skill.source_exists,
                "workflow": skill.workflow,
            }
        elif action == "context":
            return {"context": loader.get_skill_context(skill_name)}
        elif action == "search":
            results = loader.search_skills(query)
            return {
                "query": query,
                "results": [
                    {"name": s.name, "category": s.category, "purpose": s.purpose[:80]}
                    for s in results
                ],
                "count": len(results),
            }
        else:
            return {"error": f"Unknown action: {action}"}

    handler.__name__ = f"skill_{skill_name}"
    handler.__doc__ = f"SME Skill: {skill_name}"
    return handler
