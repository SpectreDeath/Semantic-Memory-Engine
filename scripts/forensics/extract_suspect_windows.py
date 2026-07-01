from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = (
    PROJECT_ROOT
    / "data/corpus/vought_baseline/project_2025_text/2025_MandateForLeadership_FULL.txt"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "data/corpus/vought_baseline/project_2025_text/suspect_windows_18_29_extracted.txt"
)
DEFAULT_START_TOKEN = 9000
DEFAULT_END_TOKEN = 16000
WORD_RE = re.compile(r"\b\w+\b")
PAGE_MARKER_RE = re.compile(r"^\s*[—–-]?\s*\d+\s*[—–-]?\s*$")
UPPER_HEADER_RE = re.compile(r"^[A-Z0-9][A-Z0-9 ,’'&:;()/.-]{7,120}$")
CHAPTER_HEADER_RE = re.compile(r"^Chapter\s+\d+", re.IGNORECASE)
SECTION_PREFIXES = (
    "Chapter ",
    "Part ",
    "Section ",
    "Title ",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract suspect rolling-delta windows from Project 2025 text."
    )
    parser.add_argument(
        "--target", type=Path, default=DEFAULT_TARGET, help="Full Project 2025 text file."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Artifact output path.")
    parser.add_argument(
        "--start-token",
        type=int,
        default=DEFAULT_START_TOKEN,
        help="Inclusive start word-token index.",
    )
    parser.add_argument(
        "--end-token", type=int, default=DEFAULT_END_TOKEN, help="Exclusive end word-token index."
    )
    parser.add_argument(
        "--print-extracted", action="store_true", help="Print the extracted text block to stdout."
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def token_span(text: str, start_token: int, end_token: int) -> tuple[int, int]:
    if start_token < 0:
        raise ValueError("start_token must be non-negative")
    if end_token <= start_token:
        raise ValueError("end_token must be greater than start_token")

    matches = list(WORD_RE.finditer(text))
    if len(matches) <= end_token:
        raise ValueError(
            f"Target text has {len(matches)} tokens; end_token {end_token} is out of range"
        )

    return matches[start_token].start(), matches[end_token - 1].end()


def is_header_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) < 8 or len(stripped) > 140:
        return False
    if PAGE_MARKER_RE.match(stripped):
        return False
    if CHAPTER_HEADER_RE.match(stripped):
        return True
    if stripped.startswith(SECTION_PREFIXES) and stripped[:1].isupper():
        return True
    if not UPPER_HEADER_RE.match(stripped):
        return False
    alpha_count = sum(1 for char in stripped if char.isalpha())
    upper_count = sum(1 for char in stripped if char.isupper())
    punctuation_count = sum(1 for char in stripped if not char.isalnum() and not char.isspace())
    alpha_ratio = alpha_count / max(len(stripped), 1)
    upper_ratio = upper_count / max(alpha_count, 1)
    return alpha_ratio >= 0.72 and upper_ratio >= 0.82 and punctuation_count <= 8


def extract_headers(text_block: str) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for line in text_block.splitlines():
        if is_header_line(line):
            header = " ".join(line.strip().split())
            if header not in seen:
                seen.add(header)
                headers.append(header)
    return headers


def console_safe(text: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def main() -> None:
    args = parse_args()
    full_text = read_text(args.target)
    start_offset, end_offset = token_span(full_text, args.start_token, args.end_token)
    extracted = full_text[start_offset:end_offset].strip()
    headers = extract_headers(extracted)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(extracted + "\n", encoding="utf-8")

    print()
    print("=" * 80)
    print("SUSPECT WINDOWS 18-29 EXTRACT")
    print("=" * 80)
    print(f"Target file: {args.target}")
    print(f"Token range: {args.start_token} inclusive to {args.end_token} exclusive")
    print(f"Extracted characters: {len(extracted)}")
    print(f"Output artifact: {args.output}")
    print()
    print("Detected section headers / chapter titles:")
    print("-" * 80)
    if headers:
        for header in headers:
            print(f"- {header}")
    else:
        print("- No major section headers detected in this token slice.")
    print()
    if args.print_extracted:
        print("=" * 80)
        print("ISOLATED TEXT BLOCK")
        print("=" * 80)
        print(console_safe(extracted))
        print()
    print("=" * 80)
    print("Artifact written successfully")
    print("=" * 80)


if __name__ == "__main__":
    main()
