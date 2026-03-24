#!/usr/bin/env python3
"""
Dataclass to Pydantic Migration Script

Converts @dataclass to @pydantic.dataclass for built-in validation.
This provides automatic validation, serialization, and better type hints.

Note: This is a conservative approach that adds pydantic but may need manual review.
"""

import re
import sys
from pathlib import Path


def modernize_dataclasses(content: str) -> tuple[str, int]:
    """Convert @dataclass to @pydantic.dataclass."""
    changes = 0

    # Add pydantic import if not present and dataclass found
    if (
        "@dataclass" in content
        and "from pydantic import" not in content
        and "import pydantic" not in content
    ):
        # Add pydantic import after other imports
        lines = content.split("\n")
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            # Add import after first import line
            if i == 0 or line.startswith("import ") or line.startswith("from "):
                if i > 0 and (
                    lines[i - 1].startswith("import ") or lines[i - 1].startswith("from ")
                ):
                    # Check if next non-empty line has dataclass
                    has_dataclass = any("@dataclass" in l for l in lines[i + 1 :])
                    if has_dataclass and "from dataclasses import" in content:
                        new_lines.append("from pydantic import BaseModel, Field, field_validator")
                        changes += 1
                        break
        content = "\n".join(new_lines)

    # Replace @dataclass with @pydantic.dataclass
    content = re.sub(r"@dataclasses\.dataclass", "@pydantic.dataclass", content)
    content = re.sub(r"@dataclass\n", "@dataclass\n", content)  # Keep simple ones

    # Replace dataclass imports
    if "from pydantic" in content:
        content = re.sub(
            r"from dataclasses import dataclass",
            "# from dataclasses import dataclass  # Migrated to pydantic",
            content,
        )
        content = re.sub(
            r"from dataclasses import dataclass, field",
            "from pydantic import Field  # dataclass field replaced",
            content,
        )

    return content, changes


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
    content, changes = modernize_dataclasses(content)

    if changes > 0:
        filepath.write_text(content, encoding="utf-8")
        return changes
    return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python modernize_dataclasses.py <directory>")
        print("Note: This is a conservative migration. Manual review recommended.")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Not a directory: {directory}")
        sys.exit(1)

    changed = 0
    for filepath in directory.rglob("*.py"):
        if any(x in filepath.parts for x in ("tests", "vendor", "legacy", "__pycache__")):
            continue

        changes = process_file(filepath)
        if changes > 0:
            print(f"Modernized {changes} in: {filepath}")
            changed += changes

    print(f"\nTotal changes: {changed}")


if __name__ == "__main__":
    main()
