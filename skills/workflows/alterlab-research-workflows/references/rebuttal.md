# Playbook — rebuttal

**Goal:** a complete, consistent, point-by-point response to reviewers that promises only
changes it specifies and invents no results. **Default output folder:** `alterlab-rebuttal/`
(`response-letter.md`, `change-log.md`, `author-actions.md`). The manuscript itself is not edited
— apply the change log with `alterlab-paper-writer` (revision mode) or by hand.

## Inputs

| Field | Default | Meaning |
|---|---|---|
| `manuscript` | required | the submitted manuscript |
| `reviews` | required | decision letter / review files (one path or a list) |
| `out_dir` | `alterlab-rebuttal` | output folder |
| `tone` | "appreciative, direct, and specific" | register for the responses |

## Stages and acceptance rules

1. **Parse** — atomic comments numbered R1.1, R1.2, …, E.1 for the editor, verbatim, classified
   (major / minor / editorial / question / praise) with what each asks for. Ids are made unique:
   the same comment listed twice counts once; two different comments sharing an id are both kept.
2. **Respond** — one drafter per comment (retried once on failure): stance on the merits (agree and
   change, partly agree, clarify, respectfully disagree with evidence), the reply, and the exact
   manuscript change (location, description, new text for wording). Anything only the authors can
   supply becomes `[AUTHORS: …]` and is listed as an author action. A comment still without a draft
   is listed for the authors — never given an invented reply.
3. **Reconcile** — all drafts read together: contradictions, the same change promised twice,
   responses claiming changes the change field doesn't make, dismissive stances, stated results
   the authors never supplied. If this pass fails (after one retry) the package says so and
   `consistency_issues` is `null` — "not checked", not "no issues".
4. **Compile** — letter (title, status line, cover note, then every comment quoted with its response
   and change location), change log, author actions; consistency fixes applied; AI assistance
   disclosed; a note that the consistency pass is by the same model that drafted the responses, so the
   authors must read the whole letter. A separate agent reads the three files back before the
   letter's path is returned.

The run is `partial` when a comment has no draft, the consistency pass did not run, or a companion
file is missing; `blocked` when parsing failed, no comment could be drafted, or the letter could not
be written or found.

## Returned payload

| Field | Contents |
|---|---|
| `status`, `status_reasons`, `report` | see `running-workflows.md`; `report` is the letter path |
| `files` | `letter`, `change_log`, `author_actions` — each `null` unless read back |
| `comments`, `actionable`, `responded`, `unanswered` | counts, and the ids without a draft |
| `consistency_checked`, `consistency_issues` | whether the pass ran; its issue count, or `null` when it did not run |
| `author_actions` | what only the authors can supply |
| `coverage` | `responses` (requested / dispatched / completed / failed / unresolved / retried), `consistency`, `report`, `id_issues`, agent totals |

## Sequential playbook

Parse, then draft responses reviewer by reviewer, then do the reconcile pass as a separate read
of the whole set before compiling. Keep the placeholder rule strictly, and list any comment you did
not answer.

## Response pattern

```markdown
**R2.3** — "<comment verbatim>"
**Response.** We thank the reviewer … We have <change>. [AUTHORS: report the robustness check
excluding site 3 — see author-actions.md]
**Change.** Methods §2.4, paragraph 2: "<new text>"
```

## Pitfalls

- "We have added the analysis" with no analysis — placeholders exist to prevent this.
- Disagreeing without evidence or without acknowledging what prompted the comment.
- Fixing the same issue differently for two reviewers.
- Reading "0 consistency issues" when the consistency pass never ran.
