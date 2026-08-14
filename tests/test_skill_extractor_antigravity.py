"""Tests for Antigravity-compliant skill generation and directory exports in SME."""

import os
import tempfile
from pathlib import Path
import pytest

from src.utils.skill_extractor import ExtractedSkill, SkillExtractor


def test_render_skill_md_includes_antigravity_frontmatter():
    extractor = SkillExtractor.__new__(SkillExtractor)
    skill = ExtractedSkill(
        skill_name="code-reviewer",
        domain="ENGINEERING",
        version="1.0.0",
        complexity="Advanced",
        skill_type="Tool",
        category="General",
        purpose="Review code for standards and spec compliance.",
        description="Performs dual-axis code review across pull requests and git diffs.",
        workflow=["Analyze branch diff", "Check repo coding standards", "Verify against issue spec"],
        inputs=["git diff or commit hash"],
        outputs=["Review report markdown"],
        tags=["review", "code-quality"],
    )

    rendered = extractor._render_skill_md(skill)
    assert rendered.startswith("---"), "Must start with YAML frontmatter delimiter"
    
    # Check frontmatter fields
    assert "name: code-reviewer" in rendered
    assert "description:" in rendered
    assert "Performs dual-axis code review across pull requests and git diffs." in rendered
    assert "Domain: ENGINEERING" in rendered
    assert "Version: 1.0.0" in rendered
    
    # Check markdown body
    assert "# code-reviewer" in rendered
    assert "## Purpose" in rendered
    assert "## Description" in rendered
    assert "## Workflow" in rendered
    assert "1. **Analyze branch diff**" in rendered


def test_save_as_directory_creates_skill_dir_and_skill_md():
    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = tempfile.mkdtemp()
    
    skill = ExtractedSkill(
        skill_name="diagnose-memory-leak",
        domain="DIAGNOSTICS",
        version="1.0.0",
        complexity="Advanced",
        skill_type="Tool",
        category="General",
        purpose="Diagnose memory leaks in background processes.",
        description="Profiles heap allocations and identifies object retention paths.",
        workflow=["Attach memory profiler", "Take heap snapshot", "Diff snapshots"],
        inputs=["PID"],
        outputs=["Heap analysis report"],
        tags=["profiling", "memory"],
    )

    md_path = extractor.save(skill, output_dir=tmpdir, as_directory=True)
    assert md_path.name == "SKILL.md", "Directory mode must output SKILL.md"
    assert md_path.parent.name == "diagnose-memory-leak", "Parent directory must be skill name"
    assert md_path.exists()
    
    meta_path = md_path.parent / "diagnose-memory-leak.metadata.json"
    assert meta_path.exists()
    
    content = md_path.read_text(encoding="utf-8")
    assert "name: diagnose-memory-leak" in content
    assert "description:" in content
