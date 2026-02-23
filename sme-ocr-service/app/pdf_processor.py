"""
PDF Processor for SME OCR Service.
Converts PDF pages to images using PyMuPDF (fitz).
"""

import io
import logging
from typing import Iterator

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PdfProcessor:
    """Handles PDF to image conversion."""

    def __init__(self, dpi: int = 200):
        """
        Initialize PDF processor.

        Args:
            dpi: Resolution for rendering PDF pages as images.
                 Higher = better quality but more memory.
                 200 is a good balance for OCR.
        """
        self.dpi = dpi

    def pdf_to_images(
        self, pdf_bytes: bytes
    ) -> Iterator[tuple[int, io.BytesIO, dict]]:
        """
        Convert PDF pages to images.

        Args:
            pdf_bytes: PDF file content as bytes.

        Yields:
            Tuple of (page_number, image_bytes, page_metadata)
        """
        logger.info(f"Opening PDF with {len(pdf_bytes)} bytes")

        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(pdf_document)
        logger.info(f"PDF has {page_count} pages")

        for page_num in range(page_count):
            try:
                page = pdf_document[page_num]

                # Get page dimensions
                width = int(page.rect.width)
                height = int(page.rect.height)

                # Render page to image
                # zoom = dpi / 72 (default PDF DPI)
                zoom = self.dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # Convert to PNG bytes
                img_bytes = pix.tobytes("png")

                metadata = {
                    "width": width * self.dpi // 72,
                    "height": height * self.dpi // 72,
                    "original_width": width,
                    "original_height": height,
                }

                logger.debug(
                    f"Page {page_num + 1}: rendered to "
                    f"{len(img_bytes)} bytes ({metadata['width']}x{metadata['height']})"
                )

                yield (page_num + 1, io.BytesIO(img_bytes), metadata)

            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
                raise
            finally:
                # Clear page reference to free memory
                del page

        pdf_document.close()
        logger.info("PDF processing complete")

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """Get the number of pages in a PDF without rendering."""
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(pdf_document)
        pdf_document.close()
        return count
