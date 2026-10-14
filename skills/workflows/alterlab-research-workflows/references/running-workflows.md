# Running AlterLab Workflows in Claude Code

## Requirements

- Claude Code v2.1.203 or later with **dynamic workflows** available (all paid plans, Anthropic API
  access, Amazon Bedrock, Google Cloud, Microsoft Foundry). On Pro, turn them on in `/config` →
  Dynamic workflows. An organization can disable them with `disableWorkflows`; then use the staged
  playbooks instead.
- The plugin: `/plugin install alterlab-workflows@alterlab-academic-skills`. It declares
  `alterlab-core` as a dependency, so the citation verifier, reviewer, and deep-research skills the
  workflows call are installed with it. Optional helpers (install when the workflow's table row
  names them): `alterlab-databases` (PubMed, OpenAlex, arXiv skills), `alterlab-writing-tools`
  (literature review, grants), `alterlab-social-science-workflow` (meta-analysis),
  `alterlab-turkish-academia` (TÜBİTAK).
- Network access for the scholarly APIs. Configure the core plugin
  (`/plugin configure alterlab-core@alterlab-academic-skills`): a free OpenAlex API key gives
  OpenAlex calls their own daily budget (export `NCBI_API_KEY` for PubMed-heavy runs) — keyless calls
  share a small per-IP budget and fail with HTTP 429 once it is spent (the verifier then reports
  UNVERIFIED, never fabricated).

## Launching

Workflows appear in `/` autocomplete as `/alterlab-workflows:<name>`. Two ways to start one:

```text
/alterlab-workflows:review-panel drafts/chapter3.pdf
Run the AlterLab grant-mock-panel workflow on proposal.pdf for TÜBİTAK 1001
```

Claude turns the request into the workflow's `args` value (a string or an object — each playbook
lists the fields). A string argument is treated as the main input (a path, a question, or a topic).

## Approving the run

The permission prompt lists the phases. Choose **Yes, run it**, or **Yes, and don't ask again** for
a workflow you run often. The agents then use your normal permission rules — for an uninterrupted
run, allow in advance:

- `Bash` (the verifier scripts run with `uv run python …`)
- `WebFetch` and `WebSearch` (lookups, full texts)
- `Write` for the output directory

In `claude -p` and the Agent SDK there is no prompt: allow `Workflow(citation-audit)`-style rules or
use auto mode.

## Cost

Workflows trade tokens for separation and coverage. Rough agent counts are in the SKILL.md table;
the `/workflows` view shows live token totals and lets you stop at any time without losing finished
agents. Start with a slice — one chapter, 100 records, three claims — before a full run. Claude Code
flags runs above 25 agents or 1.5M projected tokens as "Large workflow"; that warning is advisory.

## Watching, stopping, resuming

- `/workflows` → select the run → Enter: phases, agents, each agent's prompt and result.
- `p` pauses/resumes, `x` stops an agent or the run, `r` restarts a running agent.
- A stopped run relaunched in the same session replays finished agents from cache and reruns from
  the first agent whose input changed.
- If an agent hits a usage limit on a subscription, the run waits for the reset (v2.1.271+).

## Outputs

Each workflow writes Markdown (and, where useful, JSONL) into the working directory — the default
file or folder is named in its playbook and can be changed with `out` / `out_dir`. The workflow's
return value (shown in the session) holds the status, the coverage counts, the key numbers, and a
short summary.

## Reading the result: status and coverage

Every workflow returns the same top-level fields, so a partial run cannot pass for a complete one:

| Field | Meaning |
|---|---|
| `status` | `complete` — every required check finished and the report was read back from disk; `partial` — the report exists, but some work failed, was capped, or is unresolved; `blocked` — no usable deliverable (a required stage failed, there was nothing to work on, or the report could not be written or confirmed) |
| `status_reasons` | one plain sentence per gap: what was capped, failed, or left unresolved (empty only when `complete`) |
| `report` | the report path — set only after a separate read-back agent found the file on disk; otherwise `null` |
| `coverage` | per stage: `requested` (items the stage set out to handle), `dispatched` (sent to an agent), `completed` (an accepted answer came back), `failed` (dispatched, no accepted answer), `unresolved` (requested − completed), `retried` (retry calls); plus `agents`, `retries`, `failed_calls`, `failed_call_labels`, `id_issues`, and `report` (attempts and the read-back) |

`coverage.id_issues` counts answers that were ignored, so none can inflate a count: `duplicate` (an
id answered twice counts once; if the two answers disagree they are `conflicting` and the item is
asked again), `unknown` (an id that was not sent in that call), and `missing` (an answer with no id).

How the workflows handle failure:

- An agent that returns nothing or throws is retried **once**, and an item a batch left out is
  re-sent once. Nothing is attempted more than twice.
- What still has no answer is counted as failed / unresolved and listed by id in the payload and in
  the report — never dropped, never counted as checked.
- *Validated*, *verified*, *standing*, *open*, *screened*, *included*, and *excluded* are used only
  after the check behind them completed. Items whose check did not complete are listed on their own
  as *unverified*, *provisional*, *unchecked*, *unrated*, or *UNRESOLVED*.
- The report opens with `Status: COMPLETE` or `Status: PARTIAL` and a coverage table. The read-back
  agent reports which status the file states; a mismatch keeps the run `partial`.
- Separate agents of the same model avoid anchoring on each other but share the model's blind spots:
  two re-checks, two screeners, or a reviewer panel agreeing is not independent verification, and
  every report says so. A human confirms the findings.
- Runs stay under the runtime's 1,000-agent cap: a few agents are held back for the report, and work
  that would exceed the cap is counted as not dispatched instead of being silently skipped.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/alterlab-workflows:…` not in autocomplete | plugin not installed/enabled, or workflows disabled | `/plugin` → enable; check `/config` → Dynamic workflows |
| Run stops at a permission prompt | a tool the agents need isn't allowed | allow Bash/WebFetch/WebSearch/Write, or run in auto mode |
| Many `UNVERIFIED` citations | API rate limits or no network | add an OpenAlex API key; rerun later — UNVERIFIED is never an accusation |
| Screening report says κ is not defined | a screener used a single category for every record | check the codebook; tiny or homogeneous record sets can do this legitimately |
| `status: partial` | some agents failed after their retry, or a cap applied | read `status_reasons` and the unchecked / unresolved lists; re-run that slice (one chapter, the unresolved records) |
| `status: blocked`, `report: null` | a required stage failed, there was no input to work on, or the report could not be written or read back | read `status_reasons`; the coverage counts are still returned; fix the cause (permissions, path) and re-run |
| Screening shows UNRESOLVED records | a screener or the adjudicator failed for them, or a stand-in second reviewer disagreed | screen them by hand from `unresolved.jsonl`; they are retained, never excluded |
| "nothing to resume" | the earlier run's results are gone (new session) | start the workflow again as a new run |

## Adapting a workflow

The scripts are plain JavaScript in the plugin's `workflows/` folder. To make a variant, copy one
into your project's `.claude/workflows/`, change it, and run `/reload-skills`. Keep `export const
meta` as the first statement and a pure literal, and keep `meta.name` equal to the file name. The
repository validates every script with `node scripts/workflow_dryrun.mjs <script>`.
