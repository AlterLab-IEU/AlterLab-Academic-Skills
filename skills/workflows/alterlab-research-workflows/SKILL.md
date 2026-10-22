---
name: alterlab-research-workflows
description: "Runs AlterLab's packaged multi-agent academic workflows — citation audit, peer-review panel of separate reviewers, claim stress-test, PRISMA dual-screening for systematic reviews, point-by-point rebuttal, grant mock panel, and literature map. In Claude Code they run as dynamic workflows (/alterlab-workflows:<name>) with separate agent contexts, adversarial re-checks, tallies computed in code, and an explicit complete/partial/blocked status; on claude.ai, the API, or anywhere without the Workflow runtime this skill runs the same stages as a staged playbook. Use when a research task needs many separate readers or a second, adversarial opinion at scale — auditing every citation in a manuscript, dual-screening hundreds of records, simulating a review panel or study section, drafting a response to reviewers, or mapping a field before a proposal. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash WebFetch WebSearch Task
compatibility: "Claude Code with dynamic workflows (paid plans or API access; v2.1.203+) runs the /alterlab-workflows:* commands; installing this plugin also installs alterlab-core, whose skills the workflows call. Other surfaces use the staged playbooks in references/. Database-backed stages use public scholarly APIs (Crossref, OpenAlex, PubMed, arXiv) and need network access."
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-citation-verifier, alterlab-paper-reviewer, alterlab-deep-research (alterlab-core); optionally alterlab-openalex, alterlab-pubmed, alterlab-arxiv, alterlab-literature-review, alterlab-meta-analysis, alterlab-research-grants, alterlab-tubitak-proposal, alterlab-paper-writer"
---

# AlterLab Research Workflows

Seven academic jobs are too big or too judgment-sensitive for one pass of one model: checking
every citation in a 90-reference paper, dual-screening 800 abstracts, getting reviewers who
can't anchor on each other. This skill packages each as a **workflow** — a fixed orchestration
of many agents with separate passes and adversarial checks, and with counts, votes, coverage,
and agreement statistics computed in code rather than estimated by a model.

In Claude Code each workflow is a saved dynamic-workflow script shipped by the
`alterlab-workflows` plugin. Everywhere else, follow the staged playbook for the same workflow
in `references/` — same stages, same acceptance rules, run sequentially.

## When to Use This Skill

- Audit the reference list and up to 150 cited claims of a manuscript, thesis, or grant before submission
- Get a **peer-review panel** whose reviewers work blind to each other, with each major concern checked against the text
- **Stress-test** a paper's headline claims against counter-evidence, citation support, and inferential logic
- **Screen records** for a systematic or scoping review with two separate screener agents and adjudication (PRISMA 2020)
- Draft a **point-by-point response to reviewers** that is internally consistent and never invents results
- Run a **mock study section** for a grant on the funder's own criteria and scale (NIH, NSF, ERC, Horizon Europe, TÜBİTAK)
- **Map a literature**: themes, landmark works, methods, and research gaps that survive a search for existing answers

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Checking a handful of references, or one bibliography file | `alterlab-citation-verifier` (the tool the audit calls) |
| A single-pass review report in one context | `alterlab-paper-reviewer` or `alterlab-peer-review` |
| The full research → write → review → revise pipeline for one paper | `alterlab-research-pipeline` |
| Designing a custom multi-agent workflow, or learning the orchestration patterns | `alterlab-workflow-orchestration` |
| An investigative, cited research report on an open question | `alterlab-deep-research` (or Claude Code's bundled `/deep-research`) |
| Full-text extraction, risk-of-bias, and pooling after screening | `alterlab-literature-review`, `alterlab-meta-analysis` |
| Writing the grant itself | `alterlab-research-grants`, `alterlab-tubitak-proposal` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-citation-verifier`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

If the user doesn't know which skill fits, `alterlab-skill-finder` routes; it launches these
workflows in its orchestrate (`alterflow`) mode.

## The Workflows

| Command (Claude Code) | What it does | Input (`args`) | Agents, typical | Composes |
|---|---|---|---|---|
| `/alterlab-workflows:citation-audit` | Existence + metadata of every reference; support for up to 150 cited claims; a flag counts only after two separate re-checks both complete without clearing it (TF/PAC/IH/PH/SH taxonomy) | path, or `{path, mailto?, out?}` | 10–40 | alterlab-citation-verifier |
| `/alterlab-workflows:review-panel` | 4–6 blind reviewers chosen for the paper's field and design; every major concern re-read against the manuscript (unchecked ones go to the editor as unverified); editor decision + revision roadmap | path, or `{path, venue?, field?, lenses?, out?}` | 8–20 | alterlab-paper-reviewer (field analysis) |
| `/alterlab-workflows:claim-stress-test` | 3 skeptics per headline claim (counter-evidence, citation support, inference); majority rating (or "unrated" when missing lenses could change it) + calibrated rewrites | path, or `{path?, claims?, max_claims?, out?}` | 10–30 | alterlab-deep-research, alterlab-citation-verifier |
| `/alterlab-workflows:systematic-review-screening` | Codebook → optional database searches → de-duplication → two blinded screeners per batch → third-reviewer adjudication → PRISMA 2020 flow (unresolved records shown separately) + Cohen's κ | `{question, records?, include?, exclude?, databases?, max_per_database?, batch?, out_dir?}` | 2 per batch of 25 records, plus adjudication | alterlab-pubmed, alterlab-openalex |
| `/alterlab-workflows:rebuttal` | Reviews split into atomic comments; one drafter per comment; a consistency pass across all drafts; response letter + change log + author action list | `{manuscript, reviews, out_dir?, tone?}` | 1 per comment + 4 | alterlab-paper-writer (revision) |
| `/alterlab-workflows:grant-mock-panel` | Funder criteria and scale → primary, secondary, tertiary reviewer + skeptic → major weaknesses checked (unchecked ones marked unverified) → score spread computed → summary statement | `{path, funder, mechanism?, out?}` | 8–20 | alterlab-research-grants, alterlab-tubitak-proposal |
| `/alterlab-workflows:literature-map` | 4–6 search angles swept in parallel → merged in code → themes → up to 12 proposed gaps searched for existing answers → field map | topic, or `{topic, seeds?, years?, out_dir?}` | 10–25 | alterlab-openalex, alterlab-pubmed, alterlab-arxiv, alterlab-citation-graph |

Each workflow writes its deliverable to a file (default name in its playbook), has a separate agent read it back, and returns `status` (`complete` / `partial` / `blocked`),
`status_reasons`, a `coverage` object (requested / dispatched / completed / failed / unresolved), and the key numbers — see `references/running-workflows.md`.

## Running a Workflow in Claude Code

1. **Install once**: `/plugin install alterlab-workflows@alterlab-academic-skills` (this also
   installs `alterlab-core`). Dynamic workflows need a paid plan or API access; on Pro, enable
   them under `/config` → Dynamic workflows.
2. **Launch** with the command and its input, or in plain words — Claude passes structured
   arguments for you:
   `/alterlab-workflows:citation-audit manuscript/paper.tex` ·
   `Run the AlterLab systematic-review-screening workflow on records.ris for the question "…" excluding non-English studies`.
3. **Approve** the run in the permission prompt (it lists the phases). Allow the tools the agents
   need (Bash for the verifier scripts, WebFetch/WebSearch for lookups) so a long run is not
   stopped by prompts.
4. **Watch** with `/workflows`; each phase shows agent counts and tokens. A stopped run resumes
   in the same session with completed agents cached.

**Before a large run, say what it will cost.** A workflow spawns many agents, so tell the user
the expected agent count from the table above and offer a small first slice — one chapter's
references, 100 records, three claims. See `references/running-workflows.md` for arguments,
permissions, cost control, resuming, and troubleshooting.

## Answering a Request

Whether you launch the workflow, run its playbook, or first need the user's input, the reply:

1. **Names the workflow** by its exact name and its command — "`grant-mock-panel`
   (`/alterlab-workflows:grant-mock-panel`)" — in its opening lines. The user needs the name to
   launch it, so say it even when you go on to run the playbook yourself.
2. **States the acceptance rule and what happens to an item whose check did not complete**: a
   citation flag with fewer than two completed re-checks is *provisional*; a record without a
   resolved screening decision is *UNRESOLVED*; an unchecked review concern or grant weakness is
   *unverified*. Name the categories it reports (citation-audit: the TF/PAC/IH/PH/SH taxonomy),
   the skills it calls (the Composes column) and the next step after it (for screening:
   `alterlab-literature-review`, then `alterlab-meta-analysis`).
3. **Gives the cost**: the agent count and, for a large input (a whole thesis, hundreds of
   records), a first slice. When the input is attached and fits one run (one proposal, one
   manuscript, one decision letter), give the count in a line and run it.
4. **Asks for the input if it is not attached** — never invents records, references, scores or
   results — and says the run would otherwise be `blocked`.

## Running Without the Workflow Runtime

On claude.ai, the API, or Claude Code with workflows disabled, run the same stages from the
workflow's playbook — `references/<workflow>.md`. The playbooks preserve what makes each
workflow trustworthy:

- **Separation.** Where a workflow uses separate agents (screeners, reviewers, skeptics), use
  separate subagents via the Task tool when the surface has one; otherwise finish and record each
  pass *before* starting the next, and never revise an earlier pass after reading a later one. Separate
  passes of one model avoid anchoring but are not independent verification — say so in the deliverable.
- **Code for arithmetic.** Tallies, majority votes, agreement statistics, and score spreads are
  computed with a short script (the playbooks give the formulas), not estimated.
- **The same acceptance rules.** A citation flag counts only after two separate re-checks both
  complete without clearing it; a major review concern is "validated" only after its re-read completes.

Scale the sequential run down to what one conversation can hold, and report what was left out as
unchecked, with status `partial` (for example "references 1–40 of 112 audited").

## Choosing a Workflow

- The document is a **draft about to be submitted** → `citation-audit`, then `review-panel`.
- The user asks **"does my argument hold?"** → `claim-stress-test`.
- A **decision letter arrived** → `rebuttal` (then `citation-audit` on the revised draft).
- A **systematic or scoping review** is underway → `systematic-review-screening`, then
  `alterlab-literature-review` for full text and `alterlab-meta-analysis` for pooling.
- A **grant deadline** is weeks away → `grant-mock-panel`; an early-stage idea → `literature-map`.
- The request doesn't fit any of these → hand-design with `alterlab-workflow-orchestration`.
- **One bibliography file or a handful of references** (DOIs resolve, titles match) → no workflow:
  open with `alterlab-citation-verifier` per the hand-off rule, even while asking for the file.

## Quality Standards

| Standard | What it means here |
|---|---|
| Evidence before verdicts | Every flag, concern, or gap carries a source (DOI/URL) and a verbatim quote, or the searches that came up empty. |
| No fabrication | Agents report only works they retrieved; results only the authors have become `[AUTHORS: …]` placeholders. |
| Lookup failure ≠ fabrication | A reference that could not be checked (network, rate limit) is `UNVERIFIED`, never `NOT_FOUND`, and keeps the audit `partial`. |
| No silent caps or failures | A capped, failed, or omitted item is counted as unresolved and listed — never as checked; the run is then `partial`, never `complete`. |
| Human sign-off | Screening decisions, integrity flags, and review decisions are drafts for the researcher to confirm. |
| AI disclosure | Every deliverable ends with an AI-assistance statement suitable for journal or funder policies. |

Measurable checks when reviewing a workflow's output: it opens with its status and coverage; every
integrity-table row has evidence; PRISMA numbers add up (screened + unresolved = submitted for
screening; screened − excluded = sought for retrieval); the κ and agreement values match the decision
files and name the number of dual-screened records; no reference in a literature map lacks a DOI or URL.

## Edge Cases

- **No reference list / no claims / no records, or a failed agent** — the workflow returns `blocked` with the reason; nothing is invented to fill the gap. A failed agent is retried once, then counted as failed — never as an empty result.
- **Paywalled sources** — claim checks fall back to the abstract and mark `UNCHECKABLE` when that isn't enough; the audit is then `partial`.
- **Very large inputs** — citation-audit checks at most 150 cited claims and screening at most 2,000 records per run; the rest are counted as not checked and the run is `partial`.
- **Non-English material** — agents work in the source language; reports follow the user's language.
- **Funder without published scoring** — the grant panel uses the funder's written criteria, notes the absence of a numeric scale, and scores on the scale it states (`partial`: scores cannot be range-checked).

## Resources

- `references/running-workflows.md` — install, arguments, permissions, cost, status and coverage, resume, troubleshooting
- `references/citation-audit.md` · `references/review-panel.md` · `references/claim-stress-test.md`
- `references/systematic-review-screening.md` · `references/rebuttal.md`
- `references/grant-mock-panel.md` · `references/literature-map.md`
- Workflow scripts: `../workflows/<name>.js` in this plugin (plain JavaScript you can read and adapt)

Part of the AlterLab Academic Skills suite.
