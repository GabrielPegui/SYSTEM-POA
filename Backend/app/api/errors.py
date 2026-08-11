"""Mapping between application/domain errors and HTTP responses.

The API layer translates use-case and domain failures into consistent HTTP
status codes (Sprint 4):

- ``OrderNotFoundError`` -> 404 (the resource in the path does not exist).
- ``CustomerNotFoundError`` / ``RouteNotFoundError`` -> 404 (a referenced
  entity does not exist).
- ``AmbiguousCustomerError`` -> 409 (the name is not a unique reference).
- ``InvalidOrderStatusTransitionError`` -> 409 (state conflict).
- ``DomainValidationError`` -> 422 (unprocessable, invalid business input).
- Unexpected exceptions -> 500 with a generic message (details are logged).

Pydantic request validation failures (400/422) are handled by FastAPI itself.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.errors import (
    AmbiguousCustomerError,
    CustomerNotFoundError,
    InvalidOrderStatusTransitionError,
    OrderNotFoundError,
    RouteNotFoundError,
)
from app.core.logging import get_logger
from app.domain.exceptions import DomainValidationError

logger = get_logger(__name__)


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})


def register_exception_handlers(app: FastAPI) -> None:
    """Register the HTTP handlers for application and domain errors."""

    @app.exception_handler(OrderNotFoundError)
    async def order_not_found(_: Request, exc: OrderNotFoundError) -> JSONResponse:
        return _error_response(404, str(exc))

    @app.exception_handler(CustomerNotFoundError)
    async def customer_not_found(_: Request, exc: CustomerNotFoundError) -> JSONResponse:
        return _error_response(404, str(exc))

    @app.exception_handler(RouteNotFoundError)
    async def route_not_found(_: Request, exc: RouteNotFoundError) -> JSONResponse:
        return _error_response(404, str(exc))

    @app.exception_handler(AmbiguousCustomerError)
    async def ambiguous_customer(_: Request, exc: AmbiguousCustomerError) -> JSONResponse:
        return _error_response(409, str(exc))

    @app.exception_handler(InvalidOrderStatusTransitionError)
    async def invalid_transition(
        _: Request, exc: InvalidOrderStatusTransitionError
    ) -> JSONResponse:
        return _error_response(409, str(exc))

    @app.exception_handler(DomainValidationError)
    async def domain_validation(_: Request, exc: DomainValidationError) -> JSONResponse:
        return _error_response(422, str(exc))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled error on %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return _error_response(500, "Internal server error")
