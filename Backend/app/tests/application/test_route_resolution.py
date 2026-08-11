"""Tests for route resolution.

The documented rule is *one customer = one route* (1:1) within the definitive
catalog: the route of a matched customer is the route of the order. Ambiguity
by name is handled by the customer matcher before reaching this service.
"""

import pytest

from app.application.services.route_resolution import RouteResolver
from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Customer, Route


@pytest.fixture
def resolver() -> RouteResolver:
    return RouteResolver()


def test_matched_customer_resolves_its_route(resolver: RouteResolver) -> None:
    route = Route(code="PPN006", name="Ruta 6")
    customer = Customer(name="MERCADAL GUARICANO", route=route)
    match = CustomerMatchResult(outcome=MatchOutcome.MATCHED, matched_customer=customer)

    result = resolver.resolve(match)

    assert result.resolved
    assert result.route == route


def test_non_matched_customer_uses_match_reason(resolver: RouteResolver) -> None:
    match = CustomerMatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED,
        reason="Name matches more than one catalog customer",
    )

    result = resolver.resolve(match)

    assert not result.resolved
    assert result.reason == "Name matches more than one catalog customer"


def test_no_match_customer_uses_match_reason(resolver: RouteResolver) -> None:
    match = CustomerMatchResult(outcome=MatchOutcome.NO_MATCH, reason="Not in catalog")

    result = resolver.resolve(match)

    assert not result.resolved
    assert result.reason == "Not in catalog"
