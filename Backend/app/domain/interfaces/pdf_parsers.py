"""Parser contract for purchase order documents (ADR-002).

The ``IPDFParser`` interface defines the contract every format-specific
parser must implement. Parsers transform raw document data into a standard
output model, keeping the rest of the system independent of the original
document format.
"""

from abc import ABC, abstractmethod

from app.domain.document_processing.models import RawDocumentData
from app.domain.document_processing.purchase_order import PurchaseOrderDocument


class IPDFParser(ABC):
    """Contract implemented by every format-specific PDF parser.

    Implementations are registered per document structure (e.g. SirenaParser,
    JumboParser, HyperParser, BravoParser). They must never contain business
    rules and must never match against the database or create entities; they
    only interpret the document structure and return a standard
    ``PurchaseOrderDocument`` (ADR-002).
    """

    @abstractmethod
    def parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        """Parse a raw document into the standard output model."""
