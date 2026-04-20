"""
Tests for gateway/skills_bridge.py - Skills registration bridge.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from unittest.mock import MagicMock, patch
import pytest

from gateway.skills_bridge import register_skills_with_registry, _make_skill_handler


def test_make_skill_handler_info():
    mock_loader = MagicMock()
    mock_skill = MagicMock()
    mock_skill.name = "test_skill"
    mock_skill.category = "utility"
    mock_skill.purpose = "A test skill"
    mock_skill.source_file = "skills/test_skill/SKILL.md"
    mock_skill.source_exists = True
    mock_skill.workflow = ["step1"]
    mock_loader.get_skill.return_value = mock_skill

    handler = _make_skill_handler("test_skill", mock_loader)

    result = handler(action="info")
    assert result["name"] == "test_skill"
    assert "A test skill" in result["purpose"]
    mock_loader.get_skill.assert_called_once_with("test_skill")


def test_make_skill_handler_context():
    mock_loader = MagicMock()
    mock_loader.get_skill_context.return_value = {"key": "value"}
    handler = _make_skill_handler("ctx_skill", mock_loader)
    result = handler(action="context")
    assert result == {"context": {"key": "value"}}
    mock_loader.get_skill_context.assert_called_once_with("ctx_skill")


def test_make_skill_handler_search():
    mock_loader = MagicMock()
    mock_skill1 = MagicMock(name="SkillA", category="catA", purpose="Purpose A")
    mock_skill2 = MagicMock(name="SkillB", category="catB", purpose="Purpose B")
    mock_loader.search_skills.return_value = [mock_skill1, mock_skill2]
    handler = _make_skill_handler("search_skill", mock_loader)
    result = handler(action="search", query="test")
    assert result["query"] == "test"
    assert len(result["results"]) == 2
    assert result["results"][0]["name"] == "SkillA"


def test_make_skill_handler_unknown_action():
    mock_loader = MagicMock()
    handler = _make_skill_handler("any", mock_loader)
    result = handler(action="unknown")
    assert "error" in result


@patch("gateway.skills_bridge.SkillsLoader")
def test_register_skills_with_registry_calls_add_tool(mock_loader_class):
    # Setup mock registry
    mock_registry = MagicMock()
    mock_loader = MagicMock()
    mock_skill = MagicMock()
    mock_skill.name = "skill1"
    mock_skill.source_exists = True
    mock_loader.load_registry.return_value = [mock_skill]
    mock_loader_class.return_value = mock_loader

    count = register_skills_with_registry(mock_registry, skills_dir="fake_dir")
    assert count == 1
    mock_registry.add_tool.assert_called_once()
    call_kwargs = mock_registry.add_tool.call_args[1]
    assert call_kwargs["name"] == "skill_skill1"
    assert call_kwargs["category"] == "skill"  # Check default category


@patch("gateway.skills_bridge.SkillsLoader")
def test_register_skills_skips_missing_source(mock_loader_class):
    mock_registry = MagicMock()
    mock_loader = MagicMock()
    mock_skill = MagicMock()
    mock_skill.name = "orphan"
    mock_skill.source_exists = False
    mock_loader.load_registry.return_value = [mock_skill]
    mock_loader_class.return_value = mock_loader

    count = register_skills_with_registry(mock_registry)
    assert count == 0
    mock_registry.add_tool.assert_not_called()
