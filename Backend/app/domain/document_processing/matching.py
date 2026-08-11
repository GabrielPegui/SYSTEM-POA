"""Matching contract between extracted customer data and the catalog (Sprint 7).

``CustomerMatchResult`` is the outcome of deciding whether a customer
extracted from a document corresponds to a catalog customer. It lets the
system express three states:

- ``MATCHED``: enough evidence to select a single catalog customer.
- ``REVIEW_REQUIRED``: candidates were found but confidence is not high
  enough (e.g. the name matches more than one catalog customer); a human must
  decide.
- ``NO_MATCH``: no candidate found.

The matcher must never silently create a catalog customer when the evidence
is not conclusive.
"""

import enum
from dataclasses import dataclass

from app.domain.entities import Customer


class MatchOutcome(enum.Enum):
    """Result of a matching decision."""

    MATCHED = "matched"
    REVIEW_REQUIRED = "review_required"
    NO_MATCH = "no_match"


@dataclass(frozen=True)
class CustomerMatchResult:
    """Outcome of matching a customer extracted from a document.

    - ``outcome``: the matching state.
    - ``matched_customer``: the catalog customer selected, when MATCHED.
    - ``confidence``: numeric confidence in ``[0, 1]``, when available.
    - ``candidates``: customers that could correspond, when not conclusive.
    - ``reason``: human-readable evidence for the decision.
    """

    outcome: MatchOutcome
    matched_customer: Customer | None = None
    confidence: float | None = None
    candidates: tuple[Customer, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.outcome is MatchOutcome.MATCHED and self.matched_customer is None:
            raise ValueError("MATCHED requires a matched customer")
        if self.outcome is not MatchOutcome.MATCHED and self.matched_customer is not None:
            raise ValueError("Only MATCHED results may carry a matched customer")
