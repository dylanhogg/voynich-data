"""Null positioning, FDR, budget accounting and the anchor protocol."""

from __future__ import annotations

import time

from translations.decipher.anchors import CATALOGUE, Anchor, anchor_score
from translations.decipher.budget import Budget, Deadline
from translations.decipher.stats import NullComparison, benjamini_hochberg


def test_p_value_counts_nulls_that_matched_or_beat_the_real_score() -> None:
    comparison = NullComparison(real=1.0, nulls={"a": 0.1, "b": 0.2, "c": 1.5})
    assert comparison.p_value == 0.5
    assert NullComparison(real=2.0, nulls={"a": 0.1, "b": 0.2, "c": 0.3}).p_value == 0.25


def test_p_value_is_one_without_nulls() -> None:
    assert NullComparison(real=5.0, nulls={}).p_value == 1.0


def test_z_score_and_best_null() -> None:
    comparison = NullComparison(real=3.0, nulls={"a": 1.0, "b": 1.0, "c": 1.0})
    assert comparison.z_score == 0.0  # no spread in the null
    assert comparison.best_null == ("a", 1.0)


def test_benjamini_hochberg_is_monotone_and_bounded() -> None:
    q_values = benjamini_hochberg({"a": 0.001, "b": 0.02, "c": 0.5})
    assert q_values["a"] <= q_values["b"] <= q_values["c"]
    assert all(0 <= value <= 1 for value in q_values.values())
    assert benjamini_hochberg({}) == {}


def test_budget_allocates_and_records() -> None:
    budget = Budget(total_seconds=100.0)
    deadline = budget.allocate("H2", 0.5)
    assert deadline.seconds == 50.0
    budget.record("H2", 20.0)
    assert budget.total_spent == 20.0
    assert budget.remaining == 80.0


def test_deadline_expires() -> None:
    deadline = Deadline(seconds=0.0, started=time.monotonic() - 1)
    assert deadline.expired
    assert not Deadline(seconds=60.0).expired


def test_anchor_catalogue_is_empty_until_phase_3() -> None:
    assert CATALOGUE == ()
    assert anchor_score({"otedy": "may"}) == 0.0


def test_anchor_score_counts_agreement_when_a_catalogue_exists() -> None:
    catalogue = (
        Anchor("a1", "f70v", "otedy", "may", "test", "low"),
        Anchor("a2", "f71r", "okal", "june", "test", "low"),
    )
    assert anchor_score({"otedy": "may"}, catalogue) == 0.5
