"""Application use cases.

``GetHistory`` is intentionally not implemented in this sprint: it depends on
``ProcessingHistory`` persistence, which was deliberately excluded from the
Database Foundation (Sprint 2) and belongs to the PDF-processing pipeline
sprint. No placeholder or parallel infrastructure is created here (Sprint 3
scope). The gap is documented in ``app/tests/application/test_get_history.py``
and in the Sprint 3 report.
"""

from app.application.use_cases.clear_development_orders import ClearDevelopmentOrders
from app.application.use_cases.create_order import CreateOrder
from app.application.use_cases.get_order import GetOrder
from app.application.use_cases.list_orders import ListOrders
from app.application.use_cases.process_purchase_order import ProcessPurchaseOrder
from app.application.use_cases.validate_order import ValidateOrder

__all__ = [
    "ClearDevelopmentOrders",
    "CreateOrder",
    "GetOrder",
    "ListOrders",
    "ProcessPurchaseOrder",
    "ValidateOrder",
]
