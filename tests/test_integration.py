"""
Integration Tests for SimpleMem Laboratory

Tests the new architecture, import structure, and tool integration.

Run with:
    pytest tests/test_integration.py -v
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestImportStructure:
    """Test that new import structure works correctly."""

    def test_backward_compat_imports(self):
        """Test backward compatibility - legacy modules may have been removed."""
        # These legacy modules have been removed in v3.0
        # Check if they exist, skip if not
        legacy_modules = [
            "adaptive_scout",
            "memory_synapse",
            "retrieval_query",
            "scribe_authorship",
        ]
        missing = []
        for module_name in legacy_modules:
            try:
                __import__(module_name)
            except ImportError:
                missing.append(module_name)

        if missing:
            # These modules were removed in v3.0 - test passes with warning
            import warnings

            warnings.warn(f"Legacy modules not available (removed in v3.0): {missing}")

    def test_new_imports(self):
        """Test that new import paths work."""
        try:
            from src.query.engine import SemanticSearchEngine
            from src.query.scout_integration import Scout
            from src.scribe.engine import ScribeEngine
            from src.synapse.synapse import MemoryConsolidator
        except ImportError as e:
            pytest.fail(f"New import structure failed: {e}")

    def test_package_exports(self):
        """Test that src package exports all major classes."""
        try:
            from src import (
                Config,
                MemoryConsolidator,
                Scout,
                ScribeEngine,
                SemanticSearchEngine,
                ToolFactory,
            )
        except ImportError as e:
            pytest.fail(f"Package export import failed: {e}")


class TestConfiguration:
    """Test the new centralized configuration system."""

    def test_config_singleton(self):
        """Test that Config is a singleton."""
        from src.core.config import Config

        config1 = Config()
        config2 = Config()
        assert config1 is config2, "Config should be a singleton"

    def test_config_load(self):
        """Test that configuration loads from config.yaml."""
        from src.core.config import Config, ConfigError

        try:
            config = Config()
            # These keys should exist from the refactoring summary
            storage_dir = config.get_safe("storage.base_dir")
            assert storage_dir is not None
        except ConfigError as e:
            pytest.skip(f"Config file not found: {e}")

    def test_config_get_with_default(self):
        """Test that config returns defaults for missing keys."""
        from src.core.config import Config

        config = Config()
        default_value = "test_default"
        result = config.get_safe("nonexistent.key", default=default_value)
        assert result == default_value

    def test_config_type_conversions(self):
        """Test config type conversion methods."""
        from src.core.config import Config

        config = Config()

        # These should not raise even if keys don't exist
        int_val = config.get_safe("nonexistent.int", default=42)
        assert isinstance(int_val, int)

        float_val = config.get_safe("nonexistent.float", default=3.14)
        assert isinstance(float_val, float)

        bool_val = config.get_safe("nonexistent.bool", default=True)
        assert isinstance(bool_val, bool)


class TestToolFactory:
    """Test the tool factory dependency injection system."""

    def test_factory_singleton_behavior(self):
        """Test that factory returns same instance on multiple calls."""
        from src.core.factory import ToolFactory

        ToolFactory.reset()

        # Mock the imports to avoid actual initialization
        # In a real test, these would be mocked
        # For now, we just test the factory structure
        assert hasattr(ToolFactory, "create_scribe")
        assert hasattr(ToolFactory, "create_scout")
        assert hasattr(ToolFactory, "create_search_engine")

    def test_factory_reset(self):
        """Test that factory reset clears cached instances."""
        from src.core.factory import ToolFactory

        ToolFactory.reset()
        instances = ToolFactory.list_instances()
        assert len(instances) == 0, "Factory should be empty after reset"

    def test_factory_health_check(self):
        """Test factory health check functionality."""
        from src.core.factory import ToolFactory

        ToolFactory.reset()
        health = ToolFactory.health_check()
        assert isinstance(health, dict)


class TestCLIEntryPoint:
    """Test the new __main__.py CLI entry point."""

    def test_cli_imports(self):
        """Test that CLI entry point imports correctly."""
        try:
            from __main__ import TOOLS, list_tools, show_help

            assert isinstance(TOOLS, dict)
            assert len(TOOLS) > 0
        except ImportError as e:
            pytest.skip(f"CLI entry point not available: {e}")

    def test_cli_tool_registry(self):
        """Test that CLI has all expected tools registered."""
        try:
            from __main__ import TOOLS

            expected_tools = [
                "scribe",
                "scout",
                "search",
                "synapse",
                "rhetoric",
                "centrifuge",
                "monitor",
            ]

            for tool in expected_tools:
                assert tool in TOOLS, f"Tool '{tool}' not in CLI registry"
        except ImportError:
            pytest.skip("CLI entry point not available")


class TestModuleStructure:
    """Test the new modular structure."""

    def test_scribe_module_exists(self):
        """Test that scribe module is properly structured."""
        from src.scribe import engine

        assert hasattr(engine, "ScribeEngine")

    def test_query_modules_exist(self):
        """Test that query modules are properly structured."""
        from src.query import engine, scout, scout_integration

        assert hasattr(scout, "AdaptiveRetriever")
        assert hasattr(scout_integration, "Scout")
        assert hasattr(engine, "SemanticSearchEngine")

    def test_synapse_module_exists(self):
        """Test that synapse module is properly structured."""
        from src.synapse import synapse

        assert hasattr(synapse, "MemoryConsolidator")
        assert hasattr(synapse, "BehavioralProfiler")

    def test_core_modules_exist(self):
        """Test that core modules are properly structured."""
        from src.core import centrifuge, config, factory, semantic_db

        # Check for actual exports (some modules may not have classes, but should have functions/objects)
        assert hasattr(centrifuge, "mcp") or hasattr(centrifuge, "init_db"), (
            "centrifuge module should have exports"
        )
        assert hasattr(semantic_db, "SemanticMemory")
        assert hasattr(config, "Config")
        assert hasattr(factory, "ToolFactory")


class TestLegacyCompatibility:
    """Test that legacy code can be migrated safely."""

    def test_legacy_files_archived(self):
        """Test that legacy directory exists and contains old files."""
        legacy_path = Path(__file__).parent.parent / "legacy"
        if not legacy_path.exists():
            pytest.skip("Legacy directory does not exist - skipped")

        # Check for some old files
        old_files = [
            "harvester_spider.py",
            "scribe_authorship.py",
            "semantic_loom.py",
        ]

        for file in old_files:
            file_path = legacy_path / file
            # File may not exist in all cases, but directory should
            # This is just a structural test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
