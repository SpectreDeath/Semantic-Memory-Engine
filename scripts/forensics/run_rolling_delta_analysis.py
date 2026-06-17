from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scribe.rolling_delta import RollingDelta

DEFAULT_TARGET = (
    PROJECT_ROOT
    / "data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data/corpus/vought_baseline/project_2025_rolling_delta_results.json"
)
PURE_PROSE_DIR = PROJECT_ROOT / "data/corpus/vought_baseline/pure_prose"
OFFICIAL_DIRECTIVES_DIR = PROJECT_ROOT / "data/corpus/vought_baseline/official_directives_text"
CONTROL_AUTHORS_DIR = PROJECT_ROOT / "data/corpus/control_authors"
TEXT_SUFFIXES = {".md", ".txt"}


@dataclass(frozen=True)
class CandidateProfile:
    name: str
    register: str
    path: Path
    text: str
    word_count: int


@dataclass(frozen=True)
class AnalysisConfig:
    target_path: Path
    output_path: Path
    window_size: int
    step: int
    threshold: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SME RollingDelta over Project 2025 text.")
    parser.add_argument(
        "--target", type=Path, default=DEFAULT_TARGET, help="Target text file to analyze."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON output path.")
    parser.add_argument(
        "--window-size", type=int, default=1500, help="Rolling window size in words."
    )
    parser.add_argument("--step", type=int, default=500, help="Window step size in words.")
    parser.add_argument(
        "--threshold", type=float, default=0.25, help="Distance threshold for highlighted matches."
    )
    parser.add_argument(
        "--candidate-mode",
        choices=["all", "prose", "bureaucratic"],
        default="all",
        help="Candidate register set to load.",
    )
    parser.add_argument(
        "--contrastive-output",
        type=Path,
        default=None,
        help="Optional JSON output path for prose-vs-bureaucratic contrastive delta.",
    )
    parser.add_argument(
        "--include-full-series",
        action="store_true",
        help="Include full per-window distance series in JSON output. Default writes compact results.",
    )
    parser.add_argument(
        "--contrastive-threshold",
        type=float,
        default=-0.05,
        help="Contrastive threshold: prose_best_distance - bureaucratic_best_distance.",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)


def sanitize_key(value: str) -> str:
    value = value.replace(" ", "_").replace("-", "_")
    value = re.sub(r"[^0-9A-Za-z_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "profile"


def load_candidates(directories: dict[str, Path]) -> dict[str, CandidateProfile]:
    candidates: dict[str, CandidateProfile] = {}
    for register, directory in directories.items():
        if not directory.exists():
            logging.warning("Candidate directory not found: %s", directory)
            continue
        for path in sorted(directory.glob("*.*")):
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = load_text(path)
            words = re.findall(r"\b\w+\b", text)
            if not words:
                logging.warning("Skipping empty candidate text: %s", path)
                continue
            base_key = sanitize_key(path.stem)
            key = f"{base_key}_{register}"
            if key in candidates:
                suffix = 2
                while f"{key}_{suffix}" in candidates:
                    suffix += 1
                key = f"{key}_{suffix}"
            candidates[key] = CandidateProfile(
                name=key,
                register=register,
                path=path,
                text=text,
                word_count=len(words),
            )
    if not candidates:
        raise RuntimeError("No candidate profiles were loaded.")
    return candidates


def load_control_author_candidates(directory: Path) -> dict[str, CandidateProfile]:
    candidates: dict[str, CandidateProfile] = {}
    if not directory.exists():
        return candidates
    grouped: dict[str, list[Path]] = {}
    for path in directory.glob("*/*.*"):
        if path.suffix.lower() in TEXT_SUFFIXES:
            grouped.setdefault(path.parent.name, []).append(path)
    for author, paths in sorted(grouped.items()):
        text = "\n\n".join(load_text(path) for path in sorted(paths))
        words = re.findall(r"\b\w+\b", text)
        if not words:
            continue
        key = f"control_{sanitize_key(author)}_prose"
        if key in candidates:
            suffix = 2
            while f"{key}_{suffix}" in candidates:
                suffix += 1
            key = f"{key}_{suffix}"
        candidates[key] = CandidateProfile(
            name=key,
            register="control_prose",
            path=directory / author,
            text=text,
            word_count=len(words),
        )
    return candidates


def summarize_low_distance_windows(
    results: dict[str, Any],
    threshold: float,
    window_size: int,
) -> list[dict[str, Any]]:
    windows = results.get("windows", [])
    series = results.get("series", {})
    hits: list[dict[str, Any]] = []
    for index, start_token in enumerate(windows):
        distances = {
            candidate: values[index] for candidate, values in series.items() if index < len(values)
        }
        if not distances:
            continue
        closest_candidate, distance = min(distances.items(), key=lambda item: item[1])
        if distance < threshold:
            hits.append(
                {
                    "window_index": index,
                    "start_token": start_token,
                    "end_token_estimate": start_token + window_size,
                    "closest_candidate": closest_candidate,
                    "distance": distance,
                }
            )
    return hits


def summarize_contrastive_windows(
    results: dict[str, Any],
    threshold: float,
    window_size: int,
) -> list[dict[str, Any]]:
    windows = results.get("windows", [])
    series = results.get("series", {})
    rows: list[dict[str, Any]] = []
    for index, start_token in enumerate(windows):
        distances = {
            candidate: values[index] for candidate, values in series.items() if index < len(values)
        }
        if not distances:
            continue
        prose_candidates = {
            candidate: distance
            for candidate, distance in distances.items()
            if candidate.endswith("_prose")
        }
        bureaucratic_candidates = {
            candidate: distance
            for candidate, distance in distances.items()
            if candidate.endswith("_bureaucratic")
        }
        if not prose_candidates or not bureaucratic_candidates:
            continue
        prose_candidate, prose_distance = min(prose_candidates.items(), key=lambda item: item[1])
        bureaucratic_candidate, bureaucratic_distance = min(
            bureaucratic_candidates.items(), key=lambda item: item[1]
        )
        contrastive_score = prose_distance - bureaucratic_distance
        rows.append(
            {
                "window_index": index,
                "start_token": start_token,
                "end_token_estimate": start_token + window_size,
                "closest_prose_candidate": prose_candidate,
                "closest_prose_distance": prose_distance,
                "closest_bureaucratic_candidate": bureaucratic_candidate,
                "closest_bureaucratic_distance": bureaucratic_distance,
                "contrastive_score": contrastive_score,
                "prose_closer_than_bureaucratic": contrastive_score < threshold,
            }
        )
    return [row for row in rows if row["contrastive_score"] < threshold]


def print_summary_table(hits: list[dict[str, Any]], threshold: float) -> None:
    print()
    print(f"Rolling Delta low-distance windows below {threshold:.2f}")
    print("-" * 104)
    print(f"{'Window':>6} {'Start Token':>12} {'Closest Candidate':<58} {'Distance':>10}")
    print("-" * 104)
    if not hits:
        print("No windows fell below the configured distance threshold.")
        return
    for hit in hits:
        print(
            f"{hit['window_index']:>6} "
            f"{hit['start_token']:>12} "
            f"{hit['closest_candidate']:<58} "
            f"{hit['distance']:>10.4f}"
        )
    print("-" * 104)


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    config = AnalysisConfig(
        target_path=args.target,
        output_path=args.output,
        window_size=args.window_size,
        step=args.step,
        threshold=args.threshold,
    )

    if not config.target_path.exists():
        raise FileNotFoundError(f"Target text not found: {config.target_path}")

    target_text = load_text(config.target_path)
    target_words = re.findall(r"\b\w+\b", target_text)
    if not target_words:
        raise RuntimeError(f"Target text contains no extractable words: {config.target_path}")

    all_candidate_dirs = {
        "prose": PURE_PROSE_DIR,
        "bureaucratic": OFFICIAL_DIRECTIVES_DIR,
        "control_prose": CONTROL_AUTHORS_DIR,
    }
    candidate_dir_modes = {
        "all": all_candidate_dirs,
        "prose": {"prose": PURE_PROSE_DIR},
        "bureaucratic": {"bureaucratic": OFFICIAL_DIRECTIVES_DIR},
    }
    candidate_dirs = candidate_dir_modes[args.candidate_mode]
    candidates = load_candidates(candidate_dirs)
    if args.candidate_mode == "all":
        candidates.update(load_control_author_candidates(CONTROL_AUTHORS_DIR))
    candidate_texts = {profile.name: profile.text for profile in candidates.values()}

    logging.info("Loaded %s candidate profiles", len(candidates))
    logging.info("Target words: %s", len(target_words))
    logging.info("Running RollingDelta window_size=%s step=%s", config.window_size, config.step)

    rolling_delta = RollingDelta()
    results = rolling_delta.analyze_rolling_delta(
        target_text=target_text,
        candidates=candidate_texts,
        window_size=config.window_size,
        step=config.step,
    )

    hits = summarize_low_distance_windows(results, config.threshold, config.window_size)
    contrastive_hits = summarize_contrastive_windows(
        results,
        args.contrastive_threshold,
        config.window_size,
    )
    results_payload = (
        results
        if args.include_full_series
        else {
            "windows": results.get("windows", []),
            "volatility": results.get("volatility", {}),
            "series_count": len(results.get("series", {})),
        }
    )
    payload = {
        "config": {
            "target_path": str(config.target_path),
            "output_path": str(config.output_path),
            "window_size": config.window_size,
            "step": config.step,
            "threshold": config.threshold,
            "candidate_mode": args.candidate_mode,
        },
        "contrastive_config": {
            "threshold": args.contrastive_threshold,
            "score_definition": "closest_prose_distance - closest_bureaucratic_distance",
            "interpretation": "Negative scores mean the closest prose profile is closer than the closest bureaucratic profile.",
        },
        "target": {
            "path": str(config.target_path),
            "word_count": len(target_words),
        },
        "candidates": {
            name: {
                "register": profile.register,
                "path": str(profile.path),
                "word_count": profile.word_count,
            }
            for name, profile in candidates.items()
        },
        "threshold": config.threshold,
        "low_distance_hits": hits,
        "contrastive_low_distance_hits": contrastive_hits,
        "results": results_payload,
    }

    write_json_atomic(config.output_path, payload)
    if args.contrastive_output:
        contrastive_config = dict(payload["config"])
        contrastive_config["output_path"] = str(args.contrastive_output)
        contrastive_config["include_full_series"] = args.include_full_series
        contrastive_payload = {
            "config": contrastive_config,
            "contrastive_config": payload["contrastive_config"],
            "target": payload["target"],
            "candidates": payload["candidates"],
            "hit_count": len(contrastive_hits),
            "window_count": len(results.get("windows", [])),
            "hit_rate": (
                len(contrastive_hits) / len(results.get("windows", []))
                if results.get("windows")
                else 0.0
            ),
            "hits": contrastive_hits,
        }
        write_json_atomic(args.contrastive_output, contrastive_payload)
        print()
        print(f"Contrastive JSON output written to: {args.contrastive_output}")
    print_summary_table(hits, config.threshold)
    if args.include_full_series:
        print("Full per-window series included in JSON output.")
    else:
        print(
            "Compact JSON output written; full series omitted. Use --include-full-series to include them."
        )
    print()
    print(f"Complete JSON output written to: {config.output_path}")


if __name__ == "__main__":
    main()
