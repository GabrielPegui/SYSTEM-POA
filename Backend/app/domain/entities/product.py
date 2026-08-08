"""Product domain entity."""

from dataclasses import dataclass

from app.domain.validation import require_not_blank, require_valid_optional_id


@dataclass(frozen=True)
class Product:
    """A product from the fixed catalog.

    ``code`` is the unique business identifier found in the source data
    (e.g. ``01010101``). It will be used to match products extracted from
    purchase order documents.
    """

    code: str
    description: str
    id: int | None = None

    def __post_init__(self) -> None:
        require_not_blank("Product code", self.code)
        require_not_blank("Product description", self.description)
        require_valid_optional_id("Product id", self.id)
