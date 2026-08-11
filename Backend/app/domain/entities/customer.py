"""Customer domain entity."""

from dataclasses import dataclass

from app.domain.entities.route import Route
from app.domain.exceptions import DomainValidationError
from app.domain.validation import require_not_blank, require_valid_optional_id


@dataclass(frozen=True)
class Customer:
    """A customer that sends purchase orders.

    The business key is the customer ``name`` from the source data
    (``docs/data/CLIENTES POR RUTA.xlsx``). There is no stable business code
    in the new model: the same name can appear on more than one route (e.g.
    ``INVERSIONES LLERS`` on PPN303 and PPN601), so the persistent uniqueness
    key is the composite ``(route, name)``.

    ``address`` is the location from the source data. It is not a unique key
    either, but it helps a human disambiguate equal names during review.
    """

    name: str
    route: Route
    address: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Customer name", self.name)
        require_valid_optional_id("Customer id", self.id)
        if self.route is None:
            raise DomainValidationError("Customer route is required")
