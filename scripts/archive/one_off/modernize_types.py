#!/usr/bin/env python3
"""
Type Hint Modernization Script

Converts legacy type hints to Python 3.10+ native syntax:
- Optional[X] -> X | None
- List[X] -> list[X]
- Dict[X, Y] -> dict[X, Y]
- Set[X] -> set[X]
- Tuple[X, Y] -> tuple[X, Y]
"""

import re
import sys
from pathlib import Path


def modernize_type_hints(content: str) -> str:
    """Convert legacy type hints to native Python 3.10+ syntax."""

    # Optional[X] -> X | None
    content = re.sub(r"Optional\[([^\]]+)\]", r"\1 | None", content)

    # List[X] -> list[X]
    content = re.sub(r"List\[", r"list[", content)

    # Dict[X, Y] -> dict[X, Y]
    content = re.sub(r"Dict\[", r"dict[", content)

    # Set[X] -> set[X]
    content = re.sub(r"Set\[", r"set[", content)

    # Tuple[X, Y] -> tuple[X, Y]
    content = re.sub(r"Tuple\[", r"tuple[", content)

    # Union[X, Y] -> X | Y
    content = re.sub(r"Union\[", r"Union[", content)  # Keep Union for now

    return content


def process_file(filepath: Path) -> int:
    """Process a single file and return number of changes."""
    if filepath.suffix != ".py":
        return 0

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0

    original = content
    content = modernize_type_hints(content)

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return 1
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python modernize_types.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Not a directory: {directory}")
        sys.exit(1)

    changed = 0
    for filepath in directory.rglob("*.py"):
        # Skip test files, vendor, legacy
        if any(x in filepath.parts for x in ("tests", "vendor", "legacy", "__pycache__")):
            continue

        if process_file(filepath):
            print(f"Modernized: {filepath}")
            changed += 1

    print(f"\nTotal files changed: {changed}")


if __name__ == "__main__":
    main()
