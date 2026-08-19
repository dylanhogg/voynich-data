# Phase 1 — Transcription robustness

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Metrics per transcription (`T0-char`; CD/FG/GC are not EVA)

| source | tokens | h2 | mean_word_length | ttr | hapax_rate | near_repeat_within_2 |
| --- | --- | --- | --- | --- | --- | --- |
| zl (all lines) | 33,728 | 2.126 | 5.070 | 0.215 | 0.701 | 0.115 |
| it (33,176 tokens) | 33,176 | 2.132 | 5.171 | 0.223 | 0.700 | 0.113 |
| cd (15,874 tokens) | 15,874 | 2.358 | 4.162 | 0.258 | 0.698 | 0.193 |
| fg (33,045 tokens) | 33,045 | 2.301 | 4.279 | 0.199 | 0.664 | 0.167 |
| gc (36,100 tokens) | 36,100 | 2.567 | 3.890 | 0.232 | 0.704 | 0.189 |

## Paired differences against ZL on the same lines

| source | lines | h2 | mean_word_length | ttr | hapax_rate | near_repeat_within_2 |
| --- | --- | --- | --- | --- | --- | --- |
| it | 4,061 | 0.007 | 0.101 | 0.008 | -0.001 | -0.002 |
| cd | 2,154 | 0.242 | -0.823 | 0.008 | -0.011 | 0.066 |
| fg | 3,971 | 0.178 | -0.796 | -0.017 | -0.037 | 0.052 |
| gc | 4,070 | 0.441 | -1.180 | 0.017 | 0.003 | 0.074 |

## Stability ranking

| metric | ZL value | bootstrap CI width | abs Δ (ZL vs IT) | Δ / CI (EVA) | abs Δ (all sources) | Δ / CI (all) | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hapax_rate | 0.701 | 0.028 | 0.001 | 0.039 | 0.037 | 1.302 | robust within EVA |
| near_repeat_within_2 | 0.115 | 0.007 | 0.002 | 0.322 | 0.074 | 11.143 | robust within EVA |
| h2 | 2.126 | 0.019 | 0.007 | 0.351 | 0.441 | 22.903 | robust within EVA |
| ttr | 0.215 | 0.005 | 0.008 | 1.532 | 0.017 | 3.503 | transcription-limited |
| mean_word_length | 5.070 | 0.044 | 0.101 | 2.304 | 1.180 | 26.796 | transcription-limited |

The verdict column uses the EVA pair (ZL vs IT) only. CD, FG and GC use different alphabets, so their deltas measure alphabet plus transcription and are reported as context, not as instability of the metric. A metric marked *transcription-limited* varies more between two EVA transcriptions than its own sampling error, and cannot by itself support a decipherment claim.
