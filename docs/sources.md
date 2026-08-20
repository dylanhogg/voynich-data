# VCAT Data Sources

This document provides comprehensive information about all data sources used in the Voynich Computational Analysis Toolkit (VCAT).

## Source Summary

| Source Name | Version | Format | Status | Primary Use |
|-------------|---------|--------|--------|-------------|
| ZL Transcription | 3b | IVTFF 2.0 | ✓ Primary | EVA lines dataset |
| IT Interlinear | 2a | IVTFF 2.0 | ✓ Verified | Comparison/mismatch |
| Stolfi Interlinear | 1.6e6 | IVTFF 1.7 | ✓ Verified | Historical reference |
| voynich.nu | Current | HTML/Text | ✓ Verified | Metadata |
| Beinecke Library | Current | IIIF | ✓ Verified | Images |

## Primary Source: Zandbergen-Landini (ZL) Transcription

### Attribution

**Full Name**: Zandbergen-Landini Transcription  
**Maintainer**: René Zandbergen  
**Version Used**: 3b (May 2025)  
**URL**: `http://www.voynich.nu/data/ZL3b-n.txt`

### Why ZL is the Primary Source

The ZL transcription was selected as VCAT's primary source because:

1. **Most Accurate**: Represents the most careful, complete transcription available
2. **Modern Format**: Uses IVTFF 2.0 with rich metadata
3. **Actively Maintained**: René Zandbergen continues to update and correct
4. **Rich Metadata**: Includes page variables (quire, hand, language, etc.)
5. **Community Standard**: Widely used in computational Voynich research

### Content

The ZL transcription contains:
- **226 pages** (all folios including foldout panels)
- **4,072 text loci** (lines, labels, circular text)
- **Complete EVA text** including rare characters
- **Page-level metadata** for each page

### Format Details

```
#=IVTFF Eva- 2.0 M 5
<f1r>      <! $Q=A $P=A $L=A $H=1 $I=H>
<f1r.1,@P0>       fachys.ykal.ar.ataiin.shol.shory
<f1r.2,+P0>       cthres.y.kor.sholdy
...
```

### Known Limitations

- **Subjective readings**: Some glyph identifications are judgment calls
- **EVA limitations**: EVA alphabet cannot capture all visual distinctions
- **Incomplete weirdos**: Rare/unusual glyphs may be normalized

### Local Copy

**File**: `data_sources/raw_sources/ZL3b-n.txt`  
**SHA256**: `bf5b6d4a...` (see checksums.txt)  
**Retrieved**: 2026-01-17

---

## Comparison Source: IT Interlinear

### Attribution

**Full Name**: Interlinear Transcription File  
**Source**: voynich.nu  
**Version Used**: 2a  
**URL**: `http://www.voynich.nu/data/IT2a-n.txt`

### Purpose

The IT file is used for transcription comparison and mismatch analysis. It contains multiple historical transcriptions aligned line-by-line.

### Content

Contains transcriptions from multiple historical transcribers:

| Code | Transcriber | Period | Notes |
|------|-------------|--------|-------|
| H | Takeshi Takahashi | 1990s | First complete transcription |
| C | Prescott Currier | 1970s | Cryptographic analysis focus |
| F | First Study Group | 1940s | Friedman team (punchcard era) |
| L | Don Latham | 1990s | Partial |
| R | Mike Roe | 1990s | Partial |

### Usage in VCAT

- Cross-validate ZL transcription
- Build transcription mismatch index
- Historical comparison analysis

### Local Copy

**File**: `data_sources/raw_sources/IT2a-n.txt`  
**SHA256**: `7f27a8b0...` (see checksums.txt)  
**Retrieved**: 2026-01-17

---

## Historical Reference: Stolfi Interlinear

### Attribution

**Full Name**: Stolfi's UNICAMP Interlinear File  
**Maintainer**: Jorge Stolfi (University of Campinas, Brazil)  
**URL**: `https://www.ic.unicamp.br/~stolfi/voynich/98-12-28/`

### Historical Significance

Jorge Stolfi's collection represents foundational computational Voynich work:

- Early systematic transcription alignment
- Pioneering statistical analyses
- First comprehensive word concordance
- Still-valuable analytical resources

### Content

| Resource | Description |
|----------|-------------|
| `text16e6.evt` | Interlinear file v1.6e6 |
| Concordance | Complete word concordance |
| Statistics | Word length distributions |

### Limitations

- **Older Format**: Uses IVTFF 1.7 conventions
- **Historical Data**: May not reflect latest corrections
- **Limited Metadata**: Less rich than modern files

### Local Copy

**File**: `data_sources/raw_sources/text16e6.evt`  
**SHA256**: `309e717d...` (see checksums.txt)  
**Retrieved**: 2026-01-17

---

## Metadata Sources

### voynich.nu

**URL**: `https://www.voynich.nu/`  
**Maintainer**: René Zandbergen

The most comprehensive Voynich research site, providing:

| Resource | URL | Content |
|----------|-----|---------|
| Transcriptions | `/transcr.html` | File downloads and documentation |
| Folios | `/folios.html` | Per-folio information |
| Quires | `/quire.html` | Quire structure |
| EVA | `/extra/eva.html` | EVA alphabet specification |

### Beinecke Library

**URL**: `https://brbl-dl.library.yale.edu/vufind/Record/3519597`  
**IIIF Manifest**: `https://collections.library.yale.edu/manifests/oid/2002046`

Official repository of the Voynich Manuscript (Beinecke MS 408):

- High-resolution scans of all folios
- Official catalog information
- IIIF API for programmatic access

---

## File Verification

### How to Verify Sources

Run the verification script:

```bash
cd voynich-data
python data_sources/verify_sources.py
```

This script:
1. Checks URL accessibility
2. Downloads content samples
3. Computes SHA256 hashes
4. Verifies file structure
5. Reports any issues

### Verification Output

Results are saved to:
- `reports/source_verification.json` — Machine-readable results
- `reports/source_verification_report.md` — Human-readable report

### Checksums

Expected file hashes are stored in `data_sources/raw_sources/checksums.txt`:

```
bf5b6d4a...  ZL3b-n.txt
7f27a8b0...  IT2a-n.txt  
309e717d...  text16e6.evt
```

To verify:
```bash
cd data_sources/raw_sources
sha256sum -c checksums.txt
```

---

## Licensing Considerations

### Transcription Data

The transcription files are scholarly works created by individual researchers:

| Source | Creator | Licensing Notes |
|--------|---------|-----------------|
| ZL | Zandbergen | Academic use generally permitted |
| IT | Multiple | Community resource |
| Stolfi | Stolfi | Academic use permitted |

**Policy**: VCAT publishes derived datasets (statistics, indexes) and builder scripts. If licensing concerns arise, we provide scripts and checksums rather than raw redistributions.

### Manuscript Images

The Voynich Manuscript is held by Yale's Beinecke Library:

- Images are in the public domain (15th-century work)
- Beinecke provides open access via IIIF
- Attribution to Beinecke is appropriate

### VCAT Outputs

VCAT-produced datasets and code are released under MIT License:
- Free for commercial and non-commercial use
- Attribution appreciated but not required
- No warranty provided

---

## Reference Corpora (non-Voynich baselines)

Plan 001 Phase 0 adds a second class of source: non-Voynich text used for null
models, matched-sample baselines and (later) language models. These are
declared under `reference_corpora:` in `data_sources/sources.yaml`, fetched by
`scripts/fetch_corpora.py` into `data_sources/cache/corpora/`, and verified by
SHA256 before any loader touches them.

They are **fetched, not vendored**: the cache directory is git-ignored and the
checksum is the reproducibility contract. A checksum mismatch is fatal, not a
warning — upstream drift must be noticed, then re-pinned deliberately.

| ID | Text | Lang | Group | Role |
|----|------|------|-------|------|
| `vulgate_clementine` | Clementine Vulgate | la | latin | Primary plaintext hypothesis |
| `clusius_rariorum` | Clusius, *De Rariorum Animalium atque Stirpium Historia* (1605) | la | latin | Herbal / natural-history register |
| `caesar_bello_gallico` | Caesar, *De Bello Gallico* I–IV | la | latin | Classical Latin prose |
| `dante_commedia` | Dante, *La Divina Commedia* | it | romance | Old Italian |
| `chaucer_canterbury` | Chaucer, *The Canterbury Tales* | enm | germanic | Middle English |
| `german_bible_elberfelder` | Elberfelder Bibel 1905 | de | germanic | Germanic, verse-parallel |
| `finnish_bible` | Pyhä Raamattu 1933/38 | fi | contrast | Agglutinative contrast, verse-parallel |
| `douay_rheims` | Douay-Rheims Bible | en | english | English rendering of the Vulgate, verse-parallel |
| `austen_pride_prejudice` | Austen, *Pride and Prejudice* | en | english | Modern English prose |
| `whitakers_words` | Whitaker's Words `DICTLINE.GEN` | la | lexicon | Latin→English gloss inventory (Phase 4) |
| `herbal_latin` | Isidore, *Etymologiae* IV + XVII; Columella, *De re rustica* | la | latin | Register-matched plant/medicine Latin (Phase 3) |
| `iau_star_names` | IAU Catalog of Star Names | mul | lexicon | Star-name lexicon for astronomical labels (Phase 4) |

Four of these (Vulgate, Douay-Rheims, Elberfelder, Finnish) are the same text
in four languages, which holds genre constant when comparing distributions
across languages.

`herbal_latin` is the only multi-part entry: it declares `urls:` rather than
`url:`, and the 15 files are concatenated in the listed order, joined by a
newline, with the checksum taken over the concatenation. It exists because the
herbal-register corpus Phase 2 leaned on (`clusius_rariorum`) is 11,638 words —
too thin for an order-3 character model. It is 128,497 words, and it is *not* a
medieval herbal: Isidore (c. 625) is encyclopaedic and Columella (1st c.) is
Roman agronomy. Both were retrievable as checksummable plain text; the medieval
herbals were not.

Corpora are read through `translations/corpora/`, which strips the delivery
format (Project Gutenberg header/footer, `[chapter:verse]` references) and then
normalises: casefold, fold diacritics and ligatures (`æ`→`ae`), keep letters and
spaces only.

### Known gaps

No checksummed public-domain source was found for Old Occitan, Middle High
German, a medieval Latin herbal proper (*Circa Instans*, *Herbarium Apuleii*),
or Semitic text in Latin transliteration. Those hypotheses are therefore tested
against the nearest available proxy, and the gap is stated wherever it matters.

Phase 3 searched for three more and found none that could be pinned: a
machine-readable illustration↔label (plant-ID) concordance, a marginalia
transcription with dispute flags, and a plant-name lexicon. The candidates are
narrative HTML pages or application databases covering a handful of folios.
See `reports/phase3/gap_analysis.md` for what each gap costs and the fallback
each one triggers.

---

## Fetching Sources

### Automatic Fetch

```bash
python scripts/fetch_sources.py    # transcriptions
python scripts/fetch_corpora.py    # reference corpora (make corpora)
```

### Manual Download

1. Download files from URLs listed above
2. Place in `data_sources/raw_sources/`
3. Verify hashes match expected values
4. Run verification script

### If Sources Change

If upstream sources are modified:

1. Update `sources.yaml` with new versions
2. Update expected hashes in `checksums.txt`
3. Re-run builders
4. Document changes in CHANGELOG

---

## Troubleshooting

### Source Not Accessible

**Symptom**: HTTP 404 or timeout

**Solutions**:
1. Check alternative URLs in `sources.yaml`
2. Use cached local copies if available
3. Check voynich.nu for relocated files

### Hash Mismatch

**Symptom**: Verification fails with different hash

**Solutions**:
1. Confirm correct file was downloaded
2. Check if source was updated (new version)
3. Update expected hash after verification

### Format Changed

**Symptom**: Parser fails on previously-working file

**Solutions**:
1. Review changes in source format
2. Update parser to handle new format
3. Document format version in output metadata

---

## Related Documentation

- [data_model.md](data_model.md) — Data model specification
- [eva_alphabet.md](eva_alphabet.md) — EVA character reference
- [decisions.md](decisions.md) — Project decisions

---

*Last updated: 2026-01-17 | VCAT v0.1.0*
