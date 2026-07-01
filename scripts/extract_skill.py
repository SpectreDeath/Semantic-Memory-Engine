#!/usr/bin/env python3
"""
extract_skill.py — Terminal Wrapper for SME Pattern Extraction
==============================================================

Extracts structured skill definitions (SKILL.md format) from raw unstructured
text — clipboard content, documentation fragments, or unformatted files — using
the native SME v3.0.1 model.

Architecture
------------
  Raw Text (clipboard / file) -> Gold Standards (few-shot, VRAM-limited to 2)
                           -> AI Provider (Sentinel GGUF / Langflow / Mock)
                           -> JSON Output -> Validation
                           -> .kilo/vault/{skill-name}.md

Prerequisites
-------------
  - Python 3.13 (3.14 incompatible with spacy)
  - SME project installed: pip install -e .
  - AI provider configured via SME_AI_PROVIDER env var:
      sentinel  (local GGUF, GTX 1660 Ti, default)
      langflow  (remote Langflow service)
      mock      (testing/CI)
  - For clipboard: pywin32 (included in project dependencies on win32)

Usage
-----
  # Extract from clipboard:
  python scripts/extract_skill.py --clipboard

  # Extract from a file:
  python scripts/extract_skill.py --input path/to/notes.md

  # Extract with explicit options:
  python scripts/extract_skill.py --input notes.txt --max-gold 2 --verbose

  # Dry run (show output without writing to vault):
  python scripts/extract_skill.py --clipboard --dry-run

  # List previously extracted skills in vault:
  python scripts/extract_skill.py vault list

  # Check system health and VRAM:
  python scripts/extract_skill.py doctor
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: allow running as `python scripts/extract_skill.py` from repo root
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Initialize colorama for Windows ANSI support
from colorama import Fore, Style, init

init(autoreset=True)

import click

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_GOLD_DIR = str(REPO_ROOT / "skills" / "gold_standard")
DEFAULT_VAULT_DIR = str(REPO_ROOT / ".kilo" / "vault")
DEFAULT_TIMEOUT = 120.0
MAX_GOLD_DEFAULT = 2  # VRAM constraint: GTX 1660 Ti 6GB
REQUIRED_CLICK_VERSION = "8.0.0"

logger = logging.getLogger("extract_skill")

try:
    from src.utils.skill_extractor import (
        ExtractedSkill,
        ExtractionResult,
        GoldStandard,
        ProviderError,
        SkillExtractionError,
        SkillExtractor,
        ValidationError,
    )
except ImportError:
    SkillExtractor = None  # type: ignore[assignment,misc]
    SkillExtractionError = Exception  # type: ignore[misc,assignment]
    ValidationError = Exception  # type: ignore[misc,assignment]
    ProviderError = Exception  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Terminal Output Helpers
# ---------------------------------------------------------------------------
def _status_icon(success: bool) -> str:
    return (
        f"{Fore.GREEN}[PASS]{Style.RESET_ALL}" if success else f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
    )


def _warn_icon() -> str:
    return f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"


def _info_icon() -> str:
    return f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"


def _header(text: str) -> str:
    return f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}\n{Fore.CYAN}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}"


def _step(number: int, label: str) -> str:
    return f"\n{Fore.BLUE}{Style.BRIGHT}Step {number}: {label}{Style.RESET_ALL}"


def _section(text: str) -> str:
    return f"\n{Fore.MAGENTA}{Style.BRIGHT}--- {text} ---{Style.RESET_ALL}"


# ---------------------------------------------------------------------------
# Error Recovery Decorator
# ---------------------------------------------------------------------------
def _with_error_handling(f):
    """Wrap Click command with top-level exception handling."""

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            click.echo(f"\n{Fore.YELLOW}Aborted by user.{Style.RESET_ALL}")
            sys.exit(130)
        except SkillExtractionError as exc:
            click.echo(f"\n{Fore.RED}Extraction Error: {exc}{Style.RESET_ALL}")
            sys.exit(1)
        except ValidationError as exc:
            click.echo(f"\n{Fore.RED}Validation Error: {exc}{Style.RESET_ALL}")
            sys.exit(2)
        except ProviderError as exc:
            click.echo(
                f"\n{Fore.RED}Provider Error: {exc}{Style.RESET_ALL}\n"
                f"{Fore.YELLOW}Hint: Check SME_AI_PROVIDER env var and model path.{Style.RESET_ALL}"
            )
            sys.exit(3)
        except ValueError as exc:
            click.echo(f"\n{Fore.RED}Input Error: {exc}{Style.RESET_ALL}")
            sys.exit(4)
        except Exception as exc:
            logger.exception("Unexpected error")
            click.echo(f"\n{Fore.RED}Unexpected Error: {exc}{Style.RESET_ALL}")
            if os.getenv("EXTRACT_SKILL_DEBUG"):
                raise
            sys.exit(99)

    return wrapper


# ---------------------------------------------------------------------------
# Shared Context Object
# ---------------------------------------------------------------------------
class ExtractionContext:
    """Holds shared state across extraction steps."""

    def __init__(
        self,
        gold_dir: str,
        vault_dir: str,
        max_gold: int,
        timeout: float,
        verbose: bool,
        dry_run: bool,
        provider_override: str | None,
    ):
        self.gold_dir = gold_dir
        self.vault_dir = vault_dir
        self.max_gold = max_gold
        self.timeout = timeout
        self.verbose = verbose
        self.dry_run = dry_run
        self.provider_override = provider_override
        self.extractor = None
        self.raw_text = ""
        self.result = None


def _make_context(
    gold_dir: str,
    vault_dir: str,
    max_gold: int,
    timeout: float,
    verbose: bool,
    dry_run: bool,
    provider: str | None,
) -> ExtractionContext:
    ctx = ExtractionContext(
        gold_dir=gold_dir,
        vault_dir=vault_dir,
        max_gold=max_gold,
        timeout=timeout,
        verbose=verbose,
        dry_run=dry_run,
        provider_override=provider,
    )

    # Lazy import to keep startup fast
    from src.utils.skill_extractor import SkillExtractor

    provider_instance = None
    if provider:
        try:
            provider_instance = _resolve_provider(provider)
        except Exception as exc:
            click.echo(f"{_warn_icon()} Could not pre-resolve provider '{provider}': {exc}")
            click.echo("   Provider will be resolved at extraction time.")

    ctx.extractor = SkillExtractor(
        gold_standards_dir=gold_dir,
        vault_dir=vault_dir,
        max_gold_standards=max_gold,
        timeout=timeout,
        provider=provider_instance,
    )
    return ctx


def _resolve_provider(provider_type: str):
    """Resolve and return an AI provider by name string."""
    from src.ai.providers.factory import get_provider

    os.environ.setdefault("SME_AI_PROVIDER", provider_type)
    return get_provider()


def _apply_vram_cap(max_gold: int, gold_dir: str) -> int:
    """Enforce VRAM-aware cap on max_gold few-shot examples.

    Queries GPU VRAM via ``SkillExtractor.check_vram_status()`` and
    reduces ``max_gold`` to the hardware-safe threshold if the user
    requested more than the system can handle.

    Parameters
    ----------
    max_gold : int
        User-requested maximum few-shot examples (1–3).
    gold_dir : str
        Path to gold standards directory (passed to the extractor).

    Returns
    -------
    int
        Effective max_gold after VRAM enforcement (>= 1).
    """
    try:
        from src.utils.skill_extractor import SkillExtractor

        probe = SkillExtractor.__new__(SkillExtractor)
        vram = probe.check_vram_status()
        recommended = vram.get("recommended_gold_standards", max_gold)

        if recommended < max_gold:
            logger.warning(
                "VRAM boundary enforced: user requested --max-gold=%d, "
                "but recommended_gold_standards=%d. Capping to %d.",
                max_gold,
                recommended,
                recommended,
            )
            click.echo(
                f"  {_warn_icon()} {Fore.YELLOW}VRAM cap applied: "
                f"requested {max_gold} gold standard(s), "
                f"but hardware safety threshold is {recommended}. "
                f"Enforcing --max-gold={recommended}.{Style.RESET_ALL}"
            )
            return max(recommended, 1)
    except Exception as exc:
        logger.debug("VRAM cap enforcement skipped: %s", exc)

    return max_gold


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------
@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx, verbose):
    """SME Pattern Extraction — Terminal Wrapper v3.0.1

    Extract structured skill definitions from raw text using the native
    SME model and save them as SKILL.md files to .kilo/vault/.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    provider_type = os.getenv("SME_AI_PROVIDER", "sentinel").lower()
    click.echo(f"{_info_icon()} AI Provider: {Fore.CYAN}{provider_type}{Style.RESET_ALL}")


# ---------------------------------------------------------------------------
# Main Extraction Command
# ---------------------------------------------------------------------------
@cli.command("extract")
@click.option(
    "--input",
    "-i",
    "input_path",
    type=click.Path(exists=False),
    default=None,
    help="Path to a text file containing raw skill description.",
)
@click.option(
    "--clipboard",
    "-c",
    is_flag=True,
    default=False,
    help="Read raw text from the Windows system clipboard.",
)
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
    help="Directory containing gold standard SKILL.md examples.",
)
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
    help="Output directory for extracted SKILL.md files.",
)
@click.option(
    "--max-gold",
    "-g",
    default=MAX_GOLD_DEFAULT,
    show_default=True,
    type=click.IntRange(1, 3),
    help="Max few-shot gold standards (1-3). Default 2 for 6GB VRAM.",
)
@click.option(
    "--timeout",
    "-t",
    default=DEFAULT_TIMEOUT,
    show_default=True,
    type=float,
    help="Model call timeout in seconds.",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    default=False,
    help="Run extraction but do not write files to vault.",
)
@click.option(
    "--provider",
    "-p",
    default=None,
    help="Override AI provider (sentinel/langflow/mock).",
)
@click.option(
    "--show-prompt",
    is_flag=True,
    default=False,
    help="Print the constructed prompt and exit (debug).",
)
@click.pass_context
@_with_error_handling
def extract_cmd(
    ctx,
    input_path,
    clipboard,
    gold_dir,
    vault_dir,
    max_gold,
    timeout,
    dry_run,
    provider,
    show_prompt,
):
    """Extract a skill definition from raw text (clipboard or file)."""
    verbose = ctx.obj.get("verbose", False)

    if not input_path and not clipboard:
        click.echo(
            f"{Fore.RED}Error: Provide input via --input <file> or --clipboard.{Style.RESET_ALL}"
        )
        ctx.invoke(extract_cmd.get_help(ctx))
        sys.exit(1)

    if input_path and clipboard:
        click.echo(
            f"{Fore.YELLOW}Warning: Both --input and --clipboard provided. Using --input.{Style.RESET_ALL}"
        )
        clipboard = False

    effective_max_gold = _apply_vram_cap(max_gold, gold_dir)

    if effective_max_gold != max_gold:
        click.echo(
            f"  {_warn_icon()} {Fore.YELLOW}--max-gold adjusted: "
            f"{max_gold} -> {effective_max_gold} (VRAM safety).{Style.RESET_ALL}"
        )
        max_gold = effective_max_gold

    run_context = _make_context(
        gold_dir=gold_dir,
        vault_dir=vault_dir,
        max_gold=max_gold,
        timeout=timeout,
        verbose=verbose,
        dry_run=dry_run,
        provider=provider,
    )

    click.echo(_header("SME SKILL EXTRACTION — v3.0.1"))
    click.echo(f"  Vault:    {Fore.CYAN}{vault_dir}{Style.RESET_ALL}")
    click.echo(f"  Gold Dir: {Fore.CYAN}{gold_dir}{Style.RESET_ALL}")
    click.echo(f"  Max Gold: {Fore.CYAN}{max_gold}{Style.RESET_ALL} (VRAM-limited)")
    click.echo(f"  Dry Run:  {Fore.YELLOW}{dry_run}{Style.RESET_ALL}")

    # ---- Step 1: System / VRAM check ----

    click.echo(_step(1, "System & VRAM Check"))
    click.echo(_step(1, "System & VRAM Check"))
    vram = run_context.extractor.check_vram_status()
    if vram.get("available"):
        click.echo(
            f"  {_status_icon(True)} GPU Memory: "
            f"{vram['free_mb']}MB free / {vram['total_mb']}MB total "
            f"({vram['pct_used']}% used)"
        )
        rec = vram.get("recommended_gold_standards", max_gold)
        if rec < max_gold:
            click.echo(
                f"  {_warn_icon()} VRAM low — recommended max gold: {rec} (using {max_gold})"
            )
    else:
        click.echo(f"  {_warn_icon()} Cannot read GPU VRAM: {vram.get('error', 'unknown')}")
        click.echo(f"     Using configured max: {max_gold} gold standard(s)")

    # ---- Step 2: Load gold standards ----
    click.echo(_step(2, "Loading Gold Standards"))
    standards = run_context.extractor.load_gold_standards()
    if standards:
        for gs in standards:
            click.echo(
                f"  {_status_icon(True)} {Fore.GREEN}{gs.name}{Style.RESET_ALL} "
                f"({gs.file_path.name})"
            )
            if gs.use_when:
                click.echo(f"     Use when: {gs.use_when}")
    else:
        click.echo(
            f"  {_warn_icon()} No gold standards found in {gold_dir}\n"
            f"     Extraction will proceed with zero-shot prompting."
        )

    summary = run_context.extractor.get_gold_standards_summary()
    click.echo(
        f"  {_info_icon()} Few-shot config: {summary['total_loaded']} loaded, "
        f"{summary['max_few_shot']} max injected"
    )

    # ---- Step 3: Load input text ----
    click.echo(_step(3, "Loading Input Text"))
    try:
        if clipboard:
            click.echo(f"  {_info_icon()} Reading from Windows clipboard...")
            run_context.raw_text = run_context.extractor.load_input_text(source=None)
            source_label = "clipboard"
        else:
            click.echo(f"  {_info_icon()} Reading file: {input_path}")
            run_context.raw_text = run_context.extractor.load_input_text(source=input_path)
            source_label = str(input_path)
    except ValueError as exc:
        click.echo(f"  {_status_icon(False)} {Fore.RED}{exc}{Style.RESET_ALL}")
        sys.exit(4)

    char_count = len(run_context.raw_text)
    line_count = run_context.raw_text.count("\n") + 1
    click.echo(
        f"  {_status_icon(True)} Loaded {char_count} chars, {line_count} lines "
        f"from {Fore.CYAN}{source_label}{Style.RESET_ALL}"
    )

    if not run_context.raw_text.strip():
        click.echo(
            f"  {_status_icon(False)} {Fore.RED}Input text is empty. Nothing to extract.{Style.RESET_ALL}"
        )
        sys.exit(4)

    # ---- Step 4: Build & inspect prompt (debug mode) ----
    prompt = run_context.extractor._build_extraction_prompt(run_context.raw_text)
    click.echo(f"  {_info_icon()} Prompt size: {len(prompt)} chars, ~{len(prompt.split())} tokens")

    if show_prompt:
        click.echo(_section("FULL PROMPT"))
        click.echo(prompt)
        return

    # ---- Step 5: Execute extraction ----
    click.echo(_step(4, "Executing Extraction"))
    click.echo(f"  {_info_icon()} Calling provider (timeout: {timeout}s, max_tokens: 512)...")

    provider_label = provider or os.getenv("SME_AI_PROVIDER", "sentinel")
    click.echo(f"  Provider: {Fore.CYAN}{provider_label}{Style.RESET_ALL}")

    t_model_start = time.perf_counter()
    run_context.result = run_context.extractor.extract(run_context.raw_text)
    t_model_ms = (time.perf_counter() - t_model_start) * 1000

    if run_context.result.success:
        click.echo(
            f"  {_status_icon(True)} Extraction completed in "
            f"{Fore.GREEN}{t_model_ms:.0f}ms{Style.RESET_ALL}"
        )
        if run_context.result.gold_standards_used:
            click.echo(
                f"  Gold standards used: {', '.join(run_context.result.gold_standards_used)}"
            )
        click.echo(f"  Tokens in response: {run_context.result.tokens_used}")
    else:
        click.echo(
            f"  {_status_icon(False)} Extraction failed in "
            f"{Fore.RED}{t_model_ms:.0f}ms{Style.RESET_ALL}"
        )
        if run_context.result.errors:
            click.echo("  Errors:")
            for err in run_context.result.errors[:3]:
                click.echo(f"    {Fore.RED}  - {err}{Style.RESET_ALL}")
        if run_context.result.warnings:
            click.echo("  Warnings:")
            for warn in run_context.result.warnings:
                click.echo(f"    {Fore.YELLOW}  - {warn}{Style.RESET_ALL}")
        if run_context.result.raw_response:
            click.echo("  Raw response (first 500 chars):")
            click.echo(f"    {run_context.result.raw_response[:500]}")
        if dry_run:
            click.echo(f"\n{Fore.YELLOW}[DRY RUN] Not writing to vault.{Style.RESET_ALL}")
        sys.exit(2)

    skill = run_context.result.skill
    assert skill is not None

    # ---- Step 6: Display extracted skill ----
    click.echo(_section("EXTRACTED SKILL"))
    click.echo(f"  Name:        {Fore.GREEN}{skill.skill_name}{Style.RESET_ALL}")
    click.echo(f"  Domain:      {skill.domain}")
    click.echo(f"  Version:     {skill.version}")
    click.echo(f"  Complexity:  {skill.complexity}")
    click.echo(f"  Type:        {skill.skill_type}")
    click.echo(f"  Category:    {skill.category}")
    if skill.source_file:
        click.echo(f"  Source File: {skill.source_file}")
    if skill.source:
        click.echo(f"  Source:      {skill.source}")
    click.echo(f"  Purpose:     {skill.purpose[:120]}{'...' if len(skill.purpose) > 120 else ''}")
    click.echo(
        f"  Description: {skill.description[:120]}{'...' if len(skill.description) > 120 else ''}"
    )

    if skill.workflow:
        click.echo(f"  Workflow ({len(skill.workflow)} steps):")
        for i, step in enumerate(skill.workflow, 1):
            click.echo(f"    {i}. {step}")

    if skill.inputs:
        click.echo(f"  Inputs: {', '.join(skill.inputs[:5])}")
    if skill.outputs:
        click.echo(f"  Outputs: {', '.join(skill.outputs[:5])}")
    if skill.tags:
        click.echo(f"  Tags: {', '.join(f'#{t}' for t in skill.tags[:8])}")

    # ---- Step 7: Write to vault ----
    click.echo(_step(5, "Writing to Vault"))

    if dry_run:
        click.echo(f"  {_warn_icon()} {Fore.YELLOW}DRY RUN — skipping write.{Style.RESET_ALL}")
        click.echo(
            f"  Would write to: {Fore.CYAN}{vault_dir}/{skill.skill_name}.md{Style.RESET_ALL}"
        )
    else:
        try:
            written_path = run_context.extractor.save(skill, output_dir=vault_dir)
            click.echo(f"  {_status_icon(True)} {Fore.GREEN}SKILL.md written:{Style.RESET_ALL}")
            click.echo(f"    {written_path}")
            meta_path = written_path.with_suffix(".metadata.json")
            click.echo(f"    {meta_path}")
            click.echo(f"  Size: {written_path.stat().st_size} bytes")
        except ValidationError as exc:
            click.echo(
                f"  {_status_icon(False)} {Fore.RED}Save failed (validation): {exc}{Style.RESET_ALL}"
            )
            sys.exit(2)
        except OSError as exc:
            click.echo(
                f"  {_status_icon(False)} {Fore.RED}IO Error writing to vault: {exc}{Style.RESET_ALL}"
            )
            sys.exit(5)

    # ---- Summary ----
    total_time = t_model_ms
    click.echo(_header("EXTRACTION COMPLETE"))
    click.echo(f"  Status:      {Fore.GREEN}SUCCESS{Style.RESET_ALL}")
    click.echo(f"  Skill Name:  {Fore.GREEN}{skill.skill_name}{Style.RESET_ALL}")
    click.echo(f"  Inference:   {total_time:.0f}ms")
    click.echo(f"  Output:      {vault_dir}/{skill.skill_name}.md")
    click.echo(f"  Gold stds:   {run_context.result.gold_standards_used}")
    click.echo()


# ---------------------------------------------------------------------------
# Vault management sub-command
# ---------------------------------------------------------------------------
@cli.group("vault")
def vault_group():
    """Manage the .kilo/vault/ skill store."""

    pass


@vault_group.command("list")
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
    help="Path to vault directory.",
)
@click.pass_context
@_with_error_handling
def vault_list_cmd(ctx, vault_dir):
    """List all extracted skills in the vault."""
    from src.utils.skill_extractor import SkillExtractor

    extractor = SkillExtractor(vault_dir=vault_dir)
    entries = extractor.list_vault()

    click.echo(_header("VAULT CONTENTS"))
    click.echo(f"  Directory: {Fore.CYAN}{vault_dir}{Style.RESET_ALL}")

    if not entries:
        click.echo(f"  {_warn_icon()} Vault is empty. Run 'extract' to add skills.")
        return

    click.echo(f"  {_info_icon()} {len(entries)} skill(s) stored:\n")
    for entry in entries:
        name = entry.get("skill_name", entry["file"])
        cat = entry.get("category", "?")
        comp = entry.get("complexity", "?")
        size = entry.get("size_bytes", "?")
        modified = entry.get("modified", "?")
        click.echo(
            f"  {Fore.GREEN}{name}{Style.RESET_ALL}\n"
            f"    Category: {cat} | Complexity: {comp} | "
            f"Size: {size}B | Modified: {modified}"
        )
    click.echo()


@vault_group.command("show")
@click.argument("skill_name")
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
    help="Path to vault directory.",
)
@click.pass_context
@_with_error_handling
def vault_show_cmd(ctx, skill_name, vault_dir):
    """Show the full content of an extracted skill."""
    from src.utils.skill_extractor import SkillExtractor

    extractor = SkillExtractor(vault_dir=vault_dir)
    safe = extractor._safe_filename(skill_name)
    md_path = Path(vault_dir) / f"{safe}.md"

    if not md_path.exists():
        # Try direct match
        for f in Path(vault_dir).glob("*.md"):
            if f.stem == safe:
                md_path = f
                break

    if not md_path.exists():
        click.echo(f"{_status_icon(False)} Skill not found: {skill_name}")
        sys.exit(1)

    click.echo(_header(f"SKILL: {md_path.stem}"))
    click.echo(md_path.read_text(encoding="utf-8"))


@vault_group.command("sync")
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
)
@click.option(
    "--skills-dir",
    default=str(REPO_ROOT / "skills"),
    show_default=True,
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
)
@click.pass_context
@_with_error_handling
def vault_sync_cmd(ctx, vault_dir, skills_dir, dry_run):
    """Sync vault skills to the main skills/ directory."""
    vault_path = Path(vault_dir)
    skills_path = Path(skills_dir)

    if not vault_path.exists():
        click.echo(f"{_warn_icon()} Vault directory does not exist: {vault_dir}")
        return

    md_files = list(vault_path.glob("*.md"))
    if not md_files:
        click.echo(f"{_warn_icon()} Vault is empty, nothing to sync.")
        return

    click.echo(_header("VAULT → SKILLS SYNC"))
    click.echo(f"  {_info_icon()} Found {len(md_files)} skill(s) in vault")

    for md_file in md_files:
        target = skills_path / md_file.name
        if target.exists():
            click.echo(
                f"  {_warn_icon()} {md_file.name} already exists in skills/. {Style.DIM}(skipped){Style.RESET_ALL}"
            )
            continue
        if dry_run:
            click.echo(f"  {_info_icon()} Would copy {md_file.name} -> {target}")
        else:
            target.write_text(md_file.read_text(encoding="utf-8"), encoding="utf-8")
            click.echo(f"  {_status_icon(True)} Copied {md_file.name} -> skills/")

    if dry_run:
        click.echo(f"\n{Fore.YELLOW}[DRY RUN] No files were actually copied.{Style.RESET_ALL}")
    else:
        click.echo(f"\n{_status_icon(True)} Sync complete.")


# ---------------------------------------------------------------------------
# Gold standard management
# ---------------------------------------------------------------------------
@cli.group("gold")
def gold_group():
    """Manage gold standard examples for few-shot prompting."""

    pass


@gold_group.command("list")
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
)
@_with_error_handling
def gold_list_cmd(gold_dir):
    """List available gold standard examples."""
    from src.utils.skill_extractor import SkillExtractor

    extractor = SkillExtractor(gold_standards_dir=gold_dir)
    standards = extractor.load_gold_standards()

    click.echo(_header("GOLD STANDARDS"))
    click.echo(f"  Directory: {Fore.CYAN}{gold_dir}{Style.RESET_ALL}")

    if not standards:
        click.echo(f"  {_warn_icon()} No gold standards found.")
        click.echo(f"  Place SKILL.md files in {gold_dir} to add few-shot examples.")
        return

    for gs in standards:
        click.echo(
            f"  {Fore.GREEN}{gs.name}{Style.RESET_ALL}\n"
            f"    File:  {gs.file_path.name}\n"
            f"    Size:  {gs.file_path.stat().st_size} bytes\n"
            f"    When:  {gs.use_when or 'Any extraction'}"
        )
    click.echo()


@gold_group.command("add")
@click.argument("skill_file", type=click.Path(exists=True))
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
)
@click.option(
    "--use-when",
    default="",
    help="Description of when this gold standard is most useful.",
)
@_with_error_handling
def gold_add_cmd(skill_file, gold_dir, use_when):
    """Add a new gold standard SKILL.md example."""
    gold_path = Path(gold_dir)
    gold_path.mkdir(parents=True, exist_ok=True)

    source = Path(skill_file)
    import shutil

    dest = gold_path / source.name
    if dest.exists():
        if not click.confirm(f"{dest.name} already exists. Overwrite?"):
            click.echo("Aborted.")
            return

    shutil.copy2(source, dest)
    click.echo(f"  {_status_icon(True)} Gold standard added: {dest.name}")

    manifest_path = gold_path / "manifest.json"
    manifest: dict[str, Any] = {"gold_standards": []}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    for entry in manifest.get("gold_standards", []):
        if entry.get("file") == dest.name:
            entry["use_when"] = use_when
            break
    else:
        manifest.setdefault("gold_standards", []).append(
            {
                "file": dest.name,
                "name": dest.stem,
                "use_when": use_when,
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    click.echo(f"  {_info_icon()} Manifest updated: {manifest_path}")


# ---------------------------------------------------------------------------
# Doctor / Health Check Command
# ---------------------------------------------------------------------------
@cli.command("doctor")
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
)
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
)
@_with_error_handling
def doctor_cmd(gold_dir, vault_dir):
    """Run system health checks for the extraction pipeline."""
    click.echo(_header("EXTRACTION PIPELINE — DOCTOR CHECK"))

    # 1. Python version
    click.echo(f"\n{Fore.CYAN}Python Version:{Style.RESET_ALL}")
    py_ver = sys.version.split()[0]
    major, minor = py_ver.split(".")[:2]
    ok = int(major) == 3 and int(minor) == 13
    click.echo(
        f"  {_status_icon(ok)} {py_ver} "
        f"{'' if ok else Fore.YELLOW + '(requires 3.13)' + Style.RESET_ALL}"
    )

    # 2. Dependencies
    click.echo(f"\n{Fore.CYAN}Core Dependencies:{Style.RESET_ALL}")
    deps = {
        "click": "CLI framework",
        "colorama": "Terminal colors",
        "src.utils.skill_extractor": "Extraction engine",
        "src.ai.providers.factory": "AI Provider factory",
    }
    for mod, desc in deps.items():
        try:
            if mod.startswith("src."):
                __import__(mod, fromlist=[mod.split(".")[-1]])
            else:
                __import__(mod)
            available = True
        except ImportError:
            available = False
        click.echo(f"  {_status_icon(available)} {mod:<35} {desc}")

    # 3. GPU / VRAM
    click.echo(f"\n{Fore.CYAN}GPU / VRAM:{Style.RESET_ALL}")
    try:
        from src.utils.skill_extractor import SkillExtractor

        temp_extractor = SkillExtractor.__new__(SkillExtractor)
        vram = temp_extractor.check_vram_status()
        if vram.get("available"):
            click.echo(
                f"  {_status_icon(True)} {vram['total_mb']}MB total, "
                f"{vram['free_mb']}MB free ({vram['pct_used']}% used)"
            )
            click.echo(
                f"  {_info_icon()} Recommended max gold standards: "
                f"{vram.get('recommended_gold_standards', '?')}"
            )
        else:
            click.echo(f"  {_warn_icon()} Cannot read GPU: {vram.get('error', 'unknown')}")
    except Exception as exc:
        click.echo(f"  {_warn_icon()} VRAM check failed: {exc}")

    # 4. Gold standards
    click.echo(f"\n{Fore.CYAN}Gold Standards:{Style.RESET_ALL}")
    gold_path = Path(gold_dir)
    if gold_path.exists():
        md_files = list(gold_path.glob("*.md"))
        manifest = gold_path / "manifest.json"
        click.echo(f"  {_status_icon(bool(md_files))} {len(md_files)} .md file(s) in {gold_dir}")
        if manifest.exists():
            try:
                m = json.loads(manifest.read_text(encoding="utf-8"))
                max_fs = m.get("max_few_shot", "not set")
                click.echo(f"  {_info_icon()} manifest max_few_shot: {max_fs}")
            except (json.JSONDecodeError, OSError):
                click.echo(f"  {_warn_icon()} manifest.json is invalid JSON")
    else:
        click.echo(f"  {_status_icon(False)} Gold standards directory not found: {gold_dir}")
        click.echo(f"     Create it with: mkdir {gold_dir}")

    # 5. Vault
    click.echo(f"\n{Fore.CYAN}Vault:{Style.RESET_ALL}")
    vault_path = Path(vault_dir)
    if vault_path.exists():
        md_files = list(vault_path.glob("*.md"))
        click.echo(f"  {_status_icon(True)} {len(md_files)} skill(s) in {vault_dir}")
        for f in sorted(md_files)[:5]:
            size = f.stat().st_size
            click.echo(f"    - {f.name} ({size}B)")
        if len(md_files) > 5:
            click.echo(f"    ... and {len(md_files) - 5} more")
    else:
        click.echo(f"  {_info_icon()} Vault not yet created (will be created on first save).")

    # 6. Provider test
    click.echo(f"\n{Fore.CYAN}AI Provider Test:{Style.RESET_ALL}")
    provider_type = os.getenv("SME_AI_PROVIDER", "sentinel").lower()
    click.echo(f"  Configured: {Fore.CYAN}{provider_type}{Style.RESET_ALL}")
    try:
        from src.utils.skill_extractor import SkillExtractor

        temp_extractor = SkillExtractor.__new__(SkillExtractor)
        provider = temp_extractor._get_provider()
        meta = provider.get_metadata()
        click.echo(f"  {_status_icon(True)} Provider initialized: {meta}")
    except Exception as exc:
        click.echo(
            f"  {_status_icon(False)} Provider init failed: {Fore.RED}{exc}{Style.RESET_ALL}"
        )

    click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}All checks complete.{Style.RESET_ALL}\n")


# ---------------------------------------------------------------------------
# SkillsMP Live Crawl
# ---------------------------------------------------------------------------
def _skillsmp_search(
    topic: str,
    page: int = 1,
    limit: int = 10,
    api_key: str | None = None,
    sort_by: str = "stars",
) -> dict[str, Any]:
    """Query SkillsMP API for skills matching *topic*.

    Returns the parsed JSON response. Raises on network errors,
    HTTP errors, or API-reported failures.
    """
    import requests as _requests

    url = "https://skillsmp.com/api/v1/skills/search"
    params: dict[str, Any] = {
        "q": topic,
        "page": page,
        "limit": limit,
        "sortBy": sort_by,
    }
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = _requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        error = data.get("error", {})
        raise ValueError(
            f"SkillsMP API error: {error.get('message', error.get('code', 'unknown'))}"
        )
    return data


def _github_url_to_raw(github_url: str) -> str | None:
    """Convert a SkillsMP ``githubUrl`` to a raw.githubusercontent.com endpoint.

    Patterns handled
    ----------------
    * ``https://github.com/<owner>/<repo>/tree/<branch>/<path>``
    * ``https://github.com/<owner>/<repo>/blob/<branch>/<path>``

    Appends ``/SKILL.md`` so that the raw URL points at the skill manifest
    file rather than the directory listing.
    """
    github_url = github_url.strip()
    if not github_url.startswith("https://github.com/"):
        return None

    suffix = github_url[len("https://github.com/") :]
    parts = suffix.split("/")
    if len(parts) < 3:
        return None

    owner = parts[0]
    repo = parts[1]

    if len(parts) >= 4 and parts[2] in ("tree", "blob"):
        branch = parts[3]
        path_parts = parts[4:]
    else:
        branch = "main"
        path_parts = parts[2:]

    if not path_parts:
        return None

    path = "/".join(path_parts)
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md"


def _stream_github_raw(raw_url: str) -> str:
    """Fetch a single file from GitHub's raw CDN in bounded chunks.

    Uses ``stream=True`` and reads 4 KB at a time so that the caller
    never holds more than a few kilobytes in memory at once, even for
    unexpectedly large sources.
    """
    import requests as _requests

    resp = _requests.get(raw_url, stream=True, timeout=30)
    resp.raise_for_status()
    if not resp.encoding:
        resp.encoding = "utf-8"

    chunks: list[str] = []
    for chunk in resp.iter_content(chunk_size=4096, decode_unicode=True):
        if chunk:
            chunks.append(chunk)
    return "".join(chunks)


def _is_plausible_skill_md(text: str) -> bool:
    """Return True if *text* looks like a real SKILL.md, not an HTML stub."""
    if not text or len(text.strip()) < 50:
        return False
    lower = text.lower()
    return "---" in text or "## purpose" in lower or "## description" in lower


# ---------------------------------------------------------------------------
# Crawl command group
# ---------------------------------------------------------------------------
@cli.group("crawl")
def crawl_group():
    """Live keyword ingestion from SkillsMP.com."""


@crawl_group.command("fetch")
@click.option(
    "--topic",
    "-t",
    required=True,
    help="Search topic / keyword for SkillsMP discovery.",
)
@click.option(
    "--page",
    default=1,
    show_default=True,
    type=int,
    help="Results page number.",
)
@click.option(
    "--limit",
    default=10,
    show_default=True,
    type=int,
    help="Results per page (API max is 100).",
)
@click.option(
    "--api-key",
    default=None,
    envvar="SKILLSMP_API_KEY",
    help="SkillsMP API key (optional; raises rate limits).",
)
@click.option(
    "--sort-by",
    default="stars",
    show_default=True,
    type=click.Choice(["stars", "recent"]),
    help="Sort order for search results.",
)
@click.option(
    "--min-stars",
    default=0,
    show_default=True,
    type=int,
    help="Minimum stars to qualify (0 = no filter).",
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=False,
    help="Skip skills already present in vault.",
)
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
)
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
)
@click.option(
    "--max-gold",
    "-g",
    default=MAX_GOLD_DEFAULT,
    type=click.IntRange(1, 3),
)
@click.option(
    "--timeout",
    "-t",
    default=DEFAULT_TIMEOUT,
    show_default=True,
    type=float,
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
)
@click.option(
    "--provider",
    "-p",
    default=None,
)
@click.pass_context
@_with_error_handling
def crawl_fetch_cmd(
    ctx,
    topic,
    page,
    limit,
    api_key,
    sort_by,
    min_stars,
    skip_existing,
    gold_dir,
    vault_dir,
    max_gold,
    timeout,
    dry_run,
    provider,
):
    """Discover and extract skills from SkillsMP.com by keyword."""
    verbose = ctx.obj.get("verbose", False)

    effective_max_gold = _apply_vram_cap(max_gold, gold_dir)
    if effective_max_gold != max_gold:
        click.echo(
            f"  {_warn_icon()} {Fore.YELLOW}--max-gold adjusted: "
            f"{max_gold} -> {effective_max_gold} (VRAM safety).{Style.RESET_ALL}"
        )
        max_gold = effective_max_gold

    if limit > 100:
        click.echo(
            f"  {_warn_icon()} {Fore.YELLOW}Limit capped to 100 (API maximum).{Style.RESET_ALL}"
        )
        limit = 100

    click.echo(_header(f"CRAWL FETCH — topic: '{topic}'"))
    click.echo(f"  Max Gold: {Fore.CYAN}{max_gold}{Style.RESET_ALL} (VRAM-limited)")
    click.echo(f"  Dry Run:  {Fore.YELLOW}{dry_run}{Style.RESET_ALL}")

    # Step 1: Query SkillsMP
    click.echo(_step(1, "Querying SkillsMP"))
    click.echo(f"  {_info_icon()} Searching: {Fore.CYAN}{topic}{Style.RESET_ALL}")
    click.echo(f"  Page: {page} | Limit: {limit} | Sort: {sort_by}")

    try:
        api_resp = _skillsmp_search(
            topic=topic,
            page=page,
            limit=limit,
            api_key=api_key,
            sort_by=sort_by,
        )
    except Exception as exc:
        click.echo(f"  {_status_icon(False)} API query failed: {exc}")
        sys.exit(6)

    skills_data = api_resp.get("data", {}).get("skills", [])
    if not skills_data:
        click.echo(f"  {_warn_icon()} No skills found for topic '{topic}'.")
        return

    if min_stars > 0:
        skills_data = [s for s in skills_data if (s.get("stars", 0) or 0) >= min_stars]
        click.echo(f"  {_info_icon()} Filtered to {len(skills_data)} with ≥ {min_stars} stars")

    if not skills_data:
        click.echo(f"  {_warn_icon()} No skills match the minimum-stars filter.")
        return

    click.echo(f"  {_status_icon(True)} Discovered {len(skills_data)} skill(s) to process")

    # Step 2: Build extraction context
    run_context = _make_context(
        gold_dir=gold_dir,
        vault_dir=vault_dir,
        max_gold=max_gold,
        timeout=timeout,
        verbose=verbose,
        dry_run=dry_run,
        provider=provider,
    )
    run_context.extractor.load_gold_standards()

    passed = 0
    failed = 0
    skipped = 0

    for i, entry in enumerate(skills_data, 1):
        name = entry.get("name", "unknown")
        gh_url = entry.get("githubUrl", "")
        skill_url = entry.get("skillUrl", "")
        stars = entry.get("stars", 0)
        author = entry.get("author", "unknown")

        click.echo(f"\n{'─' * 40}")
        click.echo(
            f"{Fore.BLUE}[{i}/{len(skills_data)}]{Style.RESET_ALL} "
            f"{Fore.GREEN}{name}{Style.RESET_ALL} "
            f"by {Fore.CYAN}{author}{Style.RESET_ALL} "
            f"(★ {stars})"
        )
        if skill_url:
            click.echo(f"  {_info_icon()} {skill_url}")

        if not gh_url:
            click.echo(f"  {_warn_icon()} No GitHub URL in catalog entry. Skipping.")
            skipped += 1
            continue

        raw_url = _github_url_to_raw(gh_url)
        if not raw_url:
            click.echo(f"  {_warn_icon()} Cannot convert GitHub URL to raw CDN: {gh_url}")
            skipped += 1
            continue

        if skip_existing:
            safe_name = run_context.extractor._safe_filename(name)
            existing = Path(vault_dir) / f"{safe_name}.md"
            if existing.exists():
                click.echo(f"  {_warn_icon()} Already in vault. Skipping.")
                skipped += 1
                continue

        # Step 3: Stream fetch from GitHub raw CDN
        click.echo(f"  {_info_icon()} Fetching: {raw_url}")
        try:
            raw_text = _stream_github_raw(raw_url)
        except Exception as exc:
            click.echo(f"  {_status_icon(False)} Fetch failed: {exc}")
            skipped += 1
            continue

        if not _is_plausible_skill_md(raw_text):
            click.echo(f"  {_warn_icon()} Source looks incomplete or malformed. Skipping.")
            skipped += 1
            continue

        char_count = len(raw_text)
        click.echo(f"  {_status_icon(True)} Fetched {char_count} chars")

        # Step 4: Run extraction pipeline
        run_context.raw_text = raw_text
        run_context.result = run_context.extractor.extract(raw_text)

        if run_context.result.success:
            skill = run_context.result.skill
            assert skill is not None
            click.echo(
                f"  {_status_icon(True)} {Fore.GREEN}{skill.skill_name}{Style.RESET_ALL} "
                f"({skill.complexity}, {len(skill.workflow)} steps)"
            )
            if not dry_run:
                try:
                    run_context.extractor.save(skill, output_dir=vault_dir)
                    click.echo(f"  {_status_icon(True)} Saved to vault: {skill.skill_name}.md")
                except (ValidationError, OSError) as exc:
                    click.echo(f"  {_status_icon(False)} Save error: {exc}")
                    failed += 1
                    continue
            passed += 1
        else:
            click.echo(f"  {_status_icon(False)} Extraction failed:")
            for err in run_context.result.errors[:3]:
                click.echo(f"    {Fore.RED}- {err}{Style.RESET_ALL}")
            failed += 1

    click.echo(f"\n{'─' * 40}")
    click.echo(_header("CRAWL COMPLETE"))
    click.echo(f"  {_status_icon(True)} Passed:  {Fore.GREEN}{passed}{Style.RESET_ALL}")
    click.echo(f"  {_status_icon(False)} Failed:  {Fore.RED}{failed}{Style.RESET_ALL}")
    click.echo(f"  {_warn_icon()} Skipped: {Fore.YELLOW}{skipped}{Style.RESET_ALL}")
    click.echo(f"  Total:    {len(skills_data)}")
    click.echo()


# ---------------------------------------------------------------------------
# Batch extraction from directory
# ---------------------------------------------------------------------------
@cli.command("batch")
@click.argument(
    "input_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--pattern",
    "-p",
    default="*.txt",
    show_default=True,
    help="Glob pattern for input files.",
)
@click.option(
    "--gold-dir",
    default=DEFAULT_GOLD_DIR,
    show_default=True,
)
@click.option(
    "--vault-dir",
    default=DEFAULT_VAULT_DIR,
    show_default=True,
)
@click.option(
    "--max-gold",
    "-g",
    default=MAX_GOLD_DEFAULT,
    type=click.IntRange(1, 3),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
)
@click.option(
    "--provider",
    "-p",
    default=None,
)
@click.pass_context
@_with_error_handling
def batch_cmd(
    ctx,
    input_dir,
    pattern,
    gold_dir,
    vault_dir,
    max_gold,
    dry_run,
    provider,
):
    """Batch-extract skills from all matching files in a directory."""
    import glob

    verbose = ctx.obj.get("verbose", False)

    effective_max_gold = _apply_vram_cap(max_gold, gold_dir)
    if effective_max_gold != max_gold:
        click.echo(
            f"  {_warn_icon()} {Fore.YELLOW}--max-gold adjusted: "
            f"{max_gold} -> {effective_max_gold} (VRAM safety).{Style.RESET_ALL}"
        )
        max_gold = effective_max_gold

    input_path = Path(input_dir)
    files = sorted(input_path.glob(pattern))

    if not files:
        click.echo(f"{_warn_icon()} No files matching '{pattern}' found in {input_dir}")
        sys.exit(1)

    click.echo(_header(f"BATCH EXTRACTION — {len(files)} file(s)"))
    click.echo(f"  Pattern: {Fore.CYAN}{pattern}{Style.RESET_ALL}")
    click.echo(f"  Directory: {Fore.CYAN}{input_dir}{Style.RESET_ALL}")

    run_context = _make_context(
        gold_dir=gold_dir,
        vault_dir=vault_dir,
        max_gold=max_gold,
        timeout=DEFAULT_TIMEOUT,
        verbose=verbose,
        dry_run=dry_run,
        provider=provider,
    )
    run_context.extractor.load_gold_standards()

    passed = 0
    failed = 0
    skipped = 0

    for i, filepath in enumerate(files, 1):
        click.echo(f"\n{'─' * 40}")
        click.echo(
            f"{Fore.BLUE}[{i}/{len(files)}]{Style.RESET_ALL} "
            f"Processing: {Fore.CYAN}{filepath.name}{Style.RESET_ALL}"
        )

        try:
            raw = filepath.read_text(encoding="utf-8")
            if not raw.strip():
                click.echo(f"  {_warn_icon()} Empty file, skipping.")
                skipped += 1
                continue
        except OSError as exc:
            click.echo(f"  {_status_icon(False)} Read error: {exc}")
            failed += 1
            continue

        run_context.raw_text = raw
        run_context.result = run_context.extractor.extract(raw)

        if run_context.result.success:
            skill = run_context.result.skill
            assert skill is not None
            click.echo(
                f"  {_status_icon(True)} {Fore.GREEN}{skill.skill_name}{Style.RESET_ALL} "
                f"({skill.complexity}, {len(skill.workflow)} steps)"
            )
            if not dry_run:
                try:
                    run_context.extractor.save(skill, output_dir=vault_dir)
                    click.echo(f"  {_status_icon(True)} Saved to vault: {skill.skill_name}.md")
                except (ValidationError, OSError) as exc:
                    click.echo(f"  {_status_icon(False)} Save error: {exc}")
                    failed += 1
                    continue
            passed += 1
        else:
            click.echo(f"  {_status_icon(False)} Extraction failed:")
            for err in run_context.result.errors[:3]:
                click.echo(f"    {Fore.RED}- {err}{Style.RESET_ALL}")
            failed += 1

    click.echo(f"\n{'─' * 40}")
    click.echo(_header("BATCH COMPLETE"))
    click.echo(f"  {_status_icon(True)} Passed:  {Fore.GREEN}{passed}{Style.RESET_ALL}")
    click.echo(f"  {_status_icon(False)} Failed:  {Fore.RED}{failed}{Style.RESET_ALL}")
    click.echo(f"  {_warn_icon()} Skipped: {Fore.YELLOW}{skipped}{Style.RESET_ALL}")
    click.echo(f"  Total:    {len(files)}")
    click.echo()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def main():
    """Entry point registered in pyproject.toml [project.scripts]."""
    cli(obj={})


if __name__ == "__main__":
    main()
