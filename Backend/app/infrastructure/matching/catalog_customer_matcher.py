"""Customer matcher against the definitive catalog (name-based).

Implements the ``CustomerMatcher`` contract using the strategy documented for
the new model (``docs/data/CLIENTES POR RUTA.xlsx``): the customer ``name`` is
the business key. There is no RNC or ``CL…`` code in the new model, so the
matcher resolves purely by name.

Decision order:

1. Exact normalized name: a single catalog customer -> MATCHED; more than one
   catalog customer (e.g. ``INVERSIONES LLERS`` on PPN303 and PPN601) ->
   REVIEW_REQUIRED with the candidate customers and their routes.
2. Name similarity: candidates must satisfy BOTH signals, then are ranked by
   sequence similarity (``difflib``) on the normalized names:
   - token containment over informative tokens (``Mercadal Guaricanos`` covers
     ``MERCADAL GUARICANO`` but not ``APREZIO GUARICANOS`` - that account only
     shares one token);
   - sequence similarity (``APREZIO GUARICANOS`` stays below the threshold
     even though it contains the same tokens as ``MERCADAL GUARICANO``).
   Requiring both avoids both failure modes seen on the real catalog: pure
   token scoring ties ``MERCADAL GUARICANO`` with ``APREZIO GUARICANOS``,
   while pure sequence scoring lets every ``CARREFOUR ...`` store compete with
   ``HYPER DUARTE``. A single informative token is never enough. A clear
   winner above the threshold and margin -> MATCHED; otherwise REVIEW_REQUIRED
   with the best candidates.
3. No usable name (blank or a single informative word) -> NO_MATCH; a usable
   name that does not match any catalog customer -> NO_MATCH.
"""

from difflib import SequenceMatcher

from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Customer
from app.domain.interfaces.customer_matching import CustomerMatcher
from app.domain.interfaces.repositories import CustomerRepository
from app.infrastructure.matching.text_utils import (
    containment,
    informative_token_set,
    informative_tokens,
    normalize_text,
)

_ALIASES = {"hyper": ("carrefour",), "hiper": ("carrefour",)}

# Document-level account synonyms: a name extracted from a purchase order that
# identifies the same account as a catalog customer under a different legal or
# operating name. Keys are normalized document names (see ``normalize_text``),
# values the normalized catalog name. Example: the Hilton document prints
# ``EMBASSY SUITES HOTEL (OWP)`` for the account OPERADORA WESTPARK, SAS.
_NAME_SYNONYMS = {
    "embassy suites hotel owp": "operadora westpark sas",
}

_NAME_MATCH_THRESHOLD = 0.6
_NAME_MARGIN = 0.3
_MAX_CANDIDATES = 5


class CatalogCustomerMatcher(CustomerMatcher):
    """CustomerMatcher implementation over the customer catalog."""

    def __init__(self, customers: CustomerRepository) -> None:
        self._customers = customers
        self._all = tuple(customers.list())

    def match(self, customer_name: str | None) -> CustomerMatchResult:
        customer_name = self._canonical_name(customer_name)
        exact_result = self._match_exact_name(customer_name)
        if exact_result is not None:
            return exact_result
        return self._match_name(customer_name)

    def _canonical_name(self, customer_name: str | None) -> str | None:
        """Map a document account name to its catalog-equivalent name."""
        if not customer_name:
            return customer_name
        return _NAME_SYNONYMS.get(normalize_text(customer_name), customer_name)

    def _match_exact_name(self, customer_name: str | None) -> CustomerMatchResult | None:
        normalized = normalize_text(customer_name or "")
        if not normalized:
            return None
        exact = tuple(
            customer for customer in self._all if normalize_text(customer.name) == normalized
        )
        if not exact:
            return None
        if len(exact) == 1:
            return CustomerMatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_customer=exact[0],
                confidence=1.0,
                reason=f"Exact name '{customer_name}' identifies {exact[0].name}",
            )
        detail = (
            f"Name '{customer_name}' exists on more than one route: "
            + ", ".join(sorted({f"{customer.route.code} ({customer.name})" for customer in exact}))
        )
        return CustomerMatchResult(
            outcome=MatchOutcome.REVIEW_REQUIRED,
            candidates=tuple(exact[:_MAX_CANDIDATES]),
            reason=detail,
        )

    def _match_name(self, customer_name: str | None) -> CustomerMatchResult:
        tokens = self._expanded_tokens(customer_name)
        if tokens is None:
            return CustomerMatchResult(
                outcome=MatchOutcome.NO_MATCH,
                reason="No usable customer name was found in the document",
            )
        expanded_name = self._expanded_name(customer_name)
        scored = self._score_all(expanded_name, tokens)
        if not scored:
            return CustomerMatchResult(
                outcome=MatchOutcome.NO_MATCH,
                reason=f"Name '{customer_name}' does not match any catalog customer",
            )
        top_score, top = scored[0]
        runner_score = scored[1][0] if len(scored) > 1 else 0.0
        if top_score >= _NAME_MATCH_THRESHOLD and top_score - runner_score >= _NAME_MARGIN:
            return CustomerMatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_customer=top,
                confidence=top_score,
                reason=f"Name '{customer_name}' identifies {top.name} uniquely in the catalog",
            )
        if top_score >= _NAME_MATCH_THRESHOLD:
            return CustomerMatchResult(
                outcome=MatchOutcome.REVIEW_REQUIRED,
                candidates=tuple(customer for _, customer in scored[:_MAX_CANDIDATES]),
                reason=f"Name '{customer_name}' matches {len(scored)} accounts ambiguously",
            )
        return CustomerMatchResult(
            outcome=MatchOutcome.NO_MATCH,
            reason=f"Name '{customer_name}' does not match any catalog customer",
        )

    def _expanded_tokens(self, customer_name: str | None) -> frozenset[str] | None:
        if not customer_name or not normalize_text(customer_name):
            return None
        # The length guard counts base informative words (before stem
        # expansion): a single informative word is never enough to pin a
        # customer account (e.g. an address line overlapping a store name).
        if len(informative_tokens(customer_name)) < 2:
            return None
        tokens = set(informative_token_set(customer_name))
        for alias, expansions in _ALIASES.items():
            if alias in tokens:
                tokens.update(expansions)
        return frozenset(tokens)

    def _expanded_name(self, customer_name: str) -> str:
        """Normalized name with aliases expanded, for sequence comparison."""
        words = normalize_text(customer_name).split()
        expanded: list[str] = []
        for word in words:
            expanded.extend(_ALIASES.get(word, (word,)))
        return " ".join(expanded)

    def _score_all(self, expanded_name: str, tokens: frozenset[str]) -> list[tuple[float, Customer]]:
        scored = []
        for customer in self._all:
            containment_score = containment(tokens, informative_token_set(customer.name))
            similarity = SequenceMatcher(None, expanded_name, normalize_text(customer.name)).ratio()
            if containment_score < _NAME_MATCH_THRESHOLD or similarity < _NAME_MATCH_THRESHOLD:
                continue
            scored.append((similarity, customer))
        scored.sort(reverse=True, key=lambda pair: (pair[0], pair[1].name, pair[1].route.code))
        return scored
