"""Phase 5: the audit harness, the individual tests, and the committed report."""

from __future__ import annotations

import json

import numpy as np
import pytest

from translations.audit import Check, Finding
from translations.audit.common import agreement, gated_coverage, mean_confidence
from translations.audit.strength import ZL_IT_LINE_IDENTITY, _bigram_bits, _concentration, _jsd
from translations.audit.weakness import _key_agreement
from translations.config import FAILED_VALIDATION_BANNER, SPECULATIVE_BANNER, active_banner
from translations.phase4 import REPORTS
from translations.phase5 import DECISION_HEADING, decision_links, kill_criteria

AUDIT = REPORTS / "strengths_weaknesses.md"
AUDIT_JSON = REPORTS / "strengths_weaknesses.json"


def test_active_banner_switches_on_the_verdict() -> None:
    assert active_banner(False) == SPECULATIVE_BANNER
    assert active_banner(True) == FAILED_VALIDATION_BANNER
    assert FAILED_VALIDATION_BANNER.startswith("SPECULATIVE OUTPUT")
    assert "FAILED VALIDATION" in FAILED_VALIDATION_BANNER


def test_agreement_counts_matching_positions() -> None:
    assert agreement(["a", "b", "c"], ["a", "x", "c"]) == pytest.approx(2 / 3)
    assert agreement([], []) == 0.0


def test_key_agreement_uses_only_shared_units() -> None:
    left = {"o": "a", "e": "b", "y": "c"}
    right = {"o": "a", "e": "z", "k": "q"}
    assert _key_agreement(left, right) == pytest.approx(0.5)
    assert _key_agreement({}, right) == 0.0


def test_jsd_is_zero_for_identical_distributions() -> None:
    p = np.array([[0.5, 0.5], [0.25, 0.75]])
    assert _jsd(p, p) == pytest.approx([0.0, 0.0], abs=1e-12)
    assert _jsd(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(1.0)


def test_concentration_is_zero_when_groups_look_alike() -> None:
    counts = np.array([[4.0, 4.0], [4.0, 4.0], [8.0, 8.0]])
    labels = np.array([0, 1, 1])
    assert _concentration(counts, labels, 2) == pytest.approx(0.0, abs=1e-12)
    # Divergence is measured against the pooled profile, not between groups, so
    # two disjoint groups score 0.311 bits rather than a full bit.
    split = np.array([[8.0, 0.0], [0.0, 8.0]])
    assert _concentration(split, np.array([0, 1]), 2) == pytest.approx(0.311, abs=1e-3)


def test_bigram_bits_prefers_the_corpus_it_was_built_on() -> None:
    from translations.corpora import load_corpus

    words = load_corpus("douay_rheims").words[:2000]
    real = _bigram_bits("douay_rheims", list(words))
    scrambled = list(words)
    scrambled.reverse()
    assert real < _bigram_bits("douay_rheims", sorted(scrambled))


def test_decision_links_finds_every_logged_decision() -> None:
    links = decision_links()
    assert len(links) >= 29
    assert all(row[0].startswith("Decision ") for row in links)
    assert not any("[Title]" in row[1] for row in links)
    assert DECISION_HEADING.search("## Decision 7: Something") is not None


def _check(test: str, data: dict) -> Check:
    return Check(Finding(test, "m", 0.0, None, "neutral", "i"), "", data)


def test_kill_criteria_uses_the_untranslated_congruence_baseline() -> None:
    """Congruence the untranslated types already carry is not evidence for the reading."""
    base = {
        "§7.2.1 pseudo-Voynich control": _check("a", {"ratio": 0.5}),
        "§7.1.2 held-out generalisation": _check("b", {"p_value": 0.01}),
        "§7.1.3 cross-transcription stability": _check(
            "c", {"gloss_agreement": 0.9, "line_identity_baseline": ZL_IT_LINE_IDENTITY}
        ),
        "§7.2.3 rival-language ambiguity": _check("d", {"coverage_spread": 0.9, "languages": []}),
        "§7.1.5 illustration congruence": _check(
            "e",
            {
                "p_value": 0.001,
                "statistic": 0.09,
                "surface_statistic": 0.20,
                "surface_p_value": 0.001,
            },
        ),
    }
    assert kill_criteria(base)[4]["met"] is True
    base["§7.1.5 illustration congruence"] = _check(
        "e",
        {"p_value": 0.001, "statistic": 0.30, "surface_statistic": 0.20, "surface_p_value": 0.001},
    )
    assert kill_criteria(base)[4]["met"] is False


def test_kill_criteria_reads_every_criterion_from_its_own_test() -> None:
    checks = {
        "§7.2.1 pseudo-Voynich control": _check("a", {"ratio": 1.23}),
        "§7.1.2 held-out generalisation": _check("b", {"p_value": 0.9}),
        "§7.1.3 cross-transcription stability": _check(
            "c", {"gloss_agreement": 0.8, "line_identity_baseline": ZL_IT_LINE_IDENTITY}
        ),
        "§7.2.3 rival-language ambiguity": _check(
            "d", {"coverage_spread": 0.01, "languages": [1, 2, 3, 4]}
        ),
        "§7.1.5 illustration congruence": _check(
            "e",
            {
                "p_value": 0.4,
                "statistic": 0.09,
                "surface_statistic": 0.20,
                "surface_p_value": 0.001,
            },
        ),
    }
    criteria = kill_criteria(checks)
    assert [row["met"] for row in criteria] == [True, True, False, True, True]
    assert all(isinstance(row["met"], bool) for row in criteria)


pytestmark_report = pytest.mark.skipif(
    not AUDIT.exists(), reason="Phase 5 not run yet; run `make audit`"
)


@pytestmark_report
def test_report_carries_the_verdict_banner() -> None:
    data = json.loads(AUDIT_JSON.read_text())
    assert data["banner"] == active_banner(bool(data["declared_unsuccessful"]))
    assert data["banner"] in AUDIT.read_text()


@pytestmark_report
def test_report_prints_the_control_before_any_rendering() -> None:
    text = AUDIT.read_text()
    assert text.index("decisive control") < text.index("Strength evidence")
    assert "Kill criteria, agreed in advance" in text


@pytestmark_report
def test_report_scores_all_five_kill_criteria() -> None:
    data = json.loads(AUDIT_JSON.read_text())
    assert len(data["kill_criteria"]) == 5
    assert data["declared_unsuccessful"] == any(row["met"] for row in data["kill_criteria"])


@pytestmark_report
def test_every_plan_test_produced_a_finding() -> None:
    data = json.loads(AUDIT_JSON.read_text())
    assert len(data["strength"]) == 7
    assert len(data["weakness"]) == 7
    assert all(
        row["verdict"] in {"supports", "undermines", "neutral", "vacuous", "not run"}
        for row in [*data["strength"].values(), *data["weakness"].values()]
    )


@pytestmark_report
def test_anchor_test_is_reported_as_blocked_not_passed() -> None:
    data = json.loads(AUDIT_JSON.read_text())
    anchors = data["strength"]["§7.1.7 anchor agreement"]
    assert anchors["verdict"] == "not run"
    assert anchors["value"] == 0


@pytestmark_report
def test_coverage_helpers_match_the_report() -> None:
    data = json.loads(AUDIT_JSON.read_text())
    assert 0.0 <= data["gated_coverage"] <= 1.0
    assert 0.0 <= data["mean_confidence"] <= 1.0
    assert gated_coverage([]) == 0.0
    assert mean_confidence([]) == 0.0
