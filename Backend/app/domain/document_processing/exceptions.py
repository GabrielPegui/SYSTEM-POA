"""Exceptions for document processing."""


class DocumentProcessingError(Exception):
    """Base error for the document processing pipeline."""


class PDFReadError(DocumentProcessingError):
    """Raised when a PDF cannot be read or is invalid."""


class PDFNoTextError(DocumentProcessingError):
    """Raised when a PDF has no extractable text (requires OCR in the future)."""
