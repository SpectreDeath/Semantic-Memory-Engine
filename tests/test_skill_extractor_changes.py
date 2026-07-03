"""Quick verification of new skill_extractor features."""

import os
import tempfile
from pathlib import Path

from src.utils.skill_extractor import ExtractedSkill, SkillExtractor


def test_force_json_wraps_plain_text():
    extractor = SkillExtractor.__new__(SkillExtractor)
    raw_text = "[MOCK AI RESULT] Flow: extract_skill | Input: some text"
    wrapped = extractor._force_json_response(raw_text)
    assert wrapped.startswith("{"), "Should wrap plain text"
    assert "auto-extracted-pattern" in wrapped, "Should contain fallback name"
    print("PASS: _force_json_response wraps plain text")


def test_force_json_passes_valid_json():
    extractor = SkillExtractor.__new__(SkillExtractor)
    valid_json = '{"status": "success", "extraction": {"name": "test"}}'
    passed = extractor._force_json_response(valid_json)
    assert passed == valid_json, "Should pass valid JSON unchanged"
    print("PASS: _force_json_response passes valid JSON")


def test_atomic_save_creates_both_files():
    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = tempfile.mkdtemp()
    skill = ExtractedSkill(
        skill_name="atomic-test",
        domain="TEST",
        version="1.0.0",
        complexity="Intermediate",
        skill_type="Tool",
        category="General",
        source_file=None,
        source=None,
        purpose="Test atomic save pattern for crash safety.",
        description="Validates atomic rename with os.replace on Windows.",
        workflow=["step one", "step two", "step three"],
        inputs=[],
        outputs=[],
        estimated_time="minutes",
        tags=["test"],
        examples_text="",
    )
    md_path = extractor.save(skill, output_dir=tmpdir)
    assert md_path.exists(), "MD file should exist"
    meta_path = Path(tmpdir) / "atomic-test.metadata.json"
    assert meta_path.exists(), "Metadata file should exist"
    files = os.listdir(tmpdir)
    assert "atomic-test.md" in files, "MD file in dir"
    assert "atomic-test.metadata.json" in files, "Meta file in dir"
    print("PASS: Atomic save creates both .md and .metadata.json")


def test_no_tmp_files_remain():
    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = tempfile.mkdtemp()
    skill = ExtractedSkill(
        skill_name="atomic-test-2",
        domain="TEST",
        version="1.0.0",
        complexity="Intermediate",
        skill_type="Tool",
        category="General",
        source_file=None,
        source=None,
        purpose="Test no tmp files remain.",
        description="Ensures cleanup on success.",
        workflow=["step one", "step two", "step three"],
        inputs=[],
        outputs=[],
        estimated_time="minutes",
        tags=["test"],
        examples_text="",
    )
    extractor.save(skill, output_dir=tmpdir)
    tmp_files = [f for f in os.listdir(tmpdir) if f.startswith(".tmp_")]
    assert not tmp_files, f"No temp files should remain, found: {tmp_files}"
    print("PASS: No temp files remain after atomic save")


def test_sentinel_provider_fails_fast_when_model_not_loaded():
    from src.ai.providers.sentinel_provider import SentinelProvider

    provider = SentinelProvider.__new__(SentinelProvider)
    provider.model = None
    provider._init_error = "Failed to load llama-cpp: No module named 'llama_cpp'"
    try:
        provider.run("extract_skill", "some input")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert "Sentinel model not loaded" in str(exc), (
            "Error message should mention model not loaded"
        )
        assert "llama_cpp" in str(exc), "Error message should include init error details"
        print("PASS: SentinelProvider fails fast with clear error")


def test_resolve_collision_no_collision():
    from scripts.extract_skill import _resolve_collision

    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = Path(tempfile.mkdtemp())

    name, did_collide = _resolve_collision(
        output_name="unique-skill",
        author="author1",
        target_dir=tmpdir,
        extractor=extractor,
        on_collision="author-suffix",
    )
    assert name == "unique-skill"
    assert did_collide is False
    print("PASS: _resolve_collision returns original name when no collision")


def test_resolve_collision_overwrite():
    from scripts.extract_skill import _resolve_collision

    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "collision-skill.md").write_text("existing", encoding="utf-8")

    name, did_collide = _resolve_collision(
        output_name="collision-skill",
        author="author1",
        target_dir=tmpdir,
        extractor=extractor,
        on_collision="overwrite",
    )
    assert name == "collision-skill"
    assert did_collide is True
    print("PASS: _resolve_collision overwrite returns original name")


def test_resolve_collision_skip():
    from scripts.extract_skill import _resolve_collision

    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "collision-skill.md").write_text("existing", encoding="utf-8")

    name, did_collide = _resolve_collision(
        output_name="collision-skill",
        author="author1",
        target_dir=tmpdir,
        extractor=extractor,
        on_collision="skip",
    )
    assert name == "collision-skill"
    assert did_collide is True
    print("PASS: _resolve_collision skip returns original name")


def test_resolve_collision_author_suffix():
    from scripts.extract_skill import _resolve_collision

    extractor = SkillExtractor.__new__(SkillExtractor)
    tmpdir = Path(tempfile.mkdtemp())
    (tmpdir / "data-analysis.md").write_text("existing", encoding="utf-8")

    name, did_collide = _resolve_collision(
        output_name="data-analysis",
        author="nix-community",
        target_dir=tmpdir,
        extractor=extractor,
        on_collision="author-suffix",
    )
    assert name == "data-analysis--nix-community"
    assert did_collide is True
    resolved_path = tmpdir / "data-analysis--nix-community.md"
    assert not resolved_path.exists(), "Should not write yet, just resolve name"
    print("PASS: _resolve_collision author-suffix appends author handle")


def test_sentinel_switch_lens_fails_fast_when_model_not_loaded():
    from src.ai.providers.sentinel_provider import SentinelProvider

    provider = SentinelProvider.__new__(SentinelProvider)
    provider.model = None
    provider._init_error = "Failed to load llama-cpp: No module named 'llama_cpp'"

    try:
        provider.switch_lens("some-lens")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert "Sentinel model not loaded" in str(exc), (
            "Error message should mention model not loaded"
        )
        assert "Cannot switch lens" in str(exc), (
            "Error message should mention lens operation"
        )
    print("PASS: SentinelProvider.switch_lens fails fast when model not loaded")


def test_sentinel_offload_to_ram_fails_fast_when_model_not_loaded():
    from src.ai.providers.sentinel_provider import SentinelProvider

    provider = SentinelProvider.__new__(SentinelProvider)
    provider.model = None
    provider._init_error = "Failed to load llama-cpp: No module named 'llama_cpp'"

    try:
        provider.offload_to_ram()
        assert False, "Should have raised RuntimeError"
    except RuntimeError as exc:
        assert "Sentinel model not loaded" in str(exc), (
            "Error message should mention model not loaded"
        )
        assert "Cannot offload layers" in str(exc), (
            "Error message should mention offload operation"
        )
    print("PASS: SentinelProvider.offload_to_ram fails fast when model not loaded")


if __name__ == "__main__":
    test_force_json_wraps_plain_text()
    test_force_json_passes_valid_json()
    test_atomic_save_creates_both_files()
    test_no_tmp_files_remain()
    test_sentinel_provider_fails_fast_when_model_not_loaded()
    test_resolve_collision_no_collision()
    test_resolve_collision_overwrite()
    test_resolve_collision_skip()
    test_resolve_collision_author_suffix()
    test_sentinel_switch_lens_fails_fast_when_model_not_loaded()
    test_sentinel_offload_to_ram_fails_fast_when_model_not_loaded()
    print("\nAll tests passed.")
