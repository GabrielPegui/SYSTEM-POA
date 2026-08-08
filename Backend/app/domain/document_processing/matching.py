"""Matching contract between extracted products and the catalog (pre-Sprint 7).

``MatchResult`` is the outcome of deciding whether an extracted product
corresponds to a catalog product. It lets the system express three states:

- ``MATCHED``: enough evidence to select a single catalog product.
- ``REVIEW_REQUIRED``: candidates were found but confidence is not high
  enough; a human must decide.
- ``NO_MATCH``: no candidate found.

No fuzzy algorithms, EAN matching, ML or external services are implemented
here yet. This contract only makes the boundary explicit so Sprint 7 can
implement the real matcher safely: it must never silently create a catalog
product when the evidence is not conclusive.
"""

import enum
from dataclasses import dataclass

from app.domain.entities import Product


class MatchOutcome(enum.Enum):
    """Result of a product matching decision."""

    MATCHED = "matched"
    REVIEW_REQUIRED = "review_required"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class MatchResult:
    """Outcome of matching a single extracted product line.

    - ``outcome``: the matching state.
    - ``matched_product``: the catalog product selected, when ``MATCHED``.
    - ``confidence``: numeric confidence in ``[0, 1]``, when available.
    - ``candidates``: products that could correspond, when not conclusive.
    - ``reason``: human-readable evidence for the decision.
    """

    outcome: MatchOutcome
    matched_product: Product | None = None
    confidence: float | None = None
    candidates: tuple[Product, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.outcome is MatchOutcome.MATCHED and self.matched_product is None:
            raise ValueError("MATCHED requires a matched product")
        if self.outcome is not MatchOutcome.MATCHED and self.matched_product is not None:
            raise ValueError("Only MATCHED results may carry a matched product")
