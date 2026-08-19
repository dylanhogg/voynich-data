"""Induced acceptors: they must accept their training set and generalise from it."""

from __future__ import annotations

from translations.analysis.fsa import merge_k_tails, prefix_tree, score
from translations.determinism import derived_rng

WORDS = [
    list("qokeedy"),
    list("qokeey"),
    list("qokain"),
    list("chedy"),
    list("chey"),
    list("shedy"),
    list("shey"),
    list("okeedy"),
]


def test_prefix_tree_accepts_exactly_its_input() -> None:
    automaton = prefix_tree(tuple(word) for word in WORDS)
    assert all(automaton.accepts(word) for word in WORDS)
    assert not automaton.accepts(list("qqqq"))


def test_k_tails_merging_shrinks_the_automaton_and_generalises() -> None:
    tree = prefix_tree(tuple(word) for word in WORDS)
    merged = merge_k_tails(tree, k=1)
    assert merged.n_states < tree.n_states
    assert all(merged.accepts(word) for word in WORDS)


def test_larger_k_keeps_more_states() -> None:
    tree = prefix_tree(tuple(word) for word in WORDS)
    assert merge_k_tails(tree, k=1).n_states <= merge_k_tails(tree, k=3).n_states


def test_score_reports_acceptance_and_overgeneration() -> None:
    result = score(WORDS * 20, derived_rng("test"), samples=200)
    assert 0.0 <= result.heldout_type_acceptance <= 1.0
    assert 0.0 <= result.overgeneration <= 1.0
    assert result.states > 0
    assert result.as_dict()["train_types"] > 0


def test_score_is_deterministic() -> None:
    first = score(WORDS * 20, derived_rng("test"), samples=200)
    second = score(WORDS * 20, derived_rng("test"), samples=200)
    assert first == second
