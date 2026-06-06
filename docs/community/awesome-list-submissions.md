# Awesome-list submissions

Tracking and drafts for submitting **AlterLab Academic Skills** to the major Claude/Agent-Skills
"awesome" indices. The suite is currently absent from the four lists below; this file holds
ready-to-paste entries in each list's native format, plus a correction note for the one list that
already features us with a stale count.

Canonical facts to cite (keep these in sync with the repo):

- **Name:** AlterLab Academic Skills
- **Repo:** https://github.com/AlterLab-IEU/AlterLab-Academic-Skills
- **Count:** **183 skills across 13 research domains**
- **One-liner:** Turn an AI agent into a domain-specific academic research expert — 183 skills with
  executable evals, citation/integrity audits, and bilingual (EN/TR) docs; installable as a Claude
  Code plugin and via the open Agent Skills standard.
- **License:** MIT
- **Author:** AlterLab Creative Technologies Laboratory, Izmir University of Economics (IEU)

---

## 1. ComposioHQ/awesome-claude-skills

- **Repo:** https://github.com/ComposioHQ/awesome-claude-skills
- **Format:** Markdown bullet under the relevant category section: `- [Name](link) - description.`
- **Status:** not listed — submit via PR adding the bullet to the most fitting section (research /
  science / collections).

**Entry to add:**

```markdown
- [AlterLab Academic Skills](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills) - 183 skills across 13 research domains that turn an AI agent into a domain-specific academic research expert (literature review, paper writing/review, citation & integrity verification, bioinformatics, cheminformatics, data science, and more). Ships executable evals per skill, license/citation audits, per-domain installable bundles, and bilingual EN/TR docs. MIT.
```

---

## 2. hesreallyhim/awesome-claude-code

- **Repo:** https://github.com/hesreallyhim/awesome-claude-code
- **Format:** entries are managed through `THE_RESOURCES_TABLE.csv` plus the `templates/` flow —
  do **not** hand-edit the rendered README. Follow the repo's contribution template/PR process.
- **Status:** not listed — submit a resource-addition PR using their template.

**Field values for the resource template:**

| Field | Value |
|---|---|
| Display Name | AlterLab Academic Skills |
| Primary Link | https://github.com/AlterLab-IEU/AlterLab-Academic-Skills |
| Category | Skills (collection) |
| Author Name | AlterLab Creative Technologies Laboratory (IEU) |
| Author Link | https://github.com/AlterLab-IEU |
| License | MIT |
| Description | 183 academic research skills across 13 domains for Claude Code and the open Agent Skills standard, with executable evals, citation/integrity audits, per-domain bundles, and bilingual EN/TR docs. |

---

## 3. VoltAgent/awesome-claude-code-subagents

- **Repo:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **Format:** a collection of specialized **subagents**; entries are Markdown bullets grouped by
  category.
- **Status:** not listed. **Caveat:** this list is subagent-centric. AlterLab's relevance here is
  the **35 core research agents** registered in the plugin surface (e.g. bibliography, integrity
  verification, source verification, socratic mentor) rather than the full 183-skill catalog —
  frame the submission around the agents, not the skills, so it fits the list's scope.

**Entry to add (under a Research/Academic section):**

```markdown
- [AlterLab Academic research agents](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills) - A set of academic research subagents bundled in the AlterLab Academic Skills plugin: literature search, bibliography building, citation-existence & claim-faithfulness verification, peer-review, and Socratic research mentoring. Part of a 183-skill, 13-domain suite. MIT.
```

---

## 4. InternScience/Awesome-Scientific-Skills

- **Repo:** https://github.com/InternScience/Awesome-Scientific-Skills
- **Format:** curated collection of scientific Agent Skills; Markdown listing.
- **Status:** not listed — the closest-fit index to AlterLab's content. Note the shared lineage:
  both AlterLab and InternScience's collection sit in the scientific Agent-Skills ecosystem seeded
  by K-Dense's work; the submission should be transparent about AlterLab being a content fork of
  [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
  re-aimed at the academic-faculty audience (see [`PROVENANCE.md`](../../PROVENANCE.md)).

**Entry to add:**

```markdown
- [AlterLab Academic Skills](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills) - 183 Agent Skills across 13 research domains, re-aimed at the academic faculty / research-lifecycle audience. Content fork of scientific-agent-skills, extended with executable evals on every skill, deterministic citation-existence & integrity gates, script-correctness CI, per-domain installable bundles, and bilingual EN/TR docs. MIT.
```

---

## Correction note — BehiSecc/awesome-claude-skills

- **Repo:** https://github.com/BehiSecc/awesome-claude-skills
- **Status:** AlterLab is **already featured** here (the repo README's "Featured in" badge points
  to this list). The listing, however, advertises an inflated skill count of **"186+"**.
- **Correction needed:** the accurate, CI-verified count is **183 skills** (183 `SKILL.md` files;
  the marketplace and READMEs are gated to this number). Open a PR or issue on BehiSecc's list
  updating the AlterLab entry from "186+" to **"183 skills across 13 domains"**.

**Suggested corrected entry text:**

```markdown
- [AlterLab Academic Skills](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills) - 183 academic research skills across 13 domains, with executable evals, citation/integrity audits, and bilingual EN/TR docs. MIT.
```

> Also worth flagging in the same PR: confirm the star/recency metadata if the list tracks it — the
> count was the load-bearing inaccuracy.

---

## Submission checklist

- [ ] ComposioHQ — PR opened
- [ ] hesreallyhim — resource PR opened (CSV/template flow)
- [ ] VoltAgent — PR opened (agents framing)
- [ ] InternScience — PR opened (provenance disclosed)
- [ ] BehiSecc — correction PR/issue opened ("186+" → 183)

When a submission lands, link the merged PR next to its checkbox and, if a list shows a badge,
ensure the README "Featured in" row reflects it.
