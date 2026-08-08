"""Validation gate before persisting a processed purchase order.

The gate decides the overall ``ProcessingStatus`` from the resolved customer,
route and per-item matches, and only builds a domain ``Order`` when every
reference is conclusive. Nothing is persisted on REVIEW_REQUIRED / NO_MATCH /
ERROR (ADR-003: matching first, persistence after; never create catalog
entities implicitly).
"""

from dataclasses import dataclass
from datetime import date

from app.application.services.route_resolution import RouteResolution
from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.document_processing.processing import (
    ProcessedItemResult,
    ProcessingStatus,
)
from app.domain.entities import Order, OrderItem


@dataclass(frozen=True)
class ValidationDecision:
    """Result of the validation gate.

    ``status`` is the overall outcome; ``reasons`` are the human-readable
    explanations for every block found. ``order`` is only built (not persisted)
    when ``status`` is PROCESSED.
    """

    status: ProcessingStatus
    reasons: tuple[str, ...]
    order: Order | None = None


class OrderValidationService:
    """Evaluates a processed document and builds the order when valid."""

    def evaluate(
        self,
        *,
        customer_match: CustomerMatchResult | None,
        route_resolution: RouteResolution,
        item_results: tuple[ProcessedItemResult, ...],
        delivery_date: date | None,
        order_number: str | None,
    ) -> ValidationDecision:
        reasons: list[str] = []
        has_no_match = customer_match is None or customer_match.outcome is MatchOutcome.NO_MATCH
        has_review = customer_match is not None and customer_match.outcome is MatchOutcome.REVIEW_REQUIRED

        if customer_match is None:
            reasons.append("Customer could not be identified")
        elif customer_match.outcome is not MatchOutcome.MATCHED:
            reasons.append(customer_match.reason)

        if not route_resolution.resolved:
            has_review = True
            if route_resolution.reason not in reasons:
                reasons.append(route_resolution.reason)
        if not order_number:
            has_review = True
            reasons.append("Order number is missing")
        if delivery_date is None:
            has_review = True
            reasons.append("Delivery date is missing")
        if not item_results:
            has_review = True
            reasons.append("No items were extracted from the document")

        for result in item_results:
            match = result.match
            if match.outcome is MatchOutcome.NO_MATCH:
                has_no_match = True
                reasons.append(f"Item '{result.item.description}': {match.reason}")
            elif match.outcome is MatchOutcome.REVIEW_REQUIRED:
                has_review = True
                reasons.append(f"Item '{result.item.description}': {match.reason}")

        if has_no_match:
            status = ProcessingStatus.NO_MATCH
        elif has_review:
            status = ProcessingStatus.REVIEW_REQUIRED
        else:
            status = ProcessingStatus.PROCESSED

        order = (
            self._build_order(order_number, customer_match, item_results, delivery_date)
            if status is ProcessingStatus.PROCESSED
            else None
        )
        return ValidationDecision(status=status, reasons=tuple(reasons), order=order)

    @staticmethod
    def _build_order(
        order_number: str | None,
        customer_match: CustomerMatchResult,
        item_results: tuple[ProcessedItemResult, ...],
        delivery_date: date | None,
    ) -> Order:
        assert customer_match.matched_customer is not None
        assert order_number is not None
        assert delivery_date is not None
        items = tuple(
            OrderItem(product=result.match.matched_product, quantity=result.item.quantity)
            for result in item_results
            if result.match.matched_product is not None
        )
        return Order(
            order_number=order_number,
            customer=customer_match.matched_customer,
            delivery_date=delivery_date,
            items=items,
        )
