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
    """

    code: str
    name: str
    route: Route
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Customer code", self.code)
        require_not_blank("Customer name", self.name)
        require_valid_optional_id("Customer id", self.id)
        if self.route is None:
            raise DomainValidationError("Customer route is required")
