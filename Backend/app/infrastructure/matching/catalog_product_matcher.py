"""Product matcher against the fixed catalog (Sprint 7).

Implements the ``ProductMatcher`` contract using the documented strategy
(ADR-003): the catalog has no usable EAN and the PDF codes differ from the
catalog keys, so matching is by description.

``pdf_code`` is traceability only (``PurchaseOrderItemDocument``): it is an
identifier printed in the PDF, NOT a catalog key, and it never drives
matching. Selecting by ``pdf_code`` could silently match the wrong catalog
product when a PDF code happens to equal a catalog key, so the matcher
deliberately ignores it. Whether ``pdf_code`` corresponds to the official
BOLIN catalog code is a pending business question (documented in
``docs/ANALISIS_DATOS_MVP.md`` and the sprint report).

Decision order:

1. Normalized exact description.
2. Token similarity (Jaccard with gender-stemmed normalization).

Outcome rules (calibrated against the real catalog and sample PDFs):

- ``MATCHED``: best score >= 0.70, or best >= 0.50 with a margin >= 0.15
  over the runner-up.
- ``REVIEW_REQUIRED``: best score >= 0.35 but not conclusive; top candidates
  are reported.
- ``NO_MATCH``: best score < 0.35 (e.g. ``BOLIN BURGER`` against the real
  catalog scores ~0.17 and must never be persisted).

The catalog product marked ``NO USAR`` is excluded from candidates: it is
explicitly unusable and must never be selected.
"""

from app.domain.document_processing.matching import MatchOutcome, MatchResult
from app.domain.document_processing.purchase_order import PurchaseOrderItemDocument
from app.domain.entities import Product
from app.domain.interfaces import ProductMatcher
from app.domain.interfaces.repositories import ProductRepository
from app.infrastructure.matching.text_utils import jaccard, normalize_text, token_set

_MATCHED_THRESHOLD = 0.70
_LOW_MATCH_THRESHOLD = 0.50
_REVIEW_THRESHOLD = 0.35
_MARGIN = 0.15
_MAX_CANDIDATES = 3
_NO_USAR = "no usar"


class CatalogProductMatcher(ProductMatcher):
    """ProductMatcher implementation over the product catalog."""

    def __init__(self, products: ProductRepository) -> None:
        catalog = [product for product in products.list() if normalize_text(product.description) != _NO_USAR]
        self._catalog = tuple(sorted(catalog, key=lambda p: p.code))

    def match(self, item: PurchaseOrderItemDocument) -> MatchResult:
        exact = self._exact_description(item.description)
        if exact is not None:
            return MatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_product=exact,
                confidence=1.0,
                reason="Exact description match",
            )

        query = token_set(item.description)
        if not query:
            return MatchResult(outcome=MatchOutcome.NO_MATCH, reason="Item description has no tokens")

        scored = sorted(
            ((jaccard(query, token_set(product.description)), product) for product in self._catalog),
            reverse=True,
            key=lambda pair: (pair[0], pair[1].code),
        )
        if not scored:
            return MatchResult(outcome=MatchOutcome.NO_MATCH, reason="Catalog has no products")
        best_score, best = scored[0]
        runner_score = scored[1][0] if len(scored) > 1 else 0.0

        if best_score >= _MATCHED_THRESHOLD:
            return self._matched(best, best_score, f"Description similarity {best_score:.2f}")
        if best_score >= _LOW_MATCH_THRESHOLD and best_score - runner_score >= _MARGIN:
            return self._matched(
                best, best_score, f"Description similarity {best_score:.2f} (margin {best_score - runner_score:.2f})"
            )
        if best_score >= _REVIEW_THRESHOLD:
            return MatchResult(
                outcome=MatchOutcome.REVIEW_REQUIRED,
                confidence=best_score,
                candidates=tuple(product for _, product in scored[:_MAX_CANDIDATES]),
                reason=f"Ambiguous description; best score {best_score:.2f}",
            )
        return MatchResult(
            outcome=MatchOutcome.NO_MATCH,
            confidence=best_score,
            reason=f"No catalog product is close enough (best score {best_score:.2f})",
        )

    def _exact_description(self, description: str) -> Product | None:
        query = normalize_text(description)
        if not query:
            return None
        for product in self._catalog:
            if normalize_text(product.description) == query:
                return product
        return None

    @staticmethod
    def _matched(product: Product, confidence: float, reason: str) -> MatchResult:
        return MatchResult(
            outcome=MatchOutcome.MATCHED,
            matched_product=product,
            confidence=confidence,
            reason=reason,
        )
