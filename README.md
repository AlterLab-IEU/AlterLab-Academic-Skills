<div align="center">
<img src=".github/header-banner.svg" width="100%" alt="AlterLab Academic Skills">
<br>

<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Skills-242-7C3AED?style=for-the-badge&logo=bookstack&logoColor=white" alt="Skills: 242"></a>
<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Domains-18-2563EB?style=for-the-badge&logo=databricks&logoColor=white" alt="Domains: 18"></a>
<a href="#licensing"><img src="https://img.shields.io/badge/License-MIT%20repo%20%2B%20per--skill-10B981?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License: MIT repository, per-skill licenses"></a>
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases"><img src="https://img.shields.io/github/v/release/AlterLab-IEU/AlterLab-Academic-Skills?style=for-the-badge&logo=github&color=8B5CF6&logoColor=white&label=Release" alt="Release"></a>
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/actions/workflows/pytest.yml"><img src="https://img.shields.io/github/actions/workflow/status/AlterLab-IEU/AlterLab-Academic-Skills/pytest.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=tests" alt="Tests"></a>

**Read in:** [English](README.md) · [Türkçe](README.tr-TR.md)

### 242 skills · 18 domains — Claude Agent Skills for faculty and researchers

</div>

AlterLab Academic Skills is a library of [Agent Skills](https://agentskills.io) for academic work:
literature review, manuscript writing and review, citation checking, research design and
statistics, scientific databases and toolkits, and the Turkish academic system (YÖK, ÜAK,
DergiPark, TÜBİTAK). Each skill is a `SKILL.md` instruction file, usually with reference
documents and small helper scripts, that gives Claude a method for one kind of task.

Treat what a skill produces the way you would treat a capable research assistant's draft:
useful, and something you check. The skills ask Claude to cite sources and to disclose AI
assistance, but they do not make its output correct, complete, or ready to submit.

Built by [AlterLab Creative Technologies Laboratory](https://github.com/AlterLab-IEU) for
faculty and researchers (student skills live in
[AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills)).

## What has been checked, and what has not

| Level | Status |
|---|---|
| Skills with a structurally valid eval file | **242 / 242** — 1,535 cases, checked in CI on every PR (schema and trigger coverage only; no model is called) |
| Eval cases that supply input files | 6 cases in 5 skills, plus the benchmark fixtures below |
| Skills evaluated behaviorally against a live model | **5** — the five benchmark tasks below. The other 237 skills have no recorded behavioral result. (The nightly CI job that was meant to grade them graded nothing for weeks: its API key was missing and failures were reported as success. It has been removed, and a run that grades nothing now exits non-zero.) |
| Skills shown to beat the bare model | **1 of 5** benchmark tasks (doçentlik pre-screening). On the other four the bare model was already at or near the ceiling. |
| Helper scripts | unit-tested: input validation, reference values, and fault paths (see `tests/`) |
| Dynamic workflows (`/alterlab-workflows:*`) | dry-run against a mocked runtime, including injected failures; not run live |
| Skill auto-selection (activation) | a harness exists (`run_evals.py --activation`); no current recorded run |

### Benchmark

Five tasks, each with a standard case, a difficult-negative case, and an incomplete-input case;
the model labels every item and a script scores the labels against expected answers with
evidence anchors (no LLM judge). Both arms run in isolated workspaces with the same tools; the
skilled arm also gets the skill. Model `claude-opus-5-5` through the Claude Code CLI,
2 runs per arm, 2026-10-14.

| Task (skill) | Correct — skill | Correct — bare | False approvals / accusations — skill | — bare |
|---|---:|---:|---:|---:|
| citation-integrity (`alterlab-citation-verifier`) | 56/56 | 55/56 | 0 / 0 | 0 / 0 |
| manuscript-review (`alterlab-paper-reviewer`) | 40/40 | 40/40 | 0 / 0 | 0 / 0 |
| screening (`alterlab-research-workflows`) | 38/38 | 38/38 | 0 / 0 | 0 / 0 |
| analysis-check (`alterlab-test-selection-guard`) | 30/32 | 30/32 | 2 / 0 | 2 / 0 |
| docentlik (`alterlab-docentlik-eligibility`) | **41/42** | 30/42 | 0 / 0 | 2 / 0 |
| **All five** | **205/208** | 193/208 | 2 / 0 | 4 / 0 |

The skilled arm cost about 39% more (CLI-reported) and took about 24% longer. The two false approvals with the skill are one borderline analysis item that both arms missed identically.

Read these as small-sample results on synthetic fixtures, not as validation of the catalog.
Full results, per-item errors, method and limitations:
[`docs/benchmark-results.md`](docs/benchmark-results.md).

## Install

**Claude Code (plugins)** — validated with `claude plugin validate`:

```bash
/plugin marketplace add AlterLab-IEU/AlterLab-Academic-Skills
/plugin install alterlab-essentials@alterlab-academic-skills   # starter set, or any single domain:
/plugin install alterlab-turkish-academia@alterlab-academic-skills
/reload-plugins
```

Domain plugins: `alterlab-core`, `-databases`, `-bioinformatics`, `-cheminformatics`,
`-clinical-research`, `-data-science`, `-visualization`, `-writing-tools`, `-lab-integrations`,
`-domain-specific`, `-document-tools`, `-research-tools`, `-finance-economics`,
`-turkish-academia`, `-faculty-life`, `-methodology`, `-social-science-workflow`, `-workflows`;
bundles `alterlab-essentials` and `alterlab-complete`.

**Plain install** (Claude Code skills directory or the cross-tool `~/.agents/skills/`; needs
`python3`). Skills a selected skill depends on are installed with it (`--no-deps` to skip):

```bash
git clone https://github.com/AlterLab-IEU/AlterLab-Academic-Skills.git && cd AlterLab-Academic-Skills
scripts/install.sh --list
scripts/install.sh core/alterlab-citation-verifier      # one skill (+ its dependencies)
scripts/install.sh turkish-academia                     # a domain
```

**claude.ai / Claude app** — upload one skill at a time: download `skill-<name>-<version>.zip`
from [Releases](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases) and use
Customize ▸ Skills ▸ Upload a skill (code execution must be on). These archives carry the
skill's shared files and license notices and drop frontmatter the uploader is reported to
reject; skills that need a companion skill say so in the release notes. Packaging is tested
here; acceptance by the live uploader is not. The `alterlab-<domain>-<version>.zip` archives
are not uploads — unzip them into a skills directory.

**Other agents** — the skills follow the open Agent Skills format;
[`docs/portability.md`](docs/portability.md) lists what carries over and what is
Claude-Code-specific. Other runtimes have not been tested here.

## Using it

You do not need skill names. Describe the task, or say *"use AlterLab skills"*, and
`alterlab-skill-finder` picks a skill and says which and why. In Claude Code, the
`alterlab-workflows` plugin adds seven multi-agent workflows:

| Command | What it does |
|---|---|
| `/alterlab-workflows:citation-audit` | resolves references against Crossref / OpenAlex / Semantic Scholar / arXiv and checks up to 150 cited claims against their sources; flags need two completed re-checks |
| `/alterlab-workflows:review-panel` | a panel of separate reviewers; each major concern is re-checked against the manuscript, and one whose check did not complete reaches the editor labelled unverified |
| `/alterlab-workflows:claim-stress-test` | three critics per headline claim; calibrated rewrites |
| `/alterlab-workflows:systematic-review-screening` | PRISMA 2020 title/abstract screening with two screeners per record and adjudication; records whose screening failed are kept and reported as unresolved |
| `/alterlab-workflows:rebuttal` | point-by-point response to reviewers with a consistency pass |
| `/alterlab-workflows:grant-mock-panel` | mock review on the funder's own criteria (NIH, NSF, ERC, Horizon Europe, TÜBİTAK) |
| `/alterlab-workflows:literature-map` | themes, landmark works, and gaps checked against existing answers |

Every workflow returns `status: complete | partial | blocked` with a coverage account
(requested, completed, failed, unresolved) and returns a report path only after the report
file has been read back. Separate agents of the same model avoid anchoring on each other but are
not independent verification, and the reports say so.

## Integrity tools: what they establish

- **`alterlab-citation-verifier`** checks that references exist and that their metadata
  agrees with Crossref, OpenAlex, Semantic Scholar, arXiv, and doi.org, and flags retractions.
  An entry it could not check is `unverified`, never a pass; input it could not parse makes the
  run `PARTIAL` (exit 3), never a pass.
- **`claim_faithfulness.py`** compares a claim with the cited work's **abstract only**. It
  never reports a claim as verified: a heuristic match is `LEXICAL_MATCH_REQUIRES_REVIEW`, a
  model judgment is `MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW`, and guards make it abstain on
  wrong figures, reversed comparisons, population mismatches, and tentative evidence. Read the
  cited passage before treating a claim as supported. See [`docs/integrity.md`](docs/integrity.md).

## Domains

| Domain | Skills | Domain | Skills |
|---|---:|---|---:|
| Core pipeline | 10 | Lab integrations | 9 |
| Databases | 39 | Domain-specific | 18 |
| Bioinformatics | 38 | Document tools | 3 |
| Cheminformatics | 12 | Research tools | 14 |
| Clinical research | 7 | Finance & economics | 7 |
| Data science | 22 | Turkish academia | 13 |
| Visualization | 9 | Faculty life | 6 |
| Writing tools | 14 | Methodology | 3 |
| Social-science workflow | 17 | Research workflows | 1 + 7 workflows |

Every skill, by domain: [`docs/CATALOG.md`](docs/CATALOG.md) ·
searchable: [alterlab-ieu.github.io/AlterLab-Academic-Skills](https://alterlab-ieu.github.io/AlterLab-Academic-Skills/)
· machine-readable: [`skills.json`](skills.json).

## Check it yourself

```bash
uv run --frozen pytest tests/ -q                       # the validation suite
uv run python scripts/run_evals.py --strict            # eval-file structure (static)
uv run python scripts/run_evals.py --behavioral --skill alterlab-docentlik-eligibility
uv run python scripts/run_benchmark.py                 # the five-task benchmark
```

The live commands use the `claude` CLI's own login, so they run inside an authenticated
Claude Code environment; each run writes JSON results to `eval-results/`. A behavioral run
exits `0` only if every selected case produced a verdict and passed. See
[`docs/evals.md`](docs/evals.md).

## Licensing

The repository is MIT-licensed, but each skill's content is under the license in its own
`license:` frontmatter field, and those differ: 202 MIT, 19 Apache-2.0, 4 CC-BY-NC-4.0,
4 GPL-3.0, 2 GPL-2.0, 1 LGPL-3.0, 1 CeCILL-2.1, 2 BSD-3-Clause, 2 CC-BY-4.0, 1 CC-BY-3.0,
4 CC0-1.0. The four core pipeline skills (`alterlab-deep-research`, `alterlab-paper-writer`,
`alterlab-paper-reviewer`, `alterlab-research-pipeline`) are **non-commercial** (CC-BY-NC-4.0,
from their upstream). Check a skill's license before redistributing it or using it
commercially. Every installed or packaged skill carries `LICENSE`, `NOTICE`, and
`THIRD_PARTY_NOTICES.md`; lineage is in [`PROVENANCE.md`](PROVENANCE.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Cite

```bibtex
@software{alterlab_academic_skills_2026,
  title   = {AlterLab Academic Skills},
  author  = {{AlterLab Creative Technologies Laboratory, Izmir University of Economics (IEU)}},
  year    = {2026},
  version = {3.0.1},
  url     = {https://github.com/AlterLab-IEU/AlterLab-Academic-Skills}
}
```

[`CITATION.cff`](CITATION.cff) has the full metadata. Release history is in
[`CHANGELOG.md`](CHANGELOG.md).

## Contributing and credits

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). Behavioral evidence
(new benchmark cases with anchored answers, or a recorded run of a skill's evals) is the most
useful contribution right now.

The suite began as a content fork of K-Dense's
[scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) (MIT) and
adapts the core research pipeline from Cheng-I Wu's
[academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
(CC-BY-NC 4.0). Sister projects:
[AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills) (communication
students) and [AlterLab_GameForge](https://github.com/AlterLab-IEU/AlterLab_GameForge) (game
development).
