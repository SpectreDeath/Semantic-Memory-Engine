"""
🔧 Workflow Generator
====================
Generates workflow definitions from natural language task descriptions.
Used by AI agents to automatically create and execute multi-step workflows.

Usage:
    generator = WorkflowGenerator()
    workflow_def = generator.generate("Research AI ethics and analyze sentiment")
    result = await engine.execute(workflow_def, {"topic": "AI ethics"})
"""

import logging
from typing import Any

logger = logging.getLogger("WorkflowGenerator")


class WorkflowGenerator:
    """Generates workflow definitions from task descriptions."""

    def __init__(self):
        self._step_templates = self._build_templates()

    def _build_templates(self) -> dict[str, dict]:
        """Build step templates mapping keywords to handlers."""
        return {
            # HARVESTING
            "harvest": {
                "handler": "harvest_url",
                "params": {"url": "$input.url"},
                "keywords": ["harvest", "fetch", "crawl", "scrape", "ingest", "collect"],
            },
            "rss": {
                "handler": "rss_fetch",
                "params": {"feed_url": "$input.rss_url"},
                "keywords": ["rss", "feed", "news", "blog"],
            },
            "scholar": {
                "handler": "scholar_search",
                "params": {"query": "$input.query", "max_results": 10},
                "keywords": ["academic", "research", "paper", "scholar", "study"],
            },
            "osint": {
                "handler": "osint_scan",
                "params": {"username": "$input.username"},
                "keywords": ["osint", "investigate", "profile", "social", "account"],
            },
            # ANALYSIS
            "sentiment": {
                "handler": "sentiment",
                "params": {"text": "$prev.text"},
                "keywords": ["sentiment", "emotion", "feeling", "tone", "mood"],
            },
            "stylometry": {
                "handler": "stylometry",
                "params": {"text": "$prev.text", "author_id": "$input.author_id"},
                "keywords": ["stylometry", "author", "writing style", "fingerprint", "attribution"],
            },
            "summarize": {
                "handler": "summarize",
                "params": {"text": "$prev.text", "ratio": 0.3},
                "keywords": ["summarize", "summary", "extract", "condense", "brief"],
            },
            "rhetoric": {
                "handler": "rhetorical_analysis",
                "params": {"text": "$prev.text"},
                "keywords": ["rhetoric", "argument", "persuasion", "structure"],
            },
            "overlap": {
                "handler": "overlap_detection",
                "params": {"texts": "$input.texts"},
                "keywords": ["overlap", "similarity", "duplicate", "compare", "plagiarism"],
            },
            # AI
            "ai_flow": {
                "handler": "ai_flow",
                "params": {"flow_name": "$input.flow_name", "input_data": "$input"},
                "keywords": ["ai", "llm", "generate", "model", "prompt"],
            },
            "concept": {
                "handler": "concept_lookup",
                "params": {"term": "$input.term"},
                "keywords": ["concept", "lookup", "define", "understand"],
            },
            # SECURITY
            "trust": {
                "handler": "trust_score",
                "params": {"data_source": "$input.source", "content": "$prev.text"},
                "keywords": ["trust", "credibility", "reliability", "score"],
            },
            "bot": {
                "handler": "bot_detection",
                "params": {"username": "$input.username", "platform": "$input.platform"},
                "keywords": ["bot", "fake", "automation", "detection"],
            },
            # DATA
            "save": {
                "handler": "save_to_db",
                "params": {"data": "$prev", "table": "$input.table"},
                "keywords": ["save", "store", "persist", "database", "db"],
            },
            "query": {
                "handler": "query_db",
                "params": {"query": "$input.query"},
                "keywords": ["query", "search", "retrieve", "sql"],
            },
            "gephi": {
                "handler": "gephi_export",
                "params": {"mode": "$input.mode", "data": "$prev"},
                "keywords": ["visualize", "graph", "network", "gephi", "export"],
            },
        }

    def generate(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate workflow definition from task description."""
        context = context or {}
        task_lower = task.lower()

        steps = []
        used_handlers = set()

        for step_name, template in self._step_templates.items():
            keywords = template["keywords"]
            for keyword in keywords:
                if keyword in task_lower and template["handler"] not in used_handlers:
                    step = {
                        "id": f"step_{len(steps)}",
                        "name": step_name,
                        "handler": template["handler"],
                        "params": self._resolve_params(template["params"], context),
                        "depends_on": [steps[-1]["id"]] if steps else [],
                    }
                    steps.append(step)
                    used_handlers.add(template["handler"])
                    break

        if not steps:
            logger.warning(f"No steps matched for task: {task}")
            return {
                "name": "Generated Workflow",
                "description": f"Auto-generated from: {task}",
                "steps": [],
                "error": "No matching steps found",
            }

        workflow = {
            "name": self._extract_workflow_name(task),
            "description": f"Auto-generated from: {task}",
            "steps": steps,
            "parallel": self._should_parallel(task, steps),
        }

        logger.info(f"Generated workflow with {len(steps)} steps: {[s['handler'] for s in steps]}")
        return workflow

    def _resolve_params(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Resolve parameter references."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str):
                if value.startswith("$input."):
                    input_key = value.split(".")[1]
                    resolved[key] = context.get(input_key, "")
                elif value.startswith("$prev."):
                    resolved[key] = f"$prev.{key}"
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved

    def _extract_workflow_name(self, task: str) -> str:
        """Extract workflow name from task."""
        words = task.split()[:4]
        return " ".join(words).title().replace(",", "").replace("?", "")

    def _should_parallel(self, task: str, steps: list[dict]) -> bool:
        """Determine if workflow should run in parallel."""
        task_lower = task.lower()
        parallel_keywords = ["multiple", "parallel", "concurrent", "all at once", "simultaneously"]
        return any(kw in task_lower for kw in parallel_keywords) and len(steps) > 2

    def list_available_handlers(self) -> list[dict[str, Any]]:
        """List all available step handlers."""
        handlers = []
        for name, template in self._step_templates.items():
            handlers.append(
                {
                    "name": name,
                    "handler": template["handler"],
                    "keywords": template["keywords"],
                }
            )
        return handlers


async def generate_and_execute(task: str, input_data: dict[str, Any]) -> dict[str, Any]:
    """Generate workflow from task and execute it."""
    from src.orchestration.step_registry import get_step_registry
    from src.orchestration.workflow_engine import get_engine

    generator = WorkflowGenerator()
    engine = get_engine()
    registry = get_step_registry()

    workflow_def = generator.generate(task, input_data)

    if "error" in workflow_def:
        return {"status": "error", "message": workflow_def["error"]}

    for step in workflow_def["steps"]:
        handler = registry.get_handler(step["handler"])
        if handler:
            engine.register_step(step["handler"], handler)

    workflow = engine.create_workflow(
        name=workflow_def["name"],
        description=workflow_def["description"],
        steps=workflow_def["steps"],
        parallel=workflow_def.get("parallel", False),
    )

    result = await engine.execute(workflow, input_data)
    return result


def get_generator() -> WorkflowGenerator:
    """Get a WorkflowGenerator instance."""
    return WorkflowGenerator()
