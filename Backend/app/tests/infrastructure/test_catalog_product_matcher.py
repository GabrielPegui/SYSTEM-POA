"""Tests for the catalog product matcher (Sprint 7).

The expectations are calibrated against the real catalog and sample PDFs
(``docs/ANALISIS_DATOS_MVP.md``): ``PEPIN PAN HOT DOG 8/1`` matches, ``PEPIN
VIGA BLANCA PEQUEÑA`` matches via the gender-stemmed tokens, ``PEPIN VIGA
MEDIANA 1PZA`` is ambiguous, ``BOLIN BURGER`` must never match, and the
catalog product marked ``NO USAR`` is never selected.
"""

import pytest

from app.domain.document_processing.matching import MatchOutcome
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument
from app.domain.entities import Product
from app.infrastructure.matching.catalog_product_matcher import CatalogProductMatcher
from app.tests.application.fakes import InMemoryProductRepository

CATALOG = [
    Product(code="01010101", description="PEPIN VIGA MEDIANA BLANCO"),
    Product(code="01010103", description="PEPIN VIGA BLANCO PEQUEÑA"),
    Product(code="01020104", description="PEPIN VIGA CLUB SANDWICH INTEGRAL 850 GR"),
    Product(code="02010101", description="PEPIN PAN HOT DOG 8/1"),
    Product(code="01010301", description="NO USAR"),
]


@pytest.fixture
def matcher() -> CatalogProductMatcher:
    return CatalogProductMatcher(InMemoryProductRepository(CATALOG))


def _item(description: str, pdf_code: str | None = None) -> PurchaseOrderItemDocument:
    return PurchaseOrderItemDocument(description=description, quantity=1, pdf_code=pdf_code)


def test_pdf_code_does_not_override_description_matching(matcher: CatalogProductMatcher) -> None:
    """pdf_code is traceability only and never drives selection (Pre-Sprint 8.1).

    ``01010101`` belongs to ``PEPIN VIGA MEDIANA BLANCO``; a line printed with
    that code but the description ``PEPIN PAN HOT DOG 8/1`` must match the
    product whose description fits, never the product matching the PDF code.
    """
    result = matcher.match(_item("PEPIN PAN HOT DOG 8/1", pdf_code="01010101"))

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_product.code == "02010101"
    assert result.confidence == 1.0


def test_exact_normalized_description_matches(matcher: CatalogProductMatcher) -> None:
    result = matcher.match(_item("PEPIN VIGA CLUB SANDWICH INTEGRAL 850 GR"))

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_product.code == "01020104"
    assert result.confidence == 1.0


def test_gender_stemmed_description_matches(matcher: CatalogProductMatcher) -> None:
    result = matcher.match(_item("PEPIN VIGA BLANCA PEQUEÑA"))

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_product.code == "01010103"
    assert result.confidence == 0.75


def test_similar_but_ambiguous_description_requires_review(matcher: CatalogProductMatcher) -> None:
    result = matcher.match(_item("PEPIN VIGA INTEGRAL LIGHT 14OZ"))

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_product is None
    assert result.candidates
    assert all(candidate.code != "01010301" for candidate in result.candidates)


def test_unrelated_description_does_not_match(matcher: CatalogProductMatcher) -> None:
    result = matcher.match(_item("BOLIN BURGER"))

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_product is None


def test_catalog_of_only_no_usar_products_is_no_match() -> None:
    matcher = CatalogProductMatcher(InMemoryProductRepository([CATALOG[-1]]))
    result = matcher.match(_item("PEPIN VIGA BLANCA PEQUEÑA"))

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_product is None


def test_empty_catalog_is_no_match() -> None:
    matcher = CatalogProductMatcher(InMemoryProductRepository([]))
    result = matcher.match(_item("PEPIN VIGA BLANCA PEQUEÑA"))

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_product is None


def test_unknown_code_falls_back_to_description(matcher: CatalogProductMatcher) -> None:
    result = matcher.match(_item("PEPIN VIGA BLANCA PEQUEÑA", pdf_code="999999"))

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_product.code == "01010103"
