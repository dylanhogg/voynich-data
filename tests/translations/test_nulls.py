"""Null and surrogate generators: reproducible, and destroying only what they claim."""

from __future__ import annotations

from collections import Counter

from translations.determinism import derived_rng
from translations.nulls import (
    encipher,
    grille,
    markov_chars,
    markov_words,
    selfcite,
    shuffle_chars,
    shuffle_within_word,
    shuffle_word_order,
)
from translations.nulls.pseudo import induce_table
from translations.tokenize import tokenize_line

TEXT = (
    "fachys.ykal.ar.ataiin.shol.shory.cthres.y.kor.sholdy."
    "sory.ckhar.ory.kair.chtaiin.shar.ase.cthar.cthardan"
)
WORDS = tokenize_line(TEXT)


def units(words: list[list[str]]) -> Counter[str]:
    return Counter(unit for word in words for unit in word)


def test_shuffle_chars_keeps_inventory_and_word_lengths() -> None:
    shuffled = shuffle_chars(WORDS, derived_rng("test"))
    assert units(shuffled) == units(WORDS)
    assert [len(word) for word in shuffled] == [len(word) for word in WORDS]
    assert shuffled == shuffle_chars(WORDS, derived_rng("test"))


def test_shuffle_within_word_keeps_each_word_multiset() -> None:
    shuffled = shuffle_within_word(WORDS, derived_rng("test"))
    assert [sorted(word) for word in shuffled] == [sorted(word) for word in WORDS]


def test_shuffle_word_order_keeps_vocabulary() -> None:
    shuffled = shuffle_word_order(WORDS, derived_rng("test"))
    assert sorted("".join(word) for word in shuffled) == sorted("".join(word) for word in WORDS)
    assert shuffled != WORDS


def test_markov_chars_generates_matched_length_and_is_reproducible() -> None:
    generated = markov_chars(WORDS, 2, derived_rng("test"))
    total = sum(len(word) for word in WORDS)
    assert abs(sum(len(word) for word in generated) - total) <= len(WORDS)
    assert generated == markov_chars(WORDS, 2, derived_rng("test"))


def test_markov_words_preserves_vocabulary() -> None:
    generated = markov_words(WORDS, 1, derived_rng("test"))
    assert len(generated) == len(WORDS)
    vocabulary = {"".join(word) for word in WORDS}
    assert {"".join(word) for word in generated} <= vocabulary


def test_grille_generates_from_the_table_only() -> None:
    table = induce_table(WORDS, size=8)
    generated = grille(table, 25, derived_rng("test"))
    assert len(generated) == 25
    assert generated == grille(table, 25, derived_rng("test"))
    forms = {"".join(word) for word in generated}
    parts = set(table.prefixes) | set(table.midfixes) | set(table.suffixes)
    assert all(any(form.startswith(prefix) for prefix in table.prefixes) for form in forms)
    assert parts


def test_selfcite_produces_near_repeats() -> None:
    generated = selfcite(WORDS, 60, derived_rng("test"))
    assert len(generated) == 60
    assert generated == selfcite(WORDS, 60, derived_rng("test"))
    repeats = sum(1 for left, right in zip(generated, generated[1:], strict=False) if left == right)
    assert repeats > 0


def test_encipher_substitution_is_a_bijection_on_the_plaintext() -> None:
    plaintext = ["in", "principio", "creavit", "deus", "caelum", "et", "terram"]
    ciphertext, key = encipher(plaintext, "substitution", derived_rng("test"))
    assert [len(word) for word in ciphertext] == [len(word) for word in plaintext]
    assert len(set(key.mapping.values())) == len(key.mapping)
    inverse = {value: plain for plain, value in key.mapping.items()}
    recovered = ["".join(inverse[(unit,)] for unit in word) for word in ciphertext]
    assert recovered == plaintext


def test_encipher_verbose_doubles_length() -> None:
    plaintext = ["deus", "terram"]
    ciphertext, key = encipher(plaintext, "verbose", derived_rng("test"))
    assert [len(word) for word in ciphertext] == [8, 12]
    assert all(len(code) == 2 for code in key.mapping.values())


def test_encipher_abjad_drops_vowels() -> None:
    plaintext = ["in", "principio", "creavit"]
    ciphertext, key = encipher(plaintext, "abjad", derived_rng("test"))
    assert not set(key.plaintext_alphabet) & set("aeiou")
    assert [len(word) for word in ciphertext] == [1, 5, 4]
