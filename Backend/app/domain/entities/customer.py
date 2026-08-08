"""Customer domain entity."""

from dataclasses import dataclass

from app.domain.entities.route import Route
from app.domain.exceptions import DomainValidationError
from app.domain.validation import require_not_blank, require_valid_optional_id


@dataclass(frozen=True)
class Customer:
    """A customer that sends purchase orders.

    ``code`` is the business identifier found in the source data (e.g.
    ``CL000168``). Each customer belongs to exactly one route.

    ``rnc`` is the tax identifier present in the source data (``OUT_CLIENTES``
    column 2) and in the database schema. It is not a unique key: a single RNC
    maps to many accounts (``docs/ANALISIS_DATOS_MVP.md``), which is why it is
    only used as reinforcement by the customer matcher.
    """

    code: str
    name: str
    route: Route
    rnc: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Customer code", self.code)
        require_not_blank("Customer name", self.name)
        require_valid_optional_id("Customer id", self.id)
        if self.route is None:
            raise DomainValidationError("Customer route is required")
