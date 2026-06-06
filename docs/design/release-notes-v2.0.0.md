<div align="center">

# 🚀 AlterLab Academic Skills — v2.0.0

<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases/tag/v2.0.0"><img src="https://img.shields.io/badge/Release-v2.0.0-8B5CF6?style=for-the-badge&logo=github&logoColor=white" alt="Release v2.0.0"></a>
<a href="../../skills/"><img src="https://img.shields.io/badge/Skills-183-7C3AED?style=for-the-badge&logo=bookstack&logoColor=white" alt="Skills"></a>
<a href="../../skills/"><img src="https://img.shields.io/badge/Domains-13-2563EB?style=for-the-badge&logo=databricks&logoColor=white" alt="Domains"></a>
<a href="../evals.md"><img src="https://img.shields.io/badge/Evals-183%2F183-16A34A?style=for-the-badge&logo=checkmarx&logoColor=white" alt="Eval coverage"></a>
<a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent%20Skills-Open%20Standard-0EA5E9?style=for-the-badge&logo=anthropic&logoColor=white" alt="Agent Skills — open standard"></a>

<h3>🧬 The "Trust & Reach" release</h3>
<p><em>Every one of the 183 academic Claude skills now ships an executable eval — and installing a domain plugin finally loads only that domain.</em></p>

</div>

<br>

> *v2.0 turns the loudest objection to academic skills ("just prompts, no evals") into the headline differentiator, and fixes the marketplace scoping defect that made every plugin pull in all 183 skills.*

<br>

## ⚠️ Breaking — action required for 1.x installs

**Marketplace plugins are now per-domain scoped.** Through 1.2.0 every one of the 13 domain plugins declared `source: "./"`, so installing **any** single plugin silently pulled in **all 183 skills** (a string `source` resolves the plugin root to the repo root, and the marketplace `skills` array is *additive* to default `skills/` auto-discovery — see [`scoping-spike.md`](scoping-spike.md)).

Each plugin now points at its own folder (`source: "./skills/<domain>"`), so **installing a domain plugin loads only that domain's skills**.

**If you installed `alterlab-core` at 1.x and relied on it bringing in the whole suite, that no longer happens.** Install each domain plugin you actually use:

```bash
/plugin install alterlab-databases@alterlab-academic-skills
/plugin install alterlab-writing-tools@alterlab-academic-skills
# …compose the suite from the domains you need
```

The `install.sh` path lets you cherry-pick whole domains and/or individual skills directly. The 1.x whole-suite side effect is **deprecated and gone** — compose the suite by installing the domain plugins (or `install.sh` targets) you need.

<br>

## ✨ Highlights

### ✅ Behavioral evals across the corpus

`evals/evals.json` backfilled so **183 / 183 skills** ship executable evals on the canonical [agentskills.io](https://agentskills.io) schema — run in CI on every PR via `scripts/run_evals.py --strict` (plus a weekly `--behavioral` lane). Zero skills without evals.

### 🔎 Deterministic citation-existence verifier

Three new skills land — `alterlab-citation-verifier` (core), `alterlab-pdf-extract` and `alterlab-citation-graph` (research-tools) — taking the corpus from 180 to **183**. The verifier cross-checks every reference against **Crossref + OpenAlex + Semantic Scholar + arXiv** (all keyless), resolves DOIs / arXiv IDs with a Levenshtein title+author match, flags **Retraction Watch** entries, and maps each verdict to the suite's faithfulness taxonomy. A new **`claim-faithfulness` integrity gate** wires it into the research pipeline (Stage 2.5 / 4.5).

### 🔌 Core pipeline wired into the marketplace

Slash commands (`/cite-check`, `/lit-review`, `/review-paper`, `/research-pipeline`), the deep-research and paper-reviewer **agents**, a `figure-stamp` **hook** (`skills/core/hooks/hooks.json`), and a bundled **academic MCP** (`skills/core/.mcp.json`, `skills/databases/.mcp.json`) wiring PubMed / OpenAlex / Crossref / Zotero — with a documented `requests/` fallback when no MCP is available.

### 📦 Per-domain bundles for claude.ai

`scripts/build_bundles.py` emits one self-contained `dist/<domain>.zip` per domain (**13 bundles**, each vendoring `shared/`). Every bundle clears claude.ai's 200-file / 30 MB caps so cross-skill references resolve on upload.

### 🐛 Verified bug batch — 6 classes across 14 files

A doubled `uv uv pip` invocation; an Opentrons pipette-mount error; hardcoded model IDs in MarkItDown / TimesFM / schematic + infographic AI scripts; a wrong RDKit API call; a scrambled contact email; and bad pandas quantile dict keys in the EDA skill. Spanned cheminformatics, data-science, databases, document-tools, lab-integrations, and visualization.

### 📜 Catalog, governance & provenance

A machine-readable [`skills.json`](../../skills.json) catalog (`scripts/gen_catalog.py`) plus a static docs site (`docs/site/index.html`, published via `.github/workflows/gh-pages.yml`); `CITATION.cff`, `PROVENANCE.md`, `ROADMAP.md`, K-Dense provenance notes, GitHub issue templates, and a `scripts/install.sh` that resolves `~/.claude/skills/` vs the cross-tool `~/.agents/skills/` (idempotent, `--project` support).

### ⚙️ Hardening & single source of truth

Version unified to **2.0.0** across `pyproject.toml`, `package.json`, and `.claude-plugin/marketplace.json` (top-level + all 13 plugins), with `tests/test_versioning.py` asserting they stay in sync. CI caps gated on every PR: byte-compile, `ruff check`, strict evals, a body-length **down-only ratchet**, and a 30 MB bundle ceiling. The SKILL.md description cap dropped **1536 → 1024** (zero trims). `shared/` promoted to versioned JSON Schemas under `skills/core/shared/schemas/`. Turkish README regenerated (`README.tr-TR.md`) behind an EN/TR parity gate.

<br>

## 📦 Install

<table>
<tr><td>

**🌍 Agent Skills (open standard) — recommended**

```bash
npx skills add AlterLab-IEU/AlterLab-Academic-Skills
```

Portable across Cursor, Codex, Gemini CLI, and Copilot — not Claude only.

</td></tr>
<tr><td>

**⚡ Claude Code plugin marketplace**

```bash
/plugin marketplace add AlterLab-IEU/AlterLab-Academic-Skills
# No SSH key? Use the HTTPS marketplace path:
/plugin marketplace add https://github.com/AlterLab-IEU/AlterLab-Academic-Skills.git
/plugin install alterlab-bioinformatics@alterlab-academic-skills
/reload-plugins
```

</td></tr>
<tr><td>

**🌐 claude.ai — per-domain bundles**

Download a `dist/<domain>.zip` from this Release (e.g. `bioinformatics.zip`, `databases.zip`, `core.zip`) and upload it under **Settings → Capabilities** (requires a plan with code execution).

</td></tr>
</table>

<br>

## 📊 By the numbers

<div align="center">

| Metric | Count |
|:---|:---:|
| 🧬 Skills shipped | **183** |
| ✅ Skills with executable evals | **183 / 183** (100%) |
| 🗂️ Domains | **13** |
| 🔌 Marketplace plugins (now per-domain scoped) | **13** |
| 📦 claude.ai bundles (`dist/<domain>.zip`) | **13** |
| 🆕 New skills (180 → 183) | **3** |
| 🐛 Verified bug fixes (classes / files) | **6 / 14** |
| ⌨️ Slash commands wired | **4** |
| 🧩 Core wiring added | agents · `figure-stamp` hook · academic MCP |
| 📌 Version source of truth (3 files in sync) | **2.0.0** |

</div>

<br>

## 🔗 Links

- 📒 Full changelog: [`CHANGELOG.md`](../../CHANGELOG.md) — `[2.0.0]`
- 🧪 Eval coverage & schema: [`docs/evals.md`](../evals.md)
- 🔬 Scoping spike (why scoping was broken): [`scoping-spike.md`](scoping-spike.md)
- 📜 Provenance: [`PROVENANCE.md`](../../PROVENANCE.md) · [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)

<br>

<div align="center">

<b>183 skills · 13 domains · 183 with executable evals · 1 prompt away from expert-level research</b>

<br><br>

<sub>Built with ❤️ by <a href="https://github.com/AlterLab-IEU">AlterLab Creative Technologies Laboratory</a> — if you find this useful, please consider a ⭐</sub>

</div>
