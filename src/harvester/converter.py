"""
📄 The Harvester v2.1.0 — Document Converter (MarkItDown)

Purpose:
    Converts incoming PDFs, DOCX, and HTML files into cleaned Markdown
    using MarkItDown. Preserves structural elements (headings, tables)
    critical for rhythmic and rhetorical analysis.

    v2.1.0 Finalization:
        • Entity redaction — strips proper names, emails, URLs before
          text reaches the pipeline or laboratory.db
        • OOM guard — rejects files larger than _MAX_FILE_BYTES

Usage:
    from src.harvester.converter import DocumentProcessor

    processor = DocumentProcessor()
    markdown = processor.clean_source_material("path/to/document.pdf")
    # Returns redacted Markdown safe for storage
"""

import logging
from markitdown import MarkItDown
from src.core.redactor import Redactor

# Configure logging
logger = logging.getLogger(__name__)

# Supported file extensions for conversion
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".html", ".htm"}

# OOM guard: reject files larger than 500 MB to prevent memory exhaustion
# on a 16 GB RAM laptop during MarkItDown conversion
_MAX_FILE_BYTES = 500 * 1024 * 1024  # 500 MB

# ---------------------------------------------------------------------------
# Entity Redaction Patterns
# ---------------------------------------------------------------------------
# Patterns moved to src.core.redactor


class DocumentProcessor:
    """
    Wraps MarkItDown to convert local documents into LLM-ready Markdown.

    Supported formats:
        • PDF  (.pdf)   — Extracts text with layout preservation
        • DOCX (.docx)  — Preserves headings, lists, tables
        • HTML (.html)  — Strips scripts/styles, keeps semantic structure

    Safety features:
        • Entity redaction — proper names, emails, URLs → [REDACTED]
        • OOM guard — files > 500 MB are rejected before conversion

    Design:
        Structural elements like headings (##) and tables (| col |) are
        preserved because they carry rhythmic signals used downstream
        by the Rhetorical Fingerprinting pipeline.
    """

    def __init__(self, redact: bool = True) -> None:
        """
        Initialize the MarkItDown converter engine.

        Args:
            redact: If True (default), automatically redact entities
                    from converted output before returning.
        """
        self._converter = MarkItDown()
        self._redact = redact
        logger.info(
            f"DocumentProcessor initialized (MarkItDown engine, "
            f"redaction={'ON' if redact else 'OFF'})"
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_file(file_path: str) -> Path:
        """
        Validate file extension, existence, and size.

        Raises:
            ValueError: Unsupported extension.
            FileNotFoundError: File does not exist.
            MemoryError: File exceeds _MAX_FILE_BYTES.
        """
        path = Path(file_path).resolve()

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{path.suffix}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        file_size = path.stat().st_size
        if file_size > _MAX_FILE_BYTES:
            size_mb = file_size / (1024 * 1024)
            raise MemoryError(
                f"File too large for safe processing: {size_mb:.0f} MB "
                f"(limit: {_MAX_FILE_BYTES // (1024 * 1024)} MB). "
                f"Split the document or increase _MAX_FILE_BYTES."
            )

        return path

    # ------------------------------------------------------------------
    # Entity Redaction
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_entities(text: str) -> str:
        """
        Strip identifying metadata from Markdown text.
        Uses the centralized Redactor utility.
        """
        return Redactor.redact(text, strict=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean_source_material(self, file_path: str) -> str:
        """
        Detect file type and convert to a cleaned, redacted Markdown string.

        Pipeline: validate → convert (MarkItDown) → redact entities → return

        Structural elements like headings and tables are preserved,
        as these are critical for rhythmic analysis in the forensic pipeline.

        Args:
            file_path: Path to the source document (.pdf, .docx, .html).

        Returns:
            A Markdown string with entities redacted (if redaction is ON).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file type is unsupported.
            MemoryError: If the file exceeds the size limit.
            RuntimeError: If the conversion engine encounters an error.
        """
        path = self._validate_file(file_path)
        logger.info(f"Converting {path.suffix.upper()} → Markdown: {path.name}")

        try:
            result = self._converter.convert(str(path))
            markdown_text = result.text_content

            if not markdown_text or not markdown_text.strip():
                logger.warning(f"Conversion produced empty output for: {path.name}")
                return ""

            # --- Entity Redaction ---
            if self._redact:
                original_len = len(markdown_text)
                markdown_text = self._redact_entities(markdown_text)
                logger.info(
                    f"Redaction pass complete: "
                    f"{original_len:,} → {len(markdown_text):,} chars"
                )

            logger.info(
                f"Conversion complete: {path.name} "
                f"({len(markdown_text):,} chars)"
            )
            return markdown_text

        except MemoryError:
            raise  # Re-raise OOM without wrapping
        except Exception as e:
            logger.error(f"MarkItDown conversion failed for {path.name}: {e}")
            raise RuntimeError(
                f"Failed to convert '{path.name}': {e}"
            ) from e

    def supported_types(self) -> list[str]:
        """Return a sorted list of supported file extensions."""
        return sorted(SUPPORTED_EXTENSIONS)
