"""Description lengths for the no-plaintext hypotheses, on the same scale."""

from __future__ import annotations

import random

from translations.analysis.common import View
from translations.decipher.channel import build_ciphertext
from translations.decipher.generative import (
    grille_description,
    literal_bits,
    morphology_description,
    selfcite_description,
    slot_grammar_description,
)
from translations.decipher.score import markov_description

WORDS = [list("qokeedy"), list("chol"), list("daiin"), list("shey"), list("qokain")]
VIEW = View(name="toy", lines=[WORDS * 60])


def _repetitive_view() -> View:
    return View(name="repeats", lines=[[list("daiin")] * 300])


def _varied_view() -> View:
    rng = random.Random(0)
    return View(
        name="varied",
        lines=[[[rng.choice("qokedyalinrsch") for _ in range(5)] for _ in range(300)]],
    )


def test_literal_bits_grow_with_word_length() -> None:
    assert literal_bits(list("ab"), 20) < literal_bits(list("abcd"), 20)


def test_every_generative_description_is_positive_and_on_the_token_scale() -> None:
    for describe in (
        grille_description,
        selfcite_description,
        morphology_description,
        slot_grammar_description,
    ):
        description = describe(VIEW)
        assert description.total_bits > 0
        assert description.n_tokens == VIEW.n_words
        assert description.bits_per_token > 0


def test_autocopy_code_is_cheaper_on_repetitive_text() -> None:
    repetitive = selfcite_description(_repetitive_view()).bits_per_token
    varied = selfcite_description(_varied_view()).bits_per_token
    assert repetitive < varied


def test_grille_code_is_cheaper_on_a_tiny_vocabulary() -> None:
    small = grille_description(_repetitive_view()).bits_per_token
    large = grille_description(_varied_view()).bits_per_token
    assert small < large


def test_descriptions_are_comparable_to_the_markov_baseline() -> None:
    baseline = markov_description(build_ciphertext(VIEW, min_count=1))
    description = morphology_description(VIEW)
    assert baseline.n_tokens == description.n_tokens
