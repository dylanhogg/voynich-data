# Phase 3 — Token alignment and reliability

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Token-level agreement between ZL and IT

| quantity | value |
| --- | --- |
| tokens aligned | 33,728 |
| share with an IT counterpart | 0.968 |
| share aligned to a gap | 0.031 |
| share with no IT line at all | 0.001 |
| exact token agreement | 0.862 |
| mean agreement where aligned | 0.965 |

Phase 1 could only report that 29.3% of *lines* are identical between the two EVA transcriptions. At token level the picture is far less bleak: 86.2% of ZL tokens are read identically by the second transcriber. A line-level mismatch is usually one word, not a different reading of the line.

## The reliability weight

| quantity | value |
| --- | --- |
| mean weight | 0.911 |
| tokens below the floor (0.5) | 0.023 |
| hapax share | 0.150 |
| tokens containing a rare glyph | 0.004 |

The weight multiplies four independent doubts: cross-transcription disagreement, line-level uncertainty markers, hapax status and rare glyphs. It is a *declared* model, not a fitted one — the penalties are constants in `translations/alignment.py` — so it should be read as a documented policy for down-weighting, not as an estimate of anything.

## Where the distrust concentrates

### Currier language

| stratum | tokens | exact_agreement | mean_reliability | dropped_at_floor |
| --- | --- | --- | --- | --- |
| A | 10,774 | 0.834 | 0.892 | 0.031 |
| B | 22,521 | 0.877 | 0.921 | 0.019 |
| None | 433.000 | 0.818 | 0.889 | 0.032 |

### Section

| stratum | tokens | exact_agreement | mean_reliability | dropped_at_floor |
| --- | --- | --- | --- | --- |
| astronomical | 198.000 | 0.843 | 0.887 | 0.051 |
| biological | 6,141 | 0.897 | 0.941 | 0.012 |
| cosmological | 296.000 | 0.797 | 0.899 | 0.027 |
| herbal | 10,840 | 0.850 | 0.898 | 0.028 |
| pharmaceutical | 2,304 | 0.784 | 0.869 | 0.051 |
| stars | 11,619 | 0.872 | 0.915 | 0.019 |
| text_only | 2,330 | 0.865 | 0.917 | 0.020 |

### Line type

| stratum | tokens | exact_agreement | mean_reliability | dropped_at_floor |
| --- | --- | --- | --- | --- |
| label | 124.000 | 0.766 | 0.860 | 0.121 |
| paragraph | 33,604 | 0.863 | 0.911 | 0.023 |

If agreement varied strongly with Currier language or section, every per-stratum result in Phase 1 would inherit that variation as a confound.

## Is the weight redundant with the consensus subset?

| line status | tokens | exact agreement | mean reliability | kept at floor |
| --- | --- | --- | --- | --- |
| in consensus | 28,359 | 0.891 | 0.927 | 0.987 |
| not in consensus | 5,369 | 0.708 | 0.828 | 0.924 |

The consensus subset is a line-level filter that discards whole lines. The token weight keeps most of the tokens in those lines, which is the point: it recovers data the line-level filter throws away.
