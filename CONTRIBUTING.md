# Contributing to AlterLab Academic Skills

Thank you for your interest in contributing to AlterLab Academic Skills. This guide explains how to add new skills, submit changes, and maintain quality across the project.

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

## How to Add a New Skill

### 1. Choose a Category

Skills must belong to one of the following categories:

| Category | Path | Description |
|----------|------|-------------|
| Core | `skills/core/` | Research, Write, Review, Publish pipeline |
| Databases | `skills/databases/` | Scientific database connectors |
| Bioinformatics | `skills/bioinformatics/` | Genomics, proteomics, molecular biology |
| Cheminformatics | `skills/cheminformatics/` | Chemistry, drug discovery |
| Clinical Research | `skills/clinical-research/` | Clinical decision support, medical tools |
| Data Science | `skills/data-science/` | ML, statistics, data analysis |
| Document Tools | `skills/document-tools/` | Markdown conversion and notebook tooling |
| Domain-Specific | `skills/domain-specific/` | Quantum, geospatial, materials science |
| Faculty Life | `skills/faculty-life/` | Faculty research-lifecycle and academic administration |
| Finance & Economics | `skills/finance-economics/` | Financial data and analysis |
| Lab Integrations | `skills/lab-integrations/` | Laboratory platform connectors |
| Methodology | `skills/methodology/` | Research methodology and rigor scaffolds |
| Research Tools | `skills/research-tools/` | Search, discovery, reference management |
| Social-Science Workflow | `skills/social-science-workflow/` | Stage-gated design/measurement/sampling/inference validity gates |
| Turkish Academia | `skills/turkish-academia/` | Turkish academic system workflows (YÖK, ÜAK, DergiPark, TÜBİTAK) |
| Visualization | `skills/visualization/` | Scientific plotting and graphics |
| Writing Tools | `skills/writing-tools/` | Scientific writing, citations, posters |

If your skill does not fit any existing category, open an issue to discuss adding a new one.

### Audience boundary — faculty repo, not the student (FC) repo

This repository ships skills for **faculty members, academic researchers, and
research staff**. Student-facing skills — study aids, assignment helpers,
exam-prep, coursework tutors — belong in the separate **AlterLab FC (Faculty
Companion / student)** repository, **not here**. When a proposed skill could
serve either audience, scope its SKILL.md, description, and evals to the
*researcher* task (e.g. "audit my manuscript's inferential claims", not "help me
pass my stats exam"). A skill whose primary trigger is a student workflow will be
redirected to the FC repo in review. The `social-science-workflow` gates are a
model of this: they discipline a *researcher's* study, and route execution to
sibling research skills rather than tutoring a learner.

### 2. Naming Convention

- **Folder name**: `alterlab-{name}` (lowercase, hyphenated)
- **Examples**: `alterlab-blast`, `alterlab-pubmed`, `alterlab-r-stats`

#### Noun/tool names vs. gerunds — a deliberate deviation

Anthropic's `skill-creator` *recommends* gerund names (`analyzing-data`,
`reviewing-code`). This suite deliberately uses **noun/tool** names
(`alterlab-biopython`, `alterlab-rdkit`, `alterlab-pubmed`) for the ~200 skills
that wrap a specific tool, library, database, or academic system. This is an
intentional decision, not an oversight:

- For a tool/database wrapper, the tool's own name **is** the highest-signal
  trigger token. A researcher who wants BioPython types "biopython", not
  "manipulating biological sequences" — so `alterlab-biopython` maximizes
  discoverability where it matters most.
- Noun names keep the 39-connector database cluster and the 30-skill
  bioinformatics cluster scannable and one-to-one with the real ecosystem.

Where a gerund genuinely aids discovery — the **capability/pipeline** skills that
describe an *activity* rather than wrap a tool (`alterlab-paper-writer`,
`alterlab-deep-research`, `alterlab-paper-reviewer`) — do **not** rename the
folder. Instead, carry the gerund phrasing as concrete trigger nouns inside the
`description`'s "Use when …" clause (e.g. "Use when writing / drafting / revising a
paper …"), so the activation surface covers both registers without churning the
canonical `alterlab-` name. New tool-wrapper skills should follow the noun
convention; new capability skills should lead their description with the activity
verbs a user would actually type.

### 3. Folder Structure

```
skills/{category}/alterlab-{name}/
  SKILL.md        # The skill definition (required)
  references/     # Long-form detail, linked from SKILL.md (optional)
```

Keep `SKILL.md` lean. The body is the router: it explains what the skill does and links out to deeper material. Long detail (API tables, templates, style guides, worked examples) lives in `references/*.md` and is **cited from the body by relative path** (e.g. `references/api_patterns.md`). Every `references/*.md` path you mention in the body must exist on disk — CI fails the skill otherwise.

### 4. SKILL.md Template

Every skill must have a `SKILL.md` file with YAML frontmatter followed by the skill prompt content. The frontmatter follows the [Agent Skills spec](https://code.claude.com/docs/en/skills) and is **CI-enforced** — copy this template exactly:

```markdown
---
name: alterlab-{name}            # lowercase-hyphen, <=64 chars, MUST equal the parent directory name; no 'claude'/'anthropic'
description: <what it does AND when to use it, third person, <=1024 chars>. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(python:*)   # SPACE-separated (open-standard)
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# {Skill Name}

Describe what the skill does and when to use it, then give the full
instructions. Link long-form detail out to `references/*.md`.

Part of the AlterLab Academic Skills suite.
```

**Required frontmatter fields:**

- `name` -- lowercase-hyphen, `<=64` chars, **must equal the parent directory name** (`alterlab-{name}`); must not contain `claude` or `anthropic`
- `description` -- third person, covers **what it does AND when to use it**, `<=1024` chars; include the suite label `Part of the AlterLab Academic Skills suite.`
- `license` -- `MIT` (must come from the controlled license vocabulary)
- `allowed-tools` -- **space-separated** open-standard list, e.g. `Read Write Edit Bash(python:*)`
- `metadata.skill-author` -- must be `AlterLab`
- `metadata.version` -- quoted semver string, e.g. `"1.0.0"`
- `compatibility` -- documents the skill's target runtime / required env & keys. **Claude-Code/SDK-only**: this is the one top-level key outside the claude.ai uploader whitelist (see below).

> There is **no** top-level `version:` field, and **no** `metadata.tags` or `metadata.category`. Category is derived from the folder path, not the frontmatter.

### claude.ai custom-skill uploads

The claude.ai `.zip` uploader accepts only these top-level frontmatter keys:
`{name, description, license, allowed-tools, metadata}`. This suite ships one extra —
`compatibility` — which is valid in the open standard and Claude Code but **not** on
claude.ai. Do **not** add further non-whitelisted top-level keys: one unexpected key
fails *every* skill's upload at once. `scripts/check_claudeai_compat.py --strict` (run
in CI) catches such drift, and `scripts/check_claudeai_compat.py --package OUT` writes
claude.ai-safe copies with `compatibility` stripped, ready to zip and upload.

## Pull Request Process

1. **Fork the repository** and create a feature branch from `main`.
2. **Follow the naming conventions** described above.
3. **Include a clear PR description** explaining:
   - What the skill does
   - Which category it belongs to
   - Any external APIs or services it depends on
4. **One skill per PR** unless the skills are closely related.
5. **v2 authoring checklist — every new skill ships `evals/evals.json`** with **≥ 3 trigger cases (`should_trigger`) + ≥ 1 negative case (`should_not_trigger`)**; validate with `python scripts/run_evals.py`. A skill without evals will not be accepted.
6. **Validate before submitting** (the validators are the source of truth, see below):
   ```bash
   python scripts/audit_skills.py     # frontmatter / references / convention audit
   pytest tests/                      # per-skill schema + body-length + references tests
   ```
   A new skill must pass cleanly with **no `known_failures` entry** — that table tracks pre-existing content debt only and is off-limits for new work.
7. **Regenerate the marketplace** if you added, removed, moved, or renamed a skill:
   ```bash
   python scripts/gen_marketplace.py  # rewrites .claude-plugin/marketplace.json
   python scripts/gen_catalog.py      # rewrites skills.json (also required after any version bump:
                                      # the catalog embeds summary.version from pyproject.toml)
   ```
   Commit the regenerated `marketplace.json` alongside your skill.
8. **Wait for review** -- a maintainer will review your PR and may request changes.

## Commit Convention

Follow the project commit convention:

- `feat: add {skill-name}` -- new skill
- `improve: {skill-name} -- {what changed}` -- skill enhancement
- `fix: {skill-name} -- {what was wrong}` -- bug fix
- `docs: update {what}` -- documentation changes
- `chore: {description}` -- project maintenance

## Testing Guidelines

The **source of truth for validation** is the repo's own tooling — if it passes there, it passes in CI:

- `python scripts/audit_skills.py` -- audits every `SKILL.md` for frontmatter shape, naming/`name`-matches-folder, license vocabulary, the suite label, and that all cited `references/*.md` paths exist.
- `pytest tests/` -- per-skill schema, body-length, and reference-existence tests.

New skills must pass both with **no `known_failures` entry**. Beyond the automated checks, also:

- Test the skill prompt with Claude to verify it produces expected behavior
- Check that the skill does not request or expose sensitive information (API keys, credentials)
- Verify the skill handles edge cases gracefully (empty input, malformed data)
- Review for prompt injection risks -- skills should not blindly pass untrusted user input into sensitive operations

## Modifying Existing Skills

- Bump the `metadata.version` field in the frontmatter (quoted semver string)
- Describe the change in your commit message using the `improve:` prefix
- If the change is a breaking modification to the skill's behavior, note it in the PR description
- If you move or rename a skill, re-run `python scripts/gen_marketplace.py` and commit the updated `.claude-plugin/marketplace.json`

## Skill Quality Standards

Every skill must clear this bar (enforced by `python scripts/audit_skills.py` + `uv run pytest tests/`):

- **`name`** equals the parent directory, lowercase-hyphen, ≤ 64 chars, and contains no reserved word (`claude`/`anthropic`).
- **`description`** (the field that decides whether Claude triggers the skill) is **third person**, leads with *what* the skill does, includes an explicit **"Use when …"** trigger clause packed with keywords a user's request would contain, and ends with `Part of the AlterLab Academic Skills suite.` — never leads with it. ≤ 1024 chars, no changelog/version noise.
- **Disambiguate** against overlapping siblings ("For X prefer Y") so the right skill loads.
- **Body** under ~500 lines; move long detail into `references/*.md` (loaded on demand). Cited `references/` and `scripts/` paths must exist.
- **No fabrication**: real APIs, real citations/DOIs, no unsourced vendor benchmarks; if a script sends data to a third-party API, say so.
- **`allowed-tools`** scoped to what the skill needs (space-separated).
- Add **`evals/evals.json`** (≥ 3 `should_trigger` + ≥ 1 near-miss `should_not_trigger`); validate with `python scripts/run_evals.py`.

A copy-paste scaffold lives in [`template/`](template/).

## Reporting Issues

Open a GitHub issue with:

- The skill name and category
- Steps to reproduce the problem
- Expected vs. actual behavior
- Claude model version used (if relevant)

## Questions?

Open a discussion or issue on the repository. We welcome suggestions for new categories, skill improvements, and documentation enhancements.
