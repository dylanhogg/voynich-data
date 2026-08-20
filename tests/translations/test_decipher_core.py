"""Language models, channels and description lengths."""

from __future__ import annotations

import numpy as np
import pytest

from translations.analysis.common import View
from translations.decipher.channel import (
    build_ciphertext,
    decode,
    fixed_width_units,
    identity_key,
    key_as_dict,
    key_description_bits,
    merge_description_bits,
    merge_units,
)
from translations.decipher.lm import ALPHABET, abbreviate, train_char_lm
from translations.decipher.score import (
    Description,
    ambiguity_bits,
    gain_per_token,
    lm_bits,
    markov_description,
    ngram_index,
    substitution_description,
)
from vcat.exceptions import ConfigurationError

WORDS = [list("qokeedy"), list("chol"), list("daiin"), list("daiin"), list("shey")]
VIEW = View(name="toy", lines=[WORDS * 40])


def test_lm_prefers_its_own_language() -> None:
    latin = train_char_lm("in principio creavit deus caelum et terram " * 50, 3, "la")
    english = train_char_lm("it is a truth universally acknowledged that a man " * 50, 3, "en")
    sample = latin.index("#in#principio#creavit#")
    assert latin.bits_per_symbol(sample) < english.bits_per_symbol(sample)


def test_lm_rejects_unsupported_order() -> None:
    with pytest.raises(ConfigurationError):
        train_char_lm("abc def", 9)


def test_abbreviate_applies_suspension_and_contraction() -> None:
    assert abbreviate("omnibus").startswith("o")
    assert abbreviate("quoque") == "quoq"
    assert abbreviate("creavit") == "creavit"


def test_ciphertext_folds_rare_units() -> None:
    view = View(name="rare", lines=[[list("aaa"), list("aaz")]])
    ciphertext = build_ciphertext(view, min_count=2)
    assert "?" in ciphertext.units
    assert "z" not in ciphertext.units


def test_ciphertext_shape_and_counts() -> None:
    ciphertext = build_ciphertext(VIEW, min_count=1)
    assert ciphertext.n_tokens == VIEW.n_words
    assert ciphertext.units[0] == "#"
    assert ciphertext.n_units == VIEW.n_units


def test_merge_units_treats_sequences_as_one_unit() -> None:
    merged = merge_units(VIEW, (("d", "y"),), "merged", min_count=1)
    assert "dy" in merged.units
    assert merged.n_units < build_ciphertext(VIEW, min_count=1).n_units


def test_fixed_width_units_chops_words() -> None:
    merged = fixed_width_units(VIEW, 2, "w2", min_count=1)
    assert "qo" in merged.units
    assert merged.n_units < build_ciphertext(VIEW, min_count=1).n_units


def test_key_and_merge_costs_grow_with_size() -> None:
    assert key_description_bits(30) > key_description_bits(10)
    assert merge_description_bits(((("q", "o")),), 25) > 0


def test_decode_and_key_readback() -> None:
    ciphertext = build_ciphertext(VIEW, min_count=1)
    key = identity_key(ciphertext)
    plaintext = decode(key, ciphertext)
    assert plaintext.shape == ciphertext.ids.shape
    assert set(key_as_dict(key, ciphertext)) == set(ciphertext.units[1:])


def test_ambiguity_bits_punish_a_collapsing_key() -> None:
    ciphertext = build_ciphertext(VIEW, min_count=1)
    index = ngram_index(ciphertext, 2)
    spread = identity_key(ciphertext)
    collapsed = np.where(np.arange(ciphertext.size) == 0, 0, 1)
    assert ambiguity_bits(collapsed, index) > ambiguity_bits(spread, index)


def test_markov_baseline_is_cheaper_than_a_bad_substitution() -> None:
    ciphertext = build_ciphertext(VIEW, min_count=1)
    lm = train_char_lm("in principio creavit deus caelum et terram " * 50, 3, "la")
    index = ngram_index(ciphertext, lm.order)
    baseline = markov_description(ciphertext)
    description = substitution_description(identity_key(ciphertext), index, lm, ciphertext, "H1")
    assert gain_per_token(description, baseline) < 0


def test_lm_bits_scale_with_the_index() -> None:
    ciphertext = build_ciphertext(VIEW, min_count=1)
    lm = train_char_lm("abcde " * 200, 2, "toy")
    index = ngram_index(ciphertext, 2)
    assert lm_bits(identity_key(ciphertext), index, lm) > 0


def test_description_arithmetic() -> None:
    description = Description("H1", model_bits=100.0, data_bits=900.0, n_tokens=100)
    assert description.total_bits == 1000.0
    assert description.bits_per_token == 10.0
    assert description.as_dict()["hypothesis"] == "H1"


def test_alphabet_starts_with_the_boundary() -> None:
    assert ALPHABET[0] == "#"
    assert len(ALPHABET) == 27
