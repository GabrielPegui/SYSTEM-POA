"""Mappers between domain entities and SQLAlchemy models.

The domain layer never depends on the ORM. Mapping happens at the edges of
the infrastructure layer so repositories can return domain entities while
persisting with SQLAlchemy models (ADR-001, ADR-003).
"""

from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.document_processing.processing import ProcessingStatus
from app.domain.entities import Customer, Order, OrderItem, Route
from app.domain.enums import OrderStatus
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    ProcessingHistoryModel,
    RouteModel,
)


def route_to_domain(model: RouteModel) -> Route:
    """Convert a route ORM model to a domain entity."""
    return Route(code=model.code, name=model.name, id=model.id)


def customer_to_domain(model: CustomerModel) -> Customer:
    """Convert a customer ORM model to a domain entity (route included)."""
    return Customer(
        name=model.name,
        route=route_to_domain(model.route),
        address=model.address,
        id=model.id,
    )


def order_to_domain(model: OrderModel) -> Order:
    """Convert an order ORM model to a domain entity (aggregate).

    Requires the relationship ``customer.route`` to be loaded (the
    repositories use eager loading).
    """
    return Order(
        order_number=model.order_number,
        customer=customer_to_domain(model.customer),
        delivery_date=model.delivery_date,
        items=tuple(
            OrderItem(
                description=item.description,
                quantity=item.quantity,
                pdf_code=item.pdf_code,
                ean=item.ean,
                id=item.id,
            )
            for item in model.items
        ),
        status=OrderStatus(model.status),
        id=model.id,
    )


def domain_to_item_model(item: OrderItem) -> OrderItemModel:
    """Build an order item ORM model from a domain item."""
    return OrderItemModel(
        description=item.description,
        quantity=item.quantity,
        pdf_code=item.pdf_code,
        ean=item.ean,
    )


def processing_history_to_domain(model: ProcessingHistoryModel) -> ProcessingHistoryRecord:
    """Convert a processing history ORM model to a domain entity."""
    return ProcessingHistoryRecord(
        source_filename=model.source_filename,
        status=ProcessingStatus(model.status),
        processed_at=model.processed_at,
        reasons=tuple(model.reasons or ()),
        order_number=model.order_number,
        parser_id=model.parser_id,
        customer_code=model.customer_code,
        customer_name=model.customer_name,
        route_code=model.route_code,
        route_name=model.route_name,
        item_count=model.item_count,
        id=model.id,
    )


def domain_to_history_model(record: ProcessingHistoryRecord) -> ProcessingHistoryModel:
    """Build a processing history ORM model from a domain record."""
    return ProcessingHistoryModel(
        source_filename=record.source_filename,
        status=record.status.value,
        reasons=list(record.reasons),
        order_number=record.order_number,
        parser_id=record.parser_id,
        customer_code=record.customer_code,
        customer_name=record.customer_name,
        route_code=record.route_code,
        route_name=record.route_name,
        item_count=record.item_count,
    )
