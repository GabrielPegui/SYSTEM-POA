"""Tests for the GetOrder use case."""

import pytest

from app.application.errors import OrderNotFoundError


def test_get_order_success(order_repo, order, get_order) -> None:
    order_repo.save(order)

    result = get_order.execute(order.order_number)

    assert result.order_number == order.order_number
    assert result.id is not None
    assert result.customer.name == order.customer.name
    assert result.items[0].description == order.items[0].description


def test_get_order_not_found(get_order) -> None:
    with pytest.raises(OrderNotFoundError):
        get_order.execute("does-not-exist")
