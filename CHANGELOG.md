# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.0] — 2026-07-02

Social-science methods spine — a new **17th domain**, `social-science-workflow`, adds a
stage-gated chain of four **discipline-enforcing validity gates** that a study passes through
before it is analyzed or written: **design** (pin the identifying assumption), **measurement**
(reliability is not validity), **sampling** (power/precision/saturation, not a rule of thumb),
and **inference** (the claim may not exceed the design). Each gate ships a stdlib helper script,
a loaded-on-demand reference, and vignette-in / routing-out evals with near-miss negatives.
**221 → 225 skills** (new `social-science-workflow` 0 → 4), still 100% eval coverage across
16 → 17 domains.

### Added

- **`alterlab-ssci-design-gate`** (social-science-workflow) — routes a study to its design
  family (experiment / DiD / IV / RDD / ITS / fixed-effects / observational / qualitative /
  mixed) by the data-generating process and **pins the identifying assumption** the causal claim
  rests on before any estimation. Stdlib `design_router.py`.
- **`alterlab-ssci-measurement-gate`** (social-science-workflow) — enforces *reliability ≠
  validity*: requires McDonald's omega (not Cronbach's alpha alone, which assumes tau-equivalence),
  the four validities, and measurement invariance before any cross-group comparison. Routes CFA
  execution to the psychometrics skill.
- **`alterlab-ssci-sampling-gate`** (social-science-workflow) — gates frame, method, and size,
  matching the **sizing logic to the inference** (a-priori power / precision / saturation) and
  the generalization claim to the sample type. Stdlib `sample_size.py` (Acklam inverse-normal).
- **`alterlab-ssci-inference-gate`** (social-science-workflow) — the terminal auditor: refuses
  causal language without a defended assumption, corrects p-value / CI misreadings, flags
  uncorrected multiplicity and optional stopping, and scopes generalization to the frame. Stdlib
  `claim_audit.py` claim linter.

The four gates carry mutual `prefer alterlab-x` routing and near-miss evals against existing
methodology / survey / statistics skills; `confusion_matrix.py` reports zero new routing gaps.

Foundation-model skills — the suite gains a **runnable structure-prediction** cluster, the
**protein-design** cluster that completes the design→fold→score loop, single-cell + genomics
foundation models, figure-QA and single-PDF exploration, and the provider-agnostic GPU dispatch
layer they build on. **210 → 221 skills** (bioinformatics 30 → 38, domain-specific 17 → 18,
visualization 8 → 9, document-tools 2 → 3), still 100% eval coverage.

### Added

- **`alterlab-scgpt`** (bioinformatics) — scGPT single-cell foundation model (Cui 2024):
  zero-shot / fine-tuned cell-type annotation, embeddings, and batch integration on AnnData.
- **`alterlab-borzoi`** (bioinformatics) — Borzoi (Linder 2025, `calico/borzoi`): sequence →
  genome-wide functional tracks and non-coding variant effect scoring / in-silico mutagenesis.
- **`alterlab-figure-qa`** (visualization) — render-then-verify publication-figure QA:
  data-fidelity, label legibility floor/ceiling, bbox-collision detection, 300-dpi export.
- **`alterlab-pdf-explore`** (document-tools) — deep single-PDF Q&A: parse once, answer across
  sections/figures/appendices, extract-every-instance, read values off charts.
- **Aggregated MCP connectors** (`mcp-servers/`) — four standalone FastMCP servers wrapping the
  highest-traffic data clusters behind typed tool surfaces: `structures` (RCSB PDB + AlphaFold
  DB + Complex Portal), `variants` (gnomAD + ClinVar/NCBI), `chemistry` (PubChem + BindingDB),
  and `genes-ontologies` (MyGene + UniProt + QuickGO + Reactome). Stdlib-HTTP only (dep:
  `fastmcp`), credentials read from env, graceful error objects. Their `.mcp.json` manifests
  are shape-validated by `tests/test_mcp_manifest.py` (the academic-server bundle requirement is
  scoped to the core/databases skill plugins), and the connector code is covered by
  `SECURITY_SCAN.md` and CI lint/compile.

- **`alterlab-proteinmpnn`** (bioinformatics) — ProteinMPNN (Dauparas 2022): fixed-backbone
  inverse folding with fixed positions, tied/symmetric chains, and AA bias.
- **`alterlab-ligandmpnn`** (bioinformatics) — LigandMPNN (Dauparas 2023): ligand/metal/
  nucleic-acid-aware pocket and active-site sequence design.
- **`alterlab-rfdiffusion`** (bioinformatics) — RFdiffusion (Watson 2023): de-novo backbone
  generation, motif scaffolding, binder design, symmetry. Completes the design→fold→score loop
  with proteinmpnn + alphafold.

- **`alterlab-remote-compute`** (domain-specific) — provider-agnostic `submit → poll → harvest`
  dispatch across SLURM/HPC (`sbatch`/`sacct`) and managed GPU APIs (Modal, RunPod, GCP Batch /
  Vertex AI), with a stdlib-only `scripts/dispatch.py`. The prerequisite the GPU model skills
  dispatch through; generalizes the single-provider `alterlab-modal`.
- **`alterlab-alphafold`** (bioinformatics) — AlphaFold2 folding via ColabFold (Mirdita et al.
  2022): MMseqs2 MSAs, monomer + AF2-Multimer complexes, pLDDT/pTM/ipTM/PAE confidence, and
  design self-consistency checks.
- **`alterlab-boltz`** (bioinformatics) — Boltz-2 (Passaro & Wohlwend 2025, `jwohlwend/boltz`),
  an open AlphaFold3-style model: protein + ligand (SMILES/CCD) co-folding, protein–nucleic-acid
  assemblies, and binding-affinity prediction.
- **`alterlab-chai`** (bioinformatics) — Chai-1 (Chai Discovery 2024, `chaidiscovery/chai-lab`):
  multi-entity complex prediction from a single typed FASTA, strong on antibody–antigen, with
  optional MSAs and restraints.

The three folders carry mutual `prefer alterlab-x` routing (alphafold ↔ boltz ↔ chai) and
near-miss evals; `confusion_matrix.py` reports zero new routing gaps.

The "review & trust" release: implements the external repo-review roadmap end to end —
new activation/collision benchmarks, a CI-attested trust manifest, formalized agents/teams
and portability docs, the final body splits, and sharper cross-skill routing. Still
**210 skills across 16 domains**, 210 / 210 with executable evals; audit clean (0 errors,
0 warnings), full test suite green.

### Added

- **Trust manifest** — generated, CI-enforced [`SECURITY_SCAN.md`](SECURITY_SCAN.md)
  (`scripts/gen_security_scan.py`): the full outbound-host allowlist (66 domains, each
  categorized) plus a static attestation of **no shell-pipe, no `os.system` / `shell=True`,
  no `eval`/`exec` on input, no hardcoded secrets**. `--check` fails on drift, `--strict`
  on any violation.
- **Activation harness** — `scripts/run_evals.py --activation` measures auto-selection rate
  (does the model pick the right skill from its description among same-domain distractors)
  against Anthropic's 90% bar, and reports the cross-fire rate. `--shard i/n` drives a
  **nightly rotating 1/7 behavioral** CI job so the whole corpus is LLM-judged each week.
- **Cross-skill confusion matrix** — `scripts/confusion_matrix.py` statically ranks sibling
  cross-firing risk by trigger-noun overlap and flags routing gaps; a test guards against
  dangling near-miss deferral targets.
- **claude.ai compatibility guard** — `scripts/check_claudeai_compat.py` (frontmatter
  whitelist check + `--package` to strip the `compatibility` key for uploads).
- **Agents & teams catalog** — generated [`docs/agents-and-teams.md`](docs/agents-and-teams.md)
  formalizing the 35 pipeline subagents into 4 named teams.
- **Portability statement** — generated [`docs/portability.md`](docs/portability.md):
  portable-core vs. Claude-Code/SDK-specific fields.
- Guards: `tests/test_no_readme_in_skill_root.py`, and a `frontmatter-yaml-unsafe`
  audit check + per-skill test.

### Changed

- Sharpened **42 confusable sibling descriptions** with explicit `prefer alterlab-x` routing
  (quantum, protein/structure DBs, cheminformatics toolkits, single-cell, pathology,
  plotting, RL, citation-verifier vs paper-writer, research-lookup vs parallel-web).
- Split the final **17 over-500-line** SKILL.md bodies into `references/`; the body-length
  ratchet is now **empty** — every skill is held to the 500-line soft cap.
- Documented the noun/tool-vs-gerund naming rationale in `CONTRIBUTING.md`; added
  README trust/portability links and `docs/evals.md` activation + shard sections.
- Regenerated `marketplace.json` — restored the `core` plugin's stale
  `commands` / `agents` / `hooks` entries.
- Softened the "Evals 210/210" badge to "Eval coverage 210/210" to match the honest wording.

### Fixed

- Reconciled the 209→210 skill-count drift (`CLAUDE.md`, `pyproject.toml`) and core 8→9;
  corrected the README's "39 agents" → **35** to match disk.
- Removed the two skill-root `README.md` files (the Agent Skills spec forbids `README.md`
  at a skill root); research-lookup content preserved under `references/`.
- Frontmatter YAML in `alterlab-histolab` and `alterlab-qutip` (an unquoted `:` in
  `description` broke strict parsing → Agent Skills spec failure). `audit_skills.py` now
  flags this class at the source, so — unlike the recurrences in v2.2.0 — it cannot slip
  past the tolerant parser again.

## [2.2.0] — 2026-06-10

The "elevation" release: a research-backed accuracy and depth pass over the whole
pre-existing corpus, plus one new core skill — **210 skills across 16 domains**,
210 / 210 with executable evals.

### Added

- **`alterlab-workflow-orchestration`** (core): composes AlterLab skills into
  multi-agent agentic workflows — parallel subagent fan-out, sequential pipelines,
  judge panels, adversarial verification, and loop-until-clean review cycles —
  mapped onto current Claude Code subagent / Claude Agent SDK orchestration patterns.

### Changed

- **Research-backed elevation of 191 pre-existing skills**: corrected regulation and
  API details (e.g. Akademik Teşvik MADDE 6/7–6/9 scope exclusions), slimmed
  oversized bodies into `references/`, refreshed eval rubrics, and bumped
  `metadata.version` on every touched skill.
- README (EN/TR) eval-coverage wording now states precisely what runs where: the
  schema + trigger-coverage gate runs in CI on every PR; the behavioral pass
  (claude CLI + LLM judge) runs on demand via `workflow_dispatch`.

### Fixed

- Frontmatter YAML in `alterlab-perplexity` and `alterlab-tubitak-proposal`
  (unquoted `:` in `description` broke parsing → Agent Skills spec failures).
- Re-added the suite mention to 5 rewritten descriptions; body-length ratchet
  brought back to green (4 stale entries delisted, 2 bodies re-slimmed under the
  500-line soft cap).
- Behavioral evals CI lane no longer runs on a weekly cron without credentials
  (manual `workflow_dispatch` only; requires the `ANTHROPIC_API_KEY` repo secret).

## [2.1.0] — 2026-06-06

A roadmap-clearing content release: **26 new skills across the four v2.1–v2.4 roadmap
domains**, lifting the corpus from **183 → 209 skills across 13 → 16 domain categories**,
with day-one executable evals on every new skill (coverage holds at **209 / 209**).

### Added

- **Turkish-academia suite (12 skills — the release flagship)** under
  `skills/turkish-academia/`: `alterlab-dergipark`, `alterlab-trdizin`, `alterlab-yok-tez`,
  `alterlab-yok-akademik`, `alterlab-yokatlas`, `alterlab-tubitak-proposal`,
  `alterlab-docentlik-eligibility`, `alterlab-akademik-tesvik`, `alterlab-tr-academic-style`,
  `alterlab-tr-research-ethics`, `alterlab-kvkk-dmp`, and `alterlab-aperta`. Each is wired to
  a **verified national-platform endpoint** (DergiPark's platform-wide OAI-PMH feed, the
  TR Dizin REST/Elasticsearch API, the YÖK Tez / YÖK Akademik / YÖKATLAS portals, TÜBİTAK
  ARDEB PBS, and ULAKBİM Aperta), and encodes the live regulatory rules (ÜAK doçentlik
  tables, the Akademik Teşvik Yönetmeliği scoring, KVKK Law 6698 as amended by Law 7499,
  and the TR Dizin/ULAKBİM ethics-committee trigger).
- **Faculty Life (6 skills)** under `skills/faculty-life/`: `alterlab-syllabus-ai-policy`,
  `alterlab-grant-reporting`, `alterlab-recommendation-letters`, `alterlab-accreditation-aol`,
  `alterlab-redcap-cdisc`, and `alterlab-preprint-deposition`.
- **Methodology (3 skills)** under `skills/methodology/`: `alterlab-preregistration-discipline`,
  `alterlab-test-selection-guard`, and `alterlab-results-transparency` — superpowers-style
  discipline gates (Iron Laws, Excuse-vs-Reality rationalization tables, Red-Flags-STOP lists)
  applied to research methods.
- **Bioinformatics pipelines (25 → 30)**: `alterlab-nf-core-sarek` (nf-core/sarek variant
  calling), `alterlab-qiime2-amplicon` (16S/ITS microbiome), `alterlab-rnaseq-quant`
  (salmon/kallisto), `alterlab-blast` (NCBI BLAST+), and `alterlab-squidpy-spatial`
  (spatial transcriptomics).
- **Day-one evals on all 26 new skills**: every new skill ships `evals/evals.json` on the
  canonical [agentskills.io](https://agentskills.io) schema, so eval coverage stays at
  **209 / 209**, CI-gated on every PR via `scripts/run_evals.py --strict`.

### Changed

- **Phase-0 infrastructure** ahead of the expansion: the contributor `template/` was fixed to
  the canonical eval schema; the generated `.claude-plugin/marketplace.json` gained first-class
  top-level `description` and `version` fields plus `metadata.author`; and three new domain
  plugins (`alterlab-turkish-academia`, `alterlab-faculty-life`, `alterlab-methodology`) join
  the marketplace, bringing it to **16 plugins**.
- **Version bumped to 2.1.0** across the three sources of truth (`pyproject.toml`,
  `package.json`, `.claude-plugin/marketplace.json`); `skills.json` and both READMEs
  regenerated to **209 skills / 16 domains**.

## [2.0.0] — 2026-06-06

### ⚠️ Breaking — action required for 1.x installs

- **Marketplace plugins are now per-domain scoped.** Through 1.2.0 every one of the
  13 domain plugins declared `source: "./"`, so installing *any* single plugin pulled in
  **all 183 skills** (a string `source` resolves the plugin root to the repo root, and the
  marketplace `skills` array is *additive* to default `skills/` auto-discovery — see
  [`docs/design/scoping-spike.md`](docs/design/scoping-spike.md)). Each plugin now points at
  its own folder (`source: "./skills/<domain>"`), so **installing a domain plugin loads only
  that domain's skills**. If you installed `alterlab-core` at 1.x and relied on it bringing in
  the whole suite, that no longer happens: **install each domain plugin you actually use**
  (`alterlab-databases`, `alterlab-writing-tools`, …) from the same marketplace. The
  `install.sh` path lets you cherry-pick whole domains and/or individual skills directly.

### Added

- **Behavioral evals across the corpus**: `evals/evals.json` backfilled so **183 / 183 skills**
  ship executable evals on the canonical [agentskills.io](https://agentskills.io) schema,
  run in CI on every PR via `scripts/run_evals.py --strict` (plus a weekly `--behavioral` lane).
- **Three new skills**: `alterlab-citation-verifier` (core), `alterlab-pdf-extract` and
  `alterlab-citation-graph` (research-tools) — bringing the corpus from 180 to **183 skills**.
- **Core pipeline wiring registered in the marketplace**: slash commands (`/cite-check`,
  `/lit-review`, `/review-paper`, `/research-pipeline`), the deep-research and paper-reviewer
  **agents**, a `figure-stamp` hook (`skills/core/hooks/hooks.json`), and an **academic MCP
  bundle** (`skills/core/.mcp.json`, `skills/databases/.mcp.json`) with setup notes in
  `references/mcp_setup.md`.
- **A `claim-faithfulness` integrity gate** wired into the research pipeline (Stage 2.5 / 4.5).
- **Per-domain bundles**: `scripts/build_bundles.py` emits `dist/<domain>.zip` (13 bundles,
  each vendoring `shared/`) for upload to agents that take zipped skills.
- **Catalog + docs site**: `skills.json` machine-readable catalog (`scripts/gen_catalog.py`)
  and a static site (`docs/site/index.html`, published via `.github/workflows/gh-pages.yml`).
- **Provenance & governance**: `CITATION.cff`, `PROVENANCE.md`, `ROADMAP.md`, `V2_PLAN.md`,
  K-Dense provenance notes, GitHub issue templates, and `scripts/install.sh` (resolves
  `~/.claude/skills/` vs the cross-tool `~/.agents/skills/`, idempotent, `--project` support).

### Fixed

- **Verified bug batch (6 classes, 14 skill/reference/script files)**: doubled `uv uv pip`
  invocation; an Opentrons pipette-mount error; hardcoded model IDs in MarkItDown/TimesFM/
  schematic + infographic AI scripts; a wrong RDKit API call; a scrambled contact email; and
  bad pandas quantile dict keys in the EDA skill. Spanned cheminformatics, data-science,
  databases, document-tools, lab-integrations, and visualization.

### Changed

- **Eval schema migrated to the canonical agentskills.io shape** (`scripts/migrate_eval_schema.py`,
  validated against `docs/evals.schema.json`): legacy `query → prompt`,
  `expected_behavior → expected_output`, and `should_trigger` survives as an `assertions`
  entry (`should_trigger` / `should_not_trigger`), so behavioral coverage does not regress.
- **Single version source-of-truth: 2.0.0.** `pyproject.toml`, `package.json`, and
  `.claude-plugin/marketplace.json` (top-level + all 13 plugins) now agree; the hardcoded
  version in `gen_marketplace.py` is gone and `tests/test_versioning.py` asserts the three
  stay in sync plus a per-skill `metadata.version` presence check.
- **CI caps gated**: byte-compile (`compileall skills/`), `ruff check`, strict evals, and the
  body-length **ratchet** now run on every PR. The SKILL.md description cap dropped
  **1536 → 1024** (zero trims: largest real description is 886 chars); the 500-line body soft
  cap is a *down-only ratchet* over a frozen 21-skill backlog (hard cap 1500); bundles enforce
  a 30 MB hard ceiling with a 5 MB / 200-file warn.
- **`shared/` promoted to versioned JSON Schemas** under `skills/core/shared/schemas/`
  (bibliography, rq_brief, review_report, paper_draft, integrity_report, material_passport,
  synthesis, revision_roadmap, response_to_reviewers) with worked examples.
- **Mermaid references flattened** one level (`alterlab-mermaid/references/diagrams/*.md` →
  `references/`) to satisfy the one-level-deep spec rule, with citations re-pointed atomically.
- **`compatibility` and `metadata.version` backfilled across all 183 skills** (compatibility
  was on 8; version was missing on 10).
- **Turkish README regenerated** (`README.tr-TR.md`) with an EN/TR parity gate; spec-conformance
  workflow (`scripts/check_spec.py`, `.github/workflows/spec-conformance.yml`) added.

### Deprecated

- Installing a single domain plugin as a proxy for "install everything." The 1.x whole-suite
  side effect is gone; compose the suite by installing the domain plugins (or `install.sh`
  targets) you need.

## [1.2.0] — 2026-06-03

### Added
- **Cross-agent install**: documented `npx skills add AlterLab-IEU/AlterLab-Academic-Skills`
  (the open [agentskills.io](https://agentskills.io) standard — also works in Cursor, Codex,
  Gemini CLI, and Copilot), plus the HTTPS-marketplace and `--plugin-dir` local-dev paths.
- **Marketplace metadata**: each of the 13 domain plugins now carries `category`, `keywords`,
  `author`, `homepage`, and `version` (powers the `/plugin → Discover` UI), emitted by
  `scripts/gen_marketplace.py`.
- **Behavioral evals**: `evals/evals.json` for the core pipeline skills following Anthropic's
  trigger/should-not-trigger format, plus `scripts/run_evals.py`.
- **Contributor scaffold**: `template/` (canonical `SKILL.md` + `evals/` stub) and a
  Skill Quality Standards rubric in `CONTRIBUTING.md`.
- `THIRD_PARTY_NOTICES.md` and this `CHANGELOG.md`; `.editorconfig` and a `scripts` block
  in `package.json` for family consistency with the sibling AlterLab repos.

### Changed
- **Descriptions rewritten for triggering** across all 13 domains: lead with what the skill
  does + an explicit "Use when …" trigger clause, third person, with the suite label moved to
  the end (it previously prefixed 99/180 descriptions, wasting the highest-signal tokens).
- `audit_skills.py`: description cap raised to the documented 1536; new lints for reserved
  words in `name`, leading suite-boilerplate, missing trigger clause, and non-third-person
  descriptions; cross-skill `references/` citations now resolve instead of false-positiving.

## [1.1.0] — 2026-06-03

### Removed
- The `docx`, `pdf`, `pptx`, `xlsx` document skills — they were Anthropic's proprietary
  document-skills code (`© Anthropic, PBC, All rights reserved`; no redistribution or
  derivative works) and had been incorrectly relabeled MIT. Removed for license compliance.
- The `consciousness-council`, `dhdna-profiler`, and `what-if-oracle` skills — non-clinical
  content citing self-published deposits as research; removed from `clinical-research/`.

### Added
- **Installable plugin marketplace** (`.claude-plugin/marketplace.json`, 13 domain plugins)
  generated by `scripts/gen_marketplace.py`; corrected README install instructions.
- `uv`-based CI with a committed `uv.lock`; a marketplace `--check` gate.

### Fixed
- 19 skills invoked a `scripts/generate_schematic.py` path that did not exist in their dir;
  removed the boilerplate where irrelevant and redirected to the schematics/image skills.
- Split two over-length skill bodies into `references/`; repaired dangling citations; fixed an
  LDA citation (Blei, Ng & Jordan 2003); removed unsourced vendor benchmarks; added a
  regex-de-identification caveat and third-party data-egress notes; replaced `curl | bash`.
- Corrected skill counts (180) and the frontmatter schema across README, README.tr-TR,
  CLAUDE.md, and CONTRIBUTING.

## [1.0.0] — 2026-03-24

- Initial public release of the AlterLab Academic Skills collection.

[2.1.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v2.1.0
[2.0.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v2.0.0
[1.2.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.2.0
[1.1.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.1.0
[1.0.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.0.0
