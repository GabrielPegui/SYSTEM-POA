"""Purchase order HTTP endpoints.

The router is a thin transport layer (ADR-001): it maps request schemas onto
application commands, delegates to the use cases provided by dependency
injection, and returns DTOs. It contains no business rules, no direct
database access and no domain validation.
"""

import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import (
    get_create_order,
    get_get_order,
    get_list_orders,
    get_process_purchase_order,
    get_validate_order,
)
from app.api.presenters import (
    to_order_response,
    to_process_order_response,
)
from app.api.schemas import (
    CreateOrderRequest,
    OrderResponse,
    ProcessOrderResponse,
)
from app.application.commands import CreateOrderCommand, CreateOrderItemCommand
from app.application.use_cases import (
    CreateOrder,
    GetOrder,
    ListOrders,
    ProcessPurchaseOrder,
    ValidateOrder,
)
from app.core.config import settings

router = APIRouter(prefix="/orders", tags=["orders"])

_PDF_MAGIC = b"%PDF"


@router.post(
    "/process",
    response_model=ProcessOrderResponse,
    summary="Process a purchase order PDF",
)
def process_order(
    file: Annotated[UploadFile, File(description="Purchase order PDF")],
    use_case: Annotated[ProcessPurchaseOrder, Depends(get_process_purchase_order)],
) -> ProcessOrderResponse:
    """Run the full processing pipeline on an uploaded PDF.

    The outcome is always returned as a ``ProcessOrderResponse`` with a
    ``status`` field: ``processed`` (order persisted), ``review_required``,
    ``no_match`` or ``error``. Nothing is persisted on review/no-match/error.
    Oversized or non-PDF uploads are rejected before processing.
    """
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {settings.max_upload_mb} MB",
        )
    if not content.startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Uploaded file is not a PDF",
        )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp.write(content)
        temp_path = temp.name
    try:
        source_filename = Path(file.filename or "").name or None
        result = use_case.execute(Path(temp_path), source_filename=source_filename)
        return to_process_order_response(result)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a purchase order",
)
def create_order(
    payload: CreateOrderRequest,
    use_case: Annotated[CreateOrder, Depends(get_create_order)],
) -> OrderResponse:
    """Register a structured purchase order and return it."""
    command = CreateOrderCommand(
        order_number=payload.order_number,
        customer_code=payload.customer_code,
        delivery_date=payload.delivery_date,
        items=tuple(
            CreateOrderItemCommand(product_code=item.product_code, quantity=item.quantity)
            for item in payload.items
        ),
    )
    return to_order_response(use_case.execute(command))


@router.get(
    "/{order_number}",
    response_model=OrderResponse,
    summary="Get an order by its business number",
)
def get_order(
    order_number: str,
    use_case: Annotated[GetOrder, Depends(get_get_order)],
) -> OrderResponse:
    """Return the order matching the given business number."""
    return to_order_response(use_case.execute(order_number))


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List orders",
)
def list_orders(
    use_case: Annotated[ListOrders, Depends(get_list_orders)],
) -> list[OrderResponse]:
    """Return the persisted orders, newest first."""
    return [to_order_response(order) for order in use_case.execute()]


@router.put(
    "/{order_number}/validate",
    response_model=OrderResponse,
    summary="Validate an order after human review",
)
def validate_order(
    order_number: str,
    use_case: Annotated[ValidateOrder, Depends(get_validate_order)],
) -> OrderResponse:
    """Validate the order matching the given business number."""
    return to_order_response(use_case.execute(order_number))
