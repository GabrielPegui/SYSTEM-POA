"""Product matching contract (pre-Sprint 7).

The matcher decides the correspondence between a product line extracted from
a PDF and the fixed product catalog. It must never create catalog entities and
must express uncertainty through ``MatchResult`` (MATCHED / REVIEW_REQUIRED /
NO_MATCH). The concrete matcher will be implemented in Sprint 7.
"""

from abc import ABC, abstractmethod

from app.domain.document_processing.matching import MatchResult
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument


class ProductMatcher(ABC):
    """Contract to match an extracted product line against the catalog."""

    @abstractmethod
    def match(self, item: PurchaseOrderItemDocument) -> MatchResult:
        """Return the matching decision for a single extracted product line."""
