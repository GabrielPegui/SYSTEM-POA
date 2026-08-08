"""Tests for route resolution (Sprint 7).

The documented rule is *one customer = one route* (1:1), with a single known
data-quality exception: ``CL001062`` (SURTIDORA BENERITO) is listed on two
routes and is reported as unresolved instead of silently picking one.
"""

import pytest

from app.application.services.route_resolution import (
    AMBIGUOUS_ROUTE_CODES,
    RouteResolver,
)
from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Customer, Route


@pytest.fixture
def resolver() -> RouteResolver:
    return RouteResolver()


def test_ambiguous_codes_are_documented() -> None:
    assert "CL001062" in AMBIGUOUS_ROUTE_CODES


def test_matched_customer_resolves_its_route(resolver: RouteResolver) -> None:
    route = Route(code="PPN006", name="Ruta 6")
    customer = Customer(code="CL000004-101", name="MERCADAL GUARICANO", route=route)
    match = CustomerMatchResult(outcome=MatchOutcome.MATCHED, matched_customer=customer)

    result = resolver.resolve(match)

    assert result.resolved
    assert result.route == route


def test_ambiguous_customer_reports_both_routes(resolver: RouteResolver) -> None:
    route = Route(code="PPN000", name="Ruta 0")
    customer = Customer(code="CL001062", name="SURTIDORA BENERITO", route=route)
    match = CustomerMatchResult(outcome=MatchOutcome.MATCHED, matched_customer=customer)

    result = resolver.resolve(match)

    assert not result.resolved
    assert result.route is None
    assert "PPN000" in result.reason
    assert "PPN403" in result.reason


def test_non_matched_customer_uses_match_reason(resolver: RouteResolver) -> None:
    match = CustomerMatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED,
        reason="RNC 101532483 maps to 2 accounts",
    )

    result = resolver.resolve(match)

    assert not result.resolved
    assert result.reason == "RNC 101532483 maps to 2 accounts"
