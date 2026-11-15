"""Automated ecosystem contract tests for SME extensions, skills, and docs."""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
from pathlib import Path

import yaml
from jsonschema import validate

from gateway.extension_manager import (
    FORBIDDEN_BUILTINS,
    MANIFEST_SCHEMA,
    ExtensionManager,
)
from src.core.plugin_base import BasePlugin

SME_ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS_ROOT = SME_ROOT / "extensions"
SKILLS_ROOT = SME_ROOT / "skills"
AGENT_SKILLS_ROOT = SME_ROOT / ".agent" / "skills"
DOCS_ROOT = SME_ROOT / "docs"

LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
FENCED_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
BLOCK_MATH_RE = re.compile(r"\$\$[\s\S]*?\$\$", re.MULTILINE)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$[^$\n]+\$(?!\$)")
INLINE_CODE_RE = re.compile(r"(?<!\[)`[^`\n]+`(?!\])")


class _SilentDummyDB:
    def execute(self, sql: str, params: tuple = ()) -> None:
        return None

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        return []


class _SilentDummyHSM:
    def sign(self, data: bytes) -> bytes:
        return b"sig"

    def sign_evidence(self, **kwargs) -> str:
        return "sig"

    def verify(self, data: bytes, sig: bytes) -> bool:
        return True


class _SilentDummyNexusAPI:
    def __init__(self) -> None:
        self._db = _SilentDummyDB()
        self._hsm = _SilentDummyHSM()

    @property
    def nexus(self) -> _SilentDummyDB:
        return self._db

    def get_hsm(self) -> _SilentDummyHSM:
        return self._hsm

    def register_provenance(self, *args, **kwargs) -> None:
        return None


def _iter_extension_dirs() -> list[Path]:
    return [
        p
        for p in sorted(EXTENSIONS_ROOT.iterdir())
        if p.is_dir() and not p.name.startswith(("_", "."))
    ]


def _split_frontmatter(text: str) -> tuple[dict, str]:
    assert text.startswith("---"), "Missing YAML frontmatter start delimiter"
    lines = text.splitlines(keepends=True)
    end_idx = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end_idx is not None, "Unclosed YAML frontmatter delimiter"
    parsed = yaml.safe_load("".join(lines[1:end_idx]))
    assert isinstance(parsed, dict), "Frontmatter must deserialize to a mapping"
    return parsed, "".join(lines[end_idx + 1 :])


def _find_broken_relative_links(md_path: Path, text: str) -> list[str]:
    cleaned = FENCED_RE.sub("", text)
    cleaned = BLOCK_MATH_RE.sub("", cleaned)
    cleaned = INLINE_MATH_RE.sub("", cleaned)
    cleaned = INLINE_CODE_RE.sub("", cleaned)
    broken: list[str] = []
    for label, target in LINK_RE.findall(cleaned):
        t = target.strip().strip("<>")
        if not t or t.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if t.startswith("file:///"):
            broken.append(f"absolute_file_uri:[{label}]({t})")
            continue
        clean_target = t.split("#", 1)[0].split("?", 1)[0].strip()
        if clean_target and not (md_path.parent / clean_target).resolve().exists():
            broken.append(f"missing_target:[{label}]({t})")
    return broken


def test_all_extension_manifests_valid_and_unique() -> None:
    """Verify every extension has a unique valid manifest conforming to MANIFEST_SCHEMA."""
    plugin_ids: dict[str, str] = {}
    plugin_names: dict[str, str] = {}
    ext_dirs = _iter_extension_dirs()
    assert ext_dirs, "No extensions discovered"

    for pdir in ext_dirs:
        mpath = pdir / "manifest.json"
        assert mpath.exists(), f"Missing manifest.json in {pdir.name}"
        data = json.loads(mpath.read_text(encoding="utf-8"))
        validate(instance=data, schema=MANIFEST_SCHEMA)
        pid = data["plugin_id"]
        pname = data["name"]
        assert pid not in plugin_ids, f"Duplicate plugin_id {pid}: {plugin_ids[pid]} & {pdir.name}"
        assert pname not in plugin_names, f"Duplicate plugin name {pname}: {plugin_names[pname]} & {pdir.name}"
        plugin_ids[pid] = pdir.name
        plugin_names[pname] = pdir.name


def test_all_extensions_load_strict_and_subclass_base_plugin() -> None:
    """Verify all extensions load cleanly under strict_mode=True and subclass BasePlugin."""
    os.environ.setdefault("SME_GATEWAY_SECRET", "test_secret_key_12345678901234567890")
    os.environ.setdefault("SME_ADMIN_PASSWORD", "test_admin_password")
    os.environ.setdefault("SME_HSM_SECRET", "test_hsm_secret_key")

    mgr = ExtensionManager(nexus_api=_SilentDummyNexusAPI(), strict_mode=True)
    asyncio.run(mgr.discover_and_load())

    ext_dirs = _iter_extension_dirs()
    missing = [p.name for p in ext_dirs if p.name not in mgr.extensions]
    assert not missing, f"Extensions failed to load under strict_mode=True: {missing}"

    non_base = [
        f"{pid} ({type(rec['instance']).__name__})"
        for pid, rec in mgr.extensions.items()
        if not isinstance(rec["instance"], BasePlugin)
    ]
    assert not non_base, f"Extensions not subclassing BasePlugin: {non_base}"


def test_extensions_ast_no_bare_excepts_or_forbidden_builtins() -> None:
    """Verify extensions contain zero bare excepts and zero FORBIDDEN_BUILTINS calls."""
    violations: list[str] = []
    for pdir in _iter_extension_dirs():
        for pyf in sorted(pdir.rglob("*.py")):
            if "__pycache__" in pyf.parts or pyf.name.startswith("test_"):
                continue
            tree = ast.parse(pyf.read_text(encoding="utf-8", errors="replace"), filename=str(pyf))
            rel = pyf.relative_to(SME_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    violations.append(f"{rel}:{node.lineno}: bare except:")
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in FORBIDDEN_BUILTINS:
                        violations.append(f"{rel}:{node.lineno}: forbidden builtin {node.func.id}()")
    assert not violations, f"Extension AST hygiene violations: {violations}"


def test_skills_frontmatter_unique_names_and_existing_source_files() -> None:
    """Verify all skills/*.md and .agent/skills/*/SKILL.md parse cleanly with valid source_files and links."""
    names_seen: dict[str, str] = {}
    errors: list[str] = []

    for md in sorted(SKILLS_ROOT.rglob("*.md")):
        if md.name.upper() == "README.MD":
            continue
        rel = md.relative_to(SME_ROOT).as_posix()
        txt = md.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = _split_frontmatter(txt)
        except Exception as exc:
            errors.append(f"{rel}: frontmatter error: {exc}")
            continue
        sname = str(fm.get("name") or md.stem)
        if sname in names_seen:
            errors.append(f"{rel}: duplicate skill name {sname!r} (already in {names_seen[sname]})")
        names_seen[sname] = rel
        sf = fm.get("source_file") or fm.get("Source_File")
        if sf and not (SME_ROOT / str(sf)).exists():
            errors.append(f"{rel}: missing source_file target {sf!r}")
        for bl in _find_broken_relative_links(md, txt):
            errors.append(f"{rel}: {bl}")

    for md in sorted(AGENT_SKILLS_ROOT.glob("*/SKILL.md")):
        rel = md.relative_to(SME_ROOT).as_posix()
        txt = md.read_text(encoding="utf-8", errors="replace")
        try:
            fm, _ = _split_frontmatter(txt)
        except Exception as exc:
            errors.append(f"{rel}: frontmatter error: {exc}")
            continue
        assert fm.get("name") == md.parent.name, f"{rel}: name mismatch {fm.get('name')} != {md.parent.name}"
        for bl in _find_broken_relative_links(md, txt):
            errors.append(f"{rel}: {bl}")

    assert not errors, f"Skill hygiene violations: {errors}"


def test_docs_portable_relative_links() -> None:
    """Verify documentation files do not contain broken or non-portable file:/// links."""
    broken: list[str] = []
    candidates = [SME_ROOT / "README.md", SME_ROOT / "AGENTS.md", *sorted(DOCS_ROOT.rglob("*.md"))]
    for doc in candidates:
        if not doc.exists():
            continue
        rel = doc.relative_to(SME_ROOT).as_posix()
        for err in _find_broken_relative_links(doc, doc.read_text(encoding="utf-8", errors="replace")):
            broken.append(f"{rel}: {err}")
    assert not broken, f"Documentation link violations: {broken}"
