---
name: alterlab-citation-mgmt
description: "Manages citations for academic research — searches Google Scholar and PubMed for papers, extracts complete metadata from DOIs, PMIDs, and arXiv IDs (CrossRef, doi.org content negotiation, NCBI E-utilities, arXiv API), validates BibTeX entries for required fields, format, and duplicates, and generates or cleans properly formatted BibTeX. Use when finding papers, converting DOIs to BibTeX, cleaning or deduplicating a .bib file, checking reference metadata in scientific writing, or building a bibliography. To prove that cited references actually exist or to flag fabricated or retracted citations prefer alterlab-citation-verifier; for Zotero library operations use alterlab-pyzotero. Part of the AlterLab Academic Skills suite."
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: No API key required (an optional NCBI_API_KEY raises the PubMed E-utilities limit from 3 to 10 requests/s). Needs network access to CrossRef, doi.org, NCBI E-utilities, arXiv, and Google Scholar; the helper scripts need requests, plus scholarly for Google Scholar search
metadata:
    skill-author: AlterLab
    version: "1.0.1"
    last_updated: "2026-09-23"
---

# Citation Management

## Overview

Manage citations systematically across the research and writing process: search
academic databases (Google Scholar, PubMed), extract accurate metadata from multiple
sources (CrossRef, PubMed, arXiv, DataCite), validate citation information, and
generate properly formatted BibTeX. Critical for citation accuracy, avoiding reference
errors, and reproducible research. Integrates with `alterlab-literature-review`.

## When to Use This Skill

Use when:
- Searching for specific papers on Google Scholar or PubMed
- Converting DOIs, PMIDs, or arXiv IDs to properly formatted BibTeX
- Extracting complete metadata (authors, title, journal, year, etc.)
- Validating existing citations for accuracy or checking for duplicates
- Cleaning, sorting, and formatting BibTeX files
- Finding highly cited / seminal papers in a field
- Building a bibliography for a manuscript or thesis

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Proving each reference actually exists, catching hallucinated/fabricated citations, or retraction checks | `alterlab-citation-verifier` |
| Reading or editing a Zotero library (items, collections, tags, attachments) | `alterlab-pyzotero` |
| A full systematic review — multi-database search, PRISMA screening, thematic synthesis | `alterlab-literature-review` |
| Mapping a citation/co-citation network around seed papers | `alterlab-citation-graph` |
| Writing manuscript prose around the references | `alterlab-scientific-writing` |

## Core Workflow

Citation management is a five-phase pipeline. Each phase maps to a script (full CLI
in `references/script_cli_reference.md`) and a deep-dive reference.

### Phase 1 — Paper discovery
Search Google Scholar (broad, cross-discipline) and PubMed (biomedical, MeSH-indexed).

```bash
python scripts/search_google_scholar.py "CRISPR gene editing" --limit 50 --output results.json
python scripts/search_pubmed.py "Alzheimer's disease treatment" --limit 100 --output alz.json
```
Operators, MeSH/field tags, complex queries, and high-impact-paper heuristics:
`references/search_strategy_reference.md`, `references/google_scholar_search.md`,
`references/pubmed_search.md`.

### Phase 2 — Metadata extraction
Convert any identifier (DOI, PMID, arXiv ID, URL) to complete metadata. CrossRef is the
primary DOI source (`extract_metadata.py`); PubMed E-utilities and the arXiv API cover PMIDs
and arXiv IDs. `doi_to_bibtex.py` uses doi.org content negotiation, which also resolves
DataCite DOIs (datasets, software).

```bash
python scripts/doi_to_bibtex.py 10.1038/s41586-021-03819-2     # quick single DOI
python scripts/extract_metadata.py --pmid 34265844             # any identifier type
python scripts/extract_metadata.py --input identifiers.txt --output citations.bib  # batch
```
Sources and extracted fields: `references/metadata_extraction.md` and the Metadata
Sources section of `references/search_strategy_reference.md`.

### Phase 3 — BibTeX formatting
Generate clean, standardized entries. Common types: `@article`, `@book`,
`@inproceedings`, `@incollection`, `@phdthesis`, `@misc`. Protect title capitalization
with `{}`, use `--` for page ranges, include a DOI for modern publications.

```bash
python scripts/format_bibtex.py references.bib --deduplicate --sort year --descending \
  --output clean_references.bib
```
Entry types, required fields, and formatting rules: `references/bibtex_formatting.md`.

### Phase 4 — Validation
Verify required fields are present, data is consistent, and there are no duplicates.
DOI resolution is network-bound and OFF by default — add `--check-dois` to actually
hit doi.org/CrossRef (slow). `validate_citations.py` reports only; it does not rewrite
the file. To apply fixes (page dashes, author separators, dedup), run `format_bibtex.py`.

```bash
python scripts/validate_citations.py references.bib --check-dois \
  --report validation.json --verbose
```
Validation criteria and report format: `references/citation_validation.md` and the
Validation Checks summary in `references/search_strategy_reference.md`.

### Phase 5 — Integration with writing
Export validated BibTeX into a LaTeX manuscript (`\bibliography{final_references}`).
Pairs with `alterlab-literature-review` (search/synthesis), `alterlab-scientific-writing`
(manuscript references), and `alterlab-venue-templates` (style-specific formatting). Before
submission, run `alterlab-citation-verifier` on the final `.bib` to confirm every entry exists —
this skill checks fields and formatting, not existence.

End-to-end worked examples (build a bibliography, convert a DOI list, clean a messy
`.bib`, find seminal papers): `references/example_workflows.md`.

## Best Practices

**Search**: start broad then narrow; use multiple sources; leverage "Cited by" for
seminal papers; document queries and dates.

**Metadata**: prefer DOIs (most reliable, best CrossRef metadata); verify author names,
venue, and year; handle preprints (use the published version when one exists); keep
author-name and journal-abbreviation formatting consistent.

**BibTeX quality**: meaningful citation keys (`FirstAuthor2024keyword`); protect title
capitalization with `{}`; remove redundant fields; validate syntax regularly; organize
per project and merge carefully to avoid duplicates.

**Validation**: validate early and often; fix broken DOIs and missing fields promptly;
manually review critical citations.

## Common Pitfalls

1. **Single-source bias** → search multiple databases.
2. **Accepting metadata blindly** → spot-check against originals.
3. **Ignoring DOI errors** → validate before submission.
4. **Inconsistent formatting** → standardize with `format_bibtex.py`.
5. **Duplicate entries** → use duplicate detection.
6. **Missing required fields** → validate for completeness.
7. **Outdated preprints** → update to the published version.
8. **Special-character issues** → escape or use Unicode in BibTeX.
9. **No final validation** → always run validation as the last check.
10. **Manual BibTeX entry** → always extract from metadata sources.

## Index of Bundled Resources

### References (`references/`)
- `script_cli_reference.md` — full per-script features and CLI usage
- `example_workflows.md` — four end-to-end worked workflows
- `search_strategy_reference.md` — high-impact heuristics, Scholar operators, MeSH/field tags, metadata sources
- `google_scholar_search.md` — complete Google Scholar search guide
- `pubmed_search.md` — PubMed and E-utilities API documentation
- `metadata_extraction.md` — metadata sources and field requirements
- `citation_validation.md` — validation criteria and quality checks
- `bibtex_formatting.md` — BibTeX entry types and formatting rules

### Scripts (`scripts/`)
`search_google_scholar.py`, `search_pubmed.py`, `extract_metadata.py`,
`validate_citations.py`, `format_bibtex.py`, `doi_to_bibtex.py`.

### Assets (`assets/`)
`bibtex_template.bib` (example entries for all types), `citation_checklist.md` (QA checklist).

## External Resources

- Google Scholar: https://scholar.google.com/ · PubMed: https://pubmed.ncbi.nlm.nih.gov/
- CrossRef API: https://api.crossref.org/ · PubMed E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- arXiv API: https://arxiv.org/help/api/ · DataCite API: https://api.datacite.org/
- MeSH Browser: https://meshb.nlm.nih.gov/search · DOI Resolver: https://doi.org/

## Dependencies

```bash
# All network scripts (CrossRef, doi.org, E-utilities, arXiv)
uv pip install requests
# Optional: Google Scholar search (search_google_scholar.py). scholarly scrapes Scholar,
# which has no official API and rate-limits or CAPTCHAs automated traffic.
uv pip install scholarly
```
`format_bibtex.py` and `validate_citations.py` (without `--check-dois`) need only the
standard library. Set `NCBI_EMAIL` (and optionally `NCBI_API_KEY`) for PubMed.

## Summary

This skill provides search (Scholar + PubMed), automated metadata extraction (DOI/PMID/
arXiv/URL), citation validation (DOI verification + completeness), BibTeX formatting and
cleaning, and quality assurance — all reproducible through documented search and
extraction methods. Use it to maintain accurate, publication-ready bibliographies.
