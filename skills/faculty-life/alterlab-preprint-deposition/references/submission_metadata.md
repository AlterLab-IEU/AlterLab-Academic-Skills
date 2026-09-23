# Submission Metadata Checklist

The fields each server asks for at deposit time. Assemble these *before*
starting the web submission so the upload is one pass. To **reuse an existing
record's** metadata (e.g. copy categories from a related arXiv paper), defer to
`alterlab-arxiv` / `alterlab-biorxiv` for the lookup — this skill prepares the
*new* submission, it does not search.

## Contents

- [Universal fields](#universal-fields-all-servers)
- [arXiv specifics](#arxiv-specifics)
- [bioRxiv / medRxiv specifics](#biorxiv--medrxiv-specifics)
- [ChemRxiv / Research Square / SSRN / OSF specifics](#chemrxiv--research-square--ssrn--osf-specifics)
- [Pre-submission file checklist](#pre-submission-file-checklist)

## Universal fields (all servers)

- **Title** — final, matches the manuscript.
- **Authors** — full names, order, **ORCID iDs**, affiliations, the
  corresponding author and contact email.
- **Abstract** — plain text; check the server's length/format limits.
- **License** — chosen per `licensing.md`.
- **Declarations** — competing interests, funding/grant numbers, data & code
  availability statement.
- **Manuscript file** — typically **PDF**; for arXiv, (La)TeX source is expected
  when the paper was written in TeX.

## arXiv specifics

- **Primary category** — one required (e.g. `cs.CL`, `q-bio.GN`, `stat.ML`,
  `eess.IV`). Drives moderation routing and discovery.
- **Cross-list categories** — optional secondary categories for reach.
- **Endorsement** — since 21 Jan 2026, automatic endorsement for a category
  needs an institutional email **and** a claimed paper in that endorsement
  domain; otherwise request a personal endorsement from an established author
  in the domain. Connect the institutional email and claim co-authored papers
  before the first submission.
- **Comments field** — page/figure counts, "submitted to <venue>", or version
  notes (do not put the license here).
- **MSC / ACM class** — optional subject codes for math/CS.
- Source vs PDF: submit the TeX/LaTeX source when the paper was written in TeX
  — arXiv builds the PDF (and its HTML rendering) from it, and a PDF generated
  from TeX is typically rejected. PDF-only submission is for papers not written
  in TeX (one PDF, fonts embedded, machine-readable).
- **Content-type checks** — arXiv CS takes review/survey and position papers only
  with documentation of completed peer review (since 31 Oct 2025).
- **Language** — a paper in another language must include a full English
  version (English first); an English abstract alone is not enough.

## bioRxiv / medRxiv specifics

- **Subject collection / category** — one required from the server's controlled
  list (e.g. Genomics, Neuroscience for bioRxiv; Infectious Diseases, Public &
  Global Health for medRxiv).
- **Manuscript type** — bioRxiv: New Results / Confirmatory Results /
  Contradictory Results. medRxiv takes research articles, systematic reviews
  with meta-analysis, data articles, and clinical research design protocols —
  not case reports or narrative reviews.
- **Funding** — funder name (ROR-identified) and award number are captured in
  dedicated fields and exposed through the content API; enter every grant.
- **Timing** — neither server posts a manuscript that a journal has already
  accepted; post before or at journal submission.
- **medRxiv only:** trial registration number (if applicable), ethics/IRB
  statement, participant-consent statement, and confirmation there are no
  identifiable patient data.
- **Author-supplied DOI link** — leave for post-publication linking (the server
  also auto-detects many links).

## ChemRxiv / Research Square / SSRN / OSF specifics

- **ChemRxiv:** license (CC BY / BY-NC / BY-NC-ND 4.0) plus the universal
  fields above; each posted version gets its own DOI.
- **Research Square (In Review):** an opt-in selected while submitting to a
  participating Springer Nature / BMC journal; the preprint is posted under
  CC BY 4.0 and stays public whatever the journal decides.
- **SSRN:** classification codes (e.g. JEL for economics), keywords, abstract;
  network/series selection.
- **OSF Preprints:** choose the **provider** (general OSF or a community server),
  subjects/tags, and a license from the provider's allowed set.

## Pre-submission file checklist

- [ ] Final PDF, or the LaTeX source for a TeX-written arXiv paper.
- [ ] Figures/tables embedded or in the server's required form.
- [ ] Supplementary files within size limits.
- [ ] ORCID confirmed for the submitting author.
- [ ] Funding/grant IDs and data/code availability statement written.
- [ ] License decided and reconciled with funder + journal (`licensing.md`,
      `journal_policy.md`).
- [ ] No embedded identifiable personal data (especially medRxiv).
