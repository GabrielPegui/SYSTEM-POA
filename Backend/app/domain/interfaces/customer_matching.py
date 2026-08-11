"""Customer matching contract.

Decides the correspondence between the customer name extracted from a
purchase order document (``customer_name`` as printed) and the fixed customer
catalog. It must never create catalog entities and must express uncertainty
through ``CustomerMatchResult`` (MATCHED / REVIEW_REQUIRED / NO_MATCH).

Matching strategy: the customer name is the business key (per the definitive
catalog in ``docs/data/CLIENTES POR RUTA.xlsx``). The matcher loads the full
catalog and resolves by normalized name similarity; when the same name maps
to more than one catalog customer (e.g. ``INVERSIONES LLERS`` on PPN303 and
PPN601), the result is REVIEW_REQUIRED so a human picks the right
customer + route.
"""

from abc import ABC, abstractmethod

from app.domain.document_processing.matching import CustomerMatchResult


class CustomerMatcher(ABC):
    """Contract to match a document customer name against the catalog."""

    @abstractmethod
    def match(self, customer_name: str | None) -> CustomerMatchResult:
        """Return the matching decision for the extracted customer name."""
