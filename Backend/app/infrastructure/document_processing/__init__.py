"""Document processing infrastructure: PDF readers and document detector.

Concrete implementations of the ADR-002 processing pipeline:
``PDF -> PDF Reader -> Document Detector -> Parser``.
"""

from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.reader import PdfplumberPDFReader, PDFReader

__all__ = ["DocumentDetector", "PDFReader", "PdfplumberPDFReader"]
