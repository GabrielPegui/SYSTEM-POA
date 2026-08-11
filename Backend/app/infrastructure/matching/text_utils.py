"""Text normalization helpers shared by the catalog matchers.

The real source data contains spelling variations (accents, upper/lower case,
double spaces, non-ASCII characters - ``docs/ANALISIS_DATOS_MVP.md``), so
matching compares normalized token sets instead of raw strings.

For Spanish adjectives the gender suffix is dropped (``blanca``/``blanco``
both contribute the stem ``blanc``) so ``PEPIN VIGA BLANCA`` matches
``VIGA BLANCO PEPIN``; this was calibrated against the real catalog and PDFs.
"""

import re
import unicodedata

_STOPWORDS = frozenset(
    {
        "a", "al", "de", "del", "el", "en", "es", "la", "las", "lo", "los",
        "por", "para", "y", "o", "u", "e", "con", "sin", "que",
    }
)

_ADDRESS_TOKENS = frozenset(
    {
        "av", "ava", "avda", "avenida", "aut", "autopista", "calle", "c",
        "carretera", "cl", "esq", "esquina", "ind", "industrial", "km",
        "no", "nd", "prol", "prolongacion", "rd", "sdn", "sector", "santo",
        "sd", "sdo", "dgo", "sn", "sto", "zona", "herrera", "republica",
        "dominicana", "dominican", "domingo", "distrito", "nacional",
    }
)


def normalize_text(text: str) -> str:
    """Lowercase, remove accents and punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> frozenset[str]:
    """Return normalized tokens with gender/plural-stemmed variants.

    For every word ending in ``a``/``o`` the stem (word minus final letter) is
    added and for every plural ending in ``s`` the singular is added, so
    masculine/feminine and singular/plural spellings compare equal. Short
    words are left untouched to avoid noise.
    """
    tokens: set[str] = set(normalize_text(text).split())
    for token in list(tokens):
        if len(token) > 3:
            if token[-1] in "ao":
                tokens.add(token[:-1])
            if token.endswith("s"):
                tokens.add(token[:-1])
    return frozenset(tokens)


def informative_token_set(text: str) -> frozenset[str]:
    """Informative tokens (no connectives/address words) plus stem variants.

    Combines ``informative_tokens`` with the gender/plural stems of
    ``token_set`` so name matching ignores both stop/address words and
    inflection differences (e.g. ``Mercadal Guaricanos`` matches
    ``MERCADAL GUARICANO``).
    """
    base = set(informative_tokens(text))
    for token in list(base):
        if len(token) > 3:
            if token[-1] in "ao":
                base.add(token[:-1])
            if token.endswith("s"):
                base.add(token[:-1])
    return frozenset(base)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def containment(a: frozenset[str], b: frozenset[str]) -> float:
    """Fraction of ``a`` present in ``b`` (how much of a appears in b)."""
    if not a:
        return 0.0
    return len(a & b) / len(a)


def informative_tokens(text: str) -> frozenset[str]:
    """Return normalized tokens excluding connectives and address words.

    A single informative word is not enough to pin a specific customer account
    (e.g. an address line overlapping a store name), so customer matching only
    accepts a name with at least two informative tokens.
    """
    tokens = set(normalize_text(text).split())
    tokens -= _STOPWORDS
    tokens -= _ADDRESS_TOKENS
    return frozenset(tokens)
