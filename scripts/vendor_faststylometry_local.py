#!/usr/bin/env python3
"""
Vendor faststylometry library - local version

Creates src/sme/vendor/faststylometry/ and updates internal imports
to use the new local path. Uses only standard library (os, shutil, re).

Usage:
    python scripts/vendor_faststylometry_local.py

Place the source files (corpus.py, burrows_delta.py, en.py, probability.py)
in the project root or specify their location via SOURCE_DIR.
"""

import os
import re
import shutil
from pathlib import Path

# Configuration
SOURCE_DIR = "."  # Where to find the source files (project root by default)
VENDOR_DIR = os.path.join("src", "sme", "vendor", "faststylometry")
FILES_TO_VENDOR = ["corpus.py", "burrows_delta.py", "en.py", "probability.py"]


def ensure_package_structure():
    """Create the vendor directory structure with __init__.py files."""
    dirs_to_create = [
        os.path.join("src", "sme"),
        os.path.join("src", "sme", "vendor"),
        VENDOR_DIR,
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        init_file = os.path.join(dir_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("# Vendored package\n")
            print(f"[+] Created: {init_file}")
        else:
            print(f"[=] Exists: {init_file}")


def refactor_imports(content: str, filename: str) -> str:
    """
    Update internal imports to use relative imports within the vendor package.
    
    Transforms:
      - from faststylometry import X -> from . import X
      - from faststylometry.X import Y -> from .X import Y
      - import faststylometry -> from . import __init__ as faststylometry
    """
    updated = content
    
    # Pattern 1: from faststylometry import X -> from . import X
    updated = re.sub(
        r'from\s+faststylometry\s+import\s+([A-Za-z_][A-Za-z0-9_]*)',
        r'from . import \1',
        updated
    )
    
    # Pattern 2: from faststylometry.X import Y -> from .X import Y
    updated = re.sub(
        r'from\s+faststylometry\.(\w+)\s+import\s+(.+)',
        r'from .\1 import \2',
        updated
    )
    
    # Pattern 3: import faststylometry -> from . import __init__ as faststylometry
    updated = re.sub(
        r'^import\s+faststylometry\s*$',
        r'from . import __init__ as faststylometry',
        updated,
        flags=re.MULTILINE
    )
    
    return updated


def vendor_file(filename: str) -> bool:
    """Copy and refactor a single file."""
    source_path = os.path.join(SOURCE_DIR, filename)
    dest_path = os.path.join(VENDOR_DIR, filename)
    
    if not os.path.exists(source_path):
        print(f"[!] Warning: {filename} not found in {SOURCE_DIR}. Skipping.")
        return False
    
    # Read source
    with open(source_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Refactor imports
    patched_content = refactor_imports(content, filename)
    
    # Write to vendor directory
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(patched_content)
    
    print(f"[+] Copied and patched: {filename}")
    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("Faststylometry Vendor Script (Local Version)")
    print("=" * 60)
    print(f"\n[*] Source directory: {SOURCE_DIR}")
    print(f"[*] Target directory: {VENDOR_DIR}")
    print()
    
    # Step 1: Create package structure
    print("[*] Creating package structure...")
    ensure_package_structure()
    
    # Step 2: Vendor each file
    print("\n[*] Copying and patching files...")
    success_count = 0
    for filename in FILES_TO_VENDOR:
        if vendor_file(filename):
            success_count += 1
    
    # Summary
    print()
    print("=" * 60)
    if success_count == len(FILES_TO_VENDOR):
        print(f"[✔] Successfully vendored {success_count} files")
        print("\n[*] You can now import from:")
        print("    from src.sme.vendor.faststylometry import Corpus")
        print("    from src.sme.vendor.faststylometry.burrows_delta import BurrowsDelta")
    else:
        print(f"[!] Vendored {success_count}/{len(FILES_TO_VENDOR)} files")
        print("[!] Some files were not found. Check the source directory.")
    print("=" * 60)


if __name__ == "__main__":
    main()
