# Preprint Server Selection

Routing a finished manuscript to the right preprint server. Pick by **field
fit** first, then by secondary factors (DOI need, moderation tolerance, journal
plans, funder mandate).

## Contents

- [Decision tree](#decision-tree)
- [Per-server profiles](#per-server-profiles)
- [Secondary factors](#secondary-factors)
- [Common edge cases](#common-edge-cases)

## Decision tree

0. **Has a journal already accepted it?** bioRxiv and medRxiv will not post it;
   arXiv may, subject to the journal's policy (see `journal_policy.md`).
1. **Is the work clinical / health-related (human subjects, trials, public
   health)?** → **medRxiv**. (medRxiv requires ethics, consent, and
   trial-registration declarations, and does not take case reports, narrative
   reviews, or systematic reviews without meta-analysis; do not post
   identifiable patient data.)
2. **Is it life sciences / biology (non-clinical)?** → **bioRxiv**.
3. **Is it chemistry (or chemistry-adjacent materials/chemical biology)?** →
   **ChemRxiv**.
4. **Is it physics, mathematics, computer science, statistics, electrical
   engineering & systems, economics, quantitative biology, or quantitative
   finance?** → **arXiv** (these map to arXiv's top-level archives:
   physics/math/cs/stat/eess/econ/q-bio/q-fin).
5. **Is it social science, law, business, or humanities?** → **SSRN** (or arXiv
   `econ` for economics that fits arXiv's scope).
6. **Submitting to a Springer Nature / BMC journal that offers "In Review"?** →
   **Research Square** posts the preprint as part of that submission.
7. **Cross-disciplinary, or a field with a dedicated community server (e.g.
   PsyArXiv, SocArXiv, EarthArXiv on OSF)?** → **OSF Preprints**.

When two servers both fit (e.g. computational biology → arXiv `q-bio` *or*
bioRxiv), prefer the one your **target community reads** and whose **DOI
behaviour** you need (see below). Posting the same manuscript to two preprint
servers is discouraged and can create duplicate-DOI confusion.

## Per-server profiles

### arXiv
- **Operator:** an independent nonprofit since 1 July 2026 (spun out of Cornell
  University); free to read and to submit.
- **Scope:** physics, math, CS, stat, eess, econ, q-bio, q-fin.
- **Identifier:** the **arXiv ID** is canonical (e.g. `2406.01234`), and every
  article is also assigned a DataCite DOI `10.48550/arXiv.<id>` automatically
  (it resolves to the latest version; new versions do not get new DOIs).
- **Versioning:** versions `v1, v2, …` are **permanent and immutable**. An
  announced paper **cannot be deleted**; a withdrawal creates a new version
  marked withdrawn (tombstone, no downloadable files). Revisions are submitted
  as **replacements**, not by editing in place.
- **Gatekeeping (2025–2026 changes):**
  - **Endorsement** (all categories, since 21 Jan 2026): automatic endorsement
    needs both an institutional email **and** a claimed paper in the same
    endorsement domain; otherwise ask an established arXiv author in that
    domain. An institutional email alone no longer suffices.
  - **CS review/survey and position papers** (since 31 Oct 2025) must already
    have passed peer review at a journal or conference, with documentation;
    without it they are likely to be rejected.
  - **Language:** non-English papers are accepted only with a full English
    version of the paper (English first), not just an English abstract.
  - **Format:** submit TeX/LaTeX source when the paper was written in TeX; a PDF
    generated from TeX is typically rejected.
- **Licenses:** see `licensing.md`.

### bioRxiv
- **Scope:** life sciences / biology. Operated since 2025 by **openRxiv**, an
  independent nonprofit (previously Cold Spring Harbor Laboratory).
- **Identifier:** assigns a Crossref **DOI on posting** — prefix `10.64898` for
  preprints posted from 1 Dec 2025, `10.1101` for earlier ones (both resolve;
  nothing was reissued). Revised versions keep the DOI.
- **Article types:** New Results, Confirmatory Results, Contradictory Results.
- **Timing:** may be posted before or alongside journal submission, but not once
  a journal has accepted the paper.
- **Linking:** the `api.biorxiv.org` `/details/biorxiv/{doi}` record carries the
  published-article DOI in its `published` field once detected; `/pubs/` adds
  journal name and date (per-DOI `/pubs/` lookups currently miss `10.64898`
  DOIs).

### medRxiv
- **Scope:** clinical and health sciences; operated by openRxiv (founded by
  CSHL, Yale, and BMJ). Same DOI prefixes and license set as bioRxiv.
- **Content:** research articles, systematic reviews with meta-analysis, data
  articles, and clinical research design protocols. Not for case reports,
  narrative reviews, editorials/opinion, or manuscripts already accepted or
  posted elsewhere.
- **Declarations:** ethics/IRB approval, participant consent, trial registration
  in a recognised registry, and a data-availability statement.

### ChemRxiv
- **Scope:** chemistry and related fields; co-owned by ACS, RSC, GDCh, the
  Chinese Chemical Society, and the Chemical Society of Japan (in March 2026 it
  announced a move to Wiley's Research Exchange Preprints platform; ownership is
  unchanged).
- **Identifier:** Crossref DOI per version, `10.26434/chemrxiv.<id>/v<n>`.
- **Licenses:** CC BY 4.0, CC BY-NC 4.0, or CC BY-NC-ND 4.0.

### SSRN
- **Scope:** social sciences, economics, law, business, humanities (Elsevier).
- **Identifier:** Crossref DOI `10.2139/ssrn.<abstract id>`.
- **Note:** widely used in economics/law/management; abstract-first culture.

### Research Square
- **Scope:** any field. Its **In Review** option posts the submitted manuscript
  as a preprint when you submit to a participating Springer Nature or BMC
  journal (1,000+ journals, including Nature Portfolio titles) and shows the
  peer-review status; the preprint stays public whatever the journal decides.
- **Identifier:** DOI on posting.
- **License:** preprints are provided under CC BY 4.0.

### OSF Preprints
- **Scope:** multi-disciplinary, plus community-run servers (PsyArXiv, SocArXiv,
  EarthArXiv, etc.) hosted on OSF infrastructure.
- **Identifier:** DOI via OSF.
- **Licenses:** set per provider (OSF API, checked 2026-09): general OSF
  Preprints offers CC BY 4.0 or CC0 1.0; PsyArXiv adds "No license"; SocArXiv
  also offers CC BY-NC, BY-ND, BY-NC-SA, and BY-NC-ND 4.0.

## Secondary factors

| Factor | Favours |
|--------|---------|
| Need a citable **DOI immediately** | All listed servers now issue one (arXiv via DataCite `10.48550`); prefer the server your community cites |
| Strict **funder OA mandate** (CC BY required) | any server that offers **CC BY 4.0** |
| Submitting to a **closed/selective journal** later | check the journal's preprint policy first (`journal_policy.md`); pick the least-friction license |
| **Clinical** content | medRxiv only |
| First arXiv submission, no endorser | since Jan 2026 an institutional email alone is not enough — budget time for a personal endorsement; OSF/bioRxiv have no endorsement step |
| Funder expects a preprint (e.g. Gates, 2025 policy) | any server offering **CC BY 4.0** |

## Common edge cases

- **Computational biology / bioinformatics:** arXiv `q-bio` and bioRxiv both
  accept it — choose by audience and DOI need.
- **Economics:** arXiv `econ`, SSRN, or RePEc-indexed venues; SSRN is the
  dominant social-science preprint culture.
- **Already submitted to a journal:** posting a preprint is usually still
  allowed (many journals permit the *submitted* version) but **verify the
  journal policy** before posting the *accepted* manuscript — see
  `journal_policy.md`.
- **Data / code, not a manuscript:** that is a **data repository** decision →
  defer to `alterlab-open-science` (Zenodo/Dryad/Figshare) or, for TÜBİTAK
  funding, `alterlab-aperta`.
