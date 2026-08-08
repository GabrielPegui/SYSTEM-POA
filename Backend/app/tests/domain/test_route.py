"""Tests for the Route entity."""

import pytest

from app.domain.entities import Route
from app.domain.exceptions import DomainValidationError


def test_valid_route_creation() -> None:
    route = Route(code="PPN002")

    assert route.code == "PPN002"
    assert route.name is None
    assert route.id is None


def test_route_with_name_and_id() -> None:
    route = Route(code="PPN601", name="Santiago", id=1)

    assert route.code == "PPN601"
    assert route.name == "Santiago"
    assert route.id == 1


def test_route_blank_code_raises() -> None:
    with pytest.raises(DomainValidationError):
        Route(code="   ")


@pytest.mark.parametrize("invalid_id", [0, -1])
def test_route_invalid_id_raises(invalid_id: int) -> None:
    with pytest.raises(DomainValidationError):
        Route(code="PPN002", id=invalid_id)


def test_route_is_frozen() -> None:
    route = Route(code="PPN002")
    with pytest.raises(Exception):
        route.code = "OTHER"  # type: ignore[misc]
