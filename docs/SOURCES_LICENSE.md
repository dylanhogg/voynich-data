# Source Transcription Provenance and Licensing

This project builds datasets derived from five scholarly transcriptions of
the Voynich Manuscript (Beinecke MS 408, Yale University). This document
states, as plainly as possible, what we know about the rights status of each
source and what that means for users of the derived datasets.

## The short version

- The **manuscript itself** is in the public domain (15th century).
- The **transcriptions** are scholarly works created by individual
  researchers. None of them carries a formal license statement.
- All five are **publicly distributed for research** via
  [voynich.nu](https://www.voynich.nu/), maintained by René Zandbergen.
- The **VCAT processing code** is MIT-licensed.
- The **derived datasets** are published as research resources
  (`license: other`, `license_name: research-use` on Hugging Face):
  research and educational use is the intended purpose; cite the original
  transcribers; for commercial use, verify rights independently and contact
  the transcription authors.

We believe this is an honest description of the actual rights situation.
We deliberately do not claim a Creative Commons or other formal license over
the transcription text, because the underlying rights are not ours to grant.

## Per-source detail

| ID | Source | Authors | Alphabet | Distribution |
|----|--------|---------|----------|--------------|
| ZL | Zandbergen-Landini v3b | René Zandbergen, Gabriel Landini | EVA | voynich.nu, research use |
| IT | Takahashi | Takeshi Takahashi | EVA | voynich.nu mirror, research use |
| CD | Currier/D'Imperio | Prescott Currier, Mary D'Imperio | Currier | Historical (1970s, NSA-adjacent research), voynich.nu mirror |
| FG | Friedman Study Group | First Study Group / William Friedman | FSG | Historical (1940s-50s), voynich.nu mirror |
| GC | Glen Claston | Glen Claston (Tim Rayhel) | v101 | voynich.nu mirror, research use |

Exact source files, URLs, and SHA256 checksums are recorded in
[`data_sources/sources.yaml`](../data_sources/sources.yaml) and
`data_sources/checksums_all.txt`.

## What this project redistributes

- **Derived line records** (parsed, cleaned, validated text with metadata),
  not the original source files themselves.
- **Build scripts** that let anyone re-derive the datasets from the original
  sources.
- **Statistics and indexes** (e.g., the cross-transcription mismatch index).

## If you are a rights holder

If you are an author of one of these transcriptions and would like the
attribution changed, the terms clarified, or content removed, please
[open an issue](https://github.com/noah-chelednik/voynich-data/issues) —
it will be acted on promptly.
