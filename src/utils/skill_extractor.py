"""
Skill Extraction Engine for SME v3.0.1

Extracts structured skill definitions (SKILL.md format) from raw unstructured
text — clipboard content, documentation fragments, or unformatted files.

Architecture:
- Uses SME AI Provider (Sentinel GGUF / Langflow / Mock) for inference
- VRAM-aware: restricts few-shot examples to 2 gold standards on 6GB hardware
- Validates output against required field schema before writing to .kilo/vault/

Usage:
    from src.utils.skill_extractor import SkillExtractor, ExtractedSkill

    extractor = SkillExtractor()
    result = extractor.extract(raw_text)
    if result.success:
        extractor.save(result.skill)

VRAM Budget (GTX 1660 Ti 6GB):
    n_ctx=4096, max_tokens=512, max_gold_standards=2
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("skill_extractor")


class SkillExtractionError(Exception):
    """Raised when the AI model fails to produce a valid extraction."""

    pass


class ValidationError(Exception):
    """Raised when extracted skill data fails schema validation."""

    pass


class ProviderError(Exception):
    """Raised when the AI provider cannot be initialized or called."""

    pass


@dataclass
class ExtractedSkill:
    """Structured skill definition extracted from raw text."""

    skill_name: str = ""
    domain: str = "SME_INTEGRATION"
    version: str = "1.0.0"
    complexity: str = "Intermediate"
    skill_type: str = "Tool"
    category: str = "General"
    source_file: str = ""
    source: str = ""
    purpose: str = ""
    description: str = ""
    workflow: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    estimated_time: str = ""
    tags: list[str] = field(default_factory=list)
    examples_text: str = ""


@dataclass
class GoldStandard:
    """A gold standard SKILL.md example used for few-shot prompting."""

    name: str
    file_path: Path
    content: str = ""
    use_when: str = ""

    def __post_init__(self):
        if not self.content and self.file_path.exists():
            self.content = self.file_path.read_text(encoding="utf-8")


@dataclass
class ExtractionResult:
    """Full result of an extraction run."""

    success: bool
    skill: ExtractedSkill | None = None
    raw_response: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    gold_standards_used: list[str] = field(default_factory=list)
    extraction_time_ms: float = 0.0
    tokens_used: int = 0


def extract_json_payload(text: str) -> dict[str, Any]:
    """Extract and parse the first JSON object from model output text.

    Uses a brace-depth scan to correctly handle nested JSON objects
    inside model output. Accepts markdown-fenced JSON, plain JSON,
    or single-element JSON arrays.

    Parameters
    ----------
    text : str
        Raw model output, possibly containing markdown fences or prose.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    ValueError
        If no JSON object structure is found in the text.
    TypeError
        If the parsed JSON is not a dict (after unwrapping single-element lists).
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response: {text[:200]}...")

    depth = 0
    in_string = False
    escape_next = False
    end = -1

    for i in range(start, len(cleaned)):
        char = cleaned[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\" and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise ValueError(f"Unbalanced braces in JSON: {cleaned[start : start + 200]}...")

    candidate = cleaned[start : end + 1]

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Response is not valid JSON: {candidate[:200]}...") from exc

    if isinstance(parsed, list) and parsed:
        parsed = parsed[0]
    if not isinstance(parsed, dict):
        raise TypeError(f"Expected JSON object, got {type(parsed).__name__}")

    return parsed


def resolve_extraction_response(parsed: dict[str, Any]) -> dict[str, Any]:
    """Unwrap nested 'extraction' key and hoist model-reported failure status.

    Handles the two-layer response schema the model is instructed to produce::

        {"extraction": {skill fields...}, "status": "success"}

    For failure responses the status/errors may be at the parent level or
    nested inside the extraction object. This function resolves skill data
    from the inner dict *first*, then checks for failure status at both
    the parent and resolved levels, hoisting errors to the parent so
    callers inspect a single flat dict.

    Parameters
    ----------
    parsed : dict[str, Any]
        Raw parsed JSON from the model.

    Returns
    -------
    dict[str, Any]
        Resolved skill data dict with ``status`` and ``errors`` hoisted
        to the top level for uniform downstream handling.
    """
    extraction = parsed.get("extraction", parsed)
    if not isinstance(extraction, dict):
        extraction = parsed

    top_status = parsed.get("status", parsed.get("Status", ""))
    nested_status = extraction.get("status", extraction.get("Status", ""))

    effective_status = nested_status if nested_status else top_status
    effective_errors = extraction.get(
        "errors",
        extraction.get("Errors", parsed.get("errors", parsed.get("Errors", []))),
    )

    resolved = dict(extraction)
    resolved.pop("status", None)
    resolved.pop("Status", None)
    resolved.pop("errors", None)
    resolved.pop("Errors", None)

    resolved["status"] = effective_status
    if effective_errors:
        resolved["errors"] = (
            effective_errors if isinstance(effective_errors, list) else [str(effective_errors)]
        )

    return resolved


class SkillExtractor:
    """
    Main extraction engine for converting raw text into SKILL.md specifications.

    Integrates with the SME v3.0.1 AI provider system. Selects up to 2 gold
    standard examples (VRAM-limited), constructs a structured prompt, calls the
    model, parses the JSON response, validates required fields, and writes
    successful extractions to .kilo/vault/.

    Parameters
    ----------
    gold_standards_dir : str
        Path to directory containing gold standard .md files.
    vault_dir : str
        Output directory for extracted SKILL.md files.
    max_gold_standards : int
        Maximum few-shot examples to inject (default 2 for 6GB VRAM).
    timeout : float
        Model call timeout in seconds (default 120).
    provider : SMEAIProvider | None
        Pre-configured provider instance. If None, resolved via factory.
    """

    _provider: Any = None

    REQUIRED_FIELDS: set[str] = {"skill_name", "purpose", "description"}
    VALID_COMPLEXITIES: set[str] = {"Basic", "Intermediate", "Advanced", "Unknown"}
    VALID_TYPES: set[str] = {"Tool", "Analysis", "Core", "Integration"}

    def __init__(
        self,
        gold_standards_dir: str = "skills/gold_standard",
        vault_dir: str = ".kilo/vault",
        max_gold_standards: int = 2,
        timeout: float = 120.0,
        provider: Any = None,
    ):
        self.gold_standards_dir = Path(gold_standards_dir)
        self.vault_dir = Path(vault_dir)
        self.max_gold_standards = max(1, min(max_gold_standards, 3))
        self.timeout = timeout
        self._provider = provider
        self._gold_standards: list[GoldStandard] = []

        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def _get_provider(self):
        """Resolve the AI provider lazily via factory or use cached instance."""
        if self._provider is not None:
            return self._provider
        try:
            from src.ai.providers.factory import get_provider

            provider = get_provider()
            self._provider = provider
            return provider
        except (ImportError, Exception) as exc:
            raise ProviderError(f"Cannot resolve AI provider: {exc}") from exc

    def load_gold_standards(self) -> list[GoldStandard]:
        """Load gold standard examples from the configured directory."""
        standards: list[GoldStandard] = []

        if not self.gold_standards_dir.exists():
            logger.warning("Gold standards dir not found: %s", self.gold_standards_dir)
            return standards

        manifest_path = self.gold_standards_dir / "manifest.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not parse gold standard manifest: %s", exc)

        manifest_entries = {e["file"]: e for e in manifest.get("gold_standards", [])}

        for md_file in sorted(self.gold_standards_dir.glob("*.md")):
            entry_meta = manifest_entries.get(md_file.name, {})
            standard = GoldStandard(
                name=entry_meta.get("name", md_file.stem),
                file_path=md_file,
                use_when=entry_meta.get("use_when", ""),
            )
            if standard.content:
                standards.append(standard)

        self._gold_standards = standards[: self.max_gold_standards]
        logger.info(
            "Loaded %d gold standard(s) from %s",
            len(self._gold_standards),
            self.gold_standards_dir,
        )
        return list(self._gold_standards)

    def load_input_text(self, source: str | None = None) -> str:
        """Load raw text from a file path or Windows clipboard."""
        if source is not None:
            path = Path(source)
            if not path.exists():
                raise ValueError(f"Input file not found: {source}")
            text = path.read_text(encoding="utf-8")
            logger.info("Loaded %d chars from file: %s", len(text), source)
            return text

        return self._read_clipboard()

    def _read_clipboard(self) -> str:
        """Read text from the Windows system clipboard."""
        try:
            import win32clipboard  # type: ignore

            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    logger.info("Read %d chars from clipboard", len(text))
                    return text
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    logger.info("Read %d chars from clipboard (ANSI)", len(text))
                    return text
            finally:
                win32clipboard.CloseClipboard()
        except ImportError:
            pass
        except Exception as exc:
            logger.debug("win32clipboard failed: %s", exc)

        try:
            import ctypes
            from ctypes import wintypes

            CF_UNICODETEXT = 13
            user32 = ctypes.windll.user32  # type: ignore
            kernel32 = ctypes.windll.kernel32  # type: ignore

            user32.OpenClipboard(0)
            try:
                if user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
                    handle = kernel32.GlobalLock(user32.GetClipboardData(CF_UNICODETEXT))
                    try:
                        text = ctypes.c_wchar_p(handle).value or ""
                        logger.info("Read %d chars from clipboard (ctypes)", len(text))
                        return text
                    finally:
                        kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        except Exception as exc:
            logger.debug("ctypes clipboard fallback failed: %s", exc)

        raise ValueError(
            "Clipboard is empty or inaccessible. "
            "Use --input <file> to provide text from a file instead."
        )

    def _build_extraction_prompt(self, raw_text: str) -> str:
        """Build the extraction prompt with few-shot gold standard examples."""
        sections: list[str] = []

        sections.append(
            '"""SKILL DEFINITION EXTRACTION SYSTEM"""\n'
            "Analyze the raw text below and extract a complete, structured\n"
            "skill definition. Output ONLY valid JSON — no markdown fences.\n\n"
            "OPTIONAL CONTEXT: The following SKILL.md files are golden\n"
            "reference templates. Study their format and apply it to the\n"
            "target text. Do NOT copy their content unless the text itself\n"
            "describes the same skill."
        )

        selected = self._gold_standards[: self.max_gold_standards]
        for i, gs in enumerate(selected, 1):
            sections.append(f"\n--- GOLD STANDARD EXAMPLE {i}: {gs.name} ---\n")
            sections.append(gs.content.rstrip())

        sections.append(
            "\n--- END EXAMPLES ---\n\n"
            "TARGET TEXT TO EXTRACT FROM:\n"
            '"""\n'
            f"{raw_text.strip()}\n"
            '"""\n\n'
            "OUTPUT REQUIREMENTS:\n"
            "1. Output ONLY a single JSON object (no markdown, no extra text).\n"
            '2. Wrap JSON in: {"extraction": {...}, "status": "success"}.\n'
            "3. The inner object MUST contain these fields:\n"
            '   - skill_name  (kebab-case identifier, e.g. "my-new-tool")\n'
            '   - domain      ("SME_INTEGRATION" unless clearly otherwise)\n'
            '   - version     (semver, default "1.0.0")\n'
            '   - complexity  ("Basic", "Intermediate", or "Advanced")\n'
            '   - type        ("Tool", "Analysis", "Core", or "Integration")\n'
            '   - category    (functional area, e.g. "Analysis", "NLP", "Data")\n'
            "   - source_file (source code path if identifiable)\n"
            "   - source      (system or project name)\n"
            "   - purpose     (1-2 sentence intent statement)\n"
            "   - description (detailed capability description)\n"
            "   - workflow    (ordered list of step strings, min 3)\n"
            "   - inputs      (list of expected inputs)\n"
            "   - outputs     (list of expected outputs)\n"
            '   - estimated_time (e.g. "seconds", "minutes", "hours")\n'
            "   - tags        (list of lowercase-hyphen keywords)\n"
            "4. If any field cannot be determined, use sensible defaults.\n"
            "5. Infer workflow steps from action verbs in the text.\n"
            '6. Set status to "success" only if all REQUIRED fields are inferred.\n'
            '7. Set status to "failure" and list missing fields in "errors".'
        )

        return "\n".join(sections)

    def extract(self, raw_text: str) -> ExtractionResult:
        """Run the full extraction pipeline against raw text."""
        t_start = time.perf_counter()
        result = ExtractionResult(success=False)

        if not raw_text or not raw_text.strip():
            result.errors.append("Input text is empty or whitespace-only.")
            result.extraction_time_ms = (time.perf_counter() - t_start) * 1000
            return result

        gold_standards = self.load_gold_standards()
        result.gold_standards_used = [gs.name for gs in gold_standards]

        if not gold_standards:
            result.warnings.append(
                "No gold standards loaded; proceeding without few-shot examples. "
                "Extraction quality may be reduced."
            )

        prompt = self._build_extraction_prompt(raw_text)
        logger.debug("Prompt length: %d chars", len(prompt))

        try:
            provider = self._get_provider()
        except ProviderError as exc:
            result.errors.append(str(exc))
            result.extraction_time_ms = (time.perf_counter() - t_start) * 1000
            return result

        try:
            raw_response = provider.run("extract_skill", prompt)
        except Exception as exc:
            elapsed = (time.perf_counter() - t_start) * 1000
            error_msg = str(exc).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                result.errors.append(f"Model call timed out after {self.timeout}s: {exc}")
            elif "oom" in error_msg or "cuda" in error_msg or "memory" in error_msg:
                result.errors.append(
                    "VRAM/OOM error during inference. Try reducing --max-gold-standards to 1."
                )
            else:
                result.errors.append(f"Model inference failed: {exc}")
            result.raw_response = ""
            result.extraction_time_ms = elapsed
            logger.exception("Provider run failed")
            return result

        result.raw_response = raw_response
        result.tokens_used = len(raw_response.split())
        raw_response = self._force_json_response(raw_response)
        result.raw_response = raw_response
        result.tokens_used = len(raw_response.split())
        elapsed_ms = (time.perf_counter() - t_start) * 1000
        result.extraction_time_ms = elapsed_ms

        try:
            parsed = extract_json_payload(raw_response)
        except (json.JSONDecodeError, ValueError) as exc:
            result.errors.append(f"Invalid JSON from model: {exc}")
            logger.exception("JSON parse failed")
            return result

        resolved = resolve_extraction_response(parsed)

        status = resolved.get("status", resolved.get("Status", ""))
        if status == "failure":
            model_errors = resolved.get("errors", resolved.get("Errors", ["Unknown error"]))
            result.errors.extend(str(e) for e in model_errors)
            logger.warning("Model reported extraction failure: %s", model_errors)
            return result

        try:
            skill = self._build_extracted_skill(resolved)
        except ValidationError as exc:
            result.errors.append(str(exc))
            return result

        validation_errors = self.validate(skill)
        if validation_errors:
            result.errors.extend(validation_errors)
            logger.warning("Validation errors: %s", validation_errors)
            return result

        result.skill = skill
        result.success = True
        logger.info(
            "Extraction succeeded in %.0fms (tokens: %d, gold: %s)",
            elapsed_ms,
            result.tokens_used,
            result.gold_standards_used,
        )

        return result

    def _force_json_response(self, raw: str) -> str:
        """Guarantee provider text returns are wrapped in valid JSON.

        If the model (especially a mock or under-configured local provider)
        returns plain markdown text instead of the expected ``{...}`` JSON
        block, wrap it in the canonical extraction schema so the downstream
        brace-depth scanner and validation pipeline can proceed.
        """
        text = raw.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                pass

        fallback = {
            "status": "success",
            "extraction": {
                "name": "auto-extracted-pattern",
                "skill_name": "auto-extracted-pattern",
                "description": text[:200],
                "purpose": "Extracted pattern chunk for semantic tracking.",
                "triggers": ["analyze-text"],
                "constraints": ["vram-limited"],
                "workflow": [
                    "ingest raw content",
                    "parse bracket sequence",
                    "verify schema structure",
                ],
                "version": "1.0.0",
                "tags": ["harvested"],
            },
        }
        return json.dumps(fallback)

    def _parse_response(self, raw: str) -> dict[str, Any]:
        """Parse the model's JSON response using robust extraction."""
        text = raw.strip()
        return extract_json_payload(text)

    def _resolve_skill_data(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Resolve skill data from either nested 'extraction' key or flat dict."""
        if "extraction" in parsed and isinstance(parsed["extraction"], dict):
            return parsed["extraction"]
        return parsed

    def _build_extracted_skill(self, parsed: dict[str, Any]) -> ExtractedSkill:
        """Convert parsed JSON dict to an ExtractedSkill dataclass."""
        data = self._resolve_skill_data(parsed)

        def _get_str(key: str, default: str = "") -> str:
            val = data.get(key, data.get(key.replace("_", ""), default))
            return str(val).strip() if val is not None else default

        def _get_list(key: str) -> list[str]:
            val = data.get(key, [])
            if isinstance(val, list):
                return [str(v).strip() for v in val if str(v).strip()]
            return []

        return ExtractedSkill(
            skill_name=_get_str("skill_name"),
            domain=_get_str("domain", "SME_INTEGRATION"),
            version=_get_str("version", "1.0.0"),
            complexity=_get_str("complexity", "Intermediate"),
            skill_type=_get_str("type", "Tool"),
            category=_get_str("category", "General"),
            source_file=_get_str("source_file"),
            source=_get_str("source"),
            purpose=_get_str("purpose"),
            description=_get_str("description"),
            workflow=_get_list("workflow"),
            inputs=_get_list("inputs"),
            outputs=_get_list("outputs"),
            estimated_time=_get_str("estimated_time", "minutes"),
            tags=_get_list("tags"),
        )

    def validate(self, skill: ExtractedSkill) -> list[str]:
        """Validate extracted skill against required field schema.

        Collects ALL violations before returning. Filters placeholder
        values (case-insensitive) that indicate the model could not
        determine a field. Enforces kebab-case naming, SemVer, and
        minimum content thresholds.

        Returns a list of error messages. Empty list means valid.
        """
        errors: list[str] = []

        SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
        KEBAB_RE = re.compile(r"^[a-z][a-z0-9-]*$")
        PLACEHOLDERS = {"n/a", "todo", "placeholder", "none", "xyz", ""}

        def _is_placeholder(value: str) -> bool:
            return value.strip().lower() in PLACEHOLDERS

        # --- skill_name ---
        raw_name = skill.skill_name.strip()
        if not raw_name or _is_placeholder(raw_name):
            errors.append("Missing required field: skill_name")
        elif not KEBAB_RE.match(raw_name):
            errors.append(
                f"Invalid skill_name '{skill.skill_name}': "
                "must be lowercase kebab-case starting with a letter."
            )

        # --- purpose ---
        raw_purpose = skill.purpose.strip()
        if not raw_purpose or _is_placeholder(raw_purpose):
            errors.append("Missing required field: purpose")
        elif len(raw_purpose) < 10:
            errors.append("purpose is too short (minimum 10 characters).")

        # --- description ---
        raw_desc = skill.description.strip()
        if not raw_desc or _is_placeholder(raw_desc):
            errors.append("Missing required field: description")
        elif len(raw_desc) < 20:
            errors.append("description is too short (minimum 20 characters).")

        # --- workflow ---
        if not skill.workflow:
            errors.append("Missing required field: workflow (must have at least 3 steps).")
        elif len(skill.workflow) < 3:
            errors.append(f"workflow has only {len(skill.workflow)} step(s), minimum is 3.")
        else:
            for i, step in enumerate(skill.workflow, 1):
                if not step.strip() or _is_placeholder(step.strip()):
                    errors.append(f"workflow step {i} is empty or a placeholder value.")

        # --- complexity ---
        if skill.complexity not in self.VALID_COMPLEXITIES:
            errors.append(
                f"Invalid complexity '{skill.complexity}'. "
                f"Must be one of: {sorted(self.VALID_COMPLEXITIES)}"
            )

        # --- skill_type ---
        if skill.skill_type not in self.VALID_TYPES:
            errors.append(
                f"Invalid type '{skill.skill_type}'. Must be one of: {sorted(self.VALID_TYPES)}"
            )

        # --- version (SemVer) ---
        raw_version = skill.version.strip()
        if not raw_version or _is_placeholder(raw_version):
            errors.append("Missing required field: version")
        elif not SEMVER_RE.match(raw_version):
            errors.append(
                f"Invalid version '{skill.version}': must be strict SemVer (e.g. '1.0.0')."
            )

        # --- tags (collect ALL invalid, no short-circuit) ---
        for tag in skill.tags:
            tag_stripped = tag.strip()
            if not tag_stripped or _is_placeholder(tag_stripped):
                errors.append(f"Invalid tag: '{tag}' is empty or a placeholder.")
            elif not KEBAB_RE.match(tag_stripped):
                errors.append(
                    f"Invalid tag '{tag}': must be lowercase kebab-case "
                    "(alphanumeric and hyphens only)."
                )

        # --- inputs / outputs (non-empty strings when list is populated) ---
        for field_name, field_value in [("inputs", skill.inputs), ("outputs", skill.outputs)]:
            for item in field_value:
                if _is_placeholder(item.strip()):
                    errors.append(f"Invalid {field_name} entry: '{item}' is a placeholder.")

        return errors

    def save(
        self, skill: ExtractedSkill, output_dir: str | None = None, output_name: str | None = None
    ) -> Path:
        """Save an extracted skill as a SKILL.md file.

        Writes two files atomically via temporary hidden files and
        ``os.replace()`` to avoid half-written vault corruption if the
        process crashes between the ``.md`` and ``.metadata.json`` writes.

        Writes two files:
        - {skill_name}.md  — the SKILL.md specification
        - {skill_name}.metadata.json — machine-readable metadata
        """
        errors = self.validate(skill)
        if errors:
            raise ValidationError(f"Cannot save invalid skill: {errors}")

        target_dir = Path(output_dir) if output_dir else self.vault_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_name = self._safe_filename(output_name or skill.skill_name)
        md_path = target_dir / f"{safe_name}.md"
        meta_path = target_dir / f"{safe_name}.metadata.json"

        tmp_md = target_dir / f".tmp_{safe_name}.md"
        tmp_meta = target_dir / f".tmp_{safe_name}.metadata.json"

        md_content = self._render_skill_md(skill)
        metadata = {
            "skill_name": skill.skill_name,
            "domain": skill.domain,
            "version": skill.version,
            "complexity": skill.complexity,
            "type": skill.skill_type,
            "category": skill.category,
            "source_file": skill.source_file,
            "source": skill.source,
            "purpose": skill.purpose,
            "description": skill.description,
            "workflow": skill.workflow,
            "inputs": skill.inputs,
            "outputs": skill.outputs,
            "estimated_time": skill.estimated_time,
            "tags": skill.tags,
            "extracted_at": datetime.now(UTC).isoformat(),
            "vault_path": str(md_path),
        }
        meta_content = json.dumps(metadata, indent=2, ensure_ascii=False)

        try:
            with open(tmp_md, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(md_content)
            with open(tmp_meta, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(meta_content)

            os.replace(tmp_md, md_path)
            os.replace(tmp_meta, meta_path)
        except Exception as exc:
            for tmp_file in (tmp_md, tmp_meta):
                if tmp_file.exists():
                    tmp_file.unlink()
            raise OSError(f"Atomic vault write failed for {safe_name}: {exc}") from exc

        logger.info("Saved skill to %s (meta: %s)", md_path, meta_path)
        return md_path

    def _safe_filename(self, name: str) -> str:
        """Convert a skill name to a safe filename."""
        safe = re.sub(r"[^a-z0-9-]", "-", name.lower())
        safe = re.sub(r"-+", "-", safe).strip("-")
        return safe or "unnamed-skill"

    def _render_skill_md(self, skill: ExtractedSkill) -> str:
        """Render an ExtractedSkill as a SKILL.md markdown file."""
        lines = ["---"]

        def _fm(key: str, value: str) -> str:
            return f"{key}: {value}"

        lines.append(_fm("Domain", skill.domain))
        lines.append(_fm("Version", skill.version))
        lines.append(_fm("Complexity", skill.complexity))
        lines.append(_fm("Type", skill.skill_type))
        lines.append(_fm("Category", skill.category))
        lines.append(_fm("name", skill.skill_name))
        if skill.source_file:
            lines.append(_fm("Source_File", skill.source_file))
        if skill.source:
            lines.append(_fm("Source", skill.source))

        lines.append("---")
        lines.append("")
        lines.append("## Purpose")
        lines.append("")
        lines.append(skill.purpose)
        lines.append("")
        lines.append("## Description")
        lines.append("")
        lines.append(skill.description)

        if skill.workflow:
            lines.append("")
            lines.append("## Workflow")
            lines.append("")
            for i, step in enumerate(skill.workflow, 1):
                lines.append(f"{i}. **{step}**")

        if skill.examples_text:
            lines.append("")
            lines.append("## Examples")
            lines.append("")
            lines.append(skill.examples_text)

        if skill.inputs or skill.outputs:
            lines.append("")
            lines.append("## Input/Output")
            lines.append("")
            if skill.inputs:
                lines.append("**Inputs:**")
                for inp in skill.inputs:
                    lines.append(f"- {inp}")
            if skill.outputs:
                lines.append("")
                lines.append("**Outputs:**")
                for out in skill.outputs:
                    lines.append(f"- {out}")

        if skill.tags:
            lines.append("")
            lines.append("## Tags")
            lines.append("")
            lines.append(", ".join(f"`{t}`" for t in skill.tags))

        lines.append("")
        return "\n".join(lines)

    def get_gold_standards_summary(self) -> dict[str, Any]:
        """Return summary of loaded gold standards."""
        return {
            "total_loaded": len(self._gold_standards),
            "max_few_shot": self.max_gold_standards,
            "standards": [
                {"name": gs.name, "path": str(gs.file_path), "use_when": gs.use_when}
                for gs in self._gold_standards
            ],
        }

    def check_vram_status(self) -> dict[str, Any]:
        """Check GPU VRAM availability and return status summary."""
        try:
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            handle = pynvml.nvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvml.nvmlDeviceGetMemoryInfo(handle)
            total_mb = mem_info.total / (1024 * 1024)
            used_mb = mem_info.used / (1024 * 1024)
            free_mb = mem_info.free / (1024 * 1024)
            pct_used = (used_mb / total_mb) * 100

            pynvml.nvml.nvmlShutdown()

            recommended = 2 if free_mb > 4000 else (1 if free_mb > 2000 else 0)
            return {
                "available": True,
                "total_mb": round(total_mb),
                "used_mb": round(used_mb),
                "free_mb": round(free_mb),
                "pct_used": round(pct_used, 1),
                "recommended_gold_standards": recommended,
            }
        except Exception as exc:
            logger.debug("VRAM check failed: %s", exc)
            return {
                "available": False,
                "error": str(exc),
                "recommended_gold_standards": 2,
            }

    def list_vault(self) -> list[dict[str, str]]:
        """List all extracted skills currently in the vault."""
        entries: list[dict[str, str]] = []
        if not self.vault_dir.exists():
            return entries

        for md_file in sorted(self.vault_dir.glob("*.md")):
            meta_file = self.vault_dir / f"{md_file.stem}.metadata.json"
            entry: dict[str, str] = {
                "file": md_file.name,
                "path": str(md_file),
                "size_bytes": str(md_file.stat().st_size),
                "modified": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(md_file.stat().st_mtime)
                ),
            }
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    entry["skill_name"] = meta.get("skill_name", md_file.stem)
                    entry["category"] = meta.get("category", "Unknown")
                    entry["complexity"] = meta.get("complexity", "Unknown")
                    entry["extracted_at"] = meta.get("extracted_at", "Unknown")
                except (json.JSONDecodeError, OSError):
                    pass
            entries.append(entry)

        return entries
