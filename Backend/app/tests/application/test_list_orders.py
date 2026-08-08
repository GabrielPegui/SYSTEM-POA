"""Tests for the ListOrders use case."""

from dataclasses import replace

from app.application.use_cases import ListOrders


def test_list_orders_returns_saved_orders(order_repo, order, list_orders) -> None:
    first = order_repo.save(order)
    second = order_repo.save(replace(order, order_number="12700"))

    result = list_orders.execute()

    assert len(result) == 2
    assert result[0].id == second.id
    assert result[1].id == first.id


def test_list_orders_empty(order_repo, list_orders) -> None:
    assert list_orders.execute() == []


def test_list_orders_returns_domain_orders(order_repo, order, list_orders: ListOrders) -> None:
    order_repo.save(order)

    result = list_orders.execute()

    assert result[0].order_number == order.order_number
    assert result[0].customer.code == order.customer.code
