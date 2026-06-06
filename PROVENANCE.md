# Provenance & Lineage

This document narrates where AlterLab Academic Skills came from, how it relates to its
upstream source, and the systematic work that turned a content fork into an independent,
auditable research-skills suite. The license-bearing acknowledgement and the upstream MIT
copyright notice live in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md); this file is the
narrative companion.

## Lineage

AlterLab Academic Skills began as a **content fork** of
[**K-Dense-AI/scientific-agent-skills**](https://github.com/K-Dense-AI/scientific-agent-skills)
(originally published as `claude-scientific-skills`), the scientific [Agent
Skills](https://agentskills.io/) library by **K-Dense Inc.**, released under the **MIT License**.
K-Dense's collection — curated documentation and helper scripts that make an AI agent stronger
across biology, chemistry, medicine, and drug discovery — was the seed of this project, and we
credit it as such.

It is a **content fork, not a GitHub fork**: the AlterLab repository
(`AlterLab-IEU/AlterLab-Academic-Skills`) was created as an independent repository rather than a
GitHub "Fork" of the upstream, so the lineage is recorded here and in `THIRD_PARTY_NOTICES.md`
rather than inferred from GitHub's fork graph.

**Fork-time scope.** At the point of forking, **42 skill bodies were byte-identical** to their
K-Dense counterparts. The rest had already diverged. Upstream today carries ~139 skills; the
AlterLab suite has grown to **180 skills across 13 research domains**, with the additions and
rewrites described below.

## Why AlterLab forked

K-Dense's library is built around the **scientific co-scientist** use case — wet-lab and
computational research workflows for a working scientist. AlterLab's audience is the **academic
faculty and research-lifecycle** user at a university: the person writing and reviewing papers,
running a literature review, teaching methodology, managing citations and integrity, and
producing bilingual (English/Turkish) scholarly output. The fork exists to re-aim the corpus at
that audience and to hold every skill to a stricter, CI-enforced quality bar.

## AlterLab's systematic deltas

The fork is not a re-skin. The work falls into four disciplines, each enforced by the repo's own
tooling (`scripts/audit_skills.py`, `pytest tests/`, `scripts/run_evals.py`) rather than asserted
in prose.

### 1. Evals — making "these are just prompts" false

The loudest objection to academic skills is that they ship without evaluation. AlterLab's answer
is **executable evals**: every skill carries `skills/<domain>/<skill>/evals/evals.json` on the
canonical [agentskills.io](https://agentskills.io/) eval schema (≥3 `should_trigger` cases + ≥1
near-miss `should_not_trigger` per skill), validated per-PR by `scripts/run_evals.py --strict`
and gradeable behaviorally against the `claude` CLI. The authoring contract is documented in
[`docs/evals.md`](docs/evals.md) and the schema in
[`docs/evals.schema.json`](docs/evals.schema.json). **Day-one evals are non-negotiable for new
skills** — see [`ROADMAP.md`](ROADMAP.md).

### 2. Audits — license, citation, and integrity hygiene

- **License compliance.** Proprietary material that had been incorrectly relabeled MIT was
  removed: Anthropic's `docx`/`pdf`/`pptx`/`xlsx` document-skills code (`© Anthropic, PBC`, no
  redistribution) was deleted in v1.1.0, and non-clinical skills citing self-published deposits
  as research were removed from `clinical-research/`. Each surviving skill declares an accurate
  license in its frontmatter; the per-skill distribution is tabulated in
  [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
- **Citation and claim faithfulness.** AlterLab adds a deterministic citation-existence and
  claim-faithfulness layer (Crossref / OpenAlex / Semantic Scholar / arXiv resolution, Retraction
  Watch flagging) so that generated bibliographies are verified rather than asserted.
- **No fabrication.** Real APIs, real DOIs, no unsourced vendor benchmarks; any script that sends
  data to a third-party API says so.

### 3. Fixes — script correctness

The helper scripts are gated on `python -m compileall skills/` + `ruff check skills/` in CI, and a
batch of copy-paste-fatal bugs inherited and accumulated across the corpus was squashed: `uv uv
pip` → `uv pip`, invalid Opentrons pipette identifiers corrected, hardcoded model IDs replaced
with a dated, override-able `MODEL` env var, deprecated RDKit fingerprint calls migrated to the
current generator API, a scrambled PubMed contact email fixed, and several format/quantile-key
errors corrected.

### 4. Structure — progressive disclosure and distribution

- **Lean bodies.** Skill `SKILL.md` bodies are held under ~500 lines; long detail (API tables,
  templates, worked examples) is pushed into `references/*.md` loaded on demand.
- **Spec conformance.** Descriptions are capped at 1024 characters, references are one level deep,
  and `compatibility` is declared per skill so the corpus installs across Cursor, Claude Code,
  Codex, and the open Agent Skills standard.
- **Per-domain bundles.** The corpus ships as 13 per-domain plugins/bundles that clear claude.ai's
  install caps, plus a generated `skills.json` catalog that keeps documentation from drifting from
  the on-disk source of truth.
- **Bilingual docs.** English and Turkish READMEs are kept in count-parity by a CI gate.

## Relationship summary

| | Upstream (K-Dense) | AlterLab |
|---|---|---|
| Repository | `K-Dense-AI/scientific-agent-skills` | `AlterLab-IEU/AlterLab-Academic-Skills` |
| License | MIT © 2025 K-Dense Inc. | MIT © 2026 AlterLab Creative Technologies Laboratory |
| Audience | scientific co-scientist (wet-lab / computational) | academic faculty & research lifecycle |
| Evals | — | executable, CI-gated, day-one for all skills |
| Skills | ~139 | 180 across 13 domains |
| Languages | EN | EN + TR |

## Citing this work

Machine-readable citation metadata is provided in [`CITATION.cff`](CITATION.cff). Please cite the
AlterLab Academic Skills suite when it materially supports a publication or course, and credit
K-Dense Inc. as the upstream source where appropriate.
