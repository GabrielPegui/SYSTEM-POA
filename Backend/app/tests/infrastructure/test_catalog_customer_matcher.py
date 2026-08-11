"""Tests for the catalog customer matcher (definitive model).

The matcher resolves purely by customer ``name`` (the business key of the
definitive catalog in ``docs/data/CLIENTES POR RUTA.xlsx``); there is no code
or RNC. Expectations mirror the real data:

- an exact name that identifies a single customer matches with confidence 1.0;
- an exact name that exists on more than one route (e.g. ``INVERSIONES
  LLERS``) requires review and exposes the candidate customers;
- inflection variants are tolerated (``Mercadal Guaricanos`` matches
  ``MERCADAL GUARICANO``);
- ``HYPER``/``HIPER`` expand to ``CARREFOUR``;
- a single informative token is never enough.
"""

import pytest

from app.domain.document_processing.matching import MatchOutcome
from app.domain.entities import Customer, Route
from app.infrastructure.matching.catalog_customer_matcher import CatalogCustomerMatcher
from app.tests.application.fakes import InMemoryCustomerRepository

ROUTE_1 = Route(code="PPN001", name="Ruta 1")
ROUTE_2 = Route(code="PPN002", name="Ruta 2")
ROUTE_303 = Route(code="PPN303", name="Ruta 303")
ROUTE_601 = Route(code="PPN601", name="Ruta 601")

CUSTOMERS = [
    Customer(name="MERCADAL GUARICANO", route=ROUTE_1, address="Sector Guaicanos"),
    Customer(name="CARREFOUR AUTOPISTA DUARTE", route=ROUTE_2),
    Customer(name="PLAZA LAMA SANTIAGO", route=ROUTE_2),
    Customer(name="JUMBO HIGUEY", route=ROUTE_2),
    Customer(name="MERCADAL AV DUARTE", route=ROUTE_2),
    Customer(name="INVERSIONES LLERS", route=ROUTE_303),
    Customer(name="INVERSIONES LLERS", route=ROUTE_601),
    Customer(name="OPERADORA WESTPARK, SAS", route=ROUTE_2),
]


@pytest.fixture
def matcher() -> CatalogCustomerMatcher:
    return CatalogCustomerMatcher(InMemoryCustomerRepository(CUSTOMERS))


def test_exact_unique_name_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("JUMBO HIGUEY")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == CUSTOMERS[3]
    assert result.confidence == 1.0


def test_exact_duplicated_name_requires_review(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("INVERSIONES LLERS")

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_customer is None
    assert len(result.candidates) == 2
    assert {candidate.route.code for candidate in result.candidates} == {"PPN303", "PPN601"}
    assert "more than one route" in result.reason


def test_inflected_name_matches_catalog(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("Mercadal Guaricanos")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == CUSTOMERS[0]
    assert result.confidence >= 0.9


def test_ambiguous_inflected_name_requires_review() -> None:
    duplicated = InMemoryCustomerRepository(
        [
            Customer(name="MERCADAL GUARICANO", route=ROUTE_1),
            Customer(name="MERCADAL GUARICANO", route=ROUTE_2),
        ]
    )
    matcher = CatalogCustomerMatcher(duplicated)

    result = matcher.match("Mercadal Guaricanos")

    assert result.outcome is MatchOutcome.REVIEW_REQUIRED
    assert result.matched_customer is None
    assert len(result.candidates) == 2


def test_alias_hyper_matches_carrefour(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("Hyper Duarte")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == CUSTOMERS[1]
    assert 0.7 <= result.confidence < 1.0


def test_document_synonym_matches_catalog_account(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("EMBASSY SUITES HOTEL (OWP)")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == CUSTOMERS[-1]
    assert result.confidence == 1.0


def test_full_name_matches(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("Jumbo Higuey")

    assert result.outcome is MatchOutcome.MATCHED
    assert result.matched_customer == CUSTOMERS[3]
    assert result.confidence == 1.0


def test_single_informative_token_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("Jumbo")

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None


def test_unknown_name_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match("FARMACIA CAROL")

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None
    assert result.candidates == ()


def test_no_name_does_not_match(matcher: CatalogCustomerMatcher) -> None:
    result = matcher.match(None)

    assert result.outcome is MatchOutcome.NO_MATCH
    assert result.matched_customer is None
    assert "No usable customer name" in result.reason
