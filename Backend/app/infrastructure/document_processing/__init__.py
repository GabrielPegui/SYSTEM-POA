"""Document processing infrastructure: PDF readers, detector and parsers.

Concrete implementations of the ADR-002 processing pipeline:
``PDF -> PDF Reader -> Document Detector -> Parser``.
"""

from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import (
    DEFAULT_PARSERS,
    ParserRegistry,
)
from app.infrastructure.document_processing.reader import PdfplumberPDFReader, PDFReader

__all__ = [
    "DEFAULT_PARSERS",
    "DocumentDetector",
    "PDFReader",
    "ParserRegistry",
    "PdfplumberPDFReader",
]
