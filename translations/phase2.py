"""Phase 2 entrypoint: score the pre-registered hypothesis space.

    uv run python -m translations.phase2

Runs every funded hypothesis on the training pages, repeats each search on the
null corpora, scores the winner once on the held-out pages, and writes the
ranked table. Every candidate — including the losers and the null runs — lands
in ``output/decipher/candidates.parquet``.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

import pandas as pd

from translations.analysis.common import (
    View,
    grille_view,
    null_view,
    selfcite_view,
    voynich_view,
)
from translations.analysis.context import tune_pseudo
from translations.config import CONFIG, PATHS
from translations.decipher.budget import Budget
from translations.decipher.lm import corpus_lm
from translations.decipher.run_hypothesis import (
    Hypothesis,
    load_hypotheses,
    markov_baselines,
    run_hypothesis,
)
from translations.decipher.stats import NullComparison, benjamini_hochberg
from translations.decipher.synthetic import run_recovery
from translations.determinism import derived_rng, write_manifest
from translations.report import Topic, table, write_report
from vcat.logging import get_logger

logger = get_logger(__name__)

REPORTS = PATHS.repo_root / "reports" / "phase2"
CANDIDATES = PATHS.repo_root / "output" / "decipher" / "candidates.parquet"
MANIFEST_PATH = PATHS.output_dir / "phase2_manifest.json"

SYNTHETIC_SCHEMES = ("substitution", "verbose", "abjad")

# Why a hypothesis is worth carrying forward despite losing (plan §4.7).
SHORTLIST_REASONS: dict[str, str] = {
    "H2": "best-scoring channel, and the only one that shortens words toward plausible "
    "plaintext lengths; its widest variant did not converge, so it is inconclusive rather "
    "than falsified",
    "H1": "the only hypothesis whose real score beat every surrogate run, on the herbal "
    "Latin model — a weak signal, but the only one in the table",
    "H8": "best structural description of word formation, and the inventory Phase 4 needs "
    "for morph-level glossing",
    "H6b": "carried as the rival control: Phase 5 has to keep scoring the autocopy model "
    "against whatever Phase 4 produces",
}


def build_corpora(
    replicates: int = CONFIG.null_replicates,
) -> tuple[dict[str, View], View, dict[str, Any]]:
    """Training corpora (real plus null replicates) and the untouched held-out view.

    Each null family gets ``replicates`` independently seeded surrogates. One
    surrogate per family would floor the empirical p-value at 0.2, which is not a
    significance test — it is a rounding error with a p in front of it.
    """
    train = voynich_view("voynich|train", keep=lambda row: not row.is_holdout)
    holdout = voynich_view("voynich|holdout", keep=lambda row: row.is_holdout)
    _, _, tuning = tune_pseudo(train)

    corpora: dict[str, View] = {"real": train}
    for replicate in range(replicates):
        corpora[f"grille_r{replicate}"] = grille_view(
            train, derived_rng(f"p2-grille-{replicate}"), **tuning["grille"]["params"]
        )
        corpora[f"selfcite_r{replicate}"] = selfcite_view(
            train, derived_rng(f"p2-selfcite-{replicate}"), **tuning["selfcite"]["params"]
        )
        corpora[f"shuffle_chars_r{replicate}"] = null_view(
            "shuffle_chars", train, derived_rng(f"p2-shuffle-{replicate}")
        )
        corpora[f"markov_chars_r{replicate}"] = null_view(
            "markov_chars", train, derived_rng(f"p2-markov-{replicate}"), order=2
        )
    return corpora, holdout, tuning


def summarise(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Best variant per hypothesis, with its null comparison and held-out score."""
    frame = pd.DataFrame(rows)
    summary: dict[str, dict[str, Any]] = {}
    for hypothesis in sorted(frame["hypothesis"].unique()):
        subset = frame[frame["hypothesis"] == hypothesis]
        train_real = subset[(subset["corpus"] == "real") & (subset["split"] == "train")]
        if train_real.empty:
            continue
        best = train_real.loc[train_real["gain_per_token"].idxmax()]
        nulls = subset[(subset["corpus"] != "real") & (subset["variant"] == best["variant"])]
        comparison = NullComparison(
            real=float(best["gain_per_token"]),
            nulls={row["corpus"]: float(row["gain_per_token"]) for _, row in nulls.iterrows()},
        )
        heldout = subset[subset["split"] == "holdout"]
        summary[hypothesis] = {
            "variant": best["variant"],
            "gain_per_token": float(best["gain_per_token"]),
            "bits_per_token": float(best["bits_per_token"]),
            "baseline_bits_per_token": float(best["baseline_bits_per_token"]),
            "holdout_gain_per_token": (
                float(heldout["gain_per_token"].iloc[0]) if not heldout.empty else None
            ),
            "truncated": bool(subset["truncated"].any()),
            "converged": bool(best["converged"]),
            "budget_spent_s": float(subset["budget_spent_s"].sum()),
            "null": comparison.as_dict(),
            "detail": str(best["detail"]),
            "key": str(best["key"]) if "key" in best else "",
            "merges": str(best["merges"]) if "merges" in best else "[]",
        }
    q_values = benjamini_hochberg(
        {name: float(row["null"]["p_value"]) for name, row in summary.items()}
    )
    for name, row in summary.items():
        row["q_value"] = q_values.get(name)
    return summary


def synthetic_validation() -> list[dict[str, Any]]:
    """Known-answer tests: can the engine break ciphers we built ourselves?"""
    results = []
    for scheme in SYNTHETIC_SCHEMES:
        transform = "abjad" if scheme == "abjad" else "plain"
        lm = corpus_lm("vulgate_clementine", 3, transform)
        recovery = run_recovery(
            "caesar_bello_gallico",
            8000,
            scheme,
            lm,
            derived_rng(f"synthetic-{scheme}"),
            iterations=60000,
            restarts=6,
        )
        results.append(recovery.as_dict())
    return results


def scores_topic(
    summary: dict[str, dict[str, Any]], hypotheses: list[Hypothesis], budget: Budget
) -> Topic:
    """The ranked hypothesis table."""
    ranked = sorted(summary.items(), key=lambda item: -item[1]["gain_per_token"])
    lookup = {hypothesis.hypothesis_id: hypothesis for hypothesis in hypotheses}

    rows = []
    for name, row in ranked:
        best_null = row["null"]["best_null"]
        rows.append(
            [
                name,
                lookup[name].title if name in lookup else "",
                row["variant"],
                row["gain_per_token"],
                best_null[1] if best_null else None,
                row["null"]["p_value"],
                row["q_value"],
                row["holdout_gain_per_token"],
                row["truncated"],
            ]
        )

    null_counts = {name: len(row["null"]["nulls"]) for name, row in summary.items()}
    smallest = min(null_counts.values(), default=0)
    floor = 1 / (smallest + 1) if smallest else 1.0
    unfunded = [h for h in hypotheses if not h.funded]
    sections = [
        "## Ranked hypotheses\n\n"
        + table(
            [
                "id",
                "hypothesis",
                "best variant",
                "gain (bits/token)",
                "best null gain",
                "p",
                "q (BH)",
                "held-out gain",
                "truncated",
            ],
            rows,
        )
        + "\n\n**Gain** is bits per token saved against an order-2 Markov model of the "
        + "glyph stream itself, with the key, merge partition or grammar charged as model "
        + "bits. Positive means the hypothesis describes the manuscript better than its own "
        + "local statistics do.\n\n"
        + "**Resolution of the p-values.** Each hypothesis is positioned against "
        + f"{smallest} surrogate runs, so the smallest empirical p obtainable is "
        + f"1/({smallest} + 1) = {floor:.3f}. No result in this table could have reached "
        + "p < 0.05 by design, and none comes close to the floor either: read the columns as "
        + '"the search does no better on the manuscript than on surrogate text", not as a '
        + "significance test that was passed or failed.",
        "## What each hypothesis actually cost\n\n"
        + table(
            ["id", "budget share", "spent (s)", "converged", "detail"],
            [
                [
                    name,
                    lookup[name].budget_share if name in lookup else None,
                    row["budget_spent_s"],
                    row["converged"],
                    row["detail"],
                ]
                for name, row in ranked
            ],
        )
        + f"\n\nCeiling {CONFIG.search_budget_seconds:.0f} s; spent {budget.total_spent:.0f} s.",
        "## Shortlist carried into Phase 4\n\n"
        + table(
            ["rank", "id", "gain", "beat every null", "converged", "why it is carried"],
            [
                [
                    rank,
                    name,
                    row["gain_per_token"],
                    not any(
                        value >= row["null"]["real"] for value in row["null"]["nulls"].values()
                    ),
                    row["converged"],
                    SHORTLIST_REASONS.get(name, ""),
                ]
                for rank, (name, row) in enumerate(ranked, start=1)
                if name in SHORTLIST_REASONS
            ],
        )
        + "\n\nEvery one of these lost to the baseline, so Phase 4 will be rendering "
        + "English under a *losing* model and must say so on every artifact it emits "
        + "(§0.4, §6.3). They are carried because they are the least-bad decodes "
        + "available, not because any of them is supported.",
        "## Unfunded\n\n"
        + "\n".join(
            f"- **{h.hypothesis_id} — {h.title}**: {h.record.get('unfunded_rationale', '').strip()}"
            for h in unfunded
        )
        + "\n\nUnfunded is not falsified. These records are registered with their grids so "
        + "they can be run unchanged when the budget exists.",
    ]
    return Topic(
        topic="hypothesis_scores",
        title="Phase 2 — Hypothesis scores",
        sections=sections,
        data={"summary": summary, "budget_spent_s": budget.total_spent},
    )


def synthetic_topic(results: list[dict[str, Any]]) -> Topic:
    """The known-answer report."""
    sections = [
        "## Blind recovery of hidden keys\n\n"
        + table(
            ["scheme", "corpus", "tokens", "key accuracy", "token accuracy", "found ≤ true bits"],
            [
                [
                    row["scheme"],
                    row["corpus"],
                    row["n_tokens"],
                    row["key_accuracy"],
                    row["token_accuracy"],
                    row["found_better_than_truth"],
                ]
                for row in results
            ],
        )
        + "\n\nEach line is a cipher this project built and then tried to break without the "
        + "key. A search that cannot recover a key it invented itself cannot be trusted with "
        + "the manuscript. Key accuracy is token-weighted; the verbose scheme has no "
        + "single-unit key to compare against, so only token accuracy is meaningful there.",
    ]
    return Topic(
        topic="synthetic_validation",
        title="Phase 2 — Synthetic validation of the search",
        sections=sections,
        data={"recoveries": results},
    )


def approach_topic(
    summary: dict[str, dict[str, Any]],
    hypotheses: list[Hypothesis],
    recoveries: list[dict[str, Any]],
) -> Topic:
    """The method write-up demanded by §4.7."""
    recovered = ", ".join(f"{row['scheme']} {row['token_accuracy']:.0%}" for row in recoveries)
    funded = [h for h in hypotheses if h.funded]
    sections = [
        "## The question, made scoreable\n\n"
        "Every hypothesis is treated as a *code* for the manuscript, and scored by the "
        "number of bits it needs to reconstruct the observed glyph stream exactly: the "
        "model (key, merge partition, syllable table, grammar) plus the data under that "
        "model. This is what puts 'enciphered Latin' and 'meaningless table-generated "
        "text' on one scale, and it is the MDL penalty of §4.1 — a key elaborate enough "
        "to fit anything has to pay for itself first.\n\n"
        "Two costs are charged that are easy to omit. Writing down the key costs "
        "`(units − 1) · log2 27` bits. And if a key maps several glyphs onto one letter, "
        "the plaintext no longer reconstructs the manuscript, so each occurrence is "
        "charged `log2(glyphs sharing that letter)`. Without that second term every "
        "search collapses the key onto `e`.",
        "## What a score is measured against\n\n"
        "The reference is an order-2 Markov model of the glyph stream itself, with its "
        "parameters priced at ½·log2(N) bits each. It knows nothing about language — only "
        "the manuscript's own local statistics — so a hypothesis that cannot beat it is "
        "not explaining anything. Reported **gain** is bits per token saved against that "
        "baseline.\n\n"
        "A raw score is not evidence, so every funded hypothesis is re-run, unchanged, on "
        "four null corpora: the two tuned pseudo-Voynich generators from Phase 1 (grille, "
        "autocopy), a glyph shuffle, and an order-2 Markov surrogate. Significance is the "
        "real score's position in that null distribution, Benjamini–Hochberg corrected "
        "across the grid.",
        "## Search\n\n"
        "Keys are found by simulated annealing with multi-restart, seeded, iteration-"
        "counted, and started from a frequency-matched assignment. Scoring is vectorised "
        "over *distinct* cipher n-grams rather than positions, which is what makes a "
        "million key evaluations affordable on CPU. For the order-1 case (H7) the optimal "
        "key is an exact linear assignment, so no search is needed.\n\n"
        "The verbose hypothesis (H2) is searched two ways: fixed-width segmentation "
        "(every plaintext letter written with exactly 2 or 3 glyphs) and a content-based "
        "merge search over partitions, seeded with the morphs Phase 1 induced. The merge "
        "search is stochastic steepest descent — plain hill-climbing wanders in this "
        "space, which the synthetic verbose cipher makes visible.\n\n"
        "Not implemented: Bayesian/Gibbs decipherment. At a 25-symbol cipher alphabet the "
        "annealer reaches the same optimum well inside budget; Gibbs earns its keep on key "
        "spaces an order of magnitude larger, which is H5, and H5 is registered unfunded.",
        "## Discipline\n\n"
        f"All {len(hypotheses)} hypotheses were registered as YAML records — prediction, "
        "falsifier, prior, Phase 1 evidence for and against, search grid and budget share — "
        "and committed before any run. Searches see the training pages only; the held-out "
        "pages (41 of 206, frozen in Phase 0) are scored once, at the end, with the key the "
        "search already committed to. Every candidate is written to "
        "`output/decipher/candidates.parquet`, losers and null runs included, each row "
        "carrying its budget, convergence and truncation flags.\n\n"
        "Anchors (zodiac month names, marginalia) are **not** used: the catalogue is empty "
        "until Phase 3 can source them with checksums. The protocol is implemented so that "
        "when they arrive they can only rank finished candidates, never enter the models.",
        "## Does the search work at all?\n\n"
        f"Known-answer tests, on ciphers built here and then broken blind: {recovered} "
        "token accuracy. The engine recovers keys it invented itself under substitution, "
        "fixed-width verbose and abjad schemes, which is the precondition for its verdict "
        "on the manuscript meaning anything. See `synthetic_validation.md`.",
        "## Funded this run\n\n"
        + table(
            ["id", "hypothesis", "family", "budget share", "search"],
            [[h.hypothesis_id, h.title, h.family, h.budget_share, h.kind] for h in funded],
        ),
    ]
    return Topic(
        topic="approach",
        title="Phase 2 — Approach to cracking",
        sections=sections,
        data={"hypotheses": [h.hypothesis_id for h in hypotheses], "summary": summary},
    )


def write_reports(
    summary: dict[str, dict[str, Any]],
    hypotheses: list[Hypothesis],
    budget: Budget,
    recoveries: list[dict[str, Any]],
) -> None:
    """Emit all three Phase 2 reports."""
    for topic in (
        scores_topic(summary, hypotheses, budget),
        synthetic_topic(recoveries),
        approach_topic(summary, hypotheses, recoveries),
    ):
        write_report(REPORTS, topic.topic, topic.title, topic.sections, topic.data)


def reports_only() -> int:
    """Re-emit the reports from the recorded manifest, without re-searching."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    budget = Budget(total_seconds=manifest["budget"]["ceiling_s"])
    budget.spent = dict(manifest["budget"]["spent"])
    write_reports(manifest["summary"], load_hypotheses(), budget, manifest["synthetic_validation"])
    print(f"Reports rewritten from {MANIFEST_PATH}")
    return 0


def main() -> int:
    """Run Phase 2 end to end."""
    if "--reports-only" in sys.argv:
        return reports_only()
    started = time.time()
    corpora, holdout, tuning = build_corpora()
    baselines = markov_baselines(corpora, holdout)
    hypotheses = load_hypotheses()
    budget = Budget(total_seconds=CONFIG.search_budget_seconds)

    rows: list[dict[str, Any]] = []
    for hypothesis in hypotheses:
        if not hypothesis.funded:
            logger.info("Skipping unfunded hypothesis", hypothesis=hypothesis.hypothesis_id)
            continue
        deadline = budget.allocate(hypothesis.hypothesis_id, hypothesis.budget_share)
        began = time.monotonic()
        produced = run_hypothesis(
            hypothesis,
            corpora,
            holdout,
            baselines,
            derived_rng(f"search-{hypothesis.hypothesis_id}"),
            deadline,
        )
        budget.record(hypothesis.hypothesis_id, time.monotonic() - began)
        rows.extend(produced)
        logger.info(
            "Hypothesis complete",
            hypothesis=hypothesis.hypothesis_id,
            candidates=len(produced),
            seconds=round(time.monotonic() - began, 1),
        )

    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows).sort_values(["hypothesis", "corpus", "split", "variant"])
    frame.to_parquet(CANDIDATES, index=False)

    summary = summarise(rows)
    recoveries = synthetic_validation()

    write_reports(summary, hypotheses, budget, recoveries)

    write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index, PATHS.sources_yaml],
        extra={
            "phase": 2,
            "hypotheses": {h.hypothesis_id: h.record for h in hypotheses},
            "budget": {"ceiling_s": CONFIG.search_budget_seconds, "spent": budget.spent},
            "nulls": {"replicates": CONFIG.null_replicates, "corpora": sorted(corpora)},
            "pseudo_tuning": tuning,
            "candidates": len(rows),
            "summary": summary,
            "synthetic_validation": recoveries,
        },
    )
    print(
        json.dumps(
            {name: round(row["gain_per_token"], 3) for name, row in summary.items()}, indent=2
        )
    )
    print(f"Candidates: {len(rows)} -> {CANDIDATES}")
    print(f"Reports written to {REPORTS} (wall clock {time.time() - started:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
