"""Catalog matching implementations (Sprint 7).

Contains the concrete ``ProductMatcher`` and ``CustomerMatcher``
implementations that decide the correspondence between document data and the
fixed catalog. Both follow the documented strategy (``docs/ANALISIS_DATOS_MVP.md``
and ADR-003): matching by description, never creating catalog entities, and
expressing uncertainty through MATCHED / REVIEW_REQUIRED / NO_MATCH.
"""
