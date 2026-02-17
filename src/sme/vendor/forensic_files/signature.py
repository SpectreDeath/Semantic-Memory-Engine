import os
from typing import Dict, Any, Optional

class FileSignatureChecker:
    """
    Verifies file integrity by checking magic numbers against expected extensions.
    Optimized with __slots__ for minimal memory footprint.
    """
    __slots__ = ('magic_db',)

    def __init__(self):
        # A subset of common magic numbers (first 4-8 bytes usually sufficient)
        self.magic_db = {
            'pdf':  b'\x25\x50\x44\x46',                # %PDF
            'zip':  b'\x50\x4b\x03\x04',                # PK..
            'png':  b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', # .PNG....
            'jpg':  b'\xff\xd8\xff',                    # JPEG
            'jpeg': b'\xff\xd8\xff',                    # JPEG
            'gif':  b'\x47\x49\x46\x38',                # GIF8
            'exe':  b'\x4d\x5a',                        # MZ
            'docx': b'\x50\x4b\x03\x04',                # ZIP-based
            'xlsx': b'\x50\x4b\x03\x04',                # ZIP-based
            'sqlite': b'\x53\x51\x4c\x69\x74\x65\x20\x66\x6f\x72\x6d\x61\x74\x20\x33', # SQLite format 3
        }

    def verify(self, file_path: str) -> Dict[str, Any]:
        """Reads the first 32 bytes and compares against known signatures."""
        if not os.path.exists(file_path):
            return {"error": "File not found", "status": "Error"}

        try:
            ext = file_path.split('.')[-1].lower()
            with open(file_path, 'rb') as f:
                header = f.read(32)

            expected_magic = self.magic_db.get(ext)
            if not expected_magic:
                return {
                    "status": "Skipped",
                    "message": f"No magic number baseline for extension: {ext}",
                    "header_hex": header.hex()[:16]
                }

            is_match = header.startswith(expected_magic)
            return {
                "is_match": is_match,
                "extension": ext,
                "header_hex": header.hex()[:len(expected_magic.hex())],
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

def verify_file_signature(file_path: str) -> Dict[str, Any]:
    """Standalone wrapper for file signature verification."""
    checker = FileSignatureChecker()
    return checker.verify(file_path)
