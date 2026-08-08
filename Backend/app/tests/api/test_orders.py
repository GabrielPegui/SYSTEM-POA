"""Tests for the orders HTTP endpoints.

These tests validate the transport layer: routing, request/response mapping
(DTOs), status codes and error mapping. Business behavior is already covered
by the application-layer tests; the use cases here run against in-memory
fakes provided by ``app.tests.api.conftest``.
"""

from dataclasses import replace

from app.api.deps import get_create_order
from app.application.use_cases import CreateOrder
from app.domain.enums import OrderStatus
from app.tests.application.fakes import (
    FailingOrderRepository,
    InMemoryCustomerRepository,
    InMemoryOrderRepository,
    InMemoryProductRepository,
    InMemoryRouteRepository,
)


def _order_payload(**overrides):
    payload = {
        "order_number": "12653",
        "customer_code": "CL000168",
        "delivery_date": "2026-08-10",
        "items": [{"product_code": "01010101", "quantity": 6}],
    }
    payload.update(overrides)
    return payload


class TestCreateOrder:
    def test_create_order_returns_201_with_dto(self, client) -> None:
        response = client.post("/orders", json=_order_payload())

        assert response.status_code == 201
        body = response.json()
        assert body["order_number"] == "12653"
        assert body["customer_code"] == "CL000168"
        assert body["customer_name"] == "JASON FAST FOOD"
        assert body["route_code"] == "PPN002"
        assert body["delivery_date"] == "2026-08-10"
        assert body["status"] == OrderStatus.PROCESSED.value
        assert body["items"] == [
            {"product_code": "01010101", "product_description": "VIGA MEDIANA BLANCO PEPIN", "quantity": 6}
        ]
        assert body["id"] is not None

    def test_create_order_customer_not_found_returns_404(self, client) -> None:
        response = client.post("/orders", json=_order_payload(customer_code="CL999999"))

        assert response.status_code == 404
        assert "CL999999" in response.json()["detail"]

    def test_create_order_route_not_found_returns_404(self, client, customer) -> None:
        ghost = replace(customer, route=replace(customer.route, code="PPN999"))
        client.app.dependency_overrides[get_create_order] = lambda: CreateOrder(
            InMemoryCustomerRepository([ghost]),
            InMemoryRouteRepository(),
            InMemoryProductRepository(),
            InMemoryOrderRepository(),
        )
        response = client.post("/orders", json=_order_payload(customer_code=ghost.code))

        assert response.status_code == 404
        assert "PPN999" in response.json()["detail"]

    def test_create_order_product_not_found_returns_404(self, client) -> None:
        response = client.post(
            "/orders", json=_order_payload(items=[{"product_code": "01019999", "quantity": 6}])
        )

        assert response.status_code == 404
        assert "01019999" in response.json()["detail"]

    def test_create_order_blank_fields_return_422(self, client) -> None:
        response = client.post(
            "/orders", json=_order_payload(order_number="   ", customer_code="")
        )

        assert response.status_code == 422

    def test_create_order_missing_items_return_422(self, client) -> None:
        response = client.post("/orders", json=_order_payload(items=[]))

        assert response.status_code == 422

    def test_create_order_invalid_quantity_returns_422(self, client) -> None:
        response = client.post(
            "/orders", json=_order_payload(items=[{"product_code": "01010101", "quantity": 0}])
        )

        assert response.status_code == 422

    def test_create_order_malformed_body_returns_422(self, client) -> None:
        response = client.post("/orders", json={"order_number": "12653"})

        assert response.status_code == 422


class TestGetOrder:
    def test_get_order_returns_200(self, client, order_repo, order) -> None:
        order_repo.save(order)

        response = client.get(f"/orders/{order.order_number}")

        assert response.status_code == 200
        body = response.json()
        assert body["order_number"] == order.order_number
        assert body["customer_code"] == order.customer.code
        assert body["items"][0]["quantity"] == 6

    def test_get_order_not_found_returns_404(self, client) -> None:
        response = client.get("/orders/does-not-exist")

        assert response.status_code == 404


class TestListOrders:
    def test_list_orders_returns_orders(self, client, order_repo, order) -> None:
        order_repo.save(order)

        response = client.get("/orders")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["order_number"] == order.order_number

    def test_list_orders_empty(self, client) -> None:
        response = client.get("/orders")

        assert response.status_code == 200
        assert response.json() == []


class TestValidateOrder:
    def test_validate_order_returns_200(self, client, order_repo, order) -> None:
        order_repo.save(order)

        response = client.put(f"/orders/{order.order_number}/validate")

        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.VALIDATED.value

    def test_validate_order_not_found_returns_404(self, client) -> None:
        response = client.put("/orders/does-not-exist/validate")

        assert response.status_code == 404

    def test_validate_already_validated_returns_409(self, client, order_repo, order) -> None:
        order_repo.save(replace(order, status=OrderStatus.VALIDATED))

        response = client.put(f"/orders/{order.order_number}/validate")

        assert response.status_code == 409


class TestUnexpectedErrors:
    def test_persistence_error_returns_500(self, client, customer, product) -> None:
        failing = FailingOrderRepository(RuntimeError("database unavailable"))
        client.app.dependency_overrides[get_create_order] = lambda: CreateOrder(
            InMemoryCustomerRepository([customer]),
            InMemoryRouteRepository([customer.route]),
            InMemoryProductRepository([product]),
            failing,
        )

        response = client.post("/orders", json=_order_payload())

        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
