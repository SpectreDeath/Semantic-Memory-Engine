from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PROJECT_ROOT))

from src.scribe.engine import ScribeEngine
from src.scribe.rolling_delta import RollingDelta

DEFAULT_TARGET = (
    PROJECT_ROOT
    / "data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/corpus/vought_baseline/validation_layers"
PURE_PROSE_DIR = PROJECT_ROOT / "data/corpus/vought_baseline/pure_prose"
OFFICIAL_DIRECTIVES_DIR = PROJECT_ROOT / "data/corpus/vought_baseline/official_directives_text"
CONTROL_AUTHORS_DIR = PROJECT_ROOT / "data/corpus/control_authors"
TEXT_SUFFIXES = {".md", ".txt"}
SUSPECT_WINDOW_INDICES = set(range(18, 30))
ADJECTIVE_TAGS = {"JJ", "JJR", "JJS"}
ADVERB_TAGS = {"RB", "RBR", "RBS"}
KNOWN_MODIFIERS = {
    "fundamentally",
    "weaponized",
    "corrupt",
    "pervasive",
    "hollow",
    "radical",
    "woke",
    "constitutional",
    "accountable",
    "sovereign",
    "bureaucratic",
    "administrative",
    "elite",
    "ideological",
    "institutional",
    "activist",
}
MODIFIER_BLACKLIST = {
    "t",
    "didn",
    "other",
    "congress",
    "president",
    "administration",
    "government",
    "people",
    "american",
}


@dataclass(frozen=True)
class CandidateProfile:
    name: str
    register: str
    path: Path
    text: str
    word_count: int
    author: str | None = None


def sanitize_key(value: str) -> str:
    value = value.replace(" ", "_").replace("-", "_")
    value = re.sub(r"[^0-9A-Za-z_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "profile"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)


def load_candidates_from_dir(
    directory: Path, register: str, author: str | None = None
) -> dict[str, CandidateProfile]:
    candidates: dict[str, CandidateProfile] = {}
    if not directory.exists():
        return candidates
    for path in sorted(directory.glob("*.*")):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = load_text(path)
        words = re.findall(r"\b\w+\b", text)
        if not words:
            continue
        base_key = sanitize_key(path.stem if author is None else author)
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
            author=author,
        )
    return candidates


def load_control_authors(directory: Path) -> dict[str, CandidateProfile]:
    candidates: dict[str, CandidateProfile] = {}
    if not directory.exists():
        return candidates
    grouped: dict[str, list[Path]] = defaultdict(list)
    for path in directory.glob("*/*.*"):
        if path.suffix.lower() in TEXT_SUFFIXES:
            grouped[path.parent.name].append(path)
    for author, paths in sorted(grouped.items()):
        texts = [load_text(path) for path in sorted(paths)]
        text = "\n\n".join(texts)
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
            author=author,
        )
    return candidates


def load_all_candidates(include_controls: bool) -> tuple[dict[str, CandidateProfile], list[str]]:
    candidates: dict[str, CandidateProfile] = {}
    warnings: list[str] = []
    for profile in load_candidates_from_dir(PURE_PROSE_DIR, "prose").values():
        candidates[profile.name] = profile
    for profile in load_candidates_from_dir(OFFICIAL_DIRECTIVES_DIR, "bureaucratic").values():
        candidates[profile.name] = profile
    if include_controls:
        control_candidates = load_control_authors(CONTROL_AUTHORS_DIR)
        if not control_candidates:
            warnings.append(
                f"No control-author files found under {CONTROL_AUTHORS_DIR.relative_to(PROJECT_ROOT)}"
            )
        for profile in control_candidates.values():
            candidates[profile.name] = profile
    if not candidates:
        raise RuntimeError("No candidate profiles were loaded.")
    return candidates, warnings


def moving_average(values: list[float], window: int) -> list[float]:
    if window <= 1:
        return values
    kernel = np.ones(window, dtype=float) / window
    padded = np.pad(values, (window // 2, window // 2), mode="edge")
    smoothed = np.convolve(padded, kernel, mode="valid")
    return [float(value) for value in smoothed[: len(values)]]


def generate_word_windows(text: str, window_size: int, step: int) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"\b\w+\b", text))
    total = len(matches)
    if total < window_size:
        return [(0, text)]
    windows: list[tuple[int, str]] = []
    current = 0
    while current + window_size <= total:
        start = matches[current].start()
        end = matches[current + window_size - 1].end()
        windows.append((current, text[start:end]))
        current += step
    return windows


def tokenize_words(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"\b\w+\b", text)]


def pos_tag_lightweight(tokens: list[str]) -> list[tuple[str, str]]:
    try:
        import nltk
        from nltk import pos_tag

        try:
            nltk.data.find("taggers/averaged_perceptron_tagger_eng")
        except LookupError:
            try:
                nltk.data.find("taggers/averaged_perceptron_tagger")
            except LookupError:
                nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        return [(token, tag) for token, tag in pos_tag(tokens)]
    except Exception:
        return [(token, "UNKNOWN") for token in tokens]


def extract_modifiers(text: str) -> Counter[str]:
    tokens = tokenize_words(text)
    tagged = pos_tag_lightweight(tokens)
    modifiers: list[str] = []
    for token, tag in tagged:
        if tag in ADJECTIVE_TAGS or tag in ADVERB_TAGS:
            modifiers.append(token)
    if not modifiers:
        modifiers = [token for token in tokens if token in KNOWN_MODIFIERS]
    filtered: list[str] = []
    for token in modifiers:
        if len(token) <= 1 or "_" in token or token in MODIFIER_BLACKLIST:
            continue
        filtered.append(token)
    for token in KNOWN_MODIFIERS:
        if token not in filtered and token in set(tokens):
            filtered.append(token)
    return Counter(filtered)


def log_likelihood_ratio(count_a: int, total_a: int, count_b: int, total_b: int) -> float:
    total = total_a + total_b
    if total == 0:
        return 0.0
    p = (count_a + count_b) / total
    p1 = count_a / max(total_a, 1)
    p2 = count_b / max(total_b, 1)
    ll = 0.0
    for observed, expected in (
        (count_a, p * total_a),
        (total_a - count_a, (1 - p) * total_a),
        (count_b, p * total_b),
        (total_b - count_b, (1 - p) * total_b),
    ):
        if observed > 0:
            ll += observed * math.log(observed / max(expected, 1e-12))
    direction = 1.0 if p1 > p2 else -1.0
    return direction * float(2 * ll)


def compute_modifier_keyness(
    vought_text: str,
    background_texts: list[str],
    window_texts: dict[int, str],
) -> dict[str, Any]:
    vought_counter = extract_modifiers(vought_text)
    background_counter: Counter[str] = Counter()
    background_total = 0
    for text in background_texts:
        background_counter.update(extract_modifiers(text))
        background_total += len(tokenize_words(text))
    vought_total = len(tokenize_words(vought_text))
    vocabulary = set(vought_counter) | set(background_counter) | KNOWN_MODIFIERS
    ranked: list[dict[str, Any]] = []
    for modifier in sorted(vocabulary):
        count_v = vought_counter[modifier]
        count_b = background_counter[modifier]
        llr = log_likelihood_ratio(count_v, vought_total, count_b, background_total)
        if llr == 0.0 and count_v == 0 and count_b == 0:
            continue
        ranked.append(
            {
                "modifier": modifier,
                "vought_count": count_v,
                "vought_per_1000_words": count_v / max(vought_total, 1) * 1000,
                "background_count": count_b,
                "background_per_1000_words": count_b / max(background_total, 1) * 1000,
                "log_likelihood_ratio": llr,
            }
        )
    ranked.sort(key=lambda item: item["log_likelihood_ratio"], reverse=True)
    window_hits: list[dict[str, Any]] = []
    for window_index, text in sorted(window_texts.items()):
        counter = extract_modifiers(text)
        total = len(tokenize_words(text))
        present = sorted(
            {item["modifier"] for item in ranked[:25] if counter[item["modifier"]] > 0}
        )
        window_hits.append(
            {
                "window_index": window_index,
                "modifier_count": sum(counter.values()),
                "modifier_per_1000_words": sum(counter.values()) / max(total, 1) * 1000,
                "top_ranked_present": present,
            }
        )
    return {
        "vought_total_words": vought_total,
        "background_total_words": background_total,
        "ranked_modifiers": ranked[:50],
        "window_hits": window_hits,
    }


def summarize_micro_features(
    window_features: dict[int, dict[str, float]],
    candidate_features: dict[str, dict[str, float]],
) -> dict[str, Any]:
    suspect_indices = [index for index in window_features if index in SUSPECT_WINDOW_INDICES]
    adjacent_indices = [
        index for index in window_features if 13 <= index <= 17 or 30 <= index <= 34
    ]
    feature_names = sorted(next(iter(window_features.values())).keys())
    rows: list[dict[str, Any]] = []
    for feature in feature_names:
        suspect_values = [window_features[index][feature] for index in suspect_indices]
        adjacent_values = [window_features[index][feature] for index in adjacent_indices]
        suspect_mean = float(np.mean(suspect_values)) if suspect_values else 0.0
        adjacent_mean = float(np.mean(adjacent_values)) if adjacent_values else 0.0
        delta = suspect_mean - adjacent_mean
        rows.append(
            {
                "feature": feature,
                "suspect_mean": suspect_mean,
                "adjacent_mean": adjacent_mean,
                "delta": delta,
                "candidate_values": {
                    name: values[feature] for name, values in candidate_features.items()
                },
            }
        )
    rows.sort(key=lambda item: abs(item["delta"]), reverse=True)
    return {
        "suspect_window_indices": suspect_indices,
        "adjacent_window_indices": adjacent_indices,
        "feature_rows": rows,
    }


def window_start(window: Any) -> float:
    if isinstance(window, tuple):
        return float(window[0])
    return float(window)


def suspect_window_span(results: dict[str, Any]) -> tuple[float, float]:
    windows = results.get("windows", [])
    if not windows:
        return 0.0, 0.0
    if len(windows) > 30:
        return window_start(windows[18]), window_start(windows[30])
    if len(windows) > 18:
        return window_start(windows[18]), window_start(windows[-1]) + 1.0
    return 0.0, 0.0


def build_plot(
    results: dict[str, Any],
    output_path: Path,
    vought_prose: str,
    vought_bureaucratic: str,
    sma_window: int,
) -> None:
    windows = results.get("windows", [])
    series = results.get("series", {})
    if not windows or vought_prose not in series or vought_bureaucratic not in series:
        raise RuntimeError("Requested plot candidates are missing from rolling results.")
    x = np.arange(len(windows))
    prose = series[vought_prose]
    bureaucratic = series[vought_bureaucratic]
    plt.figure(figsize=(14, 7))
    plt.plot(x, prose, alpha=0.35, label=f"{vought_prose} raw")
    plt.plot(x, bureaucratic, alpha=0.35, label=f"{vought_bureaucratic} raw")
    plt.plot(
        x, moving_average(prose, sma_window), linewidth=2.2, label=f"{vought_prose} SMA{sma_window}"
    )
    plt.plot(
        x,
        moving_average(bureaucratic, sma_window),
        linewidth=2.2,
        label=f"{vought_bureaucratic} SMA{sma_window}",
    )
    suspect_start, suspect_end = suspect_window_span(results)
    if suspect_end > suspect_start:
        plt.axvspan(suspect_start, suspect_end, color="orange", alpha=0.12, label="Windows 18-29")
    plt.xlabel("Window start token")
    plt.ylabel("Rolling distance")
    plt.title("Contrastive Rolling Delta: Vought Prose vs Vought Bureaucratic")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=180)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validation layers for the Vought contrastive delta framework."
    )
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--window-size", type=int, default=1500)
    parser.add_argument("--step", type=int, default=500)
    parser.add_argument("--sma-window", type=int, default=10)
    parser.add_argument("--include-controls", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--vought-prose-candidate", default="wng_processed_Renewing_American_Purpose_prose"
    )
    parser.add_argument(
        "--vought-bureaucratic-candidate",
        default="Fiscal_Year_2026_Discretionary_Budget_Request_bureaucratic",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    target_text = load_text(args.target)
    candidates, warnings = load_all_candidates(args.include_controls)
    candidate_texts = {name: profile.text for name, profile in candidates.items()}
    rolling_delta = RollingDelta()
    results = rolling_delta.analyze_rolling_delta(
        target_text, candidate_texts, args.window_size, args.step
    )
    write_json_atomic(output_dir / "validation_rolling_delta_results.json", results)

    scribe = ScribeEngine()
    windows = generate_word_windows(target_text, args.window_size, args.step)
    window_texts = dict(enumerate(text for _, text in windows))
    window_features = {
        index: scribe.extract_micro_features(text) for index, text in window_texts.items()
    }
    candidate_features = {
        name: scribe.extract_micro_features(text) for name, text in candidate_texts.items()
    }
    micro_summary = summarize_micro_features(window_features, candidate_features)
    write_json_atomic(output_dir / "validation_micro_features_summary.json", micro_summary)

    vought_profile = candidates.get(args.vought_prose_candidate)
    if not vought_profile:
        raise RuntimeError(f"Vought prose candidate not found: {args.vought_prose_candidate}")
    background_candidates = [
        profile
        for name, profile in candidates.items()
        if name not in {args.vought_prose_candidate, args.vought_bureaucratic_candidate}
    ]
    keyness = compute_modifier_keyness(
        vought_profile.text,
        [profile.text for profile in background_candidates],
        window_texts,
    )
    write_json_atomic(output_dir / "validation_modifier_keyness.json", keyness)

    plot_path = output_dir / "vought_prose_vs_bureaucratic_full_document.png"
    build_plot(
        results,
        plot_path,
        args.vought_prose_candidate,
        args.vought_bureaucratic_candidate,
        args.sma_window,
    )

    payload = {
        "warnings": warnings,
        "candidate_count": len(candidates),
        "control_author_candidates": sorted(
            name for name, profile in candidates.items() if profile.register == "control_prose"
        ),
        "micro_features": str(output_dir / "validation_micro_features_summary.json"),
        "modifier_keyness": str(output_dir / "validation_modifier_keyness.json"),
        "rolling_delta_results": str(output_dir / "validation_rolling_delta_results.json"),
        "full_document_plot": str(plot_path),
        "interpretation_guidance": {
            "strengthens_vought_hypothesis": [
                "Windows 18-29 remain closest to Vought pure prose after control authors are added.",
                "Micro-feature deltas show a coherent structural shift, not just shared policy vocabulary.",
                "Modifier keyness shows Vought-aligned rhetorical choices inside Windows 18-29.",
                "Full-document plot shows local returns toward Vought prose rather than a document-wide genre effect.",
            ],
            "weakens_vought_hypothesis": [
                "A control author beats Vought prose once public prose controls are included.",
                "Windows 18-29 do not differ materially from adjacent windows on micro-features.",
                "Key modifiers are common across institutional chapters and not concentrated in the suspect range.",
            ],
            "suggests_genre_detection": [
                "Vought prose and Vought bureaucratic profiles track together across the whole document.",
                "Control authors and institutional corpora cluster near Vought prose on the same conservative-policy register.",
                "Modifier keyness is dominated by generic conservative-policy terms rather than author-specific structural habits.",
            ],
        },
    }
    write_json_atomic(output_dir / "validation_summary.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
