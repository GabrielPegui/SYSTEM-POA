"""Tests for the customer matching contract.

Verifies that ``CustomerMatchResult`` can express MATCHED / REVIEW_REQUIRED /
NO_MATCH and that the ``CustomerMatcher`` interface is the seam the catalog
matcher implements. No fuzzy logic lives here.
"""

import pytest

from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Customer, Route
from app.domain.interfaces import CustomerMatcher

ROUTE = Route(code="PPN002", name="Ozama")


def _customer(name: str = "JASON FAST FOOD") -> Customer:
    return Customer(name=name, route=ROUTE)


def test_match_result_matched_carries_customer() -> None:
    customer = _customer()
    result = CustomerMatchResult(
        outcome=MatchOutcome.MATCHED,
        matched_customer=customer,
        confidence=0.98,
        reason="Exact name match",
    )

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == customer
    assert result.confidence == 0.98


def test_match_result_review_required_has_candidates() -> None:
    candidates = (_customer(name="INVERSIONES LLERS"), _customer(name="MERCADAL GUARICANO"))
    result = CustomerMatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED,
        candidates=candidates,
        reason="Multiple candidates with low confidence",
    )

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_customer is None
    assert len(result.candidates) == 2


def test_match_result_no_match() -> None:
    result = CustomerMatchResult(
        outcome=MatchOutcome.NO_MATCH,
        reason="No candidate found in catalog",
    )

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None
    assert result.candidates == ()


def test_match_result_invariants() -> None:
    with pytest.raises(ValueError, match="MATCHED requires a matched customer"):
        CustomerMatchResult(outcome=MatchOutcome.MATCHED)

    customer = _customer()
    with pytest.raises(ValueError, match="Only MATCHED results may carry a matched customer"):
        CustomerMatchResult(outcome=MatchOutcome.NO_MATCH, matched_customer=customer)


def test_customer_matcher_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        CustomerMatcher()


def test_concrete_matcher_returns_customer_match_result() -> None:
    class ExactMatcher(CustomerMatcher):
        def match(self, customer_name: str | None) -> CustomerMatchResult:
            return CustomerMatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_customer=_customer(),
                confidence=1.0,
                reason=f"Exact name '{customer_name}'",
            )

    result = ExactMatcher().match("JASON FAST FOOD")

    assert isinstance(result, CustomerMatchResult)
    assert result.matched_customer.name == "JASON FAST FOOD"
