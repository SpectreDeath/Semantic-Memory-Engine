"""
Extension Matrix Test
=====================
Systematically verifies that every extension in the extensions/ directory:
  1. Can be discovered by the ExtensionManager without raising an exception.
  2. Exposes at least one tool via get_extension_tools().
  3. Each exposed tool has the required keys: name, description, handler.
  4. Each handler is callable.

Run with:
    python -m pytest tests/test_extension_matrix.py -v
"""

import asyncio
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Ensure the project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXTENSIONS_DIR = PROJECT_ROOT / "extensions"

# Collect every extension folder that contains a Python file
def _discover_extension_dirs() -> List[Path]:
    dirs = []
    for entry in sorted(EXTENSIONS_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith("_"):
            py_files = list(entry.glob("*.py"))
            if py_files:
                dirs.append(entry)
    return dirs

EXTENSION_DIRS = _discover_extension_dirs()
EXTENSION_NAMES = [d.name for d in EXTENSION_DIRS]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def extension_manager():
    """
    Build a real ExtensionManager instance and run discovery once for the
    whole test session so we don't pay the startup cost 18 times.
    """
    from gateway.extension_manager import ExtensionManager

    manager = ExtensionManager(nexus_api=None)
    asyncio.run(manager.discover_and_load())
    return manager


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_extension_dirs_found():
    """Sanity check — the extensions directory must contain at least one entry."""
    assert len(EXTENSION_DIRS) > 0, (
        f"No extension directories found under {EXTENSIONS_DIR}. "
        "Check that the extensions/ folder exists and is not empty."
    )


def test_all_extensions_discovered(extension_manager):
    """Every extension folder must appear in the manager's loaded registry."""
    loaded = extension_manager.get_status()
    # get_status() returns List[Dict] with "id" per extension
    loaded_ids = {s["id"] for s in loaded} if isinstance(loaded, list) else set(loaded.get("loaded_extensions", []))

    missing = [name for name in EXTENSION_NAMES if name not in loaded_ids]
    assert not missing, (
        f"The following extensions were not loaded by ExtensionManager: {missing}\n"
        "Check the extension __init__.py / manifest files for import errors."
    )


@pytest.mark.parametrize("ext_name", EXTENSION_NAMES)
def test_extension_exposes_tools(extension_manager, ext_name):
    """Each extension must expose at least one tool."""
    all_tools: List[Dict[str, Any]] = extension_manager.get_extension_tools()
    ext_tools = [t for t in all_tools if t.get("plugin_id") == ext_name]

    assert len(ext_tools) > 0, (
        f"Extension '{ext_name}' exposes zero tools. "
        "Every extension must register at least one tool via its manifest."
    )


@pytest.mark.parametrize("ext_name", EXTENSION_NAMES)
def test_extension_tool_schema(extension_manager, ext_name):
    """Each tool dict must have the required keys and a callable handler."""
    all_tools: List[Dict[str, Any]] = extension_manager.get_extension_tools()
    ext_tools = [t for t in all_tools if t.get("plugin_id") == ext_name]

    required_keys = {"name", "description", "handler"}

    for tool in ext_tools:
        missing_keys = required_keys - set(tool.keys())
        assert not missing_keys, (
            f"Tool '{tool.get('name', '<unnamed>')}' from extension '{ext_name}' "
            f"is missing required keys: {missing_keys}"
        )
        assert callable(tool["handler"]), (
            f"Tool '{tool['name']}' from extension '{ext_name}' — "
            f"handler is not callable (got {type(tool['handler'])})"
        )
        assert isinstance(tool["name"], str) and tool["name"].strip(), (
            f"Extension '{ext_name}' has a tool with an empty or non-string name."
        )
        assert isinstance(tool["description"], str) and tool["description"].strip(), (
            f"Tool '{tool['name']}' from extension '{ext_name}' has an empty description."
        )


@pytest.mark.parametrize("ext_name", EXTENSION_NAMES)
def test_extension_handler_returns_string(extension_manager, ext_name):
    """
    Call each tool handler with an empty string and verify it returns a string
    (or raises a predictable ValueError/TypeError, not an unhandled crash).
    """
    all_tools: List[Dict[str, Any]] = extension_manager.get_extension_tools()
    ext_tools = [t for t in all_tools if t.get("plugin_id") == ext_name]

    for tool in ext_tools:
        handler = tool["handler"]
        try:
            if inspect.iscoroutinefunction(handler):
                result = asyncio.run(handler(""))
            else:
                result = handler("")
            # If it returns something, it must be a string (JSON or plain text)
            if result is not None:
                assert isinstance(result, str), (
                    f"Tool '{tool['name']}' returned {type(result)} instead of str."
                )
        except (ValueError, TypeError, NotImplementedError):
            # Acceptable — the handler correctly rejects empty/invalid input
            pass
        except Exception as exc:
            pytest.fail(
                f"Tool '{tool['name']}' from extension '{ext_name}' raised an "
                f"unexpected exception when called with an empty string: {exc!r}"
            )
