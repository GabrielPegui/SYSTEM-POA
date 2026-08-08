"""Tests for the matching contract (pre-Sprint 7).

Verifies that ``MatchResult`` can express MATCHED / REVIEW_REQUIRED /
NO_MATCH and that the ``ProductMatcher`` interface is the seam Sprint 7 will
implement. No fuzzy logic lives here.
"""

import pytest

from app.domain.document_processing.matching import MatchOutcome, MatchResult
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument
from app.domain.entities import Product
from app.domain.interfaces import ProductMatcher


def _product(code: str, description: str) -> Product:
    return Product(code=code, description=description)


def test_match_result_matched_carries_product() -> None:
    product = _product("01010101", "VIGA MEDIANA BLANCO PEPIN")
    result = MatchResult(
        outcome=MatchOutcome.MATCHED,
        matched_product=product,
        confidence=0.98,
        reason="Exact description match",
    )

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_product == product
    assert result.confidence == 0.98


def test_match_result_review_required_has_candidates() -> None:
    candidates = (
        _product("01010101", "BOLIN BURGUER"),
        _product("01010102", "PAN BURGER"),
    )
    result = MatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED,
        candidates=candidates,
        reason="Multiple candidates with low confidence",
    )

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_product is None
    assert len(result.candidates) == 2


def test_match_result_no_match() -> None:
    result = MatchResult(
        outcome=MatchOutcome.NO_MATCH,
        reason="No candidate found in catalog",
    )

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_product is None
    assert result.candidates == ()


def test_match_result_invariants() -> None:
    with pytest.raises(ValueError, match="MATCHED requires a matched product"):
        MatchResult(outcome=MatchOutcome.MATCHED)

    product = _product("01010101", "VIGA")
    with pytest.raises(ValueError, match="Only MATCHED results may carry a matched product"):
        MatchResult(outcome=MatchOutcome.NO_MATCH, matched_product=product)


def test_product_matcher_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ProductMatcher()


def test_concrete_matcher_returns_match_result() -> None:
    class ExactMatcher(ProductMatcher):
        def match(self, item: PurchaseOrderItemDocument) -> MatchResult:
            product = _product("01010101", item.description)
            return MatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_product=product,
                confidence=1.0,
            )

    matcher = ExactMatcher()
    result = matcher.match(PurchaseOrderItemDocument(description="VIGA", quantity=6))

    assert isinstance(result, MatchResult)
    assert result.matched_product.description == "VIGA"
