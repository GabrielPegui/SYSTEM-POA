"""Minimal domain validation guards.

Guards are intentionally small and explicit. They validate only the
invariants required by the documented business rules; they do not assume
code, name or number formats that are not documented.
"""

from app.domain.exceptions import DomainValidationError


def require_not_blank(field: str, value: str) -> None:
    """Ensure a business key or name field is not empty or whitespace only."""
    if not value or not value.strip():
        raise DomainValidationError(f"{field} must not be blank")


def require_positive_int(field: str, value: int) -> None:
    """Ensure a numeric field (e.g. quantity) is strictly positive."""
    if value <= 0:
        raise DomainValidationError(f"{field} must be greater than zero")


def require_valid_optional_id(field: str, value: int | None) -> None:
    """Ensure an optional surrogate id is a positive integer when provided."""
    if value is not None and value <= 0:
        raise DomainValidationError(f"{field} must be a positive integer when provided")
