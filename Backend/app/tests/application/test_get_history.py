"""GetHistory use case - decision documentation.

``ProcessingHistory`` persistence does not exist yet: it was deliberately
excluded from the Database Foundation (Sprint 2) and belongs to the
PDF-processing pipeline sprint. Therefore ``GetHistory`` cannot be implemented
correctly in Sprint 3 without inventing infrastructure that is out of scope.

Following the sprint rules, no placeholder and no parallel history
infrastructure is created here. These tests document that decision instead of
faking an implementation.
"""

from app.application import use_cases
from app.domain.interfaces import repositories


def test_get_history_is_deferred_until_history_persistence_exists() -> None:
    """History persistence is not part of the current architecture."""
    assert not hasattr(repositories, "ProcessingHistoryRepository")


def test_get_history_use_case_is_not_exposed_yet() -> None:
    """The application layer does not expose a GetHistory use case."""
    assert not hasattr(use_cases, "GetHistory")
