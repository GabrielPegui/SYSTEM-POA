"""Tests for repository contracts.

Contracts are abstract; concrete implementations belong to the
infrastructure layer (Sprint 3). These tests ensure the contracts exist and
cannot be instantiated directly (forcing implementations).
"""

import pytest

from app.domain.interfaces import (
    CustomerRepository,
    OrderRepository,
    RouteRepository,
)


@pytest.mark.parametrize(
    "contract",
    [RouteRepository, CustomerRepository, OrderRepository],
)
def test_repository_contracts_are_abstract(contract) -> None:
    with pytest.raises(TypeError):
        contract()


def test_repository_contracts_are_importable() -> None:
    assert RouteRepository.__name__ == "RouteRepository"
    assert CustomerRepository.__name__ == "CustomerRepository"
    assert OrderRepository.__name__ == "OrderRepository"
