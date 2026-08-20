"""Phase 3 entrypoint: close what can be closed, then re-analyse and re-score.

    uv run python -m translations.phase3

Three things happen, in order:

1. **Remediation.** The token alignment and the paragraph blocks are derived,
   and the gap register records what each remedy cost and what stayed open.
2. **Analysis round 2.** The Phase 1 battery is re-run on the representations
   Phase 2's shortlist implies, and four targeted analyses run that only make
   sense once those representations exist.
3. **Re-scoring.** Every funded hypothesis is searched again on each improved
   representation, under the same rules as Phase 2: training pages only, nulls
   with identical settings, held-out pages scored once.

Reports land in ``reports/phase3/``; every candidate lands in
``output/decipher/round2_candidates.parquet``.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import pandas as pd

from translations import alignment, gap_analysis, paragraphs
from translations.analysis import distribution, labels, paradigms, recharacterise, reliability
from translations.analysis.common import is_prose, voynich_view
from translations.analysis.context import build_context
from translations.config import CONFIG, PATHS
from translations.decipher.budget import Budget
from translations.decipher.run_hypothesis import load_hypotheses, markov_baselines, run_hypothesis
from translations.determinism import derived_rng, write_manifest
from translations.phase2 import build_corpora, summarise
from translations.report import Topic, table, write_report
from translations.represent import Representation, identity, merged, phase2_merges, reliable
from translations.strata import build_strata
from vcat.logging import get_logger

logger = get_logger(__name__)

REPORTS = PATHS.repo_root / "reports" / "phase3"
CANDIDATES = PATHS.repo_root / "output" / "decipher" / "round2_candidates.parquet"
MANIFEST_PATH = PATHS.output_dir / "phase3_manifest.json"
PHASE2_MANIFEST = PATHS.output_dir / "phase2_manifest.json"
TRANSLATOR_CONFIG = PATHS.output_dir / "phase3_translator_config.json"

# Representations searched again in round 2. ``raw`` is not re-searched: Phase 2
# ran it with this code, these seeds and this budget, and its numbers are in
# `output/translation/phase2_manifest.json`. Re-running it would spend an hour
# reproducing them.
RESEARCHED: tuple[str, ...] = ("merged", "reliable")

PARADIGM_BASELINES: tuple[str, ...] = ("vulgate_clementine", "herbal_latin", "finnish_bible")
DISTRIBUTION_BASELINES: tuple[str, ...] = ("vulgate_clementine", "austen_pride_prejudice")


def representations(rows: list[alignment.TokenRow]) -> list[Representation]:
    """The three representations Phase 3 carries."""
    merges, provenance = phase2_merges()
    return [
        identity(),
        merged(
            merges,
            origin=f"Phase 2 H2 converged merge search ({provenance['variant']}, "
            f"{provenance['n_merges']} merges)",
            detail=provenance,
        ),
        reliable(rows),
    ]


def round2_search(
    reps: list[Representation], budget: Budget
) -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    """Re-score every funded hypothesis on each re-searched representation."""
    hypotheses = load_hypotheses()
    funded = [hypothesis for hypothesis in hypotheses if hypothesis.funded]
    share = 1.0 / len(RESEARCHED)

    rows: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, dict[str, Any]]] = {}
    for representation in reps:
        if representation.name not in RESEARCHED:
            continue
        corpora, holdout, _ = build_corpora(transform=representation)
        baselines = markov_baselines(corpora, holdout)
        produced: list[dict[str, Any]] = []
        for hypothesis in funded:
            key = f"{representation.name}:{hypothesis.hypothesis_id}"
            deadline = budget.allocate(key, hypothesis.budget_share * share)
            began = time.monotonic()
            candidates = run_hypothesis(
                hypothesis,
                corpora,
                holdout,
                baselines,
                derived_rng(f"round2-{key}"),
                deadline,
            )
            budget.record(key, time.monotonic() - began)
            for row in candidates:
                row["representation"] = representation.name
            produced.extend(candidates)
            logger.info(
                "Round-2 hypothesis complete",
                representation=representation.name,
                hypothesis=hypothesis.hypothesis_id,
                candidates=len(candidates),
                seconds=round(time.monotonic() - began, 1),
            )
        rows.extend(produced)
        summaries[representation.name] = summarise(produced)
    return rows, summaries


def _phase2_summary() -> dict[str, dict[str, Any]]:
    return dict(json.loads(PHASE2_MANIFEST.read_text())["summary"])


def ranking(summaries: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """One row per hypothesis × representation, best first."""
    rows = []
    for representation, summary in summaries.items():
        for hypothesis, values in summary.items():
            rows.append(
                {
                    "hypothesis": hypothesis,
                    "representation": representation,
                    "variant": values["variant"],
                    "gain_per_token": values["gain_per_token"],
                    "holdout_gain_per_token": values["holdout_gain_per_token"],
                    "p_value": values["null"]["p_value"],
                    "q_value": values["q_value"],
                    "converged": values["converged"],
                    "beat_every_null": not any(
                        value >= values["null"]["real"]
                        for value in values["null"]["nulls"].values()
                    ),
                }
            )
    return sorted(rows, key=lambda row: -row["gain_per_token"])


def _artifact_section() -> str:
    """The caveat that has to travel with the round-2 table."""
    import pandas as pd

    frame = pd.read_parquet(CANDIDATES)
    subset = frame[
        (frame["hypothesis"] == "H2")
        & (frame["representation"] == "merged")
        & (frame["split"] == "train")
        & frame["variant"].str.contains("fixed-width-3")
        & frame["variant"].str.startswith("austen")
    ]
    real = float(subset[subset["corpus"] == "real"]["gain_per_token"].iloc[0])
    shuffles = subset[subset["corpus"].str.startswith("shuffle_chars")]["gain_per_token"]
    baselines = (
        frame[(frame["corpus"] == "real") & (frame["representation"] == "merged")]
        .groupby("split")["baseline_bits_per_token"]
        .mean()
    )

    return (
        "Every gain in the table above is larger than its Phase 2 counterpart, and the "
        "top row is within a tenth of a bit of parity. Neither fact is evidence, for two "
        "measurable reasons.\n\n"
        f"**The baseline moved.** On the merged representation the same search scores "
        f"{shuffles.min():+.2f} to {shuffles.max():+.2f} bits/token on *shuffled* "
        f"manuscript text, against {real:+.3f} on the real thing. Shuffled text has no "
        "local structure for an order-2 Markov model to exploit, so the reference "
        "collapses and a substitution code beats it easily. A channel where random text "
        "outscores the manuscript by ten bits is measuring the channel, not the text.\n\n"
        f"**The held-out baseline moved further.** The order-2 reference costs "
        f"{baselines.get('holdout', 0.0):.2f} bits/token on the 41 held-out pages against "
        f"{baselines.get('train', 0.0):.2f} on the training pages, because its parameter "
        "cost is amortised over a fifth as many tokens. That, not a better key, is why "
        "H2's held-out gain is positive while its training gain is not.\n\n"
        "**And the variant did not converge.** H2's best merged variant is fixed-width-3 "
        "over already-merged units — a codebook of hundreds of symbols against 26 letters, "
        "the same wide-alphabet corner Phase 2 recorded as inconclusive rather than "
        "falsified. Nothing here changes that verdict; it re-states it on a second "
        "representation.\n\n"
        "On the training pages, no hypothesis on any representation beats a Markov model "
        "of its own representation, and not one of the eighteen rows beat every surrogate."
    )


def rescoring_topic(
    summaries: dict[str, dict[str, dict[str, Any]]], budget: Budget, reps: list[Representation]
) -> Topic:
    """§5.2.8 — the final ranked hypothesis list."""
    rows = ranking(summaries)
    best_by_hypothesis: dict[str, dict[str, Any]] = {}
    for row in rows:
        current = best_by_hypothesis.get(row["hypothesis"])
        if current is None or row["gain_per_token"] > current["gain_per_token"]:
            best_by_hypothesis[row["hypothesis"]] = row

    phase2 = _phase2_summary()
    movement = []
    for hypothesis, row in sorted(
        best_by_hypothesis.items(), key=lambda item: -item[1]["gain_per_token"]
    ):
        before = phase2.get(hypothesis, {}).get("gain_per_token")
        movement.append(
            [
                hypothesis,
                before,
                row["representation"],
                row["gain_per_token"],
                (row["gain_per_token"] - before) if before is not None else None,
                row["holdout_gain_per_token"],
                row["p_value"],
                row["beat_every_null"],
                row["converged"],
            ]
        )

    sections = [
        "## Final ranked hypotheses, after remediation\n\n"
        + table(
            [
                "id",
                "Phase 2 gain (raw)",
                "best round-2 representation",
                "round-2 gain",
                "Δ",
                "held-out gain",
                "p",
                "beat every null",
                "converged",
            ],
            movement,
        )
        + "\n\nGain is bits per token against an order-2 Markov model **of the same "
        + "representation**. The baseline is re-based for every representation, so Δ is "
        + "not a like-for-like improvement over Phase 2 — it is the gap to a different "
        + "reference. Read the `p` and `beat every null` columns first.",
        "## Why the round-2 numbers look better, and why they are not evidence\n\n"
        + _artifact_section(),
        "## Every representation, every hypothesis\n\n"
        + table(
            ["id", "representation", "variant", "gain", "held-out", "p", "converged"],
            [
                [
                    row["hypothesis"],
                    row["representation"],
                    row["variant"],
                    row["gain_per_token"],
                    row["holdout_gain_per_token"],
                    row["p_value"],
                    row["converged"],
                ]
                for row in rows
            ],
        ),
        "## Representations searched\n\n"
        + table(
            ["representation", "re-searched", "origin"],
            [
                [
                    representation.name,
                    representation.name in RESEARCHED,
                    representation.origin,
                ]
                for representation in reps
            ],
        )
        + "\n\n`raw` is not re-searched: Phase 2 ran it with this code, these seeds and "
        + "this budget, and its numbers are carried from "
        + "`output/translation/phase2_manifest.json` rather than spent again.\n\n"
        + f"Ceiling {CONFIG.round2_budget_seconds:.0f} s; spent {budget.total_spent:.0f} s.",
    ]
    return Topic(
        topic="rescoring",
        title="Phase 3 — Re-scored hypotheses",
        sections=sections,
        data={"ranking": rows, "best_by_hypothesis": best_by_hypothesis, "phase2": phase2},
    )


def _moved(recharacterised: dict[str, Any], name: str) -> str:
    """Name the metrics a representation moved toward the natural-language range."""
    metrics = [
        row["metric"] for row in recharacterised["verdicts"] if row.get(f"{name}_moved_toward")
    ]
    return ", ".join(metrics) if metrics else "none"


def findings_topic(results: dict[str, Any], elapsed: float) -> Topic:
    """The round-2 summary demanded by §5.3."""
    recharacterised = results["recharacterise"]
    rescored = results["rescoring"]
    specificity = results["distribution"]["section_specificity"]
    reliability_summary = results["reliability"]["summary"]
    label_shape = results["labels"]["shape"]
    density = results["paradigms"]["views"]

    def paradigm(view: str, key: str) -> float:
        block = density.get(view, {}).get("density", {})
        return float(block.get(key, 0.0))

    best = max(rescored["ranking"], key=lambda row: row["gain_per_token"], default=None)
    findings = [
        [
            "Token-level agreement is far higher than line-level agreement",
            f"{reliability_summary['exact_token_agreement']:.3f} of tokens read identically "
            f"by ZL and IT, against 0.293 of lines",
            "the line-level mismatch rate overstates transcription noise for anything "
            "computed per token",
        ],
        [
            "Merging buys entropy and pays for it in word length and repetition",
            f"{recharacterised['inside_counts'].get('merged', 0)} of "
            f"{len(recharacterise.METRICS)} metrics inside the natural-language range "
            f"against {recharacterised['inside_counts'].get('raw', 0)} raw; "
            f"{recharacterised['moved_counts'].get('merged', 0)} moved toward it, "
            f"{_moved(recharacterised, 'merged')}",
            "H2's converged merge shifts the conditional entropies into the natural "
            "region but drives mean word length below every baseline and doubles the "
            "near-repeat rate — the signature of a compression, not of a plaintext",
        ],
        [
            "Reliability filtering leaves the landmarks where they were",
            f"{recharacterised['inside_counts'].get('reliable', 0)} of "
            f"{len(recharacterise.METRICS)} metrics inside the natural range, "
            f"{recharacterised['moved_counts'].get('reliable', 0)} moved toward it",
            "the landmarks are properties of the text, not artifacts of the tokens the "
            "two transcribers disagree about",
        ],
        [
            "Roots take more distinct suffixes than in either comparison language",
            f"{paradigm('raw', 'mean_suffixes_per_root'):.2f} suffixes per root against "
            f"{paradigm('vulgate_clementine', 'mean_suffixes_per_root'):.2f} (Latin) and "
            f"{paradigm('finnish_bible', 'mean_suffixes_per_root'):.2f} (Finnish)",
            "suffix choice looks freer than inflection allows — positional generation "
            "remains the live rival to morphology",
        ],
        [
            "Section-specific vocabulary is real",
            f"mean divergence {specificity['observed_mean_divergence']:.3f} bits against a "
            f"page-permutation null of {specificity['null_mean_divergence']:.3f} "
            f"(max {specificity['null_max_divergence']:.3f}), p = {specificity['p_value']:.3f}",
            "herbal-only and pharma-only vocabularies exist beyond page-topic frequency; "
            "they are the most translatable subsets if anything is",
        ],
        [
            "Labels are shorter and plainer than running text",
            f"mean length {label_shape['labels']['mean_length']:.2f} against "
            f"{label_shape['prose (matched sample)']['mean_length']:.2f} in a size-matched "
            f"prose sample; suffix rate {label_shape['labels']['suffix_rate']:.3f} against "
            f"{label_shape['prose (matched sample)']['suffix_rate']:.3f}",
            "consistent with a nomenclature, but with no concordance they still cannot be "
            "tied to what they label",
        ],
        [
            "Re-scoring narrows every gap and changes no verdict",
            (
                f"best round-2 result {best['hypothesis']} on {best['representation']} at "
                f"{best['gain_per_token']:.3f} bits/token, p = {best['p_value']:.3f}, "
                "unconverged"
                if best
                else "—"
            ),
            "the gaps narrow because the baseline is re-based per representation — on the "
            "same channel a shuffled-text surrogate gains ten bits — so no row of the "
            "eighteen is evidence, and none beat its surrogates",
        ],
    ]

    sections = [
        "## Findings\n\n"
        + table(["finding", "effect size", "what it means for the translation"], findings),
        "## What this changes for Phase 4\n\n"
        "The translator's configuration is written to "
        "`output/translation/phase3_translator_config.json`. It records two things and "
        "keeps them apart: `best_scoring`, the top of the ranked table, which is an "
        "unconverged wide-codebook variant and is there only so the number is not hidden; "
        "and `chosen`, the best *converged* candidate that committed to a key, which is "
        "what Phase 4 should actually run. It also carries the per-token reliability "
        "weights the renderer must apply, and the anchors it is allowed to use — still "
        "none.\n\n"
        "Three things Phase 3 makes available that Phase 4 should use: the paragraph "
        "blocks (so a rendering unit can be a paragraph rather than a line), the "
        "per-token reliability weight (so a gloss can be hedged token by token), and the "
        "section-specific vocabulary (so herbal and pharmaceutical pages can be glossed "
        "separately from the rest).",
        "## What we still cannot tell (input to Phase 4)\n\n"
        + "\n".join(f"{index}. {item}" for index, item in enumerate(OPEN_QUESTIONS, start=1)),
        "## Run\n\n"
        + (
            f"Wall clock: {elapsed:.0f}s (excluded from the manifest, which is byte-stable). "
            if elapsed
            else "Reports regenerated from `output/translation/phase3_manifest.json`; the "
            "run cost is recorded there. "
        )
        + "Topics: "
        + ", ".join(sorted(name for name, value in results.items() if isinstance(value, dict)))
        + ".",
    ]
    return Topic(
        topic="round2_findings",
        title="Phase 3 — Analysis round 2",
        sections=sections,
        data={"findings": findings, "open_questions": list(OPEN_QUESTIONS)},
    )


OPEN_QUESTIONS = (
    "What the labels name: no machine-readable illustration↔label concordance could be "
    "pinned, so the 115 label lines remain a nomenclature for unknown things.",
    "Whether the marginalia say anything usable: their readings are disputed and exist "
    "only as prose discussion, so no crib enters the pipeline.",
    "Whether Voynichese words are composed or generated: the paradigm probe shows suffix "
    "choice is freer than inflection and barely conditioned by context, which weakens the "
    "morphology reading without establishing generation.",
    "Whether any hypothesis in the registered space is right: every one of them loses to "
    "a Markov model of the manuscript's own statistics, on every representation tested. "
    "The space may simply not contain the answer.",
    "Whether GC and FG agree with the EVA pair at token level: the v101 mapping is "
    "unbuilt, so cross-alphabet robustness is still untested.",
)


def translator_config(results: dict[str, Any], reps: list[Representation]) -> dict[str, Any]:
    """The configuration Phase 4 consumes, written from what actually won.

    Two different "best" are recorded. ``best_scoring`` is the top of the ranked
    table, which is an unconverged wide-codebook variant, kept so the number is
    not hidden. ``chosen`` is what Phase 4 should run: the best *converged*
    candidate that committed to a key, because a translator needs a decode and an
    unconverged search has not committed to one.
    """
    import pandas as pd

    ranked = results["rescoring"]["ranking"]
    best_scoring = max(ranked, key=lambda row: row["gain_per_token"]) if ranked else {}

    frame = pd.read_parquet(CANDIDATES)
    decodable = frame[
        (frame["corpus"] == "real")
        & (frame["split"] == "train")
        & frame["converged"]
        & (frame["key"].astype(str).str.len() > 2)
    ]
    chosen = decodable.loc[decodable["gain_per_token"].idxmax()] if not decodable.empty else None

    return {
        "chosen": (
            {
                "representation": str(chosen["representation"]),
                "hypothesis": str(chosen["hypothesis"]),
                "variant": str(chosen["variant"]),
                "gain_per_token": float(chosen["gain_per_token"]),
                "key": str(chosen["key"]),
                "merges": str(chosen["merges"]),
            }
            if chosen is not None
            else None
        ),
        "best_scoring": best_scoring,
        "selection_rule": "highest gain among converged candidates that committed to a key; "
        "the top of the ranked table is unconverged and is recorded as best_scoring only",
        "anchors": [],
        "reliability": {
            "path": "output/translation/token_alignment.parquet",
            "floor": CONFIG.reliability_floor,
            "policy": "render every token, hedge by weight; never silently drop",
        },
        "paragraphs": {"source": "IVTFF <%> / <$> markers", "blocks": results["blocks"]},
        "representations": {representation.name: representation.detail for representation in reps},
        "warning": "Every hypothesis in this configuration lost to a Markov model of the "
        "manuscript's own statistics, and none beat its surrogates. Phase 4 renders under a "
        "losing model and must say so on every artifact.",
    }


def reports_only() -> int:
    """Re-emit the round-2 reports from the recorded manifest and topic JSONs.

    The searches are the expensive half of Phase 3; the write-up should be
    fixable without spending two hours reproducing numbers already committed to
    `output/translation/phase3_manifest.json`.
    """
    manifest = json.loads(MANIFEST_PATH.read_text())
    budget = Budget(total_seconds=manifest["round2"]["budget"]["ceiling_s"])
    budget.spent = dict(manifest["round2"]["budget"]["spent"])
    reps = [
        Representation(
            name=name,
            transform=lambda view: view,
            origin=str(row["origin"]),
            detail=dict(row["detail"]),
        )
        for name, row in sorted(manifest["representations"].items())
    ]

    results: dict[str, Any] = {"blocks": manifest["paragraphs"]["blocks"]}
    for topic in (
        "gap_analysis",
        "reliability",
        "recharacterise",
        "paradigms",
        "distribution",
        "labels",
    ):
        results[topic] = json.loads((REPORTS / f"{topic}.json").read_text())

    rescored = rescoring_topic(manifest["round2"]["summaries"], budget, reps)
    write_report(REPORTS, rescored.topic, rescored.title, rescored.sections, rescored.data)
    results[rescored.topic] = rescored.data

    findings = findings_topic(results, 0.0)
    write_report(REPORTS, findings.topic, findings.title, findings.sections, findings.data)

    configuration = translator_config(results, reps)
    TRANSLATOR_CONFIG.write_text(json.dumps(configuration, indent=2, sort_keys=True) + "\n")
    manifest["translator_config"] = configuration
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Reports rewritten from {MANIFEST_PATH}")
    return 0


def main() -> int:
    """Run Phase 3 end to end."""
    if "--reports-only" in sys.argv:
        return reports_only()
    started = time.time()

    token_rows = alignment.build_rows()
    written, path = alignment.write_alignment(token_rows)
    alignment_summary = alignment.summarise(token_rows)
    blocks = paragraphs.build_blocks()
    block_validation = paragraphs.validation(blocks)
    logger.info("Remediation complete", tokens=written, path=path, blocks=len(blocks))

    reps = representations(token_rows)
    ctx = build_context()
    views = {representation.name: representation(ctx.base) for representation in reps}
    strata = build_strata()

    results: dict[str, Any] = {"blocks": len(blocks)}
    topics: list[Topic] = [
        gap_analysis.run(len(blocks), written, extra={"paragraph_validation": block_validation}),
        reliability.run(token_rows, strata, alignment_summary),
        recharacterise.run(ctx, reps, views),
        paradigms.run({**views, **{name: ctx.baselines[name] for name in PARADIGM_BASELINES}}),
        distribution.run(
            {
                **views,
                **{name: ctx.baselines[name] for name in DISTRIBUTION_BASELINES},
                **ctx.pseudo,
            },
            voynich="raw",
        ),
        labels.run(
            voynich_view("voynich|labels", keep=lambda row: row.line_type == "label"),
            voynich_view("voynich|prose", keep=is_prose),
        ),
    ]
    for topic in topics:
        write_report(REPORTS, topic.topic, topic.title, topic.sections, topic.data)
        results[topic.topic] = topic.data
        logger.info("Topic complete", topic=topic.topic)

    budget = Budget(total_seconds=CONFIG.round2_budget_seconds)
    if "--analysis-only" in sys.argv:
        print(f"Analysis reports written to {REPORTS}; re-scoring skipped")
        return 0
    rows, summaries = round2_search(reps, budget)
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(
        ["representation", "hypothesis", "corpus", "split", "variant"]
    ).to_parquet(CANDIDATES, index=False)

    rescored = rescoring_topic(summaries, budget, reps)
    write_report(REPORTS, rescored.topic, rescored.title, rescored.sections, rescored.data)
    results[rescored.topic] = rescored.data

    findings = findings_topic(results, time.time() - started)
    write_report(REPORTS, findings.topic, findings.title, findings.sections, findings.data)

    configuration = translator_config(results, reps)
    TRANSLATOR_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATOR_CONFIG.write_text(json.dumps(configuration, indent=2, sort_keys=True) + "\n")

    write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index, PATHS.sources_yaml],
        extra={
            "phase": 3,
            "alignment": alignment_summary,
            "paragraphs": block_validation,
            "representations": {
                representation.name: {
                    "origin": representation.origin,
                    "detail": representation.detail,
                    "words": views[representation.name].n_words,
                    "units": views[representation.name].n_units,
                }
                for representation in reps
            },
            "gap_counts": results["gap_analysis"]["counts"],
            "round2": {
                "budget": {"ceiling_s": CONFIG.round2_budget_seconds, "spent": budget.spent},
                "candidates": len(rows),
                "summaries": summaries,
            },
            "translator_config": configuration,
        },
    )

    print(f"Reports written to {REPORTS}")
    print(f"Candidates: {len(rows)} -> {CANDIDATES}")
    print(f"Wall clock {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
