"""Domain enums."""

import enum


class OrderStatus(enum.Enum):
    """Status of an order (states documented in ADR-003).

    States:
    - ``PROCESSED``: the document was parsed and the order extracted.
    - ``PENDING_VALIDATION``: the order is waiting for human validation.
    - ``VALIDATED``: the order was validated by a human.
    - ``ERROR``: the document could not be processed correctly.
    """

    PROCESSED = "processed"
    PENDING_VALIDATION = "pending_validation"
    VALIDATED = "validated"
    ERROR = "error"
