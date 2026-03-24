#!/usr/bin/env python3
"""
Remove Pydantic v1 Patches Script

Removes all pydantic.v1 monkey patches and enables native Pydantic v2.
"""

import re
import sys
from pathlib import Path


def remove_pydantic_v1_patches(content: str) -> tuple[str, int]:
    """Remove pydantic.v1 patches from a file."""
    changes = 0

    # Remove import pydantic.v1 lines
    if "import pydantic.v1" in content:
        content = re.sub(r".*import pydantic\.v1.*\n?", "", content)
        changes += 1

    if "from pydantic.v1" in content:
        content = re.sub(r".*from pydantic\.v1.*\n?", "", content)
        changes += 1

    # Remove patch functions and their calls
    # Match function definitions that start with patch or apply and contain pydantic
    content = re.sub(r"# --- PYDANTIC V1 PATCH.*?# ----+.*?\n", "", content, flags=re.DOTALL)
    if "PYDANTIC V1 PATCH" in content:
        changes += 1

    # Remove _patch_pydantic_v1() calls
    content = re.sub(r"_\w*patch\w*_\w*\(.*?\)\n?", "", content)

    return content, changes


def process_file(filepath: Path) -> int:
    """Process a single file."""
    if filepath.suffix != ".py":
        return 0

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return 0

    original = content
    content, changes = remove_pydantic_v1_patches(content)

    if changes > 0:
        filepath.write_text(content, encoding="utf-8")
        return changes
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_pydantic_patches.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    total = 0

    for filepath in directory.rglob("*.py"):
        if any(x in filepath.parts for x in ("__pycache__", "vendor", "legacy")):
            continue

        changes = process_file(filepath)
        if changes > 0:
            print(f"Cleaned {filepath}")
            total += changes

    print(f"\nTotal changes: {total}")


if __name__ == "__main__":
    main()
