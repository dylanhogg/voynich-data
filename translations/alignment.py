"""Token-level cross-transcription alignment and the token reliability model.

Phase 1 could only say that 29.3% of *lines* are identical between ZL and IT.
That is too coarse to weight anything: a line that differs in one glyph and a
line that differs in six both count as "mismatch". This module aligns the two
EVA transcriptions word by word (Needleman–Wunsch, substitution cost = glyph
edit distance) so every ZL token carries a number saying how much of it the
second transcriber agreed with.

Only the EVA pair is aligned (plan §5.1, Decision 13): CD is sparse, and FG and
GC use different alphabets, so a glyph edit distance across them would measure
the alphabet, not the scribes.

The reliability weight multiplies four independent doubts about a token —
transcription disagreement, line-level uncertainty markers, hapax status and
rare glyphs — into one number in (0, 1] for the translator to consume.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

from translations.analysis.syntax import edit_within
from translations.config import CONFIG, PATHS, Transcription
from translations.io import Line, Mismatch, load_lines, load_mismatches, transcription_text
from translations.strata import StratumRow, build_strata
from translations.tokenize import tokenize_line

GAP_PENALTY = 0.6  # cost of leaving a word unaligned, in units of word distance
RARE_UNIT_COUNT = 20  # a unit seen fewer times than this is "rare" (matches the cipher channel)

# Reliability penalties. Each is the factor a token keeps when the doubt applies.
PENALTY_NO_COUNTERPART = 0.5  # no IT line at all, or the word aligned to a gap
PENALTY_UNCERTAIN = 0.85
PENALTY_ILLEGIBLE = 0.7
PENALTY_ALTERNATIVES = 0.85
PENALTY_HAPAX = 0.9
PENALTY_RARE_UNIT = 0.8


@dataclass(frozen=True)
class TokenRow:
    """One ZL token with its cross-transcription evidence and reliability."""

    line_id: str
    page_id: str
    token_index: int
    zl_form: str
    it_form: str
    status: str
    agreement: float
    is_hapax: bool
    has_rare_unit: bool
    line_uncertain: bool
    line_illegible: bool
    line_alternatives: bool
    in_consensus: bool
    reliability: float


def word_distance(left: list[str], right: list[str]) -> int:
    """Glyph-unit edit distance between two words (uncapped)."""
    return edit_within(left, right, max(len(left), len(right)))


def similarity(left: list[str], right: list[str]) -> float:
    """1 − normalised edit distance; 1.0 for identical words."""
    longest = max(len(left), len(right))
    if longest == 0:
        return 1.0
    return 1.0 - word_distance(left, right) / longest


Pairing = list[tuple[int | None, int | None]]


def align_words(left: list[list[str]], right: list[list[str]]) -> Pairing:
    """Needleman–Wunsch over two word sequences; ``None`` marks a gap.

    Costs are in units of normalised word distance, so a substitution between
    near-identical words is nearly free and a gap costs ``GAP_PENALTY``.
    """
    rows, columns = len(left), len(right)
    cost = [[0.0] * (columns + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        cost[i][0] = i * GAP_PENALTY
    for j in range(1, columns + 1):
        cost[0][j] = j * GAP_PENALTY
    for i in range(1, rows + 1):
        for j in range(1, columns + 1):
            substitute = cost[i - 1][j - 1] + (1.0 - similarity(left[i - 1], right[j - 1]))
            cost[i][j] = min(substitute, cost[i - 1][j] + GAP_PENALTY, cost[i][j - 1] + GAP_PENALTY)

    pairs: Pairing = []
    i, j = rows, columns
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            substitute = cost[i - 1][j - 1] + (1.0 - similarity(left[i - 1], right[j - 1]))
            if cost[i][j] == substitute:
                pairs.append((i - 1, j - 1))
                i, j = i - 1, j - 1
                continue
        if i > 0 and cost[i][j] == cost[i - 1][j] + GAP_PENALTY:
            pairs.append((i - 1, None))
            i -= 1
            continue
        pairs.append((None, j - 1))
        j -= 1
    pairs.reverse()
    return pairs


def reliability(
    agreement: float,
    status: str,
    row: StratumRow,
    is_hapax: bool,
    has_rare_unit: bool,
) -> float:
    """Combine the four doubts about a token into one weight in (0, 1].

    Multiplicative because the doubts are about different things: a hapax that
    both transcribers read identically is still less trustworthy than a common
    word, and a well-attested word in an illegible line is still doubtful.
    """
    weight = agreement if status == "aligned" else PENALTY_NO_COUNTERPART
    if row.has_uncertain:
        weight *= PENALTY_UNCERTAIN
    if row.has_illegible:
        weight *= PENALTY_ILLEGIBLE
    if row.has_alternatives:
        weight *= PENALTY_ALTERNATIVES
    if is_hapax:
        weight *= PENALTY_HAPAX
    if has_rare_unit:
        weight *= PENALTY_RARE_UNIT
    return max(weight, 0.0)


def _tokenised(text: str) -> list[list[str]]:
    return tokenize_line(text, CONFIG.default_tokenizer, CONFIG.default_comma_policy)


def build_rows(
    lines: list[Line] | None = None,
    mismatches: dict[str, Mismatch] | None = None,
    strata: list[StratumRow] | None = None,
) -> list[TokenRow]:
    """Align every line and emit one row per ZL token."""
    lines = lines if lines is not None else load_lines()
    mismatches = mismatches if mismatches is not None else load_mismatches()
    strata = strata if strata is not None else build_strata()
    by_id = {row.line_id: row for row in strata}

    zl_lines = {line.line_id: _tokenised(line.text_clean) for line in lines}
    form_counts = Counter("".join(word) for words in zl_lines.values() for word in words)
    unit_counts = Counter(unit for words in zl_lines.values() for word in words for unit in word)

    rows: list[TokenRow] = []
    for line in lines:
        stratum = by_id[line.line_id]
        left = zl_lines[line.line_id]
        it_text = transcription_text(line, mismatches.get(line.line_id), Transcription.IT)
        right = _tokenised(it_text) if it_text else []
        pairs = align_words(left, right) if right else [(index, None) for index in range(len(left))]

        for source, target in pairs:
            if source is None:
                continue
            word = left[source]
            form = "".join(word)
            if target is None:
                status = "no_it_line" if not right else "gap"
                agreement = 0.0
                counterpart = ""
            else:
                status = "aligned"
                agreement = similarity(word, right[target])
                counterpart = "".join(right[target])
            is_hapax = form_counts[form] == 1
            has_rare_unit = any(unit_counts[unit] < RARE_UNIT_COUNT for unit in word)
            rows.append(
                TokenRow(
                    line_id=line.line_id,
                    page_id=line.page_id,
                    token_index=source,
                    zl_form=form,
                    it_form=counterpart,
                    status=status,
                    agreement=agreement,
                    is_hapax=is_hapax,
                    has_rare_unit=has_rare_unit,
                    line_uncertain=stratum.has_uncertain,
                    line_illegible=stratum.has_illegible,
                    line_alternatives=stratum.has_alternatives,
                    in_consensus=stratum.in_consensus,
                    reliability=reliability(agreement, status, stratum, is_hapax, has_rare_unit),
                )
            )
    return rows


ALIGNMENT_PATH = PATHS.output_dir / "token_alignment.parquet"


def write_alignment(rows: list[TokenRow]) -> tuple[int, str]:
    """Write the alignment table to parquet; returns row count and path."""
    import pandas as pd

    ALIGNMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([asdict(row) for row in rows])
    frame.to_parquet(ALIGNMENT_PATH, index=False)
    return len(frame), str(ALIGNMENT_PATH.relative_to(PATHS.repo_root))


def summarise(rows: list[TokenRow]) -> dict[str, float]:
    """Headline numbers for the report."""
    total = max(len(rows), 1)
    aligned = [row for row in rows if row.status == "aligned"]
    exact = sum(1 for row in aligned if row.agreement == 1.0)
    weights = [row.reliability for row in rows]
    return {
        "tokens": float(len(rows)),
        "aligned": len(aligned) / total,
        "gap": sum(1 for row in rows if row.status == "gap") / total,
        "no_it_line": sum(1 for row in rows if row.status == "no_it_line") / total,
        "exact_token_agreement": exact / total,
        "mean_agreement_where_aligned": (
            sum(row.agreement for row in aligned) / len(aligned) if aligned else 0.0
        ),
        "mean_reliability": sum(weights) / total,
        "tokens_below_half": sum(1 for weight in weights if weight < 0.5) / total,
        "hapax_share": sum(1 for row in rows if row.is_hapax) / total,
        "rare_unit_share": sum(1 for row in rows if row.has_rare_unit) / total,
    }
