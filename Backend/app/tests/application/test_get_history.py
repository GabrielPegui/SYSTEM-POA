"""GetHistory use case - decision documentation.

``ProcessingHistory`` persistence now exists (Pre-Sprint 8.1, Objective B):
every processing attempt is recorded as a ``ProcessingHistoryRecord`` (ADR-003
audit/traceability) in the ``processing_history`` table via the
``ProcessingHistoryRepository`` contract.

``GetHistory`` (the read side / API endpoint for the frontend) is still not
exposed: Pre-Sprint 8.1 only implements the persistence write path inside
``ProcessPurchaseOrder``. Exposing history retrieval is a separate concern
(contract, pagination, presentation) and is deliberately left for a follow-up.
"""

from app.application import use_cases
from app.domain.interfaces import repositories


def test_processing_history_repository_is_available() -> None:
    """History persistence exists and is exposed through the domain contract."""
    assert hasattr(repositories, "ProcessingHistoryRepository")


def test_get_history_use_case_is_not_exposed_yet() -> None:
    """The application layer does not expose a GetHistory use case yet."""
    assert not hasattr(use_cases, "GetHistory")
