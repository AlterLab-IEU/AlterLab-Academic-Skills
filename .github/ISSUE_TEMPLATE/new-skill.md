---
name: New skill (authoring checklist)
about: Track a new skill you intend to author and submit. Use the authoring checklist before opening the PR.
title: "[new-skill] alterlab-<name>"
labels: ["enhancement", "new-skill"]
assignees: []
---

## Skill

- **Name:** `alterlab-<name>` (lowercase-hyphen, must equal the folder name; no `claude`/`anthropic`)
- **Domain / category:** <!-- bioinformatics, cheminformatics, core, data-science, databases, document-tools, domain-specific, finance-economics, lab-integrations, research-tools, visualization, writing-tools -->
- **What it does (one line):**
- **When it should trigger ("Use when …"):**

## Authoring checklist (CI-enforced — all required before the PR merges)

- [ ] **Evals shipped day one.** `evals/evals.json` exists with **≥3 `should_trigger`** cases and **≥1 near-miss `should_not_trigger`** case, green under `uv run python scripts/run_evals.py --strict`. (No `known_failures` entry — that table is for pre-existing debt only.)
- [ ] **Body ≤500 lines.** Long detail (API tables, templates, worked examples) lives in `references/*.md`, cited by relative path; every cited path exists.
- [ ] **Description ≤1024 chars**, third person, leads with *what* it does, includes an explicit "Use when …" trigger clause, ends with `Part of the AlterLab Academic Skills suite.`
- [ ] **Frontmatter valid:** `name` == folder name, `license` from the controlled vocabulary, `metadata.skill-author: AlterLab`, quoted `metadata.version`, `allowed-tools` space-separated and scoped.
- [ ] **No fabrication:** real APIs, real citations/DOIs, no unsourced vendor benchmarks; any third-party data egress is disclosed.
- [ ] **Disambiguated** against overlapping siblings ("For X prefer Y").
- [ ] `uv run python scripts/audit_skills.py` and `uv run pytest tests/` pass cleanly.
- [ ] **Marketplace regenerated** if a skill was added/moved/renamed (`uv run python scripts/gen_marketplace.py`).

## Notes

<!-- External APIs/services, data resources and their terms, fallbacks, anything reviewers should know. -->
