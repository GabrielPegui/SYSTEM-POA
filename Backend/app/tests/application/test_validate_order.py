"""Tests for the ValidateOrder use case."""

from dataclasses import replace

import pytest

from app.application.errors import InvalidOrderStatusTransitionError, OrderNotFoundError
from app.domain.enums import OrderStatus


def test_validate_processed_order(order_repo, order, validate_order) -> None:
    order_repo.save(order)

    result = validate_order.execute(order.order_number)

    assert result.status is OrderStatus.VALIDATED
    persisted = order_repo.get_by_number(order.order_number)
    assert persisted is not None
    assert persisted.status is OrderStatus.VALIDATED


def test_validate_pending_validation_order(order_repo, order, validate_order) -> None:
    pending = replace(order, status=OrderStatus.PENDING_VALIDATION)
    order_repo.save(pending)

    result = validate_order.execute(order.order_number)

    assert result.status is OrderStatus.VALIDATED


def test_validate_order_not_found(validate_order) -> None:
    with pytest.raises(OrderNotFoundError):
        validate_order.execute("does-not-exist")


def test_validate_already_validated_raises(order_repo, order, validate_order) -> None:
    validated = replace(order, status=OrderStatus.VALIDATED)
    order_repo.save(validated)

    with pytest.raises(InvalidOrderStatusTransitionError):
        validate_order.execute(order.order_number)


def test_validate_error_state_raises(order_repo, order, validate_order) -> None:
    errored = replace(order, status=OrderStatus.ERROR)
    order_repo.save(errored)

    with pytest.raises(InvalidOrderStatusTransitionError):
        validate_order.execute(order.order_number)
