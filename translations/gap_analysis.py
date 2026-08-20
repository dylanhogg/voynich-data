"""§5.1 — the formal gap analysis.

One record per gap: what it blocks, the remedy, what the remedy cost, what
provenance it needed, and what actually happened. Statuses are computed from
the artifacts on disk where that is possible, so a gap cannot be reported closed
because someone wrote "closed" in a table.

Two gaps are closed by *derivation* (the alignment, the paragraph blocks), two
by new checksummed sources, and three stay open. An open gap here is a
deliverable, not a failure: §5.1 pre-committed to the fallback for each one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from translations.alignment import ALIGNMENT_PATH
from translations.corpora.registry import load_specs
from translations.report import Topic, table

CLOSED = "closed"
PARTIAL = "partially closed"
OPEN = "open"


@dataclass(frozen=True)
class Gap:
    """One gap, its remedy, and what became of it."""

    gap: str
    blocks: str
    remedy: str
    cost: str
    provenance: str
    status: str
    outcome: str


def _corpus_present(corpus_id: str) -> bool:
    return any(spec.corpus_id == corpus_id and spec.path.exists() for spec in load_specs())


def gaps(blocks: int, tokens: int) -> list[Gap]:
    """The gap register, with statuses read off the artifacts where possible."""
    alignment_done = ALIGNMENT_PATH.exists()
    herbal = _corpus_present("herbal_latin")
    stars = _corpus_present("iau_star_names")
    return [
        Gap(
            gap="No token-level cross-transcription alignment",
            blocks="Per-token confidence weighting; every Phase 1 robustness claim was line-level",
            remedy="Needleman–Wunsch alignment of ZL against IT per line, substitution cost = "
            "glyph edit distance, written to `output/translation/token_alignment.parquet` "
            "with a reliability weight per token",
            cost="~3 s per run; one new module (`translations/alignment.py`)",
            provenance="Derived from built artifacts only (`eva_lines`, `mismatch_index`); "
            "no new source",
            status=CLOSED if alignment_done else OPEN,
            outcome=f"{tokens:,} ZL tokens aligned. GC/FG/CD are excluded: their alphabets "
            "differ, so a glyph edit distance against them measures the alphabet, not the "
            "scribes (Decision 13).",
        ),
        Gap(
            gap="No illustration↔label linkage",
            blocks="Anchor-based gloss seeding on labels; the 115 label lines cannot be tied "
            "to the plants, stars or nymphs beside them",
            remedy="Ingest a published concordance (plant-ID list) as a checksummed source. "
            "No hand annotation.",
            cost="Search cost only; nothing to implement without a source",
            provenance="Would need a `sources.yaml` entry with a checksum",
            status=OPEN,
            outcome="No machine-readable concordance found that could be pinned. The "
            "candidates are narrative HTML pages and one application database covering "
            "three folios. §5.1's pre-committed fallback applies: label-level anchor "
            "seeding is dropped and page-level `section` / `illustration_type` is used "
            "instead.",
        ),
        Gap(
            gap="Marginalia not in dataset",
            blocks="The best cribs (f116v, f66r, f17r) are unavailable to anchor scoring",
            remedy="Add a `marginalia.jsonl` source with transcription variants and explicit "
            "dispute flags",
            cost="Would be small to build; the blocker is the source, not the code",
            provenance="Would need a checksummed transcription source",
            status=OPEN,
            outcome="The readings exist only as prose discussion on HTML pages, and they are "
            "actively disputed — exactly the case where a hand transcription would smuggle "
            "one scholar's reading into the dataset as fact. Left open; the anchor "
            "catalogue stays empty and no crib enters Phase 4.",
        ),
        Gap(
            gap="No paragraph/block segmentation",
            blocks="Line-as-unit versus paragraph-as-unit modelling; LAAFU effects can only "
            "be tested at line level",
            remedy="Plan expected derivation from `position` plus layout heuristics",
            cost="~70 lines (`translations/paragraphs.py`); no heuristics needed",
            provenance="Derived from the raw IVTFF text already in `eva_lines`",
            status=CLOSED,
            outcome=f"{blocks} blocks. IVTFF marks paragraph starts (`<%>`) and ends (`<$>`) "
            "inline and the builders drop them on the way to `text_clean`; reading them "
            "back gives an annotated segmentation rather than a guessed one. 93% of blocks "
            "are opened and closed by a marker; the rest are closed by a page break.",
        ),
        Gap(
            gap="Currier/v101 alphabet not mapped",
            blocks="Robustness checks against GC and FG stay alphabet-limited",
            remedy="Build and test an explicit mapping table with lossiness documented",
            cost="Estimated 1–2 days: the mapping is many-to-many and needs its own "
            "validation against the images",
            provenance="Would need a decision-log entry per mapped glyph pair",
            status=OPEN,
            outcome="Deliberately deferred. Phase 3 scoped alignment to the EVA pair, so "
            "nothing in this phase depends on the mapping; a mapping asserted without "
            "validation would create the appearance of cross-alphabet robustness without "
            "the substance.",
        ),
        Gap(
            gap="No plant/star reference lexicons",
            blocks="Anchor scoring for herbal and astronomical labels",
            remedy="Add medieval herbal and star-name lexicons to `sources.yaml`",
            cost="Star names: one entry. Plant names: no comparable source located.",
            provenance="`sources.yaml` entries with checksums",
            status=PARTIAL if stars else OPEN,
            outcome="Star names are pinned (`iau_star_names`, 451 IAU-approved proper names, "
            "mostly Arabic- or Latin-derived and current in medieval lists). No plant-name "
            "lexicon was pinned; the nearest available route is filtering the already-pinned "
            "Whitaker's Words dictionary by its subject-area codes, which Phase 4 can do "
            "without new provenance. Neither lexicon is used in this phase: the anchor "
            "protocol only ranks finished candidates.",
        ),
        Gap(
            gap="Register-matched Latin scarce",
            blocks="Language-model quality for H1/H3/H4 — the herbal Latin model that scored "
            "best in Phase 2 was built on 11,638 words",
            remedy="Assemble a medieval-herbal Latin subcorpus; document its size limits",
            cost="One multi-part `sources.yaml` entry; registry gained `urls:` support",
            provenance="15 pinned files at one commit, checksum over the concatenation",
            status=CLOSED if herbal else OPEN,
            outcome="`herbal_latin`: Isidore, *Etymologiae* IV and XVII plus Columella, *De "
            "re rustica* — 128,497 words, 11× the Clusius corpus. Size limits, stated: "
            "neither text is a *medieval herbal*; Isidore (c. 625) is encyclopaedic and "
            "Columella (1st c.) is Roman agronomy. They are the closest register match "
            "retrievable as checksummable plain text.",
        ),
    ]


def run(blocks: int, tokens: int, extra: dict[str, Any] | None = None) -> Topic:
    """The gap-analysis report."""
    register = gaps(blocks, tokens)
    counts = {
        status: sum(1 for gap in register if gap.status == status)
        for status in (CLOSED, PARTIAL, OPEN)
    }

    sections = [
        "## Register\n\n"
        + table(
            ["gap", "blocks", "remedy", "cost", "provenance", "status"],
            [
                [gap.gap, gap.blocks, gap.remedy, gap.cost, gap.provenance, gap.status]
                for gap in register
            ],
        )
        + f"\n\n{counts[CLOSED]} closed, {counts[PARTIAL]} partially closed, "
        + f"{counts[OPEN]} open.",
        "## What happened to each\n\n"
        + "\n\n".join(f"**{gap.gap}** — *{gap.status}*. {gap.outcome}" for gap in register),
        "## What the open gaps cost the translation\n\n"
        "Two of the three open gaps are the same problem: the manuscript's best cribs — "
        "the labels beside the drawings and the marginalia — have no checksummable "
        "transcription or concordance. Without them the translator has no anchor it is "
        "allowed to use, so Phase 4 renders under a model with no external tie-point at "
        "all. That is a hard limit on how far a gloss can be validated, and it is why the "
        "anchor catalogue in `translations/decipher/anchors.py` is still empty.\n\n"
        "The third, the v101 mapping, costs less: it limits robustness checks to the EVA "
        "pair, and the token alignment shows the EVA pair agrees on the great majority of "
        "tokens anyway.",
    ]
    return Topic(
        topic="gap_analysis",
        title="Phase 3 — Gap analysis",
        sections=sections,
        data={
            "gaps": [gap.__dict__ for gap in register],
            "counts": counts,
            **(extra or {}),
        },
    )
