"""Shared fixtures for persistence tests.

Uses SQLite in-memory (allowed by ADR-003 for local testing) so the model
schema and repository round-trips can be exercised without a SQL Server
instance. The real schema is validated separately against SQL Server through
the versioned Alembic migrations.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.domain.entities import Customer, Order, OrderItem, Product, Route
from app.infrastructure.persistence import models  # noqa: F401  (register tables)
from app.infrastructure.persistence.models import (
    CustomerModel,
    ProductModel,
    RouteModel,
)


@pytest.fixture
def engine():
    """Fresh SQLite in-memory engine per test (isolates data between tests)."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    """Function-scoped session bound to the shared in-memory engine."""
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def route() -> Route:
    return Route(code="PPN002", name="Ozama")


@pytest.fixture
def customer(route: Route) -> Customer:
    return Customer(code="CL000168", name="JASON FAST FOOD", route=route)


@pytest.fixture
def product() -> Product:
    return Product(code="01010101", description="VIGA MEDIANA BLANCO PEPIN")


@pytest.fixture
def order_item(product: Product) -> OrderItem:
    return OrderItem(product=product, quantity=6)


@pytest.fixture
def order(customer: Customer, order_item: OrderItem) -> Order:
    return Order(
        order_number="12653",
        customer=customer,
        delivery_date=date(2026, 8, 10),
        items=(order_item,),
    )


@pytest.fixture
def seeded_catalog(session, order: Order) -> None:
    """Insert the route, customer and product referenced by ``order``.

    The persistence repository requires catalog references to already exist
    (matching first, persistence after); this fixture seeds them so ``save``
    can be exercised.
    """
    route_model = RouteModel(code=order.customer.route.code, name=order.customer.route.name)
    session.add(route_model)
    session.flush()
    session.add(
        CustomerModel(code=order.customer.code, name=order.customer.name, route_id=route_model.id)
    )
    for item in order.items:
        session.add(
            ProductModel(code=item.product.code, description=item.product.description)
        )
    session.commit()
