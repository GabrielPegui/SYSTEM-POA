"""Tests for the text normalization helpers used by the catalog matchers.

These helpers encode the documented matching strategy (ADR-003): the real
source data has spelling variations, so matching compares normalized token
sets, and for Spanish adjectives the gender suffix is dropped.
"""

from app.infrastructure.matching.text_utils import (
    containment,
    informative_tokens,
    jaccard,
    normalize_text,
    token_set,
)


def test_normalize_text_lowercases_and_removes_accents() -> None:
    assert normalize_text("PEPÍN Viga Higüey") == "pepin viga higuey"


def test_normalize_text_removes_punctuation_and_collapses_spaces() -> None:
    assert normalize_text("  Pan   De  Hot Dog, 8/1. ") == "pan de hot dog 8 1"


def test_token_set_keeps_plain_tokens() -> None:
    assert token_set("Pan De Hot Dog") == frozenset({"pan", "de", "hot", "dog"})


def test_token_set_adds_gender_stem() -> None:
    tokens = token_set("blanca")
    assert "blanc" in tokens


def test_token_set_short_words_untouched() -> None:
    tokens = token_set("pepin viga")
    assert "viga" in tokens
    assert "pepin" in tokens


def test_jaccard_symmetric() -> None:
    a = token_set("pan de hot dog")
    b = token_set("pan hot dog")
    assert jaccard(a, b) == jaccard(b, a)
    assert jaccard(a, b) > 0.0


def test_jaccard_disjoint_is_zero() -> None:
    assert jaccard(token_set("pan"), token_set("viga")) == 0.0


def test_jaccard_identical_is_one() -> None:
    assert jaccard(token_set("pan de hot dog"), token_set("pan de hot dog")) == 1.0


def test_containment_is_fraction_of_a_present_in_b() -> None:
    a = token_set("pan de hot dog")
    b = token_set("pan hot dog")
    assert containment(a, b) == 3 / 4
    assert containment(b, a) == 1.0


def test_informative_tokens_removes_stopwords() -> None:
    assert "de" not in informative_tokens("PAN DE HOT DOG")
    assert "hot" in informative_tokens("PAN DE HOT DOG")


def test_informative_tokens_removes_address_words() -> None:
    tokens = informative_tokens("MERCADAL AV DUARTE")
    assert "av" not in tokens
    assert "duarte" in tokens
    assert "mercadal" in tokens


def test_informative_tokens_keeps_address_specific_words() -> None:
    assert informative_tokens("Av. Duarte") == frozenset({"duarte"})
