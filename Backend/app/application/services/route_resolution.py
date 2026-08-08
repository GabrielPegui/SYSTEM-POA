"""Route resolution for a processed purchase order.

The documented business rule is *one customer = one route* (1:1). The route of
a resolved customer is therefore the route of the order.

Known exception (documented in ``docs/ANALISIS_DATOS_MVP.md``): the source
catalog lists account ``CL001062`` (SURTIDORA BENERITO) on two routes (PPN000
and PPN403). This is pending business confirmation, so instead of silently
picking one route the resolver reports the ambiguity and the order goes to
``REVIEW_REQUIRED``. The list of ambiguous codes is a small, documented,
data-quality guard, not format-selection logic (ADR-002 applies to parser
selection, not to this data concern).
"""

from dataclasses import dataclass

from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Route

#: Accounts whose source data is ambiguous (pending business confirmation).
AMBIGUOUS_ROUTE_CODES: frozenset[str] = frozenset({"CL001062"})


@dataclass(frozen=True)
class RouteResolution:
    """Outcome of resolving the route for a processed order.

    ``route`` is set when the route is unambiguous; otherwise ``reason``
    explains why it could not be resolved.
    """

    route: Route | None
    reason: str = ""

    @property
    def resolved(self) -> bool:
        return self.route is not None


class RouteResolver:
    """Resolves the route of an order from its matched customer."""

    def resolve(self, customer_match: CustomerMatchResult) -> RouteResolution:
        if customer_match.outcome is not MatchOutcome.MATCHED:
            return RouteResolution(None, customer_match.reason)
        customer = customer_match.matched_customer
        assert customer is not None
        if customer.code in AMBIGUOUS_ROUTE_CODES:
            return RouteResolution(
                None,
                f"{customer.name} ({customer.code}) has two routes in the source data "
                "(PPN000, PPN403); pending business confirmation",
            )
        return RouteResolution(customer.route)
