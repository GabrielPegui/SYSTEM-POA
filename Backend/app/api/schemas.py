"""Request and response schemas for the orders API.

These Pydantic models are the HTTP contract between the frontend and the
backend (ADR-001: API is the presentation layer). They are kept separate
from the database models and the domain entities; the router maps them onto
the application commands and the use-case results (ADR-003).

Decision (Sprint 4): the order identifier used in the URL paths is the
business ``order_number`` (the natural key used by the application use
cases), not the surrogate ``id``. The surrogate ``id`` is still returned in
responses for reference.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import OrderStatus


class CreateOrderItemRequest(BaseModel):
    """A single line of an order being created."""

    product_code: str = Field(min_length=1, examples=["01010101"])
    quantity: int = Field(gt=0, examples=[6])


class CreateOrderRequest(BaseModel):
    """Body to register a structured purchase order."""

    order_number: str = Field(min_length=1, examples=["12653"])
    customer_code: str = Field(min_length=1, examples=["CL000168"])
    delivery_date: date = Field(examples=["2026-08-10"])
    items: list[CreateOrderItemRequest] = Field(min_length=1)


class OrderItemResponse(BaseModel):
    """A line of an order in API responses."""

    product_code: str
    product_description: str
    quantity: int


class OrderResponse(BaseModel):
    """An order as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_code: str
    customer_name: str
    route_code: str
    delivery_date: date
    status: OrderStatus
    items: list[OrderItemResponse]


class ProcessedItemCandidateResponse(BaseModel):
    """A catalog product offered as a candidate for review."""

    code: str
    description: str


class ProcessedItemResponse(BaseModel):
    """A single extracted line plus its matching evidence."""

    description: str
    quantity: int
    pdf_code: str | None = None
    match_status: str
    product_code: str | None = None
    product_description: str | None = None
    confidence: float | None = None
    candidates: list[ProcessedItemCandidateResponse] = []
    reason: str = ""


class ProcessedCustomerCandidateResponse(BaseModel):
    """A catalog account offered as a candidate for review."""

    code: str
    name: str
    route_code: str


class ProcessOrderResponse(BaseModel):
    """Outcome of processing a purchase order PDF.

    ``status`` is one of ``processed`` / ``review_required`` / ``no_match`` /
    ``error``. ``items`` always carries per-line matching evidence so the
    frontend can show which lines need human review.
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
