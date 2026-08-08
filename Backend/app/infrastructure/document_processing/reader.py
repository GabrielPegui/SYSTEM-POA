"""PDF reader abstraction and its pdfplumber implementation.

The reader is responsible for extracting technical information from the
document: text, per-page content, tables and positional word data. It must
never contain client-specific parsing logic (ADR-002).
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pdfplumber

from app.domain.document_processing.enums import ExtractionStatus
from app.domain.document_processing.exceptions import PDFNoTextError, PDFReadError
from app.domain.document_processing.models import (
    PageData,
    RawDocumentData,
    TextElement,
)


class PDFReader(ABC):
    """Contract to read raw content from a PDF file."""

    @abstractmethod
    def read(self, path: Path, filename: str | None = None) -> RawDocumentData:
        """Read a PDF and return its raw document data.

        ``filename`` is the traceability name to attach to the result; when
        omitted it defaults to ``path.name``. Detection and parsing never
        depend on it (ADR-002: the detector works on document content only).

        Raises:
            PDFReadError: if the file is missing or not a valid PDF.
            PDFNoTextError: if the PDF has no extractable text (scanned).
        """


class PdfplumberPDFReader(PDFReader):
    """PDFReader implementation backed by pdfplumber."""

    def read(self, path: Path, filename: str | None = None) -> RawDocumentData:
        path = Path(path)
        if not path.exists():
            raise PDFReadError(f"PDF file not found: {path}")
        try:
            with pdfplumber.open(path) as pdf:
                pages = tuple(self._read_page(page, number) for number, page in enumerate(pdf.pages, start=1))
                producer = self._producer(pdf)
        except PDFReadError:
            raise
        except Exception as exc:  # pdfplumber/pypdf raise several low-level errors
            raise PDFReadError(f"Could not read PDF: {path}") from exc

        if not pages:
            raise PDFReadError(f"PDF has no pages: {path}")
        if not any(page.text.strip() for page in pages):
            raise PDFNoTextError(f"PDF has no extractable text: {path}")

        return RawDocumentData(filename=filename or path.name, pages=pages, producer=producer)

    def _read_page(self, page, page_number: int) -> PageData:
        text = page.extract_text() or ""
        words = tuple(self._read_word(word) for word in page.extract_words())
        status = ExtractionStatus.EXTRACTED if text.strip() else ExtractionStatus.NO_TEXT
        return PageData(page_number=page_number, text=text, words=words, status=status)

    @staticmethod
    def _read_word(word: dict) -> TextElement:
        return TextElement(
            text=word["text"],
            x0=word["x0"],
            top=word["top"],
            x1=word["x1"],
            bottom=word["bottom"],
        )

    @staticmethod
    def _producer(pdf) -> str | None:
        metadata = pdf.metadata or {}
        return metadata.get("Producer")
