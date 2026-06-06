# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[2.0.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v2.0.0
[1.2.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.2.0
[1.1.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.1.0
[1.0.0]: https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v1.0.0
