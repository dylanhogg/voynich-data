"""§3.10 — the blocking landmark gate.

Six properties of Voynichese are established in the literature. If this pipeline
cannot reproduce them from ``output/``, the bug is ours and no Phase 2 work
starts. Each check reads numbers the other topic modules already computed, so
the gate tests the pipeline rather than re-deriving anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from translations.report import Topic, table


@dataclass(frozen=True)
class Landmark:
    """One reproduction check."""

    name: str
    passed: bool
    detail: str
    evidence: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """JSON-friendly form."""
        return {"passed": self.passed, "detail": self.detail, "evidence": self.evidence}


def _natural_baselines(comparisons: dict[str, dict[str, Any]]) -> list[str]:
    return [
        name
        for name in comparisons
        if not name.startswith(("shuffle", "markov", "grille", "selfcite"))
    ]


def low_conditional_entropy(entropy: dict[str, Any]) -> Landmark:
    """h2 below every natural-language baseline at matched sample size."""
    voynich = entropy["headline"]["voynich_h2"]["value"]
    versus = entropy["headline"]["versus"]
    natural = {name: row for name, row in versus.items() if name in _natural_baselines(versus)}
    lowest = min(natural.items(), key=lambda item: item[1]["h2"]["value"])
    separated = all(row["ci_separated"] for row in natural.values())
    return Landmark(
        name="Conditional entropy h2 well below natural language",
        passed=voynich < lowest[1]["h2"]["value"] and separated,
        detail=f"Voynich h2 {voynich:.3f} vs lowest baseline {lowest[0]} {lowest[1]['h2']['value']:.3f}",
        evidence={"voynich_h2": voynich, "lowest_baseline": lowest[0], "ci_separated": separated},
    )


def slot_structure(entropy: dict[str, Any], morphology: dict[str, Any]) -> Landmark:
    """Word-internal order is rigid: shuffling inside words destroys structure."""
    real = entropy["headline"]["voynich_h2"]["value"]
    shuffled = entropy["comparisons"]["shuffle_within_word"]["h2"]
    acceptance = morphology["fsa"]["voynich|base|k=1"]["heldout_type_acceptance"]
    return Landmark(
        name="Rigid word-internal glyph ordering / slot structure",
        passed=(shuffled - real) > 1.0 and acceptance > 0.8,
        detail=(
            f"within-word shuffle raises h2 by {shuffled - real:.3f} bits; "
            f"k=1 acceptor accepts {acceptance:.1%} of held-out word types"
        ),
        evidence={"h2_real": real, "h2_shuffled": shuffled, "fsa_acceptance": acceptance},
    )


def zipf_tail(lexis: dict[str, Any]) -> Landmark:
    """Zipf-like frequencies with a hapax share above every natural baseline."""
    profiles = lexis["profiles"]
    voynich = profiles["voynich|base"]
    natural = {
        name: row
        for name, row in profiles.items()
        if name
        in (
            "vulgate_clementine",
            "austen_pride_prejudice",
            "chaucer_canterbury",
            "dante_commedia",
            "finnish_bible",
            "german_bible_elberfelder",
            "douay_rheims",
            "caesar_bello_gallico",
            "clusius_rariorum",
        )
    }
    highest = max(natural.items(), key=lambda item: item[1]["hapax_rate"])
    return Landmark(
        name="Zipf-like frequencies with an anomalous low-frequency tail",
        passed=1.4 < voynich["zipf_alpha"] < 3.0
        and voynich["hapax_rate"] > highest[1]["hapax_rate"],
        detail=(
            f"α = {voynich['zipf_alpha']:.3f}, hapax {voynich['hapax_rate']:.1%} vs "
            f"highest baseline {highest[0]} {highest[1]['hapax_rate']:.1%}"
        ),
        evidence={
            "alpha": voynich["zipf_alpha"],
            "hapax_rate": voynich["hapax_rate"],
            "highest_baseline": highest[0],
            "highest_baseline_hapax": highest[1]["hapax_rate"],
        },
    )


def near_repeat_rate(syntax: dict[str, Any]) -> Landmark:
    """Adjacent near-repeats far above natural language."""
    repeats = syntax["near_repeats"]
    voynich = repeats["voynich|base"]["within_2"]
    natural = {
        name: row["within_2"]
        for name, row in repeats.items()
        if name in ("vulgate_clementine", "austen_pride_prejudice")
    }
    highest = max(natural.items(), key=lambda item: item[1])
    return Landmark(
        name="High rate of near-repeat adjacent words",
        passed=voynich > highest[1] * 1.5,
        detail=f"within-2 rate {voynich:.1%} vs {highest[0]} {highest[1]:.1%}",
        evidence={"voynich": voynich, **natural},
    )


def currier_divergence(currier: dict[str, Any]) -> Landmark:
    """A/B differ after equalising sample size."""
    battery = currier["battery"]
    a = battery["currier_a (matched)"]
    b = battery["currier_b (matched)"]
    delta = abs(a["h2"] - b["h2"])
    return Landmark(
        name="Currier A/B divergence surviving sample-size control",
        passed=delta > 0.1 and currier["vocabulary"]["jaccard"] < 0.35,
        detail=(
            f"matched h2 differs by {delta:.3f} bits; vocabulary Jaccard "
            f"{currier['vocabulary']['jaccard']:.3f}"
        ),
        evidence={"h2_a": a["h2"], "h2_b": b["h2"], "jaccard": currier["vocabulary"]["jaccard"]},
    )


def line_position(position: dict[str, Any]) -> Landmark:
    """Line-initial/final glyphs differ from mid-line, and Latin's do not."""
    voynich = position["position_tests"]["voynich|base"]
    latin = position["position_tests"]["vulgate_clementine"]
    return Landmark(
        name="Line-position effects (initial/final differ from mid)",
        passed=voynich["p_value"] < 0.001
        and voynich["cramers_v"] > 0.1
        and latin["p_value"] > 0.01,
        detail=(
            f"Voynich χ² p = {voynich['p_value']:.2e}, V = {voynich['cramers_v']:.3f}; "
            f"Latin control p = {latin['p_value']:.3f}"
        ),
        evidence={"voynich": voynich, "latin_control": latin},
    )


def run(results: dict[str, dict[str, Any]]) -> Topic:
    """Evaluate all six landmarks against the topic results."""
    landmarks = [
        low_conditional_entropy(results["entropy"]),
        slot_structure(results["entropy"], results["morphology"]),
        zipf_tail(results["lexis"]),
        near_repeat_rate(results["syntax"]),
        currier_divergence(results["currier"]),
        line_position(results["position"]),
    ]
    passed = all(landmark.passed for landmark in landmarks)

    sections = [
        "## Landmark reproduction\n\n"
        + table(
            ["landmark", "result", "evidence"],
            [
                [landmark.name, "PASS" if landmark.passed else "FAIL", landmark.detail]
                for landmark in landmarks
            ],
        )
        + f"\n\n**Gate: {'GREEN' if passed else 'RED'}.** "
        + (
            "All six known properties reproduce from `output/`, so the pipeline is "
            "trustworthy enough to build Phase 2 on."
            if passed
            else "At least one known property failed to reproduce. The bug is ours; "
            "no Phase 2 work starts until this is green."
        ),
    ]
    data = {
        "passed": passed,
        "landmarks": {landmark.name: landmark.as_dict() for landmark in landmarks},
    }
    return Topic(
        topic="landmarks",
        title="Phase 1 — Landmark reproduction gate",
        sections=sections,
        data=data,
    )
