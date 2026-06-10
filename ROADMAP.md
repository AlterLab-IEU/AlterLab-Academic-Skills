# Roadmap

This roadmap schedules work **deferred out of v2.0** so that v2.0 stays a focused trust-and-reach
release rather than a net-new-authoring sprawl. v2.0's job was to make the existing corpus
provably trustworthy (executable evals everywhere, deterministic citation/integrity gates,
script-correctness CI) and reachable (spec-conformant per-domain bundles, a generated catalog,
honest provenance). The domains below were the planned **v2.x expansions**.

> **✅ All four expansion domains (v2.1–v2.4) shipped in v2.1.0** — 26 new skills across
> faculty-life, the Turkish academic ecosystem, bioinformatics pipelines, and the methodology
> layer, lifting the corpus to **209 skills / 16 domains** with day-one evals on every new skill.
> See [`CHANGELOG.md`](CHANGELOG.md) `[2.1.0]`. The day-one-evals discipline below remains the
> standing bar for all future work.

## Day-one-evals discipline (applies to everything below)

Every skill listed in this roadmap ships its `evals/evals.json` **in the same PR that introduces
the skill** — no eval debt is created, ever. Concretely, each new skill must, on its first
commit:

- carry a canonical `skills/<domain>/<skill>/evals/evals.json` (≥3 `should_trigger` + ≥1
  near-miss `should_not_trigger`), green under `scripts/run_evals.py --strict`;
- pass `scripts/audit_skills.py` and `pytest tests/` with **no `known_failures` entry** (that
  table is for pre-existing debt only and is off-limits for new work);
- keep its body under 500 lines (gated), description ≤1024 chars, references one level deep;
- declare an accurate `license` and real APIs/DOIs (no fabrication, no unsourced benchmarks).

This is the non-negotiable bar. A new domain does not "land" until its skills clear it. See
[`docs/evals.md`](docs/evals.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## v2.1 — Faculty-life / research-lifecycle domain ✅ shipped in v2.1.0

Shipped as `skills/faculty-life/` (6 skills). The strongest demand-side gap: the administrative
and pedagogical lifecycle around research that the corpus did not previously touch. Skills:

- Syllabus AI-policy drafting and course-level AI-use statements
- IRB / ethics protocol and informed-consent scaffolding
- Post-award grant administration and reporting
- Recommendation-letter and reference drafting support
- Accreditation Assurance-of-Learning support (AACSB / ABET AoL)
- Research-data capture and standards (REDCap, CDISC)
- Preprint deposition workflows

Scope is XL net-new authoring; each skill ships day-one evals. This domain is the highest-priority
expansion because it serves the faculty audience the suite is aimed at.

## v2.2 — Humanities & Turkish academic ecosystem ✅ shipped in v2.1.0

Shipped as `skills/turkish-academia/` (12 skills — expanded from the 5 original candidates to a
full national-platform suite, the flagship of v2.1.0). The strongest white-space play, and the one
that differentiates an Izmir-based, bilingual lab:

- **DergiPark** integration — Turkey's national academic journal platform
- **YÖK / YÖK Akademik** — Council of Higher Education author/affiliation lookups
- **Ulusal Tez Merkezi (YÖK Tez)** — national thesis-center search and metadata
- Musicology and social-science methodology skills
- Turkish-language citation styles and academic-writing conventions

This domain makes the EN/TR bilingual documentation substrate pay off and addresses an audience no
English-first skills library serves. XL; deferred from v2.0, every skill day-one-evaluated.

## v2.3 — Bioinformatics pipeline gaps ✅ shipped in v2.1.0

Shipped: bioinformatics grew 25 → 30. The inherited bioinformatics coverage was connector- and
analysis-rich but thin on end-to-end pipelines. Additions:

- FASTQ → VCF variant-calling pipeline (alignment, dedup, calling, filtering)
- Spatial transcriptomics (squidpy)
- Amplicon / metagenomics (QIIME2)
- Transcript quantification (salmon / kallisto)
- BLAST and sequence-search connectors as first-class scripted skills

These extend an existing strong domain rather than opening a new one, so they can land
incrementally. Day-one evals apply.

## v2.4 — Methodology layer ✅ shipped in v2.1.0

Shipped as `skills/methodology/` (3 skills). A cross-cutting methodology discipline (inspired by
"superpowers"-style rigor: Iron Laws, rationalization tables, decision/flow scaffolds) that sits
above the domain skills and enforces research-method correctness — pre-registration discipline,
statistical-test selection guards, and results-reporting transparency. Sequenced last so it could
codify patterns proven across the expanded corpus.

## Explicitly not scheduled here

- **Verbatim re-import of upstream skills** — the relationship to
  [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) is a
  one-time content fork ([`PROVENANCE.md`](PROVENANCE.md)); future work is original AlterLab
  authoring, not re-syncing upstream.
- **Behavioral-eval LLM-judge on every PR** — too slow/costly per-PR; behavioral grading runs on a
  weekly/dispatch schedule, while shape-validation stays the per-PR gate.

## Contributing to the roadmap

Have a skill or domain to propose? Open a
[skill request](.github/ISSUE_TEMPLATE/skill-request.md) or a
[new-skill PR](.github/PULL_REQUEST_TEMPLATE.md) — both are keyed to the day-one-evals authoring
checklist above.
