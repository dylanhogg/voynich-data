"""§5.2.6 — the token-level uncertainty model, reported.

The alignment and the weights are built in :mod:`translations.alignment`; this
module is the report on them. Three things need saying before a translator is
allowed to use a weight: how much of the corpus survives filtering, where the
distrust concentrates, and whether the weight is telling us anything the
line-level mismatch index did not already say.
"""

from __future__ import annotations

from collections import defaultdict

from translations.alignment import TokenRow
from translations.config import CONFIG
from translations.report import Topic, table
from translations.strata import StratumRow


def by_field(
    rows: list[TokenRow], strata: list[StratumRow], field: str
) -> dict[str, dict[str, float]]:
    """Mean agreement and reliability grouped by a stratum field."""
    lookup = {row.line_id: row for row in strata}
    groups: dict[str, list[TokenRow]] = defaultdict(list)
    for row in rows:
        stratum = lookup.get(row.line_id)
        if stratum is not None:
            groups[str(getattr(stratum, field))].append(row)
    return {
        key: {
            "tokens": float(len(items)),
            "exact_agreement": sum(1 for item in items if item.agreement == 1.0) / len(items),
            "mean_reliability": sum(item.reliability for item in items) / len(items),
            "dropped_at_floor": sum(
                1 for item in items if item.reliability < CONFIG.reliability_floor
            )
            / len(items),
        }
        for key, items in sorted(groups.items())
    }


def against_line_status(rows: list[TokenRow]) -> dict[str, dict[str, float]]:
    """Does the token weight say more than the line-level consensus flag?"""
    groups: dict[str, list[TokenRow]] = {"in consensus": [], "not in consensus": []}
    for row in rows:
        groups["in consensus" if row.in_consensus else "not in consensus"].append(row)
    return {
        key: {
            "tokens": float(len(items)),
            "exact_agreement": sum(1 for item in items if item.agreement == 1.0) / len(items),
            "mean_reliability": sum(item.reliability for item in items) / len(items),
            "reliable_tokens": sum(
                1 for item in items if item.reliability >= CONFIG.reliability_floor
            )
            / len(items),
        }
        for key, items in groups.items()
        if items
    }


def run(rows: list[TokenRow], strata: list[StratumRow], summary: dict[str, float]) -> Topic:
    """The alignment and reliability report."""
    currier = by_field(rows, strata, "currier_language")
    section = by_field(rows, strata, "section")
    line_type = by_field(rows, strata, "line_type")
    status = against_line_status(rows)

    keys = ["tokens", "exact_agreement", "mean_reliability", "dropped_at_floor"]
    sections = [
        "## Token-level agreement between ZL and IT\n\n"
        + table(
            ["quantity", "value"],
            [
                ["tokens aligned", summary["tokens"]],
                ["share with an IT counterpart", summary["aligned"]],
                ["share aligned to a gap", summary["gap"]],
                ["share with no IT line at all", summary["no_it_line"]],
                ["exact token agreement", summary["exact_token_agreement"]],
                ["mean agreement where aligned", summary["mean_agreement_where_aligned"]],
            ],
        )
        + "\n\nPhase 1 could only report that 29.3% of *lines* are identical between "
        + "the two EVA transcriptions. At token level the picture is far less bleak: "
        + f"{summary['exact_token_agreement']:.1%} of ZL tokens are read identically by "
        + "the second transcriber. A line-level mismatch is usually one word, not a "
        + "different reading of the line.",
        "## The reliability weight\n\n"
        + table(
            ["quantity", "value"],
            [
                ["mean weight", summary["mean_reliability"]],
                [
                    f"tokens below the floor ({CONFIG.reliability_floor})",
                    summary["tokens_below_half"],
                ],
                ["hapax share", summary["hapax_share"]],
                ["tokens containing a rare glyph", summary["rare_unit_share"]],
            ],
        )
        + "\n\nThe weight multiplies four independent doubts: cross-transcription "
        + "disagreement, line-level uncertainty markers, hapax status and rare "
        + "glyphs. It is a *declared* model, not a fitted one — the penalties are "
        + "constants in `translations/alignment.py` — so it should be read as a "
        + "documented policy for down-weighting, not as an estimate of anything.",
        "## Where the distrust concentrates\n\n"
        + "### Currier language\n\n"
        + table(
            ["stratum", *keys],
            [[name, *[row[key] for key in keys]] for name, row in currier.items()],
        )
        + "\n\n### Section\n\n"
        + table(
            ["stratum", *keys],
            [[name, *[row[key] for key in keys]] for name, row in section.items()],
        )
        + "\n\n### Line type\n\n"
        + table(
            ["stratum", *keys],
            [[name, *[row[key] for key in keys]] for name, row in line_type.items()],
        )
        + "\n\nIf agreement varied strongly with Currier language or section, every "
        + "per-stratum result in Phase 1 would inherit that variation as a confound.",
        "## Is the weight redundant with the consensus subset?\n\n"
        + table(
            ["line status", "tokens", "exact agreement", "mean reliability", "kept at floor"],
            [
                [
                    name,
                    row["tokens"],
                    row["exact_agreement"],
                    row["mean_reliability"],
                    row["reliable_tokens"],
                ]
                for name, row in status.items()
            ],
        )
        + "\n\nThe consensus subset is a line-level filter that discards whole lines. "
        + "The token weight keeps most of the tokens in those lines, which is the "
        + "point: it recovers data the line-level filter throws away.",
    ]
    return Topic(
        topic="reliability",
        title="Phase 3 — Token alignment and reliability",
        sections=sections,
        data={
            "summary": summary,
            "by_currier": currier,
            "by_section": section,
            "by_line_type": line_type,
            "by_line_status": status,
        },
    )
