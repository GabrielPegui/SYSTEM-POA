"""Request and response schemas for the orders API.

These Pydantic models are the HTTP contract between the frontend and the
backend (ADR-001: API is the presentation layer). They are kept separate
from the database models and the domain entities; the router maps them onto
the application commands and the use-case results (ADR-003).

Decision (Sprint 4): the order identifier used in the URL paths is the
business ``order_number`` (the natural key used by the application use
cases), not the surrogate ``id``. The surrogate ``id`` is still returned in
responses for reference.

Definitive model (Pre-Sprint 9): the customer is identified by ``name`` (its
business key) and there is no product catalog; order lines carry the product
description exactly as printed in the PDF, plus ``pdf_code``/``ean`` as
traceability only.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import OrderStatus


class CreateOrderItemRequest(BaseModel):
    """A single line of an order being created."""

    description: str = Field(min_length=1, examples=["PEPIN PAN HOT DOG 8/1"])
    quantity: int = Field(gt=0, examples=[6])
    pdf_code: str | None = None
    ean: str | None = None


class CreateOrderRequest(BaseModel):
    """Body to register a structured purchase order."""

    order_number: str = Field(min_length=1, examples=["12653"])
    customer_name: str = Field(min_length=1, examples=["SUPERMERCADO CENTRAL"])
    delivery_date: date = Field(examples=["2026-08-10"])
    items: list[CreateOrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    """A line of an order in API responses."""

    description: str
    quantity: int
    pdf_code: str | None = None
    ean: str | None = None


class OrderResponse(BaseModel):
    """An order as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_name: str
    route_code: str
    delivery_date: date
    status: OrderStatus
    items: list[OrderItemResponse]


class ProcessedCustomerCandidateResponse(BaseModel):
    """A catalog customer offered as a candidate for review."""

    name: str
    route_code: str
    address: str | None = None


class ProcessedItemResponse(BaseModel):
    """A single extracted line, as printed in the PDF."""

    description: str
    quantity: int
    pdf_code: str | None = None
    ean: str | None = None


class ProcessOrderResponse(BaseModel):
    """Outcome of processing a purchase order PDF.

    ``status`` is one of ``processed`` / ``review_required`` / ``no_match`` /
    ``error``. ``customer_code`` is the identifier as printed in the document
    (traceability). ``customer_name`` is the resolved catalog name when a
    unique match exists, otherwise the name as printed in the document;
    ``customer_candidates`` offers the catalog customers a human should choose
    from when the name is ambiguous.
    """

    source_filename: str
    parser_id: str
    document_type: str
    status: str
    processed_at: datetime
    order_number: str | None = None
    delivery_date: date | None = None
    customer_code: str | None = None
    customer_name: str | None = None
    customer_candidates: list[ProcessedCustomerCandidateResponse] = []
    route_code: str | None = None
    route_reason: str = ""
    reasons: list[str] = []
    items: list[ProcessedItemResponse] = []
