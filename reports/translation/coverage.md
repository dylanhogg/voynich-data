# Phase 4 — Coverage and confidence

> **SPECULATIVE OUTPUT — unvalidated rendering under a hypothesis that FAILED VALIDATION: the identical pipeline renders pseudo-Voynich, which encodes nothing, at least as well as it renders the manuscript (plan §7.4). This is model output, not a reading of the manuscript.**

## Bottom line

Every line of the manuscript now has an English rendering, and none of it is a reading of the manuscript. The hypothesis it is rendered under, H1, lost to a Markov model of the manuscript's own statistics (gain -5.771 bits/token, p = 0.308), and the control below renders text that encodes nothing at 123% of the rate it renders the manuscript. The gated view covers 61.1% of tokens; the confidence attached to them is conditional on a hypothesis the evidence does not support.

## Pseudo-Voynich control (read this first)

| corpus | tokens | gated coverage | mean confidence | high band | none band |
| --- | --- | --- | --- | --- | --- |
| real | 33,728 | 0.611 | 0.494 | 0.349 | 0.251 |
| grille | 33,728 | 0.751 | 0.524 | 0.249 | 0.186 |
| selfcite | 33,728 | 0.045 | 0.045 | 0.018 | 0.919 |

Both controls are matched to the manuscript in token count and built from its own
statistics: `grille` is a Rugg-style table generator, `selfcite` a Timm-style
autocopier. Neither encodes anything. The identical pipeline, the identical key and
the identical lexicon were run over them.

**The `grille` control renders *more* than the manuscript does (75.1% of tokens against 61.1%). On the test the plan named decisive, this pipeline is a fluency generator and its Voynich output carries no evidential weight.**

## Every keyed hypothesis

| id | variant | gain/token | p | converged | key accuracy (synthetic) | gated coverage | mean confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | clusius_rariorum-o3\|plain | -5.771 | 0.308 | yes | 1.000 | 0.611 | 0.494 |
| H2 | austen_pride_prejudice-o3\|fixed-width-3 | -0.105 | 0.308 | no | 1.000 | 0.096 | 0.105 |
| H3 | vulgate_clementine-abjad-o3\|plain | -3.677 | 0.308 | no | 1.000 | 0.446 | 0.375 |
| H4 | clusius_rariorum-abbrev-o3\|plain | -5.676 | 0.308 | no | 1.000 | 0.554 | 0.452 |
| H7 | austen_pride_prejudice-o1\|plain | -7.730 | 0.308 | yes | 0.491 | 0.000 | 0.025 |

Five hypotheses committed to a key and are rendered in full. The other four (H6a, H6b, H8, H9) are generative: they claim the text was produced by a process, not enciphered from a plaintext, so there is nothing to decode and nothing to gloss.

## Confidence bands

| band | share of tokens | rendering |
| --- | --- | --- |
| high (>= 0.7) | 0.349 | `word` |
| medium (0.4-0.7) | 0.262 | `*word*` |
| low (0.15-0.4) | 0.138 | `?word?` |
| none (< 0.15) | 0.251 | `⟨surface⟩(≈guess)` |

## Held-out pages, scored once

| split | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| train | 3,374 | 27,937 | 0.613 | 0.496 |
| holdout | 698 | 5,791 | 0.600 | 0.484 |

The key was searched on the training pages only. A pipeline that had learned something about the manuscript would render the held-out pages worse than the training pages; a pipeline matching a dictionary against short strings will not distinguish them.

## Gated coverage by stratum

### section

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| astronomical | 31 | 198 | 0.556 | 0.460 |
| biological | 722 | 6,141 | 0.686 | 0.564 |
| cosmological | 48 | 296 | 0.557 | 0.445 |
| herbal | 1,612 | 10,840 | 0.552 | 0.447 |
| pharmaceutical | 223 | 2,304 | 0.530 | 0.431 |
| stars | 1,159 | 11,619 | 0.641 | 0.513 |
| text_only | 277 | 2,330 | 0.630 | 0.500 |

### currier_language

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| A | 1,562 | 10,774 | 0.531 | 0.433 |
| B | 2,437 | 22,521 | 0.650 | 0.523 |
| None | 73 | 433 | 0.550 | 0.445 |

### line_type

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| label | 115 | 124 | 0.210 | 0.193 |
| paragraph | 3,957 | 33,604 | 0.612 | 0.495 |

### hand

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| 1 | 1,488 | 10,029 | 0.526 | 0.430 |
| 2 | 1,156 | 10,262 | 0.658 | 0.533 |
| 3 | 1,180 | 11,712 | 0.644 | 0.515 |
| 4 | 62 | 389 | 0.553 | 0.451 |
| 5 | 141 | 875 | 0.622 | 0.494 |
| @ | 45 | 461 | 0.610 | 0.502 |

## Where the glosses come from

| rung of the fallback chain | share of types |
| --- | --- |
| lexicon | 0.181 |
| nearest | 0.315 |
| none | 0.201 |
| stripped | 0.304 |

The distributional gloss the plan lists as fallback (b) is deliberately not implemented: it would assign real English words on the basis of frequency profile alone. See `docs/decisions.md`.

## The random-key null

Every token is scored again under 20 keys that permute the real key's letter assignments, which destroys the key's information while keeping its letter inventory. The mean per-token p-value is 0.469; 9.7% of tokens are glossed better by the real key than by any of the 20. That share, not the lexicon hit rate, is what the confidence column is built on: a two-letter string hits a 48,000-stem Latin dictionary whatever the key says.

## Validation gate (plan §6.6)

| requirement | status |
| --- | --- |
| Held-out folios scored once, results reported whatever they are | yes |
| Confidence calibration curves produced and included | `calibration.md` |
| Pseudo-Voynich control run and included | yes, above |
| Banner present in every artifact and every report | yes |
| Determinism test green | `tests/translations/test_phase4.py` |
| Framing under plan §7.4 | **failed validation** — artifacts re-bannered |

Every artifact written by this run carries:

> SPECULATIVE OUTPUT — unvalidated rendering under a hypothesis that FAILED VALIDATION: the identical pipeline renders pseudo-Voynich, which encodes nothing, at least as well as it renders the manuscript (plan §7.4). This is model output, not a reading of the manuscript.
