"""Tests for the SQLAlchemy repository implementations.

Verifies that the chain ``Domain -> Repository -> Persistence -> DB`` works:
repositories persist domain entities and return domain entities back.
"""

from dataclasses import replace

import pytest
from sqlalchemy import func, select

from app.domain.enums import OrderStatus
from app.domain.exceptions import CatalogReferenceNotFoundError
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderModel,
    ProductModel,
    RouteModel,
)
from app.infrastructure.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
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
