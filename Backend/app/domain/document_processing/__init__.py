"""Domain contracts for document processing (ADR-002).

Contains the standard data structures that flow between the PDF reader, the
document detector and the format-specific parsers. These models are pure data
and do not depend on any PDF library, so the rest of the system stays
independent of the infrastructure used to read documents.
"""

from app.domain.document_processing.enums import DocumentType, ExtractionStatus
from app.domain.document_processing.exceptions import (
    DocumentProcessingError,
    PDFNoTextError,
    PDFReadError,
)
from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.document_processing.models import (
    DetectionResult,
    PageData,
    RawDocumentData,
    TextElement,
)
from app.domain.document_processing.processing import (
    ProcessedOrderResult,
    ProcessingStatus,
)
from app.domain.document_processing.purchase_order import (
    PurchaseOrderDocument,
    PurchaseOrderItemDocument,
)

__all__ = [
    "CustomerMatchResult",
    "DetectionResult",
    "DocumentProcessingError",
    "DocumentType",
    "ExtractionStatus",
    "MatchOutcome",
    "PDFNoTextError",
    "PDFReadError",
    "PageData",
    "ProcessedOrderResult",
    "ProcessingStatus",
    "PurchaseOrderDocument",
    "PurchaseOrderItemDocument",
    "RawDocumentData",
    "TextElement",
]
