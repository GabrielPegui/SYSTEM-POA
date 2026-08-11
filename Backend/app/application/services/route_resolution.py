"""Route resolution for a processed purchase order.

The documented business rule is *one customer = one route* (1:1) within the
definitive catalog (``CLIENTES POR RUTA.xlsx``): a route is an aggregation of
customers and every customer row belongs to exactly one route. The route of a
resolved customer is therefore the route of the order.

Ambiguity is handled by the customer matcher: a name shared by two catalog
customers (e.g. ``INVERSIONES LLERS`` on PPN303 and PPN601) is never resolved
here as a route; it is reported as REVIEW_REQUIRED before reaching this
service, so no route is silently invented.
"""

from dataclasses import dataclass

from app.domain.document_processing.matching import CustomerMatchResult, MatchOutcome
from app.domain.entities import Route


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
        return RouteResolution(customer.route)
