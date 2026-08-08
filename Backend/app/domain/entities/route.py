"""Route domain entity."""

from dataclasses import dataclass

from app.domain.validation import require_not_blank, require_valid_optional_id


@dataclass(frozen=True)
class Route:
    """A distribution route.

    Routes maintain a fixed structure. Each customer belongs to exactly one
    route (documented business rule).

    ``code`` is the business identifier found in the source data (e.g.
    ``PPN002``, ``PPN601``).
    """

    code: str
    name: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Route code", self.code)
        require_valid_optional_id("Route id", self.id)
