"""Domain interfaces (abstract contracts implemented by infrastructure).

Includes repository contracts (ADR-001, ADR-003) and the PDF parser strategy
(ADR-002).
"""

from app.domain.interfaces.customer_matching import CustomerMatcher
from app.domain.interfaces.pdf_parsers import IPDFParser
from app.domain.interfaces.repositories import (
    CustomerRepository,
    OrderRepository,
    ProcessingHistoryRepository,
    RouteRepository,
)

__all__ = [
    "CustomerMatcher",
    "CustomerRepository",
    "IPDFParser",
    "OrderRepository",
    "ProcessingHistoryRepository",
    "RouteRepository",
]
