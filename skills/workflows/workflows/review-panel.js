export const meta = {
  name: 'review-panel',
  description: "Multi-reviewer peer review of a manuscript by separate reviewer agents that never see each other's reports, with every major concern re-read against the text before the editor decides; concerns whose check did not complete reach the editor marked unverified",
  whenToUse: 'Before submitting a paper, thesis chapter, or preprint, when you want reviewers who cannot anchor on each other and no concern that misreads the manuscript. Returns status complete / partial / blocked with requested-vs-completed reviewer and check counts. Args: a manuscript path, or {path, venue?, field?, lenses?, out?}.',
  phases: [
    { title: 'Profile', detail: 'detect field, design, venue norms, and reporting guideline; choose reviewer lenses' },
    { title: 'Review', detail: 'separate reviewers, one per lens, blind to each other' },
    { title: 'Verify', detail: 'each major concern re-read against the manuscript' },
    { title: 'Decide', detail: 'editor synthesis, decision letter, revision roadmap, then a read-back check that the file exists' },
  ],
}

const input = typeof args === 'string' ? { path: args } : (args || {})
if (!input.path) {
  throw new Error('review-panel needs a manuscript: /alterlab-workflows:review-panel paper.pdf — or args {path, venue?, field?, lenses?, out?}')
}
const OUT = input.out || 'alterlab-review-panel.md'
const MAX_LENSES = 6
const context = [input.venue && `Target venue: ${input.venue}.`, input.field && `Field: ${input.field}.`].filter(Boolean).join(' ')

const PROFILE = {
  type: 'object',
  required: ['field', 'paper_type', 'design', 'reporting_guideline', 'lenses'],
  properties: {
    field: { type: 'string' },
    paper_type: { type: 'string', description: 'empirical, theoretical, review, methods, qualitative, mixed, ...' },
    design: { type: 'string', description: 'study design and main analyses, one sentence' },
    reporting_guideline: { type: 'string', description: 'CONSORT, STROBE, PRISMA, COREQ, SRQR, ARRIVE, TRIPOD, none, ...' },
    lenses: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'title', 'focus'],
        properties: {
          key: { type: 'string', description: 'short slug' },
          title: { type: 'string', description: 'reviewer role, e.g. Methodology reviewer' },
          focus: { type: 'string', description: 'what this reviewer scrutinizes for this paper specifically' },
        },
      },
    },
  },
}

const REVIEW = {
  type: 'object',
  required: ['recommendation', 'summary', 'strengths', 'concerns'],
  properties: {
    recommendation: { type: 'string', enum: ['accept', 'minor_revision', 'major_revision', 'reject'] },
    summary: { type: 'string', description: "the paper's contribution in the reviewer's words" },
    strengths: { type: 'array', items: { type: 'string' } },
    concerns: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'severity', 'issue', 'location', 'suggested_fix'],
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['major', 'minor'] },
          issue: { type: 'string' },
          location: { type: 'string', description: 'section, table, figure, or page' },
          quote: { type: 'string', description: 'the manuscript text the concern is about, verbatim' },
          suggested_fix: { type: 'string' },
        },
      },
    },
    questions_for_authors: { type: 'array', items: { type: 'string' } },
  },
}

const CHECK = {
  type: 'object',
  required: ['valid', 'reason'],
  properties: {
    valid: { type: 'boolean', description: 'false if the manuscript already addresses it or the reviewer misread the text' },
    reason: { type: 'string' },
    quote: { type: 'string', description: 'verbatim manuscript text that settles it' },
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
const RESERVED = 6 // held back so the report can always be written and read back
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
  return { status, status_reasons: reasons, report: null, ...fields, coverage }
}
const statusBrief = (s) =>
  `Open the decision package with its title, then the line "Status: ${s.toUpperCase()}", then a short coverage table built from the ` +
  'Coverage object below (reviewers and concern checks: requested, dispatched, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This panel run is PARTIAL: say so plainly in the first paragraph and give the status reasons. ' : '') +
  'Never describe a concern as validated or checked unless the data below shows its check completed.'

// ---------------------------------------------------------------- 1. profile
phase('Profile')
const profile = await withRetry(
  `Read the manuscript at ${input.path}. ${context} Identify its field, paper type, study design, and the reporting guideline that applies ` +
    '(or "none"). Then choose 4–5 reviewer lenses for THIS paper: always a methodology lens, a domain-contribution lens, a statistics and ' +
    'reproducibility lens (or an analytic-rigor lens for qualitative work), and a devil\'s-advocate lens that attacks the central claim; add an ' +
    'ethics and reporting-standards lens when there are human or animal participants or a reporting guideline applies. Make each focus specific ' +
    'to this manuscript. If the alterlab-paper-reviewer skill is installed, its field-analyst guidance applies.',
  { schema: PROFILE, label: 'field analyst' },
)
if (!profile) {
  reasons.push('the field-analyst agent failed twice, so no review was run')
  return finish('blocked', { message: `Could not profile ${input.path}.` })
}
const asked = Array.isArray(input.lenses) && input.lenses.length ? input.lenses : Array.isArray(profile.lenses) ? profile.lenses : []
const lenses = asked
  .map((l, i) => (typeof l === 'string' ? { key: `lens${i + 1}`, title: l, focus: l } : l))
  .filter((l) => l && typeof l.title === 'string' && l.title.trim())
  .map((l, i) => ({ key: l.key || `lens${i + 1}`, title: l.title.trim(), focus: l.focus || l.title }))
if (!lenses.length) {
  reasons.push('no reviewer lenses were chosen or supplied, so no review was run')
  return finish('blocked', { message: 'No reviewer lenses.' })
}
const panel = lenses.slice(0, MAX_LENSES)
if (lenses.length > MAX_LENSES) {
  reasons.push(`capped: ${MAX_LENSES} of ${lenses.length} requested reviewer lenses were used`)
  log(`Using the first ${MAX_LENSES} of ${lenses.length} lenses`)
}

// ---------------------------------------------------------------- 2. separate reviews
phase('Review')
// Reviewers run in separate contexts and never see each other's reports, so none can anchor on
// another. They are still agents of the same model: where they agree, that is not independent
// confirmation, and the decision package says so.
const reviewerStat = { requested: lenses.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const reviews = await parallel(panel.map((lens, slot) => async () => {
  if (!canSpawn()) return null
  reviewerStat.dispatched++
  const r = await withRetry(
    `You are the ${lens.title} on a peer-review panel for the manuscript at ${input.path}. ${context}\n` +
      `Paper profile: ${profile.field}; ${profile.paper_type}; ${profile.design}. Reporting guideline: ${profile.reporting_guideline}.\n` +
      `Your focus: ${lens.focus}\n` +
      'Read the whole manuscript and write your own review; other panel members review it separately and you will not see their reports. ' +
      'Anchor every concern to a location and, where possible, a verbatim quote; say what would resolve it. Give each concern its own id. ' +
      'Mark a concern major only if it threatens a main conclusion. Recommend accept, minor_revision, major_revision, or reject. Be specific ' +
      'and constructive; do not invent content the paper lacks or cite literature you have not verified.',
    { schema: REVIEW, label: lens.title, phase: 'Review' },
    reviewerStat,
  )
  return r ? { ...r, lens, slot } : null
}))
// A concern listed twice (same id and text) counts once; two different concerns sharing an id are
// both kept under distinct ids.
function concernsOf(r) {
  const ids = new Set()
  const sigs = new Set()
  const out = []
  for (const c of Array.isArray(r.concerns) ? r.concerns : []) {
    if (!c || typeof c !== 'object' || typeof c.issue !== 'string' || !c.issue.trim()) continue
    let id = typeof c.id === 'string' && c.id.trim() ? c.id.trim() : ''
    if (!id) {
      idIssues.missing++
      id = `concern ${out.length + 1}`
    }
    const sig = `${id}\u0000${c.issue.trim()}`
    if (sigs.has(sig)) {
      idIssues.duplicate++
      continue
    }
    sigs.add(sig)
    if (ids.has(id)) {
      idIssues.duplicate++
      id = `${id}#${out.length + 1}`
    }
    ids.add(id)
    out.push({ ...c, id })
  }
  return out
}
const done = reviews.filter(Boolean).map((r) => ({ ...r, concerns: concernsOf(r) }))
const missingReviewers = panel.filter((_, slot) => !reviews[slot]).map((l) => l.title)
reviewerStat.completed = done.length
reviewerStat.failed = reviewerStat.dispatched - reviewerStat.completed
reviewerStat.unresolved = reviewerStat.requested - reviewerStat.completed
coverage.reviewers = { ...reviewerStat, missing: missingReviewers }
if (!done.length) {
  reasons.push(`none of the ${plural(panel.length, 'reviewer')} returned a report (each was retried once)`)
  return finish('blocked', { message: 'No reviewer returned a report.' })
}
if (missingReviewers.length) {
  reasons.push(`${missingReviewers.length} of ${panel.length} reviewers returned no report after one retry: ${missingReviewers.join(', ')}`)
  log(`No report from ${missingReviewers.join(', ')}`)
}

// ---------------------------------------------------------------- 3. verify major concerns
phase('Verify')
const majors = done.flatMap((r) => r.concerns.filter((c) => c.severity === 'major').map((c) => ({ reviewer: r.lens.title, ...c })))
const checkStat = { requested: majors.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const checks = await pipeline(majors, async (c) => {
  if (!canSpawn()) return null
  checkStat.dispatched++
  return withRetry(
    `A reviewer (${c.reviewer}) raised this major concern about the manuscript at ${input.path}:\n` +
      `"${c.issue}" (location: ${c.location}${c.quote ? `; quoted text: "${c.quote}"` : ''}).\n` +
      'Re-read the relevant parts of the manuscript, including the methods, supplementary material it references, and limitations. Decide ' +
      'whether the concern is valid as stated. It is not valid if the manuscript already addresses it or the reviewer misread the text; quote ' +
      'the passage that settles it either way.',
    { schema: CHECK, effort: 'high', label: `check: ${c.reviewer} ${c.id}`, phase: 'Verify' },
    checkStat,
  )
})
// pipeline() keeps results aligned with its inputs, so a concern whose check failed is still here.
const validated = []
const withdrawn = []
const unverified = []
majors.forEach((c, i) => {
  const v = checks[i]
  if (!v || typeof v.valid !== 'boolean') unverified.push({ ...c, check: null, verification: 'UNVERIFIED: the check did not complete' })
  else if (v.valid) validated.push({ ...c, check: v })
  else withdrawn.push({ ...c, check: v })
})
checkStat.completed = validated.length + withdrawn.length
checkStat.failed = checkStat.dispatched - checkStat.completed
checkStat.unresolved = checkStat.requested - checkStat.completed
coverage.concern_checks = checkStat
if (unverified.length) {
  reasons.push(`${unverified.length} of ${majors.length} major concerns could not be checked against the manuscript; they reach the editor marked UNVERIFIED`)
  log(`${unverified.length} major concern(s) are unverified`)
}
if (withdrawn.length) log(`${withdrawn.length} major concern(s) withdrawn after re-reading the manuscript`)

// ---------------------------------------------------------------- 4. editor decision
phase('Decide')
const tally = {}
for (const r of done) tally[r.recommendation] = (tally[r.recommendation] || 0) + 1
const brief = (c) => ({ reviewer: c.reviewer, id: c.id, issue: c.issue, location: c.location, suggested_fix: c.suggested_fix })
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `You are the handling editor. Write the decision package for the manuscript at ${input.path} to ${OUT} (Markdown). ${statusBrief(workStatus)}\n` +
    'Then: (1) the editorial decision with a short rationale, noting how many of the requested reviewers reported; (2) where reviewers agree ' +
    'and where they disagree, and how you weigh the disagreement; (3) a revision roadmap — the validated major concerns first (each was ' +
    're-read against the manuscript and found to stand), grouped by theme, each with what would resolve it; then any UNVERIFIED major ' +
    'concerns in their own clearly labelled list ("raised by a reviewer, not yet checked against the manuscript"), never presented as ' +
    'validated; then minor points, which were not re-checked; (4) each reviewer\'s report, lightly edited, and the names of any reviewers ' +
    'who did not report; (5) a note listing concerns withdrawn after re-reading the manuscript, so authors are not asked to fix what is ' +
    'already there; (6) an AI-assistance disclosure stating this is a simulated panel, not a journal decision, and that the reviewers are ' +
    'separate agents of the same model, so their agreement is not independent confirmation.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ reviewers: coverage.reviewers, concern_checks: checkStat })}\n` +
    `Recommendation tally (reporting reviewers only): ${JSON.stringify(tally)}\nProfile: ${JSON.stringify(profile)}\n` +
    `Reviews: ${JSON.stringify(done.map((r) => ({ reviewer: r.lens.title, recommendation: r.recommendation, summary: r.summary, strengths: r.strengths, minor: r.concerns.filter((c) => c.severity !== 'major'), questions: r.questions_for_authors || [] })), null, 1)}\n` +
    `Validated major concerns: ${JSON.stringify(validated, null, 1)}\n` +
    `UNVERIFIED major concerns (check did not complete): ${JSON.stringify(unverified.map(brief), null, 1)}\n` +
    `Withdrawn concerns: ${JSON.stringify(withdrawn.map((c) => ({ reviewer: c.reviewer, id: c.id, issue: c.issue, why: c.check.reason })), null, 1)}\n\n` +
    'Reply with the decision in one word (accept, minor_revision, major_revision, or reject) followed by a two-sentence rationale.',
  'editor-in-chief',
  workStatus,
  [],
  'high',
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
const result = {
  recommendations: tally,
  reviewers: { requested: lenses.length, used: panel.length, completed: done.length, missing: missingReviewers },
  major_concerns: { raised: majors.length, validated: validated.length, unverified: unverified.length, withdrawn: withdrawn.length },
  concerns: { validated: validated.map(brief), unverified: unverified.map(brief), withdrawn: withdrawn.map(brief) },
  decision: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', result)
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, ...result })
