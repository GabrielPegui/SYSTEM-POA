"""Catalog matching implementations (Sprint 7).

Contains the concrete ``CustomerMatcher`` implementation that decides the
correspondence between the document name and the customer catalog. It follows
the documented strategy (``docs/ANALISIS_DATOS_MVP.md`` and ADR-003):
matching by name, never creating catalog entities, and expressing uncertainty
through MATCHED / REVIEW_REQUIRED / NO_MATCH.
"""
