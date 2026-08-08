"""Tests for the SQLAlchemy repository implementations.

Verifies that the chain ``Domain -> Repository -> Persistence -> DB`` works:
repositories persist domain entities and return domain entities back.
"""

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.domain.document_processing.history import ProcessingHistoryRecord
from app.domain.document_processing.processing import ProcessingStatus
from app.domain.enums import OrderStatus
from app.domain.exceptions import CatalogReferenceNotFoundError
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    ProcessingHistoryModel,
    ProductModel,
    RouteModel,
)
from app.infrastructure.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProcessingHistoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyRouteRepository,
)


def test_route_repository_get_by_code(session, route) -> None:
    session.add(RouteModel(code=route.code, name=route.name))
    session.commit()

    result = SqlAlchemyRouteRepository(session).get_by_code(route.code)

    assert result is not None
    assert result.code == route.code
    assert result.name == route.name
    assert result.id is not None


def test_route_repository_get_by_code_missing(session) -> None:
    assert SqlAlchemyRouteRepository(session).get_by_code("PPN999") is None


def test_customer_repository_returns_route(session, route, customer) -> None:
    route_model = RouteModel(code=route.code, name=route.name)
    session.add(route_model)
    session.flush()
    session.add(CustomerModel(code=customer.code, name=customer.name, route_id=route_model.id))
    session.commit()

    result = SqlAlchemyCustomerRepository(session).get_by_code(customer.code)

    assert result is not None
    assert result.code == customer.code
    assert result.route.code == route.code
    assert result.id is not None


def test_product_repository_get_by_code(session, product) -> None:
    session.add(ProductModel(code=product.code, description=product.description))
    session.commit()

    result = SqlAlchemyProductRepository(session).get_by_code(product.code)

    assert result is not None
    assert result.code == product.code
    assert result.description == product.description


def test_order_repository_save_persists_aggregate(session, order, seeded_catalog) -> None:
    saved = SqlAlchemyOrderRepository(session).save(order)

    assert saved.id is not None
    assert saved.order_number == order.order_number
    assert saved.status == order.status
    assert saved.customer.code == order.customer.code
    assert saved.customer.route.code == order.customer.route.code
    assert saved.delivery_date == order.delivery_date
    assert len(saved.items) == 1
    assert saved.items[0].quantity == order.items[0].quantity
    assert isinstance(saved.items[0].quantity, int)
    assert saved.items[0].product.code == order.items[0].product.code


def test_order_repository_save_requires_existing_references(session, order) -> None:
    assert session.scalar(select(func.count()).select_from(RouteModel)) == 0
    assert session.scalar(select(func.count()).select_from(CustomerModel)) == 0
    assert session.scalar(select(func.count()).select_from(ProductModel)) == 0

    with pytest.raises(CatalogReferenceNotFoundError):
        SqlAlchemyOrderRepository(session).save(order)

    assert session.scalar(select(func.count()).select_from(RouteModel)) == 0
    assert session.scalar(select(func.count()).select_from(CustomerModel)) == 0
    assert session.scalar(select(func.count()).select_from(ProductModel)) == 0
    assert session.scalar(select(func.count()).select_from(OrderModel)) == 0


def test_order_repository_save_rolls_back_on_db_error(session, order, seeded_catalog, monkeypatch) -> None:
    """A DB failure during save must not leave partial rows and must leave the
    session usable (rollback, not a poisoned transaction)."""
    repo = SqlAlchemyOrderRepository(session)
    assert session.scalar(select(func.count()).select_from(OrderModel)) == 0

    def boom_commit(*_args, **_kwargs) -> None:
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(session, "commit", boom_commit)

    with pytest.raises(RuntimeError):
        repo.save(order)

    assert session.scalar(select(func.count()).select_from(OrderModel)) == 0
    assert session.scalar(select(func.count()).select_from(OrderItemModel)) == 0

    monkeypatch.undo()
    session.rollback()

    saved = repo.save(order)
    assert saved.id is not None
    assert session.scalar(select(func.count()).select_from(OrderModel)) == 1


def test_order_repository_save_reuses_existing_references(session, order, seeded_catalog) -> None:
    SqlAlchemyOrderRepository(session).save(order)

    assert session.scalar(select(func.count()).select_from(RouteModel)) == 1
    assert session.scalar(select(func.count()).select_from(CustomerModel)) == 1
    assert session.scalar(select(func.count()).select_from(ProductModel)) == 1
    assert session.scalar(select(func.count()).select_from(OrderModel)) == 1


def test_order_repository_get_by_number(session, order, seeded_catalog) -> None:
    SqlAlchemyOrderRepository(session).save(order)

    result = SqlAlchemyOrderRepository(session).get_by_number(order.order_number)

    assert result is not None
    assert result.order_number == order.order_number
    assert result.customer.code == order.customer.code
    assert result.items[0].product.code == order.items[0].product.code


def test_order_repository_get_by_number_missing(session) -> None:
    assert SqlAlchemyOrderRepository(session).get_by_number("does-not-exist") is None


def test_order_repository_update_status(session, order, seeded_catalog) -> None:
    repo = SqlAlchemyOrderRepository(session)
    saved = repo.save(order)

    assert saved.status is OrderStatus.PROCESSED

    updated = repo.update_status(saved.id, OrderStatus.VALIDATED)

    assert updated.status is OrderStatus.VALIDATED
    assert updated.order_number == order.order_number
    fetched = repo.get_by_number(order.order_number)
    assert fetched is not None
    assert fetched.status is OrderStatus.VALIDATED


def test_order_repository_list_newest_first(session, order, seeded_catalog) -> None:
    repo = SqlAlchemyOrderRepository(session)
    first = repo.save(order)
    second = repo.save(replace(order, order_number="12700"))

    result = repo.list()

    assert len(result) == 2
    assert result[0].id == second.id
    assert result[1].id == first.id


def test_order_repository_list_empty(session) -> None:
    assert SqlAlchemyOrderRepository(session).list() == []


def _history_record(**overrides) -> ProcessingHistoryRecord:
    fields = dict(
        source_filename="4000326758.pdf",
        status=ProcessingStatus.PROCESSED,
        reasons=("ok",),
        order_number="4000326758",
        parser_id="mercadal_parser",
        customer_code="CL000004-101",
        customer_name="MERCADAL GUARICANO",
        route_code="PPN006",
        route_name="Ruta 6",
        item_count=10,
    )
    fields.update(overrides)
    return ProcessingHistoryRecord(**fields)


def test_history_repository_save_roundtrip(session) -> None:
    record = _history_record()

    saved = SqlAlchemyProcessingHistoryRepository(session).save(record)

    assert saved.id is not None
    assert saved.source_filename == record.source_filename
    assert saved.status is ProcessingStatus.PROCESSED
    assert saved.reasons == record.reasons
    assert saved.order_number == record.order_number
    assert saved.parser_id == record.parser_id
    assert saved.customer_code == record.customer_code
    assert saved.customer_name == record.customer_name
    assert saved.route_code == record.route_code
    assert saved.route_name == record.route_name
    assert saved.item_count == record.item_count
    assert saved.processed_at is not None


def test_history_repository_saves_non_processed_statuses(session) -> None:
    repo = SqlAlchemyProcessingHistoryRepository(session)
    statuses = [
        ProcessingStatus.REVIEW_REQUIRED,
        ProcessingStatus.NO_MATCH,
        ProcessingStatus.ERROR,
    ]

    for status in statuses:
        record = _history_record(status=status, order_number=None)
        saved = repo.save(record)
        assert saved.id is not None
        assert saved.status is status

    assert session.scalar(select(func.count()).select_from(ProcessingHistoryModel)) == 3


def test_history_repository_list_newest_first(session) -> None:
    repo = SqlAlchemyProcessingHistoryRepository(session)
    first = repo.save(_history_record(source_filename="a.pdf"))
    second = repo.save(_history_record(source_filename="b.pdf"))

    result = repo.list()

    assert len(result) == 2
    assert result[0].id == second.id
    assert result[1].id == first.id


def test_history_repository_save_rolls_back_on_db_error(session, monkeypatch) -> None:
    repo = SqlAlchemyProcessingHistoryRepository(session)
    assert session.scalar(select(func.count()).select_from(ProcessingHistoryModel)) == 0

    def boom_commit(*_args, **_kwargs) -> None:
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(session, "commit", boom_commit)

    with pytest.raises(RuntimeError):
        repo.save(_history_record())

    assert session.scalar(select(func.count()).select_from(ProcessingHistoryModel)) == 0

    monkeypatch.undo()
    session.rollback()

    saved = repo.save(_history_record())
    assert saved.id is not None
    assert session.scalar(select(func.count()).select_from(ProcessingHistoryModel)) == 1
