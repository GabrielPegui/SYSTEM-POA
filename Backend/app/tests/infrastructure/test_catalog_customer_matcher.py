"""Tests for the catalog customer matcher (Sprint 7).

The expectations mirror the real data documented in ``ANALISIS_DATOS_MVP.md``:
an exact ``CL…`` code wins, a unique RNC matches, a shared RNC needs the
document name to disambiguate, ``HYPER``/``HIPER`` expand to ``CARREFOUR``,
and a single informative token (e.g. an address line) is never enough.
"""

import pytest

from app.domain.document_processing.matching import MatchOutcome
from app.domain.entities import Customer, Route
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.tests.application.fakes import InMemoryCustomerRepository

ROUTE_1 = Route(code="PPN001", name="Ruta 1")
ROUTE_2 = Route(code="PPN002", name="Ruta 2")

CUSTOMERS = [
    Customer(code="CL000004-101", name="MERCADAL GUARICANO", route=ROUTE_1, rnc="131242172"),
    Customer(code="CL000014-001", name="CARREFOUR AUTOPISTA DUARTE", route=ROUTE_2, rnc="101802456"),
    Customer(code="CL000003-008", name="PLAZA LAMA SANTIAGO", route=ROUTE_2, rnc=None),
    Customer(code="CL000002-009", name="JUMBO HIGUEY", route=ROUTE_2, rnc=None),
    Customer(code="CL000001-001", name="MERCADAL AV DUARTE", route=ROUTE_2, rnc="101532483"),
    Customer(code="CL000001-002", name="MERCADAL AUTOPISTA", route=ROUTE_1, rnc="101532483"),
]


@pytest.fixture
def matcher() -> CatalogCustomerMatcher:
    return CatalogCustomerMatcher(InMemoryCustomerRepository(CUSTOMERS))


def test_exact_customer_code_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("CL000002-009", None)

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000002-009"
    assert result.confidence == 1.0


def test_unknown_customer_code_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("CL999999", None)

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None


def test_unique_rnc_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("131242172", "Mercadal Guaricanos")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000004-101"
    assert result.confidence == 1.0


def test_shared_rnc_with_name_disambiguation_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("101532483", "Mercadal Av Duarte")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000001-001"
    assert result.confidence == 1.0


def test_shared_rnc_without_disambiguation_requires_review(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("101532483", "Av. Duarte")

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_customer is None
    assert {candidate.code for candidate in result.candidates} == {"CL000001-001", "CL000001-002"}


def test_name_with_alias_matches_carrefour(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None, "Hyper Duarte")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000014-001"
    assert result.confidence == pytest.approx(0.666, abs=0.001)


def test_full_name_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None, "Jumbo Higuey")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000002-009"


def test_single_informative_token_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None, "Jumbo")

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None


def test_address_line_alone_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None, "Av. Duarte")

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None


def test_no_identifier_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None, None)

    assert result.outcome is MatchOutcome.NO_MATCH
    assert "No customer identifier" in result.reason


def test_short_rnc_falls_through_to_name(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("12345", "Jumbo Higuey")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer.code == "CL000002-009"
