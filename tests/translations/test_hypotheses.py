"""The pre-registration itself: every hypothesis must be a complete record."""

from __future__ import annotations

import pytest

from translations.decipher.run_hypothesis import GENERATIVE_KINDS, load_hypotheses

REQUIRED = (
    "id",
    "title",
    "family",
    "description",
    "prior",
    "prior_rationale",
    "phase1_evidence",
    "prediction",
    "falsifier",
    "funded",
    "budget_share",
    "search",
    "nulls",
)
IMPLEMENTED_KINDS = {"substitution", "merge", "assignment", *GENERATIVE_KINDS}


@pytest.fixture(scope="module")
def hypotheses():  # type: ignore[no-untyped-def]
    return load_hypotheses()


def test_all_nine_are_registered(hypotheses) -> None:  # type: ignore[no-untyped-def]
    assert {h.hypothesis_id for h in hypotheses} == {
        "H1",
        "H2",
        "H3",
        "H4",
        "H5",
        "H6a",
        "H6b",
        "H7",
        "H8",
        "H9",
    }


def test_every_record_is_complete(hypotheses) -> None:  # type: ignore[no-untyped-def]
    for hypothesis in hypotheses:
        missing = [field for field in REQUIRED if field not in hypothesis.record]
        assert not missing, (hypothesis.hypothesis_id, missing)
        evidence = hypothesis.record["phase1_evidence"]
        assert evidence["for"] and evidence["against"]


def test_funded_hypotheses_have_an_implemented_search(hypotheses) -> None:  # type: ignore[no-untyped-def]
    for hypothesis in hypotheses:
        if hypothesis.funded:
            assert hypothesis.kind in IMPLEMENTED_KINDS, hypothesis.hypothesis_id
            assert hypothesis.budget_share > 0
            assert hypothesis.nulls


def test_unfunded_hypotheses_say_why(hypotheses) -> None:  # type: ignore[no-untyped-def]
    for hypothesis in hypotheses:
        if not hypothesis.funded:
            assert hypothesis.record.get("unfunded_rationale")
            assert hypothesis.budget_share == 0


def test_budget_shares_fit_inside_the_ceiling(hypotheses) -> None:  # type: ignore[no-untyped-def]
    assert sum(h.budget_share for h in hypotheses) <= 1.0


def test_the_rival_no_plaintext_hypotheses_are_funded(hypotheses) -> None:  # type: ignore[no-untyped-def]
    rivals = {h.hypothesis_id: h for h in hypotheses if h.hypothesis_id in ("H6a", "H6b")}
    assert all(hypothesis.funded for hypothesis in rivals.values())
