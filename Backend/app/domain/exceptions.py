"""Domain-level exceptions.

These are the only exception types the domain layer raises. They allow the
application layer to distinguish domain validation failures from framework
or infrastructure errors without depending on domain internals.
"""


class DomainError(Exception):
    """Base class for all domain errors."""


class DomainValidationError(DomainError):
    """Raised when an entity cannot be constructed with a valid state."""


class CatalogReferenceNotFoundError(DomainError):
    """Raised when a catalog entity referenced by an order is missing.

    Persistence must never create catalog entities implicitly (matching first,
    persistence after). If a route, customer or product referenced by an order
    is not in the catalog, the order cannot be persisted.
    """

    def __init__(self, entity: str, code: str) -> None:
        super().__init__(f"{entity} with code '{code}' is not in the catalog")
