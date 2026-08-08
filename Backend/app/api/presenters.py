"""Presenters: map domain entities to API response schemas.

This mapping belongs to the presentation layer (ADR-001/ADR-003): domain
entities are never exposed directly, only their DTO representation.
"""

from app.api.schemas import (
    OrderItemResponse,
    OrderResponse,
    ProcessedCustomerCandidateResponse,
    ProcessedItemCandidateResponse,
    ProcessedItemResponse,
    ProcessOrderResponse,
)
from app.domain.document_processing.processing import ProcessedOrderResult
from app.domain.entities import Order


def to_order_response(order: Order) -> OrderResponse:
    """Convert a domain order into its API representation."""
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        customer_code=order.customer.code,
        customer_name=order.customer.name,
        route_code=order.customer.route.code,
        delivery_date=order.delivery_date,
        status=order.status,
        items=[
            OrderItemResponse(
                product_code=item.product.code,
                product_description=item.product.description,
                quantity=item.quantity,
            )
            for item in order.items
        ],
    )


def to_process_order_response(result: ProcessedOrderResult) -> ProcessOrderResponse:
    """Convert a processing workflow result into its API representation."""
    customer = result.customer_match.matched_customer if result.customer_match else None
    customer_candidates = [
        ProcessedCustomerCandidateResponse(
            code=customer.code,
            name=customer.name,
            route_code=customer.route.code,
        )
        for customer in (result.customer_match.candidates if result.customer_match else ())
    ]
    return ProcessOrderResponse(
        source_filename=result.source_filename,
        parser_id=result.parser_id,
        document_type=result.document_type.value,
        status=result.status.value,
        processed_at=result.processed_at,
        order_number=result.order_number,
        delivery_date=result.delivery_date,
        customer_code=customer.code if customer else None,
        customer_name=customer.name if customer else None,
        customer_candidates=customer_candidates,
        route_code=result.route.code if result.route else None,
        route_reason=result.route_reason,
        reasons=list(result.reasons),
        items=[
            ProcessedItemResponse(
                description=item.item.description,
                quantity=item.item.quantity,
                pdf_code=item.item.pdf_code,
                match_status=item.match.outcome.value,
                product_code=item.match.matched_product.code if item.match.matched_product else None,
                product_description=item.match.matched_product.description if item.match.matched_product else None,
                confidence=item.match.confidence,
                candidates=[
                    ProcessedItemCandidateResponse(code=candidate.code, description=candidate.description)
                    for candidate in item.match.candidates
                ],
                reason=item.match.reason,
            )
            for item in result.items
        ],
    )
