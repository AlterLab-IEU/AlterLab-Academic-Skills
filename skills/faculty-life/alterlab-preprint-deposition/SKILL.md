---
name: alterlab-preprint-deposition
description: "Drives preprint deposition across servers (arXiv, bioRxiv, medRxiv, ChemRxiv, SSRN, Research Square, OSF Preprints): picks the server by field, prepares submission metadata and arXiv categories, sets the license from each server's real option set (arXiv non-exclusive license or CC BY/BY-SA/BY-NC-SA/BY-NC-ND/CC0; bioRxiv/medRxiv CC variants or No-reuse) against funder mandates (NIH, NSF, Gates, Plan S), handles immutable versioning and preprint DOIs, checks a journal's preprint policy via the Jisc Open Policy Finder API (formerly Sherpa Romeo), and links the preprint to the published article. Reuses alterlab-arxiv and alterlab-biorxiv for metadata. Use when depositing a preprint, choosing a preprint server, preparing an arXiv, bioRxiv, or medRxiv submission, setting a preprint license, or checking journal preprint policy; for Zenodo/Dryad/Figshare data deposition prefer alterlab-open-science, for TÜBİTAK Aperta prefer alterlab-aperta. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) WebFetch
compatibility: "No API key required for the deposition workflow itself. Optional Python helpers run via `uv run python` (stdlib-only, requests optional). The journal-policy check uses the Jisc Open Policy Finder API (successor to the Sherpa Romeo v2 API, which was switched off in 2026), which needs a free non-commercial API key sent as an x-api-key header; the bioRxiv/medRxiv preprint-to-publication check uses the keyless api.biorxiv.org content API."
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-arxiv, alterlab-biorxiv (metadata/search), alterlab-open-science (data-repository & DMP choice)"
---

# Preprint Deposition — Pick a Server, Prepare the Submission, Link the Published Version

The **write/deposit** side of preprinting. Given a finished manuscript, this
skill turns "I want to post a preprint" into a concrete, server-specific plan:
**which** server fits the field, **what** metadata and category to enter,
**which license** to choose (and what it commits you to), **how** versioning and
the preprint DOI work, **whether** the target journal even allows a preprint,
and **how** to link the preprint to the article once it is published.

It is deliberately the deposit-side complement to the read-side connectors
`alterlab-arxiv` and `alterlab-biorxiv` (which *search and fetch* preprints) and
to `alterlab-open-science` (which chooses *data* repositories and writes DMPs).
This skill does **not** reimplement their search/metadata code — it calls them.

## Quick Start

```
I finished a CS paper — how do I post it to arXiv? Which category and license?
Should this biology manuscript go on bioRxiv or medRxiv?
Does Elsevier's journal X allow me to post a preprint before submission?
My preprint just got accepted — how do I link the published DOI to the arXiv version?
What license should I pick on arXiv if I might publish in a closed journal later?
```

→ Identify the field → route to a server (see the matrix) → assemble metadata →
choose a license → run the journal-policy check **before** posting → after
acceptance, link the published DOI back to the preprint.

---

## When to Use This Skill

Use this skill when the user wants to **act on** a preprint — post it, choose
where, prepare its metadata/license, or reconcile it with a journal or a
published version. Core jobs:

1. **Server selection** — match field + manuscript type to arXiv, bioRxiv,
   medRxiv, ChemRxiv, SSRN, Research Square, or OSF Preprints. See
   `references/server_selection.md`.
2. **Submission metadata** — title, authors + ORCID, abstract, **arXiv primary
   + cross-list categories** or bioRxiv/medRxiv subject collection, funding,
   declarations. See `references/submission_metadata.md`.
3. **License choice** — pick from each server's actual license set and explain
   the downstream commitment (e.g. CC BY is irrevocable; a later journal may
   object to a permissive preprint license; a funder may require CC BY). See
   `references/licensing.md`.
4. **Versioning & DOI** — arXiv versions (v1, v2, …) are **immutable and
   permanent**; a withdrawal is a *new* version with a tombstone, never a
   deletion; every arXiv paper also gets a DataCite DOI
   (`10.48550/arXiv.<id>`). bioRxiv/medRxiv assign a Crossref DOI on posting
   (prefix `10.64898` since Dec 2025 under openRxiv, `10.1101` before) and accept
   revisions under the same DOI.
5. **Journal preprint policy** — query the **Jisc Open Policy Finder API**
   (formerly Sherpa Romeo) for the target journal's prearchiving (preprint)
   policy before posting. See `references/journal_policy.md`.
6. **Post-publication linking** — connect the preprint to the published article
   (publisher field on the server; the keyless `api.biorxiv.org` `/details/`
   record carries a `published` DOI once bioRxiv/medRxiv detect the article).

### Does NOT Trigger — route adjacent requests to the right sibling

| The request is really about… | Route to | Why not here |
|------------------------------|----------|--------------|
| **Searching / fetching** existing arXiv preprints, resolving an arXiv ID | `alterlab-arxiv` | Read-side connector; this skill deposits, it does not search |
| **Searching / fetching** existing bioRxiv preprints for a lit review | `alterlab-biorxiv` | Read-side connector |
| Choosing a **data** repository (Zenodo, Dryad, Figshare), writing a grant **DMP**, preregistration, FAIR | `alterlab-open-science` | That is data/DMP/repository policy, not manuscript preprinting |
| Depositing to **TÜBİTAK Aperta**, the açık bilim mandate, a VYP | `alterlab-aperta` | National Turkish open-science track with its own embargo rules |
| Whether cited references actually **exist** / hallucinated DOIs | `alterlab-citation-verifier` | Existence-verification, not deposition |
| **Dead-link / 404** checks across a bibliography | `alterlab-link-health` | HTTP reachability, not preprint posting |
| Picking a **target journal** / formatting for journal submission | `alterlab-open-science` (OA route) then the journal's own guide | This skill only checks whether a journal *permits* a preprint |

This skill answers **"how and where do I deposit this manuscript as a preprint,
and is that compatible with my journal plans?"** It makes no claim about
manuscript quality, novelty, or whether the work should be published.

---

## Server Matrix (summary — full detail in `references/server_selection.md`)

| Server | Field fit | DOI on post | License options | Moderation |
|--------|-----------|-------------|-----------------|------------|
| **arXiv** (independent nonprofit since Jul 2026) | physics, math, CS, quant-bio (q-bio), q-fin, stat, EE/sys (eess), econ | Yes — DataCite `10.48550/arXiv.<id>`, auto-assigned; the arXiv ID stays canonical | arXiv non-exclusive license, or CC BY / BY-SA / BY-NC-SA / BY-NC-ND 4.0 / CC0 | Moderation + endorsement (tightened Jan 2026); CS review/position papers need prior peer review; a full English version is required |
| **bioRxiv** (openRxiv) | life sciences / biology | Yes — Crossref, `10.64898/…` since Dec 2025 (`10.1101/…` before) | CC BY / BY-NC / BY-ND / BY-NC-ND / CC0 / No-reuse | Basic screening; not for manuscripts already accepted by a journal |
| **medRxiv** (openRxiv) | clinical / health sciences | Yes — same prefixes as bioRxiv | Same license set as bioRxiv | Ethics, consent, and trial-registration declarations; no case reports, narrative reviews, or already-accepted papers |
| **ChemRxiv** | chemistry and adjacent fields | Yes — Crossref `10.26434/chemrxiv…`, per version | CC BY / CC BY-NC / CC BY-NC-ND 4.0 | Basic screening; co-owned by ACS, RSC, GDCh, CCS, CSJ |
| **SSRN** (Elsevier) | social sciences, economics, law, humanities | Yes — Crossref `10.2139/ssrn.<id>` | Author selects; SSRN posting terms | Light screening |
| **Research Square** | any field; "In Review" for participating Springer Nature / BMC journals | Yes | CC BY 4.0 | Screened for author info, declarations, health risk |
| **OSF Preprints** | multi/cross-disciplinary + community servers (PsyArXiv, SocArXiv, …) | Yes (DOI via OSF) | Varies by provider — general OSF: CC BY 4.0 or CC0; community servers add "No license" or NC/ND variants | Per-provider |

> Category/license rows above name the option sets each server presents at
> submission, re-checked 2026-09-23. License *implications* (irrevocability,
> journal friction, funder mandates) are in `references/licensing.md`; never
> assert a "best" license without stating the trade-off.

---

## Workflow

### 1. Determine the field and route to a server

Read the manuscript's domain. STEM-formal (physics/math/CS/stat/eess/econ/q-bio/
q-fin) → **arXiv**. Biology → **bioRxiv**. Clinical/health → **medRxiv**.
Chemistry → **ChemRxiv**. Social science/law/economics → **SSRN** (or arXiv
econ). Submitting to a Springer Nature / BMC journal that offers "In Review" →
**Research Square** is the integrated option. Cross-disciplinary or a
field-specific community server → **OSF Preprints**. Edge cases and the full
decision tree live in `references/server_selection.md`.

Check the server's gatekeeping before promising a posting date: arXiv now needs
either an institutional email **plus** a claimed paper in the same endorsement
domain, or a personal endorsement (since 21 Jan 2026); arXiv CS posts review and
position papers only with proof of prior peer review (since 31 Oct 2025); and
bioRxiv/medRxiv will not post a manuscript that a journal has already accepted.

### 2. Run the journal-policy check FIRST (if a target journal is known)

Before posting, confirm the intended journal permits preprints. Use
`scripts/journal_policy.py` to query the **Jisc Open Policy Finder API**
(`https://api.openpolicyfinder.jisc.ac.uk/retrieve`, `item-type=publication`,
key in an `x-api-key` header; the old `v2.sherpa.ac.uk` Sherpa Romeo API was
switched off at the end of July 2026). Report the journal's **prearchiving** (preprint)
permission, any conditions (embargo, version allowed, required statement), and
link the source. If no key is available, fall back to WebFetch on the publisher's
policy page and say so. Details: `references/journal_policy.md`.

> Most major publishers permit preprints, but conditions vary (some bar posting
> the *accepted* version, some require a DOI link or a specific notice). Never
> assert a policy from memory — verify it per journal.

### 3. Assemble submission metadata

Build the metadata block the server needs: title, all authors with ORCID and
affiliations, abstract, **arXiv primary category + optional cross-lists** (or
bioRxiv/medRxiv subject collection), declarations (competing interests, funding,
data/code availability, ethics/IRB for medRxiv), and the manuscript files. For
arXiv, upload the TeX/LaTeX source when the paper was written in TeX — arXiv
typically rejects a PDF generated from TeX — and include a full English version
if the paper is in another language. The canonical field-by-field checklist is in
`references/submission_metadata.md`.
To *look up* an existing arXiv/bioRxiv record's metadata for reuse, defer to
`alterlab-arxiv` / `alterlab-biorxiv` rather than re-querying here.

### 4. Choose the license deliberately

Present the actual license set for the chosen server (see the matrix), then
explain the commitment:

- **CC BY 4.0** — maximum reuse; **irrevocable**; some closed-access journals
  dislike a permissive preprint and may ask you to change it (you cannot revoke
  CC BY on already-posted versions).
- **arXiv non-exclusive license 1.0** — arXiv-specific; you keep copyright,
  grant arXiv a distribution license; the least journal-friction option on arXiv.
- **CC BY-NC-*/-ND** — narrower reuse; check it against any funder open-access
  mandate (e.g. cOAlition S Plan S generally requires CC BY).
- **CC0** — public-domain dedication; broadest, also irrevocable.

arXiv states that the license chosen is irrevocable and cannot be changed, though
a later version may carry a different license. Confirm whether a funder mandate
forces a specific license before recommending — e.g. the Gates Foundation
(policy effective 1 Jan 2025) expects funded manuscripts to be shared as a
preprint under CC BY 4.0, and Plan S funders want CC BY. The NIH (from 1 July
2025) and NSF (awards from 22 Jan 2026) zero-embargo policies cover the
peer-reviewed accepted manuscript, not the preprint. Full table + funder-mandate
notes: `references/licensing.md`.

### 5. Post, then manage versions

After posting: record the **arXiv ID / preprint DOI** and the **version**.
Revisions are *replacements* (arXiv) or new versions (bioRxiv/medRxiv) — the old
version stays public and immutable. Do **not** advise "deleting" an announced
arXiv paper; that is impossible — only a withdrawal-version with a tombstone.

### 6. Link the published article after acceptance

When the paper is published, link the DOI back to the preprint (arXiv's
journal-ref/DOI fields; bioRxiv/medRxiv auto-detect many links). On the
`api.biorxiv.org` content API the `/details/{server}/{doi}` record carries a
`published` field with the article DOI once detected; the per-DOI
`/pubs/{server}/{doi}` lookup currently returns nothing for `10.64898` DOIs, so
read `published` first. This makes the version of record discoverable from the
preprint and vice versa.

---

## Scripts

- `scripts/journal_policy.py` — query the Jisc Open Policy Finder API for a
  journal's preprint/self-archiving policy by ISSN or title (needs a free key via
  `--api-key` or the `OPEN_POLICY_FINDER_API_KEY` environment variable; prints a
  structured summary incl. embargo and locations; degrades to a manual-check
  instruction offline).
- `scripts/server_recommender.py` — given a few flags (`--field`, `--needs-doi`,
  `--target-journal-known`, `--funder-requires-cc-by`), prints a recommended
  server + license shortlist with the trade-offs and gatekeeping notes, from the
  rules in `references/server_selection.md`.
- `scripts/preprint_link_check.py` — query the keyless `api.biorxiv.org`
  `/details/` (and, for journal name/date, `/pubs/`) endpoints to confirm a
  bioRxiv/medRxiv DOI exists and surface any detected preprint→published-article
  link; works for both `10.1101` and `10.64898` DOIs.

All scripts are stdlib-first (use `requests` if present, else `urllib`), run in a
bare `uv run python`, and never require a key except the Open Policy Finder
lookup.

---

## Self-Check Before Reporting

- Did I **verify** the journal's preprint policy (Open Policy Finder or the live
  publisher page), or did I assert it from memory? Only the former is allowed,
  because publisher policies change and a wrong "yes" can cost the submission.
- Did I name the server's **real** license options and state the irrevocability
  / journal-friction trade-off, not a bare "use CC BY"?
- Did I route a *search/fetch* request to `alterlab-arxiv`/`alterlab-biorxiv`,
  and a *data-repository/DMP* request to `alterlab-open-science`, and a TÜBİTAK
  request to `alterlab-aperta`, instead of handling it here?
- Did I avoid telling the user to "delete" an already-announced arXiv preprint?

---

## References

- `references/server_selection.md` — full server decision tree, field-by-field.
- `references/submission_metadata.md` — per-server metadata field checklist.
- `references/licensing.md` — license option sets, irrevocability, funder mandates.
- `references/journal_policy.md` — Open Policy Finder API usage and policy reading.

Part of the AlterLab Academic Skills suite.
