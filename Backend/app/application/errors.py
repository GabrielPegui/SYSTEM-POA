"""Application-layer errors.

These exceptions represent use-case-level failures (e.g. a referenced entity
does not exist, or a state transition is not allowed). Domain validation
failures (``DomainValidationError``) are propagated as-is and are not wrapped
here to avoid duplicating validation between layers.
"""

from app.domain.enums import OrderStatus


class ApplicationError(Exception):
    """Base class for application-layer errors."""


class CustomerNotFoundError(ApplicationError):
    """Raised when a customer referenced by the use case does not exist."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Customer '{name}' was not found in the catalog")


class AmbiguousCustomerError(ApplicationError):
    """Raised when a customer name matches more than one catalog customer."""

    def __init__(self, name: str, routes: tuple[str, ...]) -> None:
        super().__init__(
            f"Customer '{name}' exists on more than one route: {', '.join(routes)}"
        )


class RouteNotFoundError(ApplicationError):
    """Raised when a route referenced by the use case does not exist."""

    def __init__(self, code: str) -> None:
        super().__init__(f"Route with code '{code}' was not found")


class OrderNotFoundError(ApplicationError):
    """Raised when the order being read or validated does not exist."""

    def __init__(self, order_number: str) -> None:
        super().__init__(f"Order with number '{order_number}' was not found")


class InvalidOrderStatusTransitionError(ApplicationError):
    """Raised when an order cannot transition from its current status."""

    def __init__(self, current: OrderStatus, target: OrderStatus) -> None:
        super().__init__(
            f"Order status cannot transition from '{current.value}' to '{target.value}'"
        )
