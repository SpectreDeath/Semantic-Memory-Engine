"""
Integration Tests for SME Skills System

Tests the skills loader, registry builder, and skill specification files.

Run with:
    pytest tests/test_skills_integration.py -v
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

SKILLS_DIR = Path(__file__).parent.parent / "skills"
REGISTRY_PATH = SKILLS_DIR / "registry.json"


class TestSkillsDirectory:
    """Verify skills directory and files exist."""

    def test_skills_directory_exists(self):
        assert SKILLS_DIR.exists(), f"Skills directory not found: {SKILLS_DIR}"
        assert SKILLS_DIR.is_dir(), f"Skills path is not a directory: {SKILLS_DIR}"

    def test_skill_md_files_present(self):
        md_files = list(SKILLS_DIR.glob("*.md"))
        assert len(md_files) >= 90, f"Expected at least 90 skill files, found {len(md_files)}"

    def test_skill_files_are_valid_markdown(self):
        for skill_file in sorted(SKILLS_DIR.glob("*.md"))[:10]:
            content = skill_file.read_text(encoding="utf-8")
            assert len(content) > 50, f"Skill file too short: {skill_file.name}"
            assert "## Purpose" in content or "## Description" in content, (
                f"Missing expected sections in {skill_file.name}"
            )


class TestSkillRegistry:
    """Verify registry.json was generated correctly."""

    def test_registry_exists(self):
        assert REGISTRY_PATH.exists(), f"Registry not found: {REGISTRY_PATH}"

    def test_registry_is_valid_json(self):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list), "Registry should be a JSON array"

    def test_registry_has_entries(self):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 90, f"Expected at least 90 registry entries, got {len(data)}"

    def test_registry_entry_schema(self):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        required_keys = {
            "name",
            "domain",
            "version",
            "complexity",
            "type",
            "category",
            "source_file",
            "source_exists",
            "spec_path",
            "purpose",
            "description",
        }
        for entry in data[:5]:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Entry '{entry.get('name')}' missing keys: {missing}"

    def test_registry_has_verified_sources(self):
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        verified = sum(1 for e in data if e.get("source_exists"))
        assert verified >= 80, f"Expected at least 80 verified sources, got {verified}"


class TestSkillsLoader:
    """Test the SkillsLoader module."""

    def test_loader_import(self):
        from src.sme.skills_loader import SkillsLoader

        assert SkillsLoader is not None

    def test_loader_init(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        assert loader is not None

    def test_loader_load_registry(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        skills = loader.load_registry()
        assert len(skills) >= 90

    def test_loader_get_skill(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        skill = loader.get_skill("analysis-engine")
        assert skill is not None
        assert skill.name == "analysis-engine"
        assert skill.category == "Analysis"

    def test_loader_get_skill_not_found(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        skill = loader.get_skill("nonexistent-skill-xyz")
        assert skill is None

    def test_loader_search_skills(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        results = loader.search_skills("forensic")
        assert len(results) > 0
        for skill in results:
            assert (
                "forensic"
                in (f"{skill.name} {skill.purpose} {skill.description} {skill.category}").lower()
            )

    def test_loader_get_skills_by_category(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        analysis_skills = loader.get_skills_by_category("Analysis")
        assert len(analysis_skills) > 0
        for skill in analysis_skills:
            assert skill.category == "Analysis"

    def test_loader_validate_source_files(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        validation = loader.validate_source_files()
        assert len(validation) >= 90
        verified = sum(1 for v in validation.values() if v)
        assert verified >= 80

    def test_loader_get_summary(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        summary = loader.get_summary()
        assert "total_skills" in summary
        assert "verified_sources" in summary
        assert "categories" in summary
        assert summary["total_skills"] >= 90

    def test_loader_format_skill_for_agent(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        formatted = loader.format_skill_for_agent("analysis-engine")
        assert "analysis-engine" in formatted
        assert "Purpose" in formatted or "Description" in formatted

    def test_loader_format_not_found(self):
        from src.sme.skills_loader import SkillsLoader

        loader = SkillsLoader(str(SKILLS_DIR))
        formatted = loader.format_skill_for_agent("nonexistent-xyz")
        assert "not found" in formatted.lower()


class TestSkillRegistryBuilder:
    """Test the SkillRegistryBuilder module."""

    def test_builder_import(self):
        from src.sme.skill_registry import SkillRegistryBuilder

        assert SkillRegistryBuilder is not None

    def test_builder_parse_skill_file(self):
        from src.sme.skill_registry import SkillRegistryBuilder

        builder = SkillRegistryBuilder(str(SKILLS_DIR))
        skill_file = SKILLS_DIR / "analysis-engine.md"
        metadata = builder.parse_skill_file(skill_file)
        assert metadata is not None
        assert metadata.name == "analysis-engine"
        assert metadata.domain == "SME_INTEGRATION"

    def test_builder_validate_skills(self):
        from src.sme.skill_registry import SkillRegistryBuilder

        builder = SkillRegistryBuilder(str(SKILLS_DIR))
        issues = builder.validate_skills()
        assert "missing_source" in issues
        assert "missing_purpose" in issues

    def test_builder_generate_report(self):
        from src.sme.skill_registry import SkillRegistryBuilder

        builder = SkillRegistryBuilder(str(SKILLS_DIR))
        report = builder.generate_report()
        assert "total_skills" in report
        assert report["total_skills"] >= 90
        assert "categories" in report
