---
name: alterlab-citation-verifier
description: "Verifies that every bibliography entry actually exists by cross-checking Crossref, OpenAlex, Semantic Scholar, and arXiv (no API key required) plus doi.org DOI registration, fuzzy-matching title and authors (difflib ratio >= 0.70), flagging retractions recorded by Crossref (including Retraction Watch data) or OpenAlex, and emitting per-entry JSON verdicts in the AlterLab citation-hallucination taxonomy (TF/PAC/IH/PH/SH); a companion script scores whether a cited abstract supports a claim (SH). Accepts BibTeX, DOI/arXiv lists, or pasted references, and reports unverified instead of passing anything it could not check. Use when the request mentions verify citations, check references, fabricated or hallucinated references, fake DOI, retraction check, bibliography audit, reference existence check, or whether a source supports a claim. For drafting a manuscript prefer alterlab-paper-writer; for dead hyperlinks prefer alterlab-link-health. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) Bash WebSearch WebFetch
compatibility: "No API key required — stdlib Python (`requests` optional) via `uv run python` against Crossref, OpenAlex, Semantic Scholar, arXiv, and the doi.org Handle API; optional OPENALEX_API_KEY / S2_API_KEY only raise rate limits; offline runs return 'unverified' verdicts"
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-research-pipeline (shares the integrity taxonomy), alterlab-deep-research"
---

# Citation Verifier — Existence-Verify a Bibliography Against Public Scholarly APIs

The headline existence-verification skill: given a bibliography in any common
form, it proves entry-by-entry whether each reference **actually exists** by
querying public scholarly APIs, then maps each result to the canonical AlterLab
citation-hallucination taxonomy. It is the deterministic, network-grounded
companion to the LLM-driven `integrity_verification_agent` — where that agent
uses WebSearch + judgment, this skill uses authoritative API records and a
reproducible Python script, so every verdict rests on retrieved records and the
same input and source responses yield the same verdicts.

Verify references with the script, not from memory. A model checking citations
against what it "remembers" shares the training data that produced the
hallucination in the first place, so a fabricated reference that feels right
passes undetected; only an external record settles existence.

## Quick Start

```
Verify the citations in references.bib
Check whether these DOIs resolve to the papers I cited
Audit my bibliography for fabricated / hallucinated references
Does this reference list contain any fake citations or retractions?
```

→ Run `scripts/verify_citations.py` over the bibliography, read the JSON, then
present a verdict table grouped by severity. State the offline/degraded status
explicitly if the network or a source was unavailable.

## When to Use This Skill

- "Verify / check / audit my citations or references exist"
- "Did the AI hallucinate any of these references?" / "Is this DOI fake?"
- "Do these DOIs resolve to the papers I cited?"
- "Check this bibliography for retractions"
- "Does this source actually support the sentence I cite it for?" (SH, abstract level)
- A reproducible, scriptable existence check with an explicit offline mode

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Writing or revising the paper itself (its citation-check mode formats citations) | `alterlab-paper-writer` |
| Finding papers, extracting metadata, or generating BibTeX for new sources | `alterlab-citation-mgmt` |
| Dead or redirected hyperlinks (link rot) in docs or a reference list | `alterlab-link-health` |
| Full pre-/post-review integrity gate (citation context, data, originality) | `alterlab-research-pipeline` |
| Holistic peer review of a manuscript with an editorial decision | `alterlab-paper-reviewer` |

Grading source quality or predatory venues belongs to `alterlab-deep-research`
(`source_verification_agent`). For a whole-manuscript audit in Claude Code where every
flag should be re-checked by independent agents, offer the packaged
`/alterlab-workflows:citation-audit` workflow (`alterlab-research-workflows`, roughly
10–40 agents), which runs this skill's checks at scale.

---

## What This Does

For each bibliography entry the script:

1. **Parses** the input (auto-detects BibTeX / a bare DOI-or-arXiv list / free-form
   references, including one-reference-per-line pastes), extracting title, authors,
   year, venue, DOI, and arXiv ID. A full reference that merely contains a DOI stays
   free-form, so its title and authors are kept for the Identifier Hijacking check.
2. **Resolves identifiers** — looks up the cited DOI/arXiv ID directly when present,
   and asks the doi.org Handle API whether a DOI is registered with any agency.
3. **Searches by title + first author + year** as a fallback across the sources.
4. **Fuzzy-matches** the cited title (difflib `SequenceMatcher` ratio, default
   threshold **0.70**; a main title that is near-identical to a record stored
   without its subtitle also counts) and computes author-surname overlap. Among the
   returned records it keeps the one that matches title, then authors, then year —
   so a same-titled paper by other authors or another edition does not win.
5. **Flags retractions** on the matched work: Crossref `updated-by` / `update-to`
   notices of type retraction, withdrawal, or removal (from the publisher or, with
   `source: retraction-watch`, the Retraction Watch database that Crossref serves in
   its REST API since 2025) and OpenAlex `is_retracted`. Expressions of concern get
   a separate flag.
6. **Emits a verdict** per entry mapped to the taxonomy below, with a
   `source_status` map showing which sources answered, plus a repo-level
   `summary.verdict` (PASS / PASS_WITH_CONDITIONS / FAIL / UNVERIFIED).

### Sources (no key required; current as of 2026-09)

| Source | Endpoint | Used for | Access notes |
|--------|----------|----------|--------------|
| Crossref | `api.crossref.org/works` | DOI resolution, bibliographic search, retraction notices | `mailto` routes to the polite pool (10 req/s, 3 concurrent) |
| OpenAlex | `api.openalex.org/works` | DOI lookup + title search, `is_retracted` | `mailto` is ignored since Feb 2026. DOI lookups are free; searches draw on a daily budget shared per IP without a key (a free key gives 10× — set `OPENALEX_API_KEY`) |
| Semantic Scholar | `api.semanticscholar.org/graph/v1` | DOI/arXiv resolution, title search | Keyless pool is shared and often returns 429; `S2_API_KEY` gives a dedicated 1 req/s |
| arXiv | `export.arxiv.org/api/query` | arXiv ID resolution, preprint title search | ≥ 3 s between calls (the script throttles) |
| doi.org Handle API | `doi.org/api/handles/<doi>` | Is the DOI registered with *any* agency (Crossref, DataCite, mEDRA…)? | Authoritative for DOI existence |

Keys are optional, read from the environment, sent as headers, and never written
to the report (the report only records whether one was present). A source that
errors (rate limit, 5xx) is recorded in `source_status` and is never counted as
evidence that a work does not exist.

This skill answers **"does the cited work exist, and does its identifier point
to it?"** From API metadata alone it cannot establish Semantic Hallucination
(does the source support the claim?); `scripts/claim_faithfulness.py` gives an
abstract-level SH triage (see below), and full-text claim verification is the
research pipeline's `claim_verification_protocol` (Phase E).

---

## Verdict Taxonomy (mirrors the canonical Five-Type Taxonomy)

Identical codes and definitions to
`alterlab-research-pipeline/agents/integrity_verification_agent.md`
(GPTZero × NeurIPS 2025; Ansari, 2026). Severity feeds the same
SERIOUS / MEDIUM / MINOR scale used in the Integrity Report schema.

| Code | Name | Severity | Script trigger |
|------|------|----------|----------------|
| `verified` | — (exists, matches) | NONE | Title ratio >= threshold AND author overlap OK AND year consistent in >=1 authoritative source |
| `TF` | Total Fabrication | **SERIOUS** | Cited DOI is not registered at doi.org, or cited arXiv ID does not exist on arXiv, and no close title match exists; OR (no identifier) no record matches title + authors while Crossref and OpenAlex or Semantic Scholar answered |
| `PAC` | Partial Attribute Corruption | MEDIUM | Entry found but >=1 metadata field disagrees (year, author overlap < 50%, a cited identifier that does not resolve to it, or a garbled title whose closest record shares the authors — possible mashup) |
| `IH` | Identifier Hijacking | **SERIOUS** | Cited DOI/arXiv ID **resolved** (method=id) but the resolved record's title is unrelated (ratio < threshold) |
| `PH` | Placeholder Hallucination | **SERIOUS** | Unresolved template/placeholder (`[CITATION NEEDED]`, `\cite{}`, `et al., YYYY`, `TODO`, `forthcoming`, `in press`) — caught pre-network |
| `SH` | Semantic Hallucination | **SERIOUS** | Entry resolves but does not support its claim — **advisory only** here; asserted via `claim_faithfulness.py` / Phase E |
| `unverified` | — (could not check) | MEDIUM | Offline, the sources needed for a decision errored, or a registered DOI that no index returned. **Never treated as passing.** |

A `RETRACTED` flag is attached (and severity bumped to SERIOUS) whenever Crossref
or OpenAlex marks the *matched* work as retracted, independent of the existence
verdict; an unrelated closest hit never lends its flag to the cited entry.

`TF` is a serious accusation, so the script only asserts it on authoritative
evidence. When the deciding sources were rate-limited or down, the entry is
`unverified` with the reason and `source_status`, and it goes to the fallback below.

### Repo-level verdict

- **PASS** — every entry `verified`, no SERIOUS/MEDIUM flags.
- **PASS_WITH_CONDITIONS** — only `PAC` / MEDIUM metadata issues (fixable), and every entry was checked.
- **FAIL** — any SERIOUS verdict (`TF` / `IH` / `PH` / retraction).
- **UNVERIFIED** — nothing SERIOUS was found but at least one entry could not be
  checked (e.g. an offline run or rate-limited sources). This is **not** a pass —
  re-run with network access or an API key, or resolve those entries manually.

---

## Pipeline (how to run it)

### 1. Locate or capture the bibliography

Accept any of: a `.bib` file, a `.txt` list of DOIs/arXiv IDs, a pasted
reference list, or inline text. The script auto-detects the format; override
with `--format bibtex|doi|freeform` if detection is wrong.

### 2. Run the verifier

```bash
uv run python skills/core/alterlab-citation-verifier/scripts/verify_citations.py \
    path/to/references.bib \
    --mailto <contact-email> \
    --threshold 0.70 \
    --out citation_report.json
```

- `path/to/references.bib` may also be `-` (stdin) or inline text.
- `--threshold` tunes the fuzzy title-match ratio (0..1; default 0.70).
- `--offline` skips the network and emits `unverified` verdicts deliberately.
- Omit `--out` to print the JSON report to stdout.
- Optional: `export OPENALEX_API_KEY=…` (free key from openalex.org/settings/api)
  and/or `S2_API_KEY=…` before large bibliographies — keyless OpenAlex searches
  share a small per-IP daily budget, and the keyless Semantic Scholar pool is busy.

The script uses `requests` if installed, else the Python stdlib (`urllib`), so it
runs with no extra dependencies in a bare `uv` environment. Expect roughly 3–10 s
per entry: it spaces arXiv calls 3 s apart and backs off on rate limits.

### 3. Read the JSON and report

Parse `summary.verdict` and the per-entry `verdict` codes. Present:

1. The **headline verdict** and counts (`verdict_counts`, `severity_counts`).
2. A **table of every non-`verified` entry** with its code, severity, and `detail`.
3. For each `TF` / `IH` / `PH`: quote the cited entry and explain the evidence
   (e.g. "DOI 10.x resolved to an unrelated paper titled '…'", "DOI not registered
   at doi.org").
4. Any `RETRACTED` / `EXPRESSION_OF_CONCERN` flags, prominently.
5. For `unverified` entries: say which sources failed (`source_status`), relay the
   `manual_instructions` and any `summary.notes` (for example, an OpenAlex HTTP 429
   means the keyless per-IP budget is spent — a free `OPENALEX_API_KEY` fixes it),
   and run the fallback below.

### 4. Route fixes

- `TF` / `PH` → the reference must be removed or replaced; it does not exist.
- `IH` → the DOI/arXiv ID is wrong; find and substitute the correct identifier.
- `PAC` → correct the specific metadata field(s) named in `detail`; a possible
  mashup needs the real source identified before it can stay.
- `RETRACTED` → flag to the author; cite the retraction notice or drop the source.

---

## Graceful Degradation and the Fallback

Failures are never swallowed into a pass:

- A DNS/connection failure raises `NetworkUnavailable`; the entry becomes
  `unverified` with a populated `manual_instructions` field.
- A rate-limited or failing source is recorded in `source_status`; if the sources
  needed for a decision did not answer, the entry is `unverified`, not `TF`.
- `--offline` forces every networked entry to `unverified` up front (placeholders
  are still caught locally as `PH`).
- The repo-level verdict becomes `UNVERIFIED` whenever an entry is unverified and
  nothing SERIOUS was found.

For each `unverified` entry, re-run with connectivity or a key if possible;
otherwise look it up with the plugin's `crossref` / `openalex` MCP tools when they
are available (setup: `mcp_setup.md` under `skills/core/references`), then fall back to WebSearch with
three distinct queries (exact title in quotes; title + first author; first author +
venue + year) and, for a DOI, open `https://doi.org/<DOI>`. If a record is found, report the verdict it supports
and say it came from the fallback. If nothing is found, classify the entry as
`TF` (NOT_FOUND). There is no "difficult to verify" outcome: the Lin et al.
mashup this skill was built around slipped through three integrity rounds
precisely because it was parked in that gray zone and never searched.

---

## Claim Faithfulness (SH) — `scripts/claim_faithfulness.py`

Existence is half of the gate; a real paper cited for something it never said
(the "Frankenstein" pattern) passes every existence check. For (claim, DOI) pairs,
`claim_faithfulness.py` fetches the cited abstract (Crossref, then OpenAlex) and
returns `support` / `contradict` / `unsupported`:

```bash
uv run python skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py \
    --claim "<the sentence as written>" --doi <doi>
uv run python .../claim_faithfulness.py --input pairs.json --json        # batch
uv run python .../claim_faithfulness.py --input pairs.json --tier llm --json
```

- The default `heuristic` tier is lexical and deliberately abstains
  (`unsupported`) rather than guessing `support`; it cannot see role reversals or
  wrong numbers. The `llm` tier asks the model set by `ALTERLAB_MODEL` (see
  `shared/model_env.md`) and falls back to the heuristic, flagged, if the `claude`
  CLI is unavailable.
- It only sees the abstract (`abstract_only: true`). `unsupported` means the
  abstract does not establish the claim — non-coverage, not refutation. Report
  `contradict` as SH; send `unsupported` claims that matter to full-text checking.
- Always report existence and faithfulness separately: "the citation is real" and
  "the citation supports this sentence" are different findings.

---

## Output Shape (excerpt)

```json
{
  "tool": "alterlab-citation-verifier/verify_citations.py",
  "version": "1.1.0",
  "summary": {
    "total": 2,
    "verdict": "FAIL",
    "verdict_counts": {"verified": 1, "TF": 1, "PAC": 0, "IH": 0, "PH": 0, "SH": 0, "unverified": 0},
    "severity_counts": {"SERIOUS": 1, "MEDIUM": 0, "MINOR": 0},
    "citation_integrity_score": 0.5,
    "fabrication_risk_score": 0.5,
    "retracted": 0,
    "source_errors": {"openalex": 1},
    "notes": ["OpenAlex rate limit: the keyless daily budget shared by this IP is spent ..."]
  },
  "entries": [
    {"ref_id": "walters2023", "verdict": "verified", "severity": "NONE",
     "title_ratio": 1.0, "author_overlap": 1.0, "matches": [{"source": "crossref"}],
     "source_status": {"crossref": "record", "openalex": "record", "semanticscholar": "record", "arxiv": "no_record"}},
    {"ref_id": "ghostpaper2021", "verdict": "TF", "severity": "SERIOUS",
     "detail": "DOI 10.xxxx/... is not registered with any DOI agency (doi.org Handle API)..."}
  ]
}
```

`citation_integrity_score` and `fabrication_risk_score` (both 0..1) align with
the Integrity Report schema fields of the same name, so the report can feed
`alterlab-research-pipeline`'s integrity gate directly.

---

## Self-Check Before Reporting

- Did the run reach the network, and which sources answered? If entries are
  `unverified`, name the failing sources from `source_status`; do not imply a pass.
- Are there any `RETRACTED` flags? Surface them even on otherwise-`verified` entries.
- Did any entry score `IH`? Confirm the detail shows an **id-resolved** mismatch,
  not a loose title-search coincidence (the script enforces this distinction).
- Is the headline verdict consistent with the per-entry codes (any SERIOUS → FAIL;
  any `unverified` without SERIOUS → UNVERIFIED)?
- Did every `unverified` entry get the WebSearch fallback and a final verdict?

---

## References

- `alterlab-research-pipeline/agents/integrity_verification_agent.md` — canonical
  Five-Type Taxonomy, compound-deception patterns, and the Lin et al. (2020)
  mashup case study this skill is built to catch.
- `alterlab-research-pipeline/references/claim_verification_protocol.md` — Phase E
  full-text claim-vs-source verification (beyond the abstract-level SH triage here).
- `shared/schemas/integrity_report.schema.json` — the integrity-report shape whose
  `citation_integrity_score` / `fabrication_risk_score` this skill mirrors.
- `examples/caught_hallucination_walkthrough.md` — end-to-end run on a real mashup.
- Walters, W. H., & Wilder, E. I. (2023). Fabrication and errors in the
  bibliographic citations generated by ChatGPT. *Scientific Reports, 13*, 14045.
  https://doi.org/10.1038/s41598-023-41032-5
- Ansari, S. (2026). *Compound deception in elite peer review: A failure mode
  taxonomy of 100 fabricated citations at NeurIPS 2025* (arXiv:2602.05930).
  https://arxiv.org/abs/2602.05930
- Rittman, M. (2025, January 29). *Retraction Watch retractions now in the
  Crossref API* [Blog post]. Crossref.
  https://www.crossref.org/blog/retraction-watch-retractions-now-in-the-crossref-api/

Part of the AlterLab Academic Skills suite.
