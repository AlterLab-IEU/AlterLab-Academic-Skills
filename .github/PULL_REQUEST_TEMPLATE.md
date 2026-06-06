## Summary

<!-- Briefly describe what this PR changes and why. One skill per PR unless closely related. -->

## Type of change

- [ ] New skill (`feat: add <skill-name>`)
- [ ] Skill improvement (`improve: <skill-name> — <what changed>`)
- [ ] Bug fix (`fix: <skill-name> — <what was wrong>`)
- [ ] Docs / chore

## Authoring checklist

<!-- For skill PRs, every box below is CI-enforced. For docs/chore PRs, tick what applies. -->

- [ ] **Evals shipped** — `evals/evals.json` with **≥3 `should_trigger`** + **≥1 near-miss `should_not_trigger`**, green under `uv run python scripts/run_evals.py --strict`. No `known_failures` entry for new work.
- [ ] **Body ≤500 lines** — long detail moved to `references/*.md`; every cited `references/`/`scripts/` path exists.
- [ ] **Description ≤1024 chars** — third person, leads with *what* it does, has an explicit "Use when …" trigger clause, ends with `Part of the AlterLab Academic Skills suite.`
- [ ] **Frontmatter valid** — `name` == folder name (no `claude`/`anthropic`), `license` from the controlled vocabulary, `metadata.skill-author: AlterLab`, quoted `metadata.version`, `allowed-tools` space-separated and scoped.
- [ ] **No fabrication** — real APIs, real citations/DOIs, no unsourced vendor benchmarks; third-party data egress disclosed.
- [ ] **Disambiguated** against overlapping sibling skills.
- [ ] `uv run python scripts/audit_skills.py` and `uv run pytest tests/` pass cleanly.
- [ ] **Marketplace regenerated** if a skill was added / moved / renamed (`uv run python scripts/gen_marketplace.py`, committed).
- [ ] **Version bumped** (`metadata.version`) for modified skills.

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) and [`docs/evals.md`](../docs/evals.md) for the full bar.
