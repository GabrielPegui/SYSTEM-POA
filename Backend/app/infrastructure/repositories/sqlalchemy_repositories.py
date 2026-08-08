"""SQLAlchemy repository implementations.

These classes implement the contracts defined in
``app.domain.interfaces.repositories`` using a SQLAlchemy ``Session``. They
map persisted rows back to domain entities through
``app.infrastructure.persistence.mappers``.

``OrderRepository.save`` persists an order whose catalog references (route,
customer, products) must already exist. It never creates catalog entities
implicitly: matching must resolve the correspondence first, then persistence
stores it (matching first, persistence after). If a referenced route,
customer or product is missing, ``CatalogReferenceNotFoundError`` is raised.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.entities import Customer, Order, Product, Route
from app.domain.enums import OrderStatus
from app.domain.exceptions import CatalogReferenceNotFoundError
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
    ProductRepository,
    RouteRepository,
)
from app.infrastructure.persistence.mappers import (
    customer_to_domain,
    domain_to_item_model,
    order_to_domain,
    product_to_domain,
    route_to_domain,
)
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    ProductModel,
    RouteModel,
)


def _order_load_options() -> list:
    return [
        selectinload(OrderModel.items).selectinload(OrderItemModel.product),
        selectinload(OrderModel.customer).selectinload(CustomerModel.route),
    ]


class SqlAlchemyRouteRepository(RouteRepository):
    """SQLAlchemy implementation of the route repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Route | None:
        model = self._session.scalars(
            select(RouteModel).where(RouteModel.code == code)
        ).first()
        return route_to_domain(model) if model is not None else None


class SqlAlchemyCustomerRepository(CustomerRepository):
    """SQLAlchemy implementation of the customer repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Customer | None:
        model = self._session.scalars(
            select(CustomerModel)
            .options(selectinload(CustomerModel.route))
            .where(CustomerModel.code == code)
        ).first()
        return customer_to_domain(model) if model is not None else None


class SqlAlchemyProductRepository(ProductRepository):
    """SQLAlchemy implementation of the product repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Product | None:
        model = self._session.scalars(
            select(ProductModel).where(ProductModel.code == code)
        ).first()
        return product_to_domain(model) if model is not None else None


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of the order repository.

    ``save`` persists the full order aggregate. The referenced route, customer
    and products must already exist in the catalog; they are looked up by
    their natural codes and a ``CatalogReferenceNotFoundError`` is raised if
    any is missing. Persistence never creates catalog entities implicitly.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, order: Order) -> Order:
        self._require_route(order.customer.route.code)
        customer_model = self._require_customer(order.customer.code)

        order_model = OrderModel(
            order_number=order.order_number,
            customer_id=customer_model.id,
            delivery_date=order.delivery_date,
            status=order.status.value,
        )
        for item in order.items:
            product_model = self._require_product(item.product.code)
            order_model.items.append(domain_to_item_model(product_model, item))

        self._session.add(order_model)
        self._session.flush()
        self._session.commit()

        persisted = self._session.scalars(
            select(OrderModel)
            .options(*_order_load_options())
            .where(OrderModel.id == order_model.id)
        ).one()
        return order_to_domain(persisted)

    def get_by_number(self, order_number: str) -> Order | None:
        model = self._session.scalars(
            select(OrderModel)
            .options(*_order_load_options())
            .where(OrderModel.order_number == order_number)
            .order_by(OrderModel.id)
            .limit(1)
        ).first()
        return order_to_domain(model) if model is not None else None

    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        model = self._session.get(OrderModel, order_id)
        if model is None:
            raise RuntimeError(f"Order with id {order_id} was not found")
        model.status = status.value
        self._session.flush()
        self._session.commit()
        persisted = self._session.scalars(
            select(OrderModel)
            .options(*_order_load_options())
            .where(OrderModel.id == order_id)
        ).one()
        return order_to_domain(persisted)

    def list(self) -> list[Order]:
        models = self._session.scalars(
            select(OrderModel)
            .options(*_order_load_options())
            .order_by(OrderModel.id.desc())
        ).all()
        return [order_to_domain(model) for model in models]

    def _require_route(self, code: str) -> RouteModel:
        model = self._session.scalars(
            select(RouteModel).where(RouteModel.code == code)
        ).first()
        if model is None:
            raise CatalogReferenceNotFoundError("Route", code)
        return model

    def _require_customer(self, code: str) -> CustomerModel:
        model = self._session.scalars(
            select(CustomerModel).where(CustomerModel.code == code)
        ).first()
        if model is None:
            raise CatalogReferenceNotFoundError("Customer", code)
        return model

    def _require_product(self, code: str) -> ProductModel:
        model = self._session.scalars(
            select(ProductModel).where(ProductModel.code == code)
        ).first()
        if model is None:
            raise CatalogReferenceNotFoundError("Product", code)
        return model
