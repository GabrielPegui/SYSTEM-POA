"""Tests for the validation gate.

The gate decides the overall ``ProcessingStatus`` from the resolved customer,
route and extracted header data, and only builds a domain ``Order`` when every
reference is conclusive (ADR-003: nothing is persisted on REVIEW_REQUIRED /
NO_MATCH / ERROR).
"""

from datetime import date

import pytest

from app.application.services.order_validation import OrderValidationService
from app.application.services.route_resolution import RouteResolution
from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.document_processing.processing import ProcessingStatus
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument
from app.domain.entities import Customer, Route


@pytest.fixture
def service() -> OrderValidationService:
    return OrderValidationService()


@pytest.fixture
def route() -> Route:
    return Route(code="PPN006", name="Ruta 6")


@pytest.fixture
def customer(route: Route) -> Customer:
    return Customer(name="MERCADAL GUARICANO", route=route)


def _customer_match(customer: Customer) -> CustomerMatchResult:
    return CustomerMatchResult(
        outcome=MatchOutcome.MATCHED,
        matched_customer=customer,
        confidence=1.0,
    )


def _items(*descriptions: str) -> tuple[PurchaseOrderItemDocument, ...]:
    return tuple(
        PurchaseOrderItemDocument(description=description, quantity=1)
        for description in descriptions
    )


def test_all_conclusive_is_processed(service, customer, route) -> None:
    decision = service.evaluate(
        customer_match=_customer_match(customer),
        route_resolution=RouteResolution(route),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.PROCESSED
    assert decision.order is not None
    assert decision.order.order_number == "4000326758"
    assert decision.order.customer == customer
    assert decision.order.delivery_date == date(2026, 8, 10)
    assert len(decision.order.items) == 1
    assert decision.order.items[0].description == "PEPIN PAN HOT DOG 8/1"
    assert decision.reasons == ()


def test_no_match_customer_is_no_match(service, route) -> None:
    no_match = CustomerMatchResult(outcome=MatchOutcome.NO_MATCH, reason="Not in catalog")

    decision = service.evaluate(
        customer_match=no_match,
        route_resolution=RouteResolution(route),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.NO_MATCH
    assert decision.order is None


def test_review_customer_requires_review(service, customer, route) -> None:
    review = CustomerMatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED,
        candidates=(customer,),
        reason="Ambiguous",
    )

    decision = service.evaluate(
        customer_match=review,
        route_resolution=RouteResolution(route),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert decision.order is None


def test_unresolved_route_requires_review(service, customer, route) -> None:
    decision = service.evaluate(
        customer_match=_customer_match(customer),
        route_resolution=RouteResolution(None, "Two routes pending confirmation"),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert decision.order is None


def test_missing_order_number_requires_review(service, customer, route) -> None:
    decision = service.evaluate(
        customer_match=_customer_match(customer),
        route_resolution=RouteResolution(route),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number=None,
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert decision.order is None
    assert any("order number" in reason.lower() for reason in decision.reasons)


def test_missing_delivery_date_requires_review(service, customer, route) -> None:
    decision = service.evaluate(
        customer_match=_customer_match(customer),
        route_resolution=RouteResolution(route),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=None,
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert any("delivery date" in reason.lower() for reason in decision.reasons)


def test_no_items_requires_review(service, customer, route) -> None:
    decision = service.evaluate(
        customer_match=_customer_match(customer),
        route_resolution=RouteResolution(route),
        items=(),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert any("no items" in reason.lower() for reason in decision.reasons)


def test_no_match_dominates_review(service, route) -> None:
    no_match_customer = CustomerMatchResult(outcome=MatchOutcome.NO_MATCH, reason="Not in catalog")

    decision = service.evaluate(
        customer_match=no_match_customer,
        route_resolution=RouteResolution(None, "Unresolved route"),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.NO_MATCH


def test_route_reason_is_not_duplicated_when_equal_to_customer_reason(
    service, customer
) -> None:
    shared_reason = "Name matches more than one catalog customer"
    review_customer = CustomerMatchResult(
        outcome=MatchOutcome.REVIEW_REQUIRED, reason=shared_reason
    )

    decision = service.evaluate(
        customer_match=review_customer,
        route_resolution=RouteResolution(None, shared_reason),
        items=_items("PEPIN PAN HOT DOG 8/1"),
        delivery_date=date(2026, 8, 10),
        order_number="4000326758",
    )

    assert decision.status is ProcessingStatus.REVIEW_REQUIRED
    assert decision.reasons.count(shared_reason) == 1
