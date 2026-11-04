<div align="center">
<img src=".github/header-banner.svg" width="100%" alt="AlterLab Academic Skills">
<br>

<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Skills-241-7C3AED?style=for-the-badge&logo=bookstack&logoColor=white" alt="Skills: 241"></a>
<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Domains-18-2563EB?style=for-the-badge&logo=databricks&logoColor=white" alt="Domains: 18"></a>
<a href="docs/behavioral-results.md"><img src="https://img.shields.io/badge/Evaluated%20live-241%2F241-F97316?style=for-the-badge&logo=anthropic&logoColor=white" alt="Evaluated live: 241/241"></a>
<a href="#-what-is-this"><img src="https://img.shields.io/badge/API%20keys-none%20required-0EA5E9?style=for-the-badge&logo=keepassxc&logoColor=white" alt="API keys: none required"></a>

<br>

<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases"><img src="https://img.shields.io/github/v/release/AlterLab-IEU/AlterLab-Academic-Skills?style=for-the-badge&logo=github&color=8B5CF6&logoColor=white&label=Release" alt="Release"></a>
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/actions/workflows/pytest.yml"><img src="https://img.shields.io/github/actions/workflow/status/AlterLab-IEU/AlterLab-Academic-Skills/pytest.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=tests" alt="Tests"></a>
<a href="#-licensing"><img src="https://img.shields.io/badge/License-MIT%20repo%20%2B%20per--skill-10B981?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License: MIT repository, per-skill licenses"></a>
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/stargazers"><img src="https://img.shields.io/github/stars/AlterLab-IEU/AlterLab-Academic-Skills?style=for-the-badge&logo=github&color=EAB308&logoColor=white" alt="Stars"></a>
<a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-Welcome-22C55E?style=for-the-badge&logo=git&logoColor=white" alt="PRs welcome"></a>

<br><br>

**Read in:** [English](README.md) · [Türkçe](README.tr-TR.md)

<br>

<h3>🎓 241 Claude Agent Skills for faculty and researchers</h3>

<p><em>From the research question to the submitted paper — research, writing, review, citation integrity,<br>scientific databases and the Turkish academic system. No API key, no third-party login.</em></p>

<p>
<b>Research pipeline</b> · <b>Citation integrity</b> · <b>38 scientific databases</b> · <b>Bioinformatics</b> · <b>Statistics & methods</b> · <b>Social science</b> · <b>YÖK · ÜAK · TÜBİTAK</b>
</p>

<p>
<a href="#-quick-start"><b>Quick start »</b></a> ·
<a href="#-where-do-i-start">Where do I start?</a> ·
<a href="#-what-has-been-checked-and-what-has-not">What has been checked</a> ·
<a href="docs/CATALOG.md">Full catalog</a> ·
<a href="https://alterlab-ieu.github.io/AlterLab-Academic-Skills/">Search the skills</a> ·
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/issues">Report a bug</a>
</p>

<br>

<hr>

<table><tr><td>
<b>Built by</b> <a href="https://github.com/AlterLab-IEU"><b>AlterLab Creative Technologies Laboratory</b></a>, Izmir University of Economics (IEU)
<br><br>
<em>Install as Claude Code plugins, upload to the Claude app, or copy into any Agent Skills runtime.</em>
</td></tr></table>

</div>

<br>

<div align="center">
<table>
<tr>
<td align="center" width="25%">
<h3>🔑</h3>
<h3>Keyless</h3>
<p>No API key, account or login.<br>A key only adds extras.</p>
</td>
<td align="center" width="25%">
<h3>🧪</h3>
<h3>Evaluated live</h3>
<p>All 241 skills tested:<br><b>90%</b> pass with the skill,<br>52% without.</p>
</td>
<td align="center" width="25%">
<h3>🔎</h3>
<h3>Integrity first</h3>
<p>Every reference checked<br>in five open indexes;<br>unchecked never passes.</p>
</td>
<td align="center" width="25%">
<h3>🇹🇷</h3>
<h3>Turkish academia</h3>
<p>YÖK, ÜAK doçentlik (all<br>12 fields), DergiPark,<br>TÜBİTAK ARDEB & BİDEB.</p>
</td>
</tr>
</table>
</div>

<br>

## 📋 Table of contents

<details open>
<summary><b>Click to expand / collapse</b></summary>
<br>

- [🧬 What is this?](#-what-is-this)
- [🚀 Quick start](#-quick-start)
- [🧭 Where do I start?](#-where-do-i-start)
- [💡 Using it](#-using-it)
- [✅ What has been checked, and what has not](#-what-has-been-checked-and-what-has-not)
- [📚 Domains](#-domains)
- [🔎 Integrity tools: what they establish](#-integrity-tools-what-they-establish)
- [🔬 Check it yourself](#-check-it-yourself)
- [🔗 Sister projects](#-sister-projects)
- [📜 Licensing](#-licensing)
- [📝 Cite](#-cite)
- [🤝 Contributing and credits](#-contributing-and-credits)

</details>

<br>

## 🧬 What is this?

AlterLab Academic Skills is a library of [Agent Skills](https://agentskills.io) for academic work:
literature review, manuscript writing and review, citation checking, research design and
statistics, scientific databases and toolkits, and the Turkish academic system (YÖK, ÜAK,
DergiPark, TÜBİTAK). Each skill is a `SKILL.md` instruction file, usually with reference
documents and small helper scripts, that gives Claude a method for one kind of task.

Every skill does what it claims with **no external API key, account or login**: Claude's own
tools, keyless public APIs and local libraries. A credential may only add something (your own
private account, a higher rate limit, a paid service you ask for by name), and each one is
declared in the skill's `metadata.credentials`. `scripts/check_keyless.py` enforces this in CI.

> [!IMPORTANT]
> Treat what a skill produces the way you would treat a capable research assistant's draft:
> useful, and something you check. The skills ask Claude to cite sources and to disclose AI
> assistance, but they do not make its output correct, complete, or ready to submit.

Built for faculty and researchers. Student skills live in the sister project
[AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills).

<br>

## 🚀 Quick start

### Option 1 — Claude Code plugins *(recommended)*

Validated with `claude plugin validate`:

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

### Option 2 — claude.ai / the Claude app

Upload one skill at a time: download `skill-<name>-<version>.zip` from
[Releases](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases) and use
Customize ▸ Skills ▸ Upload a skill (code execution must be on). These archives carry the
skill's shared files and license notices and drop frontmatter the uploader is reported to
reject; skills that need a companion skill say so in the release notes. Packaging is tested
here; acceptance by the live uploader is not. The `alterlab-<domain>-<version>.zip` archives
are not uploads — unzip them into a skills directory.

### Option 3 — Plain install or another agent

Into the Claude Code skills directory or the cross-tool `~/.agents/skills/` (needs `python3`).
Skills a selected skill depends on are installed with it (`--no-deps` to skip):

```bash
git clone https://github.com/AlterLab-IEU/AlterLab-Academic-Skills.git && cd AlterLab-Academic-Skills
scripts/install.sh --list
scripts/install.sh core/alterlab-citation-verifier      # one skill (+ its dependencies)
scripts/install.sh turkish-academia                     # a domain
```

The skills follow the open Agent Skills format; [`docs/portability.md`](docs/portability.md)
lists what carries over to other agents and what is Claude-Code-specific. Other runtimes have
not been tested here.

<br>

## 🧭 Where do I start?

You do not need skill names: describe the task, and `alterlab-skill-finder` picks one and says
which and why. If you want a starting point anyway:

| Your situation | Say something like | Skill |
|:---|:---|:---|
| A topic, but no clear question yet | *"Help me turn this into a researchable question"* | `alterlab-deep-research` (Socratic mode) |
| Notes and sources, and a paper to write | *"Plan my paper chapter by chapter"* | `alterlab-paper-writer` (plan mode) |
| A manuscript before submission | *"Review this like a journal panel would"* | `alterlab-paper-reviewer` |
| A bibliography you are not sure of | *"Check that every reference exists and is not retracted"* | `alterlab-citation-verifier` |
| A systematic review to run | *"Set up a PRISMA search and screening plan"* | `alterlab-literature-review` |
| Data, and a test to choose | *"Which test fits this design, and what does it assume?"* | `alterlab-test-selection-guard` |
| A study to pre-register | *"Draft a pre-registration I can freeze"* | `alterlab-preregistration-discipline` |
| A doçentlik application ahead | *"Do my publications meet the ÜAK criteria for my field?"* | `alterlab-docentlik-eligibility` |
| A TÜBİTAK proposal or fellowship | *"Draft the 1001 proposal"* · *"Which BİDEB programme fits me?"* | `alterlab-tubitak-proposal` · `alterlab-tubitak-bideb` |
| A course to (re)design | *"Write an AI-use policy for my syllabus"* | `alterlab-syllabus-ai-policy` |
| Reviewer comments to answer | *"Draft a point-by-point response"* | `/alterlab-workflows:rebuttal` |

Every skill, by domain: [`docs/CATALOG.md`](docs/CATALOG.md).

<br>

## 💡 Using it

Describe the task, or say *"use AlterLab skills"*, and `alterlab-skill-finder` picks a skill
and says which and why. In Claude Code, the `alterlab-workflows` plugin adds seven multi-agent
workflows:

| Command | What it does |
|---|---|
| `/alterlab-workflows:citation-audit` | resolves references against Crossref / Semantic Scholar / Europe PMC / arXiv and checks up to 150 cited claims against their sources; flags need two completed re-checks |
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

<br>

## ✅ What has been checked, and what has not

| Level | Status |
|---|---|
| Skills with a structurally valid eval file | **241 / 241** — 1,598 cases, checked in CI on every PR (schema and trigger coverage only; no model is called) |
| Eval cases that supply input files | 145 cases in 85 skills, plus the benchmark fixtures below |
| Skills evaluated behaviorally against a live model | **241 / 241** — every eval case answered once with the skill and once without it, through the Claude Code CLI login with no API key (2026-10-15 to 2026-11-04): 1,532 cases graded, 50 not runnable here (they need a key, connector, host or program the runner lacks). Results, method and limits: [`docs/behavioral-results.md`](docs/behavioral-results.md). (The nightly CI job that was meant to grade them graded nothing for weeks: its API key was missing and failures were reported as success. It has been removed, and a run that grades nothing now exits non-zero.) |
| Skills shown to beat the bare model | On the same 1,532 graded cases, **90%** of answers with the skill passed against **52%** without it; the skill turned a bare FAIL into a PASS on 571 cases and the reverse on 2. The skilled answer faces more checks, grading reads only the final message, each case ran once, and a Claude model is the judge. Of the five benchmark tasks below, **1** beat the bare model (doçentlik pre-screening); on the other four the bare model was already at or near the ceiling. |
| Helper scripts | unit-tested: input validation, reference values, and fault paths (see `tests/`) |
| Dynamic workflows (`/alterlab-workflows:*`) | dry-run against a mocked runtime, including injected failures; not run live |
| Skill auto-selection (activation) | a harness exists (`run_evals.py --activation`); no current recorded run |

<details>
<summary><b>Five-task benchmark</b> (deterministic scoring, no LLM judge)</summary>
<br>

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

</details>

<br>

## 📚 Domains

| | Domain | Skills | | Domain | Skills |
|:---:|---|---:|:---:|---|---:|
| 🧭 | Core pipeline | 10 | 🧫 | Lab integrations | 9 |
| 🗄️ | Databases | 38 | 🛰️ | Domain-specific | 18 |
| 🧬 | Bioinformatics | 38 | 📄 | Document tools | 3 |
| ⚗️ | Cheminformatics | 12 | 🔍 | Research tools | 14 |
| 🩺 | Clinical research | 7 | 💹 | Finance & economics | 7 |
| 📊 | Data science | 22 | 🇹🇷 | Turkish academia | 13 |
| 📈 | Visualization | 9 | 🏛️ | Faculty life | 6 |
| ✍️ | Writing tools | 14 | 📐 | Methodology | 3 |
| 🧑‍🤝‍🧑 | Social-science workflow | 17 | 🔁 | Research workflows | 1 + 7 workflows |

Every skill, by domain: [`docs/CATALOG.md`](docs/CATALOG.md) ·
searchable: [alterlab-ieu.github.io/AlterLab-Academic-Skills](https://alterlab-ieu.github.io/AlterLab-Academic-Skills/)
· machine-readable: [`skills.json`](skills.json).

<br>

## 🔎 Integrity tools: what they establish

- **`alterlab-citation-verifier`** checks that references exist and that their metadata
  agrees with Crossref, Semantic Scholar, Europe PMC, arXiv (Open Library for books), and doi.org,
  and flags retractions.
  An entry it could not check is `unverified`, never a pass; input it could not parse makes the
  run `PARTIAL` (exit 3), never a pass.
- **`claim_faithfulness.py`** compares a claim with the cited work's **abstract only**. It
  never reports a claim as verified: a heuristic match is `LEXICAL_MATCH_REQUIRES_REVIEW`, a
  model judgment is `MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW`, and guards make it abstain on
  wrong figures, reversed comparisons, population mismatches, and tentative evidence. Read the
  cited passage before treating a claim as supported. See [`docs/integrity.md`](docs/integrity.md).

<br>

## 🔬 Check it yourself

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

<br>

## 🔗 Sister projects

| | Project | For | Skills |
|:---:|:---|:---|:---:|
| 🎓 | [AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills) | Communication students: PR & advertising, cinema, new media, GenAI production, visual design, research methods | 72 |
| 🎮 | [AlterLab_GameForge](https://github.com/AlterLab-IEU/AlterLab_GameForge) | Indie game development, from concept to launch | 34 |

<br>

## 📜 Licensing

The repository is MIT-licensed, but each skill's content is under the license in its own
`license:` frontmatter field, and those differ: 201 MIT, 19 Apache-2.0, 4 CC-BY-NC-4.0,
4 GPL-3.0, 2 GPL-2.0, 1 LGPL-3.0, 1 CeCILL-2.1, 2 BSD-3-Clause, 2 CC-BY-4.0, 1 CC-BY-3.0,
4 CC0-1.0. The four core pipeline skills (`alterlab-deep-research`, `alterlab-paper-writer`,
`alterlab-paper-reviewer`, `alterlab-research-pipeline`) are **non-commercial** (CC-BY-NC-4.0,
from their upstream). Check a skill's license before redistributing it or using it
commercially. Every installed or packaged skill carries `LICENSE`, `NOTICE`, and
`THIRD_PARTY_NOTICES.md`; lineage is in [`PROVENANCE.md`](PROVENANCE.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

<br>

## 📝 Cite

```bibtex
@software{alterlab_academic_skills_2026,
  title   = {AlterLab Academic Skills},
  author  = {{AlterLab Creative Technologies Laboratory, Izmir University of Economics (IEU)}},
  year    = {2026},
  version = {4.0.0},
  url     = {https://github.com/AlterLab-IEU/AlterLab-Academic-Skills}
}
```

[`CITATION.cff`](CITATION.cff) has the full metadata. Release history is in
[`CHANGELOG.md`](CHANGELOG.md).

<br>

## 🤝 Contributing and credits

Contributions are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md). Behavioral evidence
(new benchmark cases with anchored answers, or a recorded run of a skill's evals) is the most
useful contribution right now.

```bash
git checkout -b improve/alterlab-citation-verifier
# edit skills/core/alterlab-citation-verifier/SKILL.md, then run the checks above
git commit -m "improve: alterlab-citation-verifier — <what changed>"
```

The suite began as a content fork of K-Dense's
[scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) (MIT) and
adapts the core research pipeline from Cheng-I Wu's
[academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
(CC-BY-NC 4.0).

<br>

<div align="center">

<b>Built by <a href="https://github.com/AlterLab-IEU">AlterLab Creative Technologies Laboratory</a></b>

<br><br>

<b>241 skills · 18 domains · every one evaluated live, none needing a key</b>

<br><br>

<hr>

<sub>If you find this project useful, please consider giving it a ⭐</sub>
<br>
<a href="#">⬆ Back to top</a>

</div>

<br>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,9,5&height=100&section=footer" width="100%" alt="Footer">
