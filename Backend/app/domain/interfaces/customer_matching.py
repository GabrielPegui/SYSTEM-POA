"""Customer matching contract (Sprint 7).

Decides the correspondence between customer identifiers extracted from a
purchase order document (``customer_code``/``customer_name`` as printed) and
the fixed customer catalog. It mirrors ``ProductMatcher``: it must never
create catalog entities and must express uncertainty through
``CustomerMatchResult`` (MATCHED / REVIEW_REQUIRED / NO_MATCH).

Matching strategy (documented in ``docs/ANALISIS_DATOS_MVP.md``): the RNC is
**not** a unique identifier (a single RNC maps to many accounts, e.g. 98
Sirena clients), so the name is used as reinforcement to disambiguate
candidate accounts. ``customer_code`` extracted by the parsers is usually the
RNC; an explicit ``CL…`` code, when present, is tried first.
"""

from abc import ABC, abstractmethod

from app.domain.document_processing.matching import CustomerMatchResult


class CustomerMatcher(ABC):
    """Contract to match document customer identifiers against the catalog."""

    @abstractmethod
    def match(self, customer_code: str | None, customer_name: str | None) -> CustomerMatchResult:
        """Return the matching decision for the extracted customer identifiers."""
