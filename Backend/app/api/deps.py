"""Shared FastAPI dependencies (dependency injection entry points).

Providers wire the concrete SQLAlchemy repositories and the application use
cases. They are the seams that API tests override with in-memory fakes so
the endpoints can be exercised without a SQL Server instance.
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.use_cases import (
    CreateOrder,
    GetOrder,
    ListOrders,
    ValidateOrder,
)
from app.database.session import get_db
from app.infrastructure.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyRouteRepository,
)

DbSession = Annotated[Session | None, Depends(get_db)]


def _require_session(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    return db


def get_route_repository(db: DbSession):
    """Provide the route repository bound to the request session."""
    return SqlAlchemyRouteRepository(_require_session(db))


def get_customer_repository(db: DbSession):
    """Provide the customer repository bound to the request session."""
    return SqlAlchemyCustomerRepository(_require_session(db))


def get_product_repository(db: DbSession):
    """Provide the product repository bound to the request session."""
    return SqlAlchemyProductRepository(_require_session(db))


def get_order_repository(db: DbSession):
    """Provide the order repository bound to the request session."""
    return SqlAlchemyOrderRepository(_require_session(db))


def get_create_order(
    routes=Depends(get_route_repository),
    customers=Depends(get_customer_repository),
    products=Depends(get_product_repository),
    orders=Depends(get_order_repository),
) -> CreateOrder:
    """Provide the CreateOrder use case."""
    return CreateOrder(customers, routes, products, orders)


def get_get_order(orders=Depends(get_order_repository)) -> GetOrder:
    """Provide the GetOrder use case."""
    return GetOrder(orders)


def get_list_orders(orders=Depends(get_order_repository)) -> ListOrders:
    """Provide the ListOrders use case."""
    return ListOrders(orders)


def get_validate_order(orders=Depends(get_order_repository)) -> ValidateOrder:
    """Provide the ValidateOrder use case."""
    return ValidateOrder(orders)


__all__ = [
    "get_create_order",
    "get_customer_repository",
    "get_db",
    "get_get_order",
    "get_list_orders",
    "get_order_repository",
    "get_product_repository",
    "get_route_repository",
    "get_validate_order",
]
