"""Phase 5 entrypoint: the adversarial self-audit (plan §7).

    uv run python -m translations.phase5

Re-runs the Phase 4 pipeline over everything that should change the answer and
everything that should not, scores the five kill criteria the plan agreed in
advance, and writes `reports/translation/strengths_weaknesses.md`.

The audit does not decide whether to publish the translation — Phase 4's
artifacts stay either way (§7.4). It decides what the banner on them says.
"""

from __future__ import annotations

import re
import sys
import time
from typing import Any

from translations.analysis.common import View
from translations.audit import build_harness
from translations.audit.common import Check, Harness, gated_coverage, mean_confidence
from translations.audit.strength import run as strength_battery
from translations.audit.weakness import run as weakness_battery
from translations.config import CONFIG, PATHS, active_banner
from translations.decipher.budget import Deadline
from translations.determinism import write_manifest
from translations.phase4 import CONTROLS, REPORTS, STRATA_FIELDS, by_stratum, render_salt
from translations.pipeline import TranslatedLine
from translations.report import Topic, table, write_report
from vcat.logging import get_logger

logger = get_logger(__name__)

MANIFEST_PATH = PATHS.output_dir / "phase5_manifest.json"
DECISIONS = PATHS.repo_root / "docs" / "decisions.md"
DECISION_HEADING = re.compile(r"^## (Decision \d+): (.+)$", re.MULTILINE)


def control_views(harness: Harness) -> dict[str, View]:
    """The manuscript and the two pseudo-Voynich controls, built as Phase 4 builds them."""
    views = {"real": harness.representation(harness.base)}
    for name, build in CONTROLS.items():
        views[name] = harness.representation(build(harness.base))
    return views


def render_corpora(harness: Harness, views: dict[str, View]) -> dict[str, list[TranslatedLine]]:
    """Reproduce the committed Phase 4 renderings, salt for salt."""
    return {
        name: harness.render(
            render_salt(harness.primary.hypothesis_id, name), view, reliability=name == "real"
        )
        for name, view in views.items()
    }


def kill_criteria(checks: dict[str, Check]) -> list[dict[str, Any]]:
    """Score the five criteria §7.4 fixed in advance. Any one of them is decisive."""
    control = checks["§7.2.1 pseudo-Voynich control"].data
    holdout = checks["§7.1.2 held-out generalisation"].data
    cross = checks["§7.1.3 cross-transcription stability"].data
    rival = checks["§7.2.3 rival-language ambiguity"].data
    congruence = checks["§7.1.5 illustration congruence"].data
    return [
        {
            "criterion": "Comparable fluency and confidence on pseudo-Voynich",
            "measured": f"control renders at {control['ratio']:.0%} of the manuscript's rate",
            "met": bool(control["ratio"] >= 1.0),
        },
        {
            "criterion": "Held-out performance indistinguishable from the null distribution",
            "measured": f"permutation p = {holdout['p_value']:.3f}",
            "met": bool(holdout["p_value"] > 0.05),
        },
        {
            "criterion": "Cross-transcription gloss agreement no better than transcription identity",
            "measured": (
                f"gloss agreement {cross['gloss_agreement']:.3f} against a "
                f"{cross['line_identity_baseline']:.3f} line-identity baseline"
            ),
            "met": bool(cross["gloss_agreement"] <= cross["line_identity_baseline"]),
        },
        {
            "criterion": "Multiple unrelated plaintext languages score equivalently",
            "measured": (
                f"gated coverage spread {rival['coverage_spread']:.3f} across "
                f"{len(rival['languages'])} language models"
            ),
            "met": bool(rival["coverage_spread"] < 0.2),
        },
        {
            "criterion": "Illustration congruence shows no signal above the permutation null",
            "measured": (
                f"rendering {congruence['statistic']:.4f} bits at "
                f"p = {congruence['p_value']:.3f}; untranslated types "
                f"{congruence['surface_statistic']:.4f} at "
                f"p = {congruence['surface_p_value']:.3f}"
            ),
            # The operative question is whether *translating* adds congruence. The
            # untranslated types are the null: a signal they already carry is a
            # property of Voynichese vocabulary, not of the reading.
            "met": bool(
                congruence["p_value"] > 0.05
                or congruence["statistic"] <= congruence["surface_statistic"]
            ),
        },
    ]


def decision_links() -> list[list[str]]:
    """Every entry in the decision log, so the report links the whole programme."""
    text = DECISIONS.read_text()
    return [
        [number, title, f"`docs/decisions.md` — {number}"]
        for number, title in DECISION_HEADING.findall(text)
        if not title.startswith("[Title]")
    ]


def evidence_table(checks: list[Check]) -> str:
    """One row per test: what it measured, against what, and what it means."""
    return table(
        ["test", "metric", "value", "null / comparison", "verdict"],
        [
            [
                check.finding.test,
                check.finding.metric,
                check.finding.value,
                check.finding.null,
                check.finding.verdict,
            ]
            for check in checks
        ],
    )


def bottom_line(criteria: list[dict[str, Any]], control: dict[str, Any], overall: float) -> str:
    """What this is and what it is not, in one paragraph."""
    met = [row for row in criteria if row["met"]]
    if not met:
        return (
            "## Bottom line\n\nNone of the five kill criteria agreed in advance was met. The "
            "rendering remains speculative and unvalidated, but the audit found no result that "
            "retires the hypothesis."
        )
    return (
        "## Bottom line\n\n"
        f"**What this is:** a complete English rendering of all 4,072 lines under a stated "
        f"hypothesis, with {overall:.1%} of tokens surviving the confidence gate.\n\n"
        f"**What it is not:** a reading of the Voynich Manuscript. "
        f"{len(met)} of the 5 kill criteria the plan agreed in advance are met — chief among "
        f"them the decisive one, that the identical pipeline renders pseudo-Voynich which "
        f"encodes nothing at {control['ratio']:.0%} of the rate it renders the manuscript. "
        "Under §7.4 the decipherment attempt is declared **unsuccessful**, and that is the "
        "finding this programme publishes. The Phase 4 artifacts are not withdrawn; they are "
        "re-framed, and every one of them carries the failed-validation banner."
    )


def audit_topic(
    harness: Harness,
    strengths: list[Check],
    weaknesses: list[Check],
    lines: list[TranslatedLine],
    criteria: list[dict[str, Any]],
) -> Topic:
    """`reports/translation/strengths_weaknesses.md`, structured as §7.3 requires."""
    by_test = {check.finding.test: check for check in [*strengths, *weaknesses]}
    control = by_test["§7.2.1 pseudo-Voynich control"]
    overall = gated_coverage(lines)

    strata = "\n\n".join(
        f"### {field}\n\n"
        + table(
            ["stratum", "lines", "tokens", "gated coverage", "mean confidence"],
            [
                [
                    row["stratum"],
                    int(row["lines"]),
                    int(row["tokens"]),
                    row["gated_coverage"],
                    row["mean_confidence"],
                ]
                for row in by_stratum(lines, field)
            ],
        )
        for field in STRATA_FIELDS
    )

    sections = [
        bottom_line(criteria, control.data, overall),
        "## The decisive control (read this before any sample rendering)\n\n" + control.detail,
        "## Kill criteria, agreed in advance (§7.4)\n\n"
        + table(
            ["criterion", "measured", "met"],
            [[row["criterion"], row["measured"], row["met"]] for row in criteria],
        ),
        "## Gated coverage by stratum\n\n" + strata,
        "## Strength evidence (§7.1)\n\n"
        + evidence_table(strengths)
        + "\n\n"
        + "\n\n".join(
            f"### {check.finding.test}\n\n{check.detail}" for check in strengths if check.detail
        ),
        "## Weakness evidence (§7.2)\n\n"
        + evidence_table(weaknesses)
        + "\n\n"
        + "\n\n".join(
            f"### {check.finding.test}\n\n{check.detail}"
            for check in weaknesses
            if check.detail and check.finding.test != control.finding.test
        ),
        "## Falsification conditions\n\n"
        "**What would retire the current hypothesis** — beyond the criteria already met:\n\n"
        "- A pseudo-Voynich control that renders *less* than the manuscript would remove the "
        "decisive objection, but only removes it; it is a necessary condition, not evidence.\n"
        "- A key that survives re-searching from a different seed with near-total gloss "
        "agreement, where the current keys do not.\n"
        "- Ablations that leave the headline coverage unmoved, where changing the tokenization "
        "currently collapses it.\n\n"
        "**What would raise confidence** — none of these is available from the manuscript "
        "alone, and all are automatable once their source is:\n\n"
        "- The illustration↔label concordance that plan §5.1 still lists as an open gap, "
        "turning §7.1.5 into a label-level test rather than a page-level one.\n"
        "- A sourced anchor catalogue (zodiac month names, f116v marginalia, the v101 "
        "mapping), which would let §7.1.7 run at all.\n"
        "- A hypothesis whose gain per token beats an order-2 Markov model of the manuscript's "
        "own statistics on held-out pages. No hypothesis in this programme does; until one "
        "does, every rendering downstream is decoration on a losing model.",
        "## Decision log\n\n"
        + table(["decision", "title", "where"], decision_links())
        + "\n\nEvery negative result in this programme is written up there, as `AGENTS.md` "
        "requires: a cleanly falsified hypothesis is a deliverable.",
        f"## Run\n\n`make audit` · {CONFIG.audit_seeds} seeds and {CONFIG.audit_subsets} "
        f"training subsets per keyed hypothesis · {CONFIG.audit_permutations:,} permutations "
        f"per null · ceiling {CONFIG.audit_budget_seconds:.0f} s. No wall-clock figure is "
        "recorded here or in the manifest, so the report is byte-identical across runs.\n\n"
        "**One caveat about this audit itself.** Plan §9 asked for the Phase 5 tests to be "
        "written before any Phase 4 output was read, so that the pipeline could not be tuned "
        "against its own audit. That ordering was not followed: Phase 4 was completed and its "
        "reports read first. Nothing in Phase 4 was changed in response to an audit result — "
        "the only edit this phase made to it was the banner, which the audit's verdict "
        "requires — but the tests were chosen by someone who already knew what the pipeline "
        "produced, and a reader should weigh them accordingly. Three of them (§7.1.5's "
        "untranslated-type baseline, §7.2.1's five-draw range, §7.2.2's gloss-multiset "
        "assertion) were added *because* a first result looked better than it was, which cuts "
        "in the honest direction but is exactly the freedom the ordering rule exists to remove.",
    ]
    return Topic(
        topic="strengths_weaknesses",
        title="Phase 5 — Strengths and weaknesses of the automated translation",
        sections=sections,
        data={
            "kill_criteria": criteria,
            "declared_unsuccessful": any(row["met"] for row in criteria),
            "gated_coverage": overall,
            "mean_confidence": mean_confidence(lines),
            "strength": {check.finding.test: check.finding.as_dict() for check in strengths},
            "weakness": {check.finding.test: check.finding.as_dict() for check in weaknesses},
            "detail": {check.finding.test: check.data for check in [*strengths, *weaknesses]},
        },
    )


def main() -> int:
    """Run the Phase 5 audit end to end."""
    started = time.time()
    deadline = Deadline(seconds=CONFIG.audit_budget_seconds)
    harness = build_harness()
    views = control_views(harness)
    renderings = render_corpora(harness, views)
    lines = renderings["real"]
    logger.info("Rendered corpora", corpora=sorted(renderings), tokens=len(harness.base.words))

    strengths = strength_battery(harness, lines, renderings["grille"])
    logger.info("Strength battery done", seconds=round(time.time() - started))
    weaknesses = weakness_battery(harness, lines, renderings, views, deadline)
    logger.info("Weakness battery done", seconds=round(time.time() - started))

    by_test = {check.finding.test: check for check in [*strengths, *weaknesses]}
    criteria = kill_criteria(by_test)
    failed = any(row["met"] for row in criteria)
    topic = audit_topic(harness, strengths, weaknesses, lines, criteria)
    write_report(
        REPORTS, topic.topic, topic.title, topic.sections, topic.data, active_banner(failed)
    )

    write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index],
        extra={
            "phase": 5,
            "primary": harness.primary.hypothesis_id,
            "declared_unsuccessful": failed,
            "kill_criteria": criteria,
            "findings": [check.finding.as_dict() for check in [*strengths, *weaknesses]],
            "budget_seconds": CONFIG.audit_budget_seconds,
            "budget_expired": deadline.expired,
        },
    )
    met = sum(1 for row in criteria if row["met"])
    print(f"Audit written to {REPORTS / 'strengths_weaknesses.md'}")
    print(f"Kill criteria met: {met}/5 -> declared unsuccessful: {failed}")
    print(f"Wall clock {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
