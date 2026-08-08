"""Customer matcher against the fixed catalog (Sprint 7).

Implements the ``CustomerMatcher`` contract using the strategy documented in
``docs/ANALISIS_DATOS_MVP.md``: the RNC is not a unique identifier (one RNC
maps to many accounts, e.g. 98 Sirena clients), so the name extracted from the
document is used as reinforcement to disambiguate candidate accounts.

Decision order:

1. Exact ``CL…`` customer code when the document carries one.
2. Exact RNC: unique account -> MATCHED; multiple accounts -> name-based
   disambiguation; otherwise REVIEW_REQUIRED with the candidate accounts.
3. Name + evidence-based synonyms (``HYPER``/``HIPER`` -> ``CARREFOUR``): a
   name must contain at least two informative tokens to MATCH a single
   account; one informative token is never enough to pin an account (an
   address line must not silently select a store by coincidence).
4. No identifier -> NO_MATCH.
"""

import re

from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Customer
from app.domain.interfaces.customer_matching import CustomerMatcher
from app.domain.interfaces.repositories import CustomerRepository
from app.infrastructure.matching.text_utils import (
    containment,
    informative_tokens,
    normalize_text,
)

_ALIASES = {"hyper": ("carrefour",), "hiper": ("carrefour",)}
_NAME_MATCH_THRESHOLD = 0.6
_NAME_MARGIN = 0.3
_MAX_CANDIDATES = 5


class CatalogCustomerMatcher(CustomerMatcher):
    """CustomerMatcher implementation over the customer catalog."""

    def __init__(self, customers: CustomerRepository) -> None:
        self._customers = customers
        self._all = tuple(customers.list())

    def match(self, customer_code: str | None, customer_name: str | None) -> CustomerMatchResult:
        code_result = self._match_code(customer_code)
        if code_result is not None:
            return code_result

        rnc_result = self._match_rnc(customer_code, customer_name)
        if rnc_result is not None:
            return rnc_result

        name_result = self._match_name(customer_name)
        if name_result is not None:
            return name_result

        return CustomerMatchResult(
            outcome=MatchOutcome.NO_MATCH,
            reason="No customer identifier (code, RNC or name) was found in the document",
        )

    def _match_code(self, customer_code: str | None) -> CustomerMatchResult | None:
        if not customer_code or not re.fullmatch(r"CL\d+[-\w]*", customer_code, re.IGNORECASE):
            return None
        customer = self._customers.get_by_code(customer_code)
        if customer is None:
            return CustomerMatchResult(
                outcome=MatchOutcome.NO_MATCH,
                reason=f"Customer code '{customer_code}' is not in the catalog",
            )
        return CustomerMatchResult(
            outcome=MatchOutcome.MATCHED,
            matched_customer=customer,
            confidence=1.0,
            reason=f"Exact customer code {customer.code}",
        )

    def _match_rnc(self, customer_code: str | None, customer_name: str | None) -> CustomerMatchResult | None:
        rnc = re.sub(r"[^0-9]", "", customer_code or "")
        if len(rnc) < 7:
            return None
        by_rnc = self._customers.get_by_rnc(rnc)
        if len(by_rnc) == 1:
            return CustomerMatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_customer=by_rnc[0],
                confidence=1.0,
                reason=f"Unique RNC {rnc} ({by_rnc[0].name})",
            )
        if len(by_rnc) > 1:
            narrowed = self._narrow_by_name(by_rnc, customer_name)
            if narrowed is not None:
                return narrowed
            detail = (
                f"RNC {rnc} maps to {len(by_rnc)} accounts and the document name "
                f"'{customer_name}' does not identify one"
                if customer_name
                else f"RNC {rnc} maps to {len(by_rnc)} accounts"
            )
            return CustomerMatchResult(
                outcome=MatchOutcome.REVIEW_REQUIRED,
                candidates=tuple(by_rnc[:_MAX_CANDIDATES]),
                reason=detail,
            )
        return CustomerMatchResult(
            outcome=MatchOutcome.NO_MATCH,
            reason=f"RNC {rnc} is not in the catalog",
        )

    def _narrow_by_name(
        self, candidates: tuple[Customer, ...], customer_name: str | None
    ) -> CustomerMatchResult | None:
        scored = self._score_candidates(candidates, customer_name)
        if scored is None:
            return None
        top_score, top = scored[0]
        runner_score = scored[1][0] if len(scored) > 1 else 0.0
        if top_score >= _NAME_MATCH_THRESHOLD and top_score - runner_score >= _NAME_MARGIN:
            return CustomerMatchResult(
                outcome=MatchOutcome.MATCHED,
                matched_customer=top,
                confidence=top_score,
                reason=f"Name '{customer_name}' identifies {top.name} uniquely among RNC accounts",
            )
        return None

    def _match_name(self, customer_name: str | None) -> CustomerMatchResult | None:
        tokens = self._expanded_tokens(customer_name)
        if tokens is None:
            return None
        scored = self._score_all(tokens)
        if not scored:
            return None
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
            reason=f"Name '{customer_name}' does not match any catalog account",
        )

    def _expanded_tokens(self, customer_name: str | None) -> frozenset[str] | None:
        if not customer_name or not normalize_text(customer_name):
            return None
        tokens = set(informative_tokens(customer_name))
        if len(tokens) < 2:
            return None
        for alias, expansions in _ALIASES.items():
            if alias in tokens:
                tokens.update(expansions)
        return frozenset(tokens)

    def _score_candidates(
        self, candidates: tuple[Customer, ...], customer_name: str | None
    ) -> list[tuple[float, Customer]] | None:
        tokens = self._expanded_tokens(customer_name)
        if tokens is None:
            return None
        scored = [
            (containment(tokens, informative_tokens(customer.name)), customer)
            for customer in candidates
        ]
        scored.sort(reverse=True, key=lambda pair: (pair[0], pair[1].code))
        return scored

    def _score_all(self, tokens: frozenset[str]) -> list[tuple[float, Customer]]:
        scored = [
            (containment(tokens, informative_tokens(customer.name)), customer)
            for customer in self._all
        ]
        scored.sort(reverse=True, key=lambda pair: (pair[0], pair[1].code))
        return [pair for pair in scored if pair[0] > 0.0]
