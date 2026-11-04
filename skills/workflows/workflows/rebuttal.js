export const meta = {
  name: 'rebuttal',
  description: 'Point-by-point response to reviewers: split the reviews into atomic comments, draft a response and a manuscript change for each in parallel, then reconcile them into one consistent letter; comments without a draft and a consistency pass that did not run are reported, never hidden',
  whenToUse: 'After receiving a revise-and-resubmit decision. Drafts the response letter, change log, and the list of analyses only the authors can run — it never invents results. Returns status complete / partial / blocked with requested-vs-drafted comment counts. Args: {manuscript, reviews, out_dir?, tone?}.',
  phases: [
    { title: 'Parse', detail: 'split every review into atomic, numbered comments' },
    { title: 'Respond', detail: 'one agent per comment drafts the stance, response, and change' },
    { title: 'Reconcile', detail: 'check all responses together for contradictions and over-promising' },
    { title: 'Compile', detail: 'response letter, change log, author action list, then a read-back check that the files exist' },
  ],
}

const input = args || {}
if (!input.manuscript || !input.reviews) {
  throw new Error('rebuttal needs {manuscript: "paper.docx", reviews: "decision-letter.pdf" (or an array of files)}')
}
const reviewFiles = Array.isArray(input.reviews) ? input.reviews : [input.reviews]
const OUT_DIR = input.out_dir || 'alterlab-rebuttal'
const TONE = input.tone || 'appreciative, direct, and specific'
const LETTER = `${OUT_DIR}/response-letter.md`
const CHANGE_LOG = `${OUT_DIR}/change-log.md`
const ACTIONS_FILE = `${OUT_DIR}/author-actions.md`

const PARSE = {
  type: 'object',
  required: ['comments'],
  properties: {
    comments: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'reviewer', 'text', 'kind', 'asks_for'],
        properties: {
          id: { type: 'string', description: 'R1.1, R1.2, R2.1, ... (E.1 for the editor)' },
          reviewer: { type: 'string' },
          text: { type: 'string', description: 'the comment, verbatim' },
          kind: { type: 'string', enum: ['major', 'minor', 'editorial', 'question', 'praise'] },
          asks_for: { type: 'string', enum: ['new_analysis', 'new_data', 'clarification', 'citation', 'rewrite', 'restructure', 'none'] },
        },
      },
    },
  },
}

const RESPONSE = {
  type: 'object',
  required: ['id', 'stance', 'response', 'change', 'author_action'],
  properties: {
    id: { type: 'string' },
    stance: { type: 'string', enum: ['agree_changed', 'partly_agree', 'clarified', 'respectfully_disagree'] },
    response: { type: 'string', description: 'the reply to the reviewer, in the requested tone' },
    change: {
      type: 'object',
      required: ['location', 'description'],
      properties: {
        location: { type: 'string', description: 'section / paragraph / figure, or "none"' },
        description: { type: 'string' },
        new_text: { type: 'string', description: 'proposed revised text, when it is a wording change' },
      },
    },
    author_action: { type: 'string', description: 'what only the authors can do (run an analysis, collect data, confirm a fact), or "none"' },
  },
}

const RECONCILE = {
  type: 'object',
  required: ['issues'],
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['ids', 'problem', 'fix'],
        properties: {
          ids: { type: 'array', items: { type: 'string' } },
          problem: { type: 'string', description: 'contradiction, duplicated change, promise not backed by a change, tone, factual risk' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

const CONFIRM = {
  type: 'object',
  required: ['exists', 'bytes', 'first_heading', 'states_status'],
  properties: {
    exists: { type: 'boolean', description: 'true only if the file is on disk now' },
    bytes: { type: 'integer', description: 'its size in bytes; 0 when it does not exist' },
    first_heading: { type: 'string', description: 'its first Markdown heading verbatim, or "" when it has none' },
    states_status: { type: 'string', enum: ['COMPLETE', 'PARTIAL', 'BLOCKED', 'NONE'], description: 'the run status its opening lines state; NONE when they state none' },
    others: {
      type: 'array',
      description: 'one entry per additional file you were asked about',
      items: {
        type: 'object',
        required: ['path', 'exists', 'lines'],
        properties: { path: { type: 'string' }, exists: { type: 'boolean' }, lines: { type: 'integer' } },
      },
    },
  },
}

// ---------------------------------------------------------------- accounting helpers
// Every agent call goes through tryAgent, which never throws: a null result or a thrown error is
// recorded and comes back as null, so failed work is counted instead of vanishing. Retries are
// bounded: no call is attempted more than twice.
const AGENT_LIMIT = 1000 // the runtime's lifetime cap on agents in one workflow
const RESERVED = 6 // held back so the letter can always be written and read back
const failures = []
const idIssues = { duplicate: 0, conflicting: 0, unknown: 0, missing: 0 }
const reasons = []
let spawned = 0
let retries = 0
let capReached = false
const canSpawn = (final) => {
  if (spawned < AGENT_LIMIT - (final ? 0 : RESERVED)) return true
  if (!capReached) {
    capReached = true
    reasons.push(`the ${AGENT_LIMIT}-agent runtime cap was reached: later work was not dispatched and is counted as unresolved`)
  }
  return false
}
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`

async function tryAgent(prompt, opts, final) {
  if (!canSpawn(final)) {
    failures.push({ label: opts.label, error: 'not dispatched: agent cap reached' })
    return null
  }
  spawned++
  try {
    const out = await agent(prompt, opts)
    if (out === null || out === undefined) failures.push({ label: opts.label, error: 'no result (agent skipped or failed)' })
    return out === undefined ? null : out
  } catch (e) {
    failures.push({ label: opts.label, error: String((e && e.message) || e).slice(0, 200) })
    return null
  }
}

// One call, retried once when it fails.
async function withRetry(prompt, opts, stat, final) {
  const out = await tryAgent(prompt, opts, final)
  if (out !== null || !canSpawn(final)) return out
  retries++
  if (stat) stat.retried++
  return tryAgent(prompt, { ...opts, label: `${opts.label} (retry)` }, final)
}

// The report counts as delivered only when a separate agent reads it back from disk (the script
// itself has no file access). A failed write is retried once, and so is a write the read-back cannot
// find. `extras` are companion files whose existence and line counts are read back too.
async function deliver(path, prompt, label, expected, extras, effort) {
  const also = extras || []
  const d = { report: null, summary: null, check: null, attempts: 0, reason: null, mismatch: null, others: {} }
  while (d.attempts < 2) {
    if (d.attempts++) retries++
    const summary = await tryAgent(prompt, { label: d.attempts > 1 ? `${label} (retry)` : label, ...(effort ? { effort } : {}) }, true)
    if (summary === null) {
      d.reason = `the report-writing agent failed (${plural(d.attempts, 'attempt')})`
      continue
    }
    d.summary = summary
    const check = await withRetry(
      `Read the file ${path} from disk and describe what is there now: whether it exists, its size in bytes, its first Markdown ` +
        'heading, and which run status (COMPLETE, PARTIAL, or BLOCKED) its opening lines state.' +
        (also.length ? ` Also report, for each of ${also.join(', ')}, whether it exists and its line count.` : '') +
        ' Only read: do not create, edit, or rewrite any file.',
      { schema: CONFIRM, effort: 'low', label: 'confirm report on disk' },
      null,
      true,
    )
    if (!check) {
      d.reason = `could not confirm that ${path} was written: the read-back agent failed`
      return d
    }
    d.check = check
    for (const p of also) {
      const o = (Array.isArray(check.others) ? check.others : []).find((x) => x && typeof x.path === 'string' && (x.path === p || x.path.endsWith(`/${p}`)))
      d.others[p] = o && o.exists ? { exists: true, lines: Number.isInteger(o.lines) ? o.lines : null } : { exists: false, lines: 0 }
    }
    if (check.exists && check.bytes > 0) {
      d.report = path
      d.reason = null
      if (check.states_status !== expected.toUpperCase()) d.mismatch = `the report opens with status ${check.states_status}, expected ${expected.toUpperCase()}`
      return d
    }
    d.reason = `${path} was not found on disk after writing`
  }
  return d
}

const coverage = {}
function finish(status, fields) {
  coverage.agents = spawned
  coverage.retries = retries
  coverage.failed_calls = failures.length
  coverage.failed_call_labels = failures.slice(0, 50).map((f) => `${f.label}: ${f.error}`)
  coverage.id_issues = idIssues
  return { status, status_reasons: reasons, report: null, out_dir: OUT_DIR, ...fields, coverage }
}

// ---------------------------------------------------------------- 1. parse
phase('Parse')
const parsed = await withRetry(
  `Read the decision letter and reviews in ${reviewFiles.join(', ')}. Split them into atomic comments — one request or point each — ` +
    'numbered by reviewer (R1.1, R1.2, ...; editor comments as E.1, ...). Keep each comment verbatim, classify it, and say what it asks for. ' +
    'Keep praise items too, so the letter can thank reviewers specifically.',
  { schema: PARSE, label: 'split reviews' },
)
if (!parsed) {
  reasons.push('the review-parsing agent failed twice, so no response was drafted')
  return finish('blocked', { message: 'Could not split the reviews into comments.' })
}
// Comment ids must be unique: the same comment listed twice counts once, and two different comments
// sharing an id are kept under distinct ids.
const comments = []
const seenIds = new Set()
const seenText = new Set()
for (const [k, c] of (Array.isArray(parsed.comments) ? parsed.comments : []).entries()) {
  if (!c || typeof c.text !== 'string' || !c.text.trim()) continue
  let id = typeof c.id === 'string' && c.id.trim() ? c.id.trim() : ''
  if (!id) {
    idIssues.missing++
    id = `X.${k + 1}`
  }
  const sig = `${id}\u0000${c.text.trim()}`
  if (seenText.has(sig)) {
    idIssues.duplicate++
    continue
  }
  seenText.add(sig)
  if (seenIds.has(id)) {
    idIssues.duplicate++
    id = `${id}#${k + 1}`
  }
  seenIds.add(id)
  comments.push({ ...c, id })
}
if (!comments.length) {
  reasons.push('no reviewer comments were found in the review files')
  return finish('blocked', { message: 'No reviewer comments found.' })
}
const actionable = comments.filter((c) => c.kind !== 'praise')
log(`${comments.length} comments (${actionable.length} needing a response) from ${new Set(comments.map((c) => c.reviewer)).size} reviewer(s)`)

// ---------------------------------------------------------------- 2. respond (one agent per comment)
phase('Respond')
const draftStat = { requested: actionable.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const drafts = await pipeline(actionable, async (c) => {
  if (!canSpawn()) return null
  draftStat.dispatched++
  const r = await withRetry(
    `Draft the response to reviewer comment ${c.id} (${c.kind}; asks for ${c.asks_for}) on the manuscript at ${input.manuscript}:\n"${c.text}"\n\n` +
      'Read the parts of the manuscript it concerns. Choose a stance on the merits — agree and change, partly agree, clarify, or respectfully ' +
      'disagree with evidence. Write the reply in a tone that is ' + `${TONE}, ` +
      'and specify the manuscript change (location, what changes, and new text for wording changes). Never invent results, statistics, ' +
      'references, or data: where a response depends on an analysis or fact only the authors have, write a placeholder like ' +
      '[AUTHORS: report the sensitivity analysis excluding site 3] and describe it in author_action. The alterlab-paper-writer skill\'s ' +
      'revision mode has guidance on response style.',
    { schema: RESPONSE, label: c.id, phase: 'Respond' },
    draftStat,
  )
  return r && typeof r.response === 'string' && r.change ? r : null
})
// pipeline() keeps results aligned with its inputs; each draft is keyed by its comment, whatever id it echoes.
const responses = []
const missing = []
actionable.forEach((c, i) => {
  const r = drafts[i]
  if (!r) return missing.push(c)
  if (r.id !== c.id) idIssues.unknown++
  return responses.push({ ...r, id: c.id, comment: c })
})
draftStat.completed = responses.length
draftStat.failed = draftStat.dispatched - draftStat.completed
draftStat.unresolved = draftStat.requested - draftStat.completed
coverage.responses = draftStat
if (actionable.length && !responses.length) {
  reasons.push(`no response could be drafted for any of the ${actionable.length} comments (each was retried once)`)
  return finish('blocked', { comments: comments.length, actionable: actionable.length, responded: 0, unanswered: missing.map((c) => c.id) })
}
if (missing.length) {
  reasons.push(`${missing.length} of ${actionable.length} comments have no draft after one retry (${missing.map((c) => c.id).join(', ')}); they are listed for the authors to answer`)
  log(`No draft for ${missing.map((c) => c.id).join(', ')} — they are listed for the authors to answer`)
}

// ---------------------------------------------------------------- 3. reconcile (needs every draft at once)
phase('Reconcile')
const consistency = { requested: responses.length ? 1 : 0, completed: 0, retried: 0, ran: false, issues: null }
if (responses.length) {
  const review = await withRetry(
    'Review this full set of draft responses to reviewers as one document. Find: responses that contradict each other; the same manuscript ' +
      'change promised twice or described differently; responses that claim a change the change field does not actually make; stances that ' +
      'will read as dismissive; and any sentence that states a result or fact the authors have not supplied (those must become placeholders). ' +
      'Propose a concrete fix for each issue, naming the comment ids it concerns.\n\n' +
      JSON.stringify(responses.map(({ comment, ...r }) => ({ comment: comment.text, ...r })), null, 1),
    { schema: RECONCILE, effort: 'high', label: 'consistency pass' },
    consistency,
  )
  if (review && Array.isArray(review.issues)) {
    consistency.ran = true
    consistency.completed = 1
    const known = new Set(responses.map((r) => r.id))
    consistency.issues = review.issues.filter((x) => x && typeof x.fix === 'string')
    for (const x of consistency.issues) for (const id of Array.isArray(x.ids) ? x.ids : []) if (!known.has(id)) idIssues.unknown++
  } else {
    reasons.push('the consistency pass did not complete (after one retry), so contradictions between responses were not checked')
  }
}
coverage.consistency = { requested: consistency.requested, completed: consistency.completed, retried: consistency.retried }
const issues = consistency.issues || []

// ---------------------------------------------------------------- 4. compile
phase('Compile')
const actions = responses.filter((r) => typeof r.author_action === 'string' && r.author_action.trim() && r.author_action.toLowerCase() !== 'none').map((r) => ({ id: r.id, action: r.author_action }))
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  LETTER,
  `Assemble the revision package in ${OUT_DIR}/: (1) response-letter.md — its title, then the line "Status: ${workStatus.toUpperCase()}", ` +
    'then a short cover note to the editor, then every comment in order, quoted, followed by the response and where the manuscript changed ' +
    '(thank reviewers for the praise items specifically); a comment without a draft gets "[AUTHORS: response needed]" — never an invented ' +
    'reply; (2) change-log.md — every manuscript change by location, with new text where given; (3) author-actions.md — every placeholder, ' +
    'every comment without a draft, and every analysis the authors must supply before submitting. ' +
    (consistency.ran
      ? 'Apply each consistency fix below while assembling. '
      : 'The consistency pass did NOT run: say so at the top of author-actions.md and ask the authors to read the drafts side by side for contradictions. ') +
    (workStatus === 'partial' ? 'This package is PARTIAL: say so plainly in the first lines of response-letter.md and author-actions.md, with the reasons below. ' : '') +
    'Do not edit the manuscript itself. Add a line to the cover note disclosing AI assistance in drafting the response, per the journal\'s ' +
    'policy, and note in author-actions.md that the consistency pass was run by an agent of the same model that drafted the responses, so ' +
    'it is not an independent check: the authors must read the whole letter before sending it.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ responses: draftStat, consistency: coverage.consistency })}\n` +
    `All comments: ${JSON.stringify(comments, null, 1)}\n\nDrafts: ${JSON.stringify(responses.map(({ comment, ...r }) => r), null, 1)}\n\n` +
    `Consistency fixes: ${consistency.ran ? JSON.stringify(issues, null, 1) : 'not available — the consistency pass did not run'}\n\n` +
    `Comments without a draft: ${JSON.stringify(missing.map((c) => c.id))}\n\n` +
    'Reply with a two-sentence summary.',
  'assemble letter',
  workStatus,
  [CHANGE_LOG, ACTIONS_FILE],
)
coverage.report = { path: LETTER, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check, files: delivered.others }
const result = {
  comments: comments.length,
  actionable: actionable.length,
  responded: responses.length,
  unanswered: missing.map((c) => c.id),
  consistency_checked: consistency.ran,
  consistency_issues: consistency.ran ? issues.length : null, // null: the check did not run, not "no issues"
  author_actions: actions,
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', { files: { letter: null, change_log: null, author_actions: null }, ...result })
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
const present = (p) => delivered.others[p] && delivered.others[p].exists
for (const p of [CHANGE_LOG, ACTIONS_FILE]) if (!present(p)) reasons.push(`${p} was not found on disk after writing`)
return finish(reasons.length ? 'partial' : 'complete', {
  report: delivered.report,
  files: { letter: delivered.report, change_log: present(CHANGE_LOG) ? CHANGE_LOG : null, author_actions: present(ACTIONS_FILE) ? ACTIONS_FILE : null },
  ...result,
})
