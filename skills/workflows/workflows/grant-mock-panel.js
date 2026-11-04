export const meta = {
  name: 'grant-mock-panel',
  description: "Mock review panel for a grant proposal on the funder's own criteria and scoring scale: separate reviewer agents, a check of every major weakness (unchecked ones are marked unverified), and a summary statement",
  whenToUse: "Weeks before a deadline (NIH, NSF, ERC, Horizon Europe, TÜBİTAK 1001/1002, or another funder): see how a panel is likely to read the proposal and what to fix first. A simulation, not a prediction. Returns status complete / partial / blocked with requested-vs-completed reviewer and check counts. Args: {path, funder, mechanism?, out?}.",
  phases: [
    { title: 'Criteria', detail: "load the funder's review criteria and scoring scale" },
    { title: 'Review', detail: 'assigned reviewers plus a skeptical panelist, each scoring separately' },
    { title: 'Challenge', detail: 'each major weakness checked against the proposal' },
    { title: 'Summary', detail: 'score spread, discussion points, summary statement, fix list, then a read-back check that the file exists' },
  ],
}

const input = typeof args === 'string' ? { path: args } : (args || {})
if (!input.path || !input.funder) {
  throw new Error('grant-mock-panel needs {path: "proposal.pdf", funder: "NIH R01" | "NSF" | "ERC StG" | "TUBITAK 1001" | ...}')
}
const OUT = input.out || 'alterlab-grant-panel.md'
const program = [input.funder, input.mechanism].filter(Boolean).join(' / ')

const CRITERIA = {
  type: 'object',
  required: ['scale_min', 'scale_max', 'lower_is_better', 'criteria', 'source'],
  properties: {
    scale_min: { type: 'integer' },
    scale_max: { type: 'integer' },
    lower_is_better: { type: 'boolean', description: 'true for NIH-style 1 (exceptional) to 9 (poor) scales' },
    criteria: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'title', 'guidance'],
        properties: {
          key: { type: 'string' },
          title: { type: 'string' },
          guidance: { type: 'string', description: 'what reviewers are told to assess, in the funder\'s words where possible' },
        },
      },
    },
    source: { type: 'string', description: 'URL or document the criteria come from, with its date or version' },
  },
}

const REVIEW = {
  type: 'object',
  required: ['scores', 'overall', 'strengths', 'weaknesses'],
  properties: {
    scores: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'score', 'rationale'],
        properties: { key: { type: 'string' }, score: { type: 'number' }, rationale: { type: 'string' } },
      },
    },
    overall: { type: 'number', description: 'overall impact / overall score on the same scale' },
    strengths: { type: 'array', items: { type: 'string' } },
    weaknesses: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'severity', 'issue', 'where'],
        properties: {
          id: { type: 'string' },
          severity: { type: 'string', enum: ['major', 'minor'] },
          issue: { type: 'string' },
          where: { type: 'string', description: 'section of the proposal' },
        },
      },
    },
  },
}

const CHECK = {
  type: 'object',
  required: ['stands', 'reason'],
  properties: {
    stands: { type: 'boolean', description: 'false if the proposal already addresses it' },
    reason: { type: 'string' },
    quote: { type: 'string', description: 'verbatim proposal text that settles it' },
    fix: { type: 'string', description: 'the smallest change that would resolve it' },
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
const RESERVED = 6 // held back so the summary can always be written and read back
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
  return { status, status_reasons: reasons, report: null, program, ...fields, coverage }
}
const statusBrief = (s) =>
  `Open the summary statement with its title, then the line "Status: ${s.toUpperCase()}", then a short coverage table built from the ` +
  'Coverage object below (reviewers, scores, and weakness checks: requested, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This mock panel is PARTIAL: say so plainly in the first paragraph and give the status reasons. ' : '') +
  'Never describe a weakness as standing or checked unless the data below shows its check completed.'

// ---------------------------------------------------------------- 1. criteria
phase('Criteria')
const rubric = await withRetry(
  `Find the current peer-review criteria and scoring scale for ${program}. Use the alterlab-research-grants skill for US and other ` +
    'international funders and the alterlab-tubitak-proposal skill for TÜBİTAK programs when installed, and confirm against the funder\'s ' +
    'official call or review guidance (cite it with its date or version). Return the scale, its direction, and each scored criterion with ' +
    'the guidance reviewers receive. If the funder uses unscored criteria, include them with the scale noted in the guidance.',
  { schema: CRITERIA, label: 'funder criteria' },
)
if (!rubric || !Array.isArray(rubric.criteria) || !rubric.criteria.length) {
  reasons.push(rubric ? `no review criteria were found for ${program}` : 'the criteria agent failed twice')
  return finish('blocked', { message: `Could not establish review criteria for ${program}.` })
}
// A funder without a usable numeric scale still gets a panel, but scores cannot be range-checked or
// compared by spread, and the run says so.
const usableScale = Number.isFinite(rubric.scale_min) && Number.isFinite(rubric.scale_max) && rubric.scale_min < rubric.scale_max
if (!usableScale) {
  reasons.push(`the scoring scale returned for ${program} is not usable (${rubric.scale_min}–${rubric.scale_max}): scores are reported as given, without a range check or spread analysis`)
}
// Criterion keys must be unique: a repeated key is suffixed so its scores are not merged with another criterion's.
const criteria = []
const keys = new Set()
for (const [k, c] of rubric.criteria.entries()) {
  if (!c || typeof c.title !== 'string') continue
  let key = typeof c.key === 'string' && c.key.trim() ? c.key.trim() : `criterion${k + 1}`
  if (keys.has(key)) {
    idIssues.duplicate++
    key = `${key}#${k + 1}`
  }
  keys.add(key)
  criteria.push({ ...c, key })
}
const scale = usableScale
  ? `${rubric.scale_min}–${rubric.scale_max}, ${rubric.lower_is_better ? 'lower is better' : 'higher is better'}`
  : 'no usable numeric scale was found: score on the scale the funder\'s guidance describes, and say which'
const onScale = (x) => typeof x === 'number' && Number.isFinite(x) && (!usableScale || (x >= rubric.scale_min && x <= rubric.scale_max))
const criteriaText = criteria.map((c) => `- ${c.key} · ${c.title}: ${c.guidance}`).join('\n')

// ---------------------------------------------------------------- 2. separate reviews
phase('Review')
// Separate agents so no reviewer anchors on another's scores. They are agents of the same model,
// so a tight score spread is not independent agreement, and the summary says so.
const ROLES = [
  { key: 'primary', brief: 'You are the primary (assigned) reviewer: read everything closely, including the budget justification and appendices.' },
  { key: 'secondary', brief: 'You are the secondary reviewer: focus on feasibility, preliminary data, team, and whether the aims hang together.' },
  { key: 'tertiary', brief: 'You are the tertiary reviewer from an adjacent field: judge significance and clarity for a non-specialist panel.' },
  { key: 'skeptic', brief: 'You are the panel\'s most skeptical member: look for the fatal flaw, overreach, and missing alternatives.' },
]
const reviewerStat = { requested: ROLES.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const reviews = await parallel(ROLES.map((role) => async () => {
  if (!canSpawn()) return null
  reviewerStat.dispatched++
  const r = await withRetry(
    `${role.brief}\nProposal: ${input.path}. Program: ${program}. Scale: ${scale}.\nCriteria:\n${criteriaText}\n\n` +
      'Score every criterion (one score per criterion key) and give an overall score on that scale, with a rationale per score anchored in ' +
      'the proposal. List strengths and weaknesses; mark a weakness major only if it would move the overall score. Review on your own — ' +
      'other panelists read the same proposal separately and you will not see their scores.',
    { schema: REVIEW, label: `${role.key} reviewer`, phase: 'Review' },
    reviewerStat,
  )
  return r ? { ...r, role: role.key } : null
}))
const panel = reviews.filter(Boolean)
const missingReviewers = ROLES.filter((_, i) => !reviews[i]).map((r) => r.key)
reviewerStat.completed = panel.length
reviewerStat.failed = reviewerStat.dispatched - reviewerStat.completed
reviewerStat.unresolved = reviewerStat.requested - reviewerStat.completed
coverage.reviewers = { ...reviewerStat, missing: missingReviewers }
if (!panel.length) {
  reasons.push(`none of the ${ROLES.length} reviewers returned scores (each was retried once)`)
  return finish('blocked', { message: 'No reviewer returned scores.' })
}
if (missingReviewers.length) reasons.push(`${missingReviewers.length} of ${ROLES.length} reviewers returned no review after one retry: ${missingReviewers.join(', ')}`)

// Scores: one valid on-scale score per reviewer per criterion. Off-scale, repeated-but-different, and
// unknown-key scores are excluded and counted; a missing score is never imputed.
const scoreStat = { requested: panel.length * criteria.length, completed: 0, missing: 0, off_scale: 0, conflicting: 0 }
const scoreOf = new Map() // `${role}|${key}` -> score
for (const r of panel) {
  const seen = new Map()
  const bad = new Set()
  for (const s of Array.isArray(r.scores) ? r.scores : []) {
    if (!s || !keys.has(s.key)) {
      idIssues.unknown++
    } else if (!onScale(s.score)) {
      scoreStat.off_scale++
    } else if (seen.has(s.key)) {
      idIssues.duplicate++
      if (seen.get(s.key) !== s.score) bad.add(s.key)
    } else {
      seen.set(s.key, s.score)
    }
  }
  for (const k of bad) {
    seen.delete(k)
    scoreStat.conflicting++
    idIssues.conflicting++
  }
  for (const [k, v] of seen) scoreOf.set(`${r.role}|${k}`, v)
}
scoreStat.completed = scoreOf.size
scoreStat.missing = scoreStat.requested - scoreStat.completed
coverage.scores = scoreStat
const validOverall = panel.filter((r) => onScale(r.overall))
coverage.overall_scores = { requested: panel.length, completed: validOverall.length, off_scale: panel.length - validOverall.length }
if (scoreStat.missing) reasons.push(`${scoreStat.missing} of ${scoreStat.requested} criterion scores are missing, off-scale, or contradictory and were excluded`)
if (validOverall.length < panel.length) reasons.push(`${panel.length - validOverall.length} overall score(s) were off the ${scale} scale and were excluded`)

// ---------------------------------------------------------------- 3. challenge major weaknesses
phase('Challenge')
const majors = panel.flatMap((r) => (Array.isArray(r.weaknesses) ? r.weaknesses : [])
  .filter((w) => w && w.severity === 'major' && typeof w.issue === 'string')
  .map((w, k) => ({ reviewer: r.role, ...w, id: typeof w.id === 'string' && w.id.trim() ? w.id.trim() : `W${k + 1}` })))
const checkStat = { requested: majors.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const checks = await pipeline(majors, async (w) => {
  if (!canSpawn()) return null
  checkStat.dispatched++
  return withRetry(
    `A ${w.reviewer} reviewer flagged this major weakness in the proposal at ${input.path} (${program}): "${w.issue}" (${w.where}).\n` +
      'Re-read the proposal, including the approach, alternatives/pitfalls, preliminary data, and letters. Decide whether the weakness ' +
      'stands or the proposal already addresses it, quoting the text that settles it, and name the smallest change that would resolve it.',
    { schema: CHECK, effort: 'high', label: `check ${w.reviewer} ${w.id}`, phase: 'Challenge' },
    checkStat,
  )
})
// pipeline() keeps results aligned with its inputs, so a weakness whose check failed is still here.
const standing = []
const withdrawn = []
const unverified = []
majors.forEach((w, i) => {
  const c = checks[i]
  if (!c || typeof c.stands !== 'boolean') unverified.push({ ...w, check: null })
  else if (c.stands) standing.push({ ...w, check: c })
  else withdrawn.push({ ...w, check: c })
})
checkStat.completed = standing.length + withdrawn.length
checkStat.failed = checkStat.dispatched - checkStat.completed
checkStat.unresolved = checkStat.requested - checkStat.completed
coverage.weakness_checks = checkStat
if (unverified.length) reasons.push(`${unverified.length} of ${majors.length} major weaknesses could not be checked against the proposal; they are listed as UNVERIFIED`)

// ---------------------------------------------------------------- 4. summary (spread computed here)
phase('Summary')
const span = usableScale ? rubric.scale_max - rubric.scale_min : null
const perCriterion = criteria.map((c) => {
  const s = panel.map((r) => scoreOf.get(`${r.role}|${c.key}`)).filter((x) => x !== undefined)
  const mean = s.length ? Math.round((s.reduce((a, b) => a + b, 0) / s.length) * 10) / 10 : null
  const spread = s.length > 1 ? Math.max(...s) - Math.min(...s) : null
  // A spread of a third of the scale or more is where a real panel would argue.
  return { key: c.key, title: c.title, scores: s, n: s.length, of: panel.length, mean, spread, discuss: span !== null && spread !== null && spread / span >= 1 / 3 }
})
const overall = validOverall.map((r) => r.overall)
const overallMean = overall.length ? Math.round((overall.reduce((a, b) => a + b, 0) / overall.length) * 10) / 10 : null
const brief = (w) => ({ reviewer: w.reviewer, id: w.id, issue: w.issue, where: w.where })
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `Write the mock-panel summary statement for the proposal at ${input.path} (${program}) to ${OUT} (Markdown). ${statusBrief(workStatus)}\n` +
    'Then: overall impact and the mean score (state how many reviewers it is computed from), the per-criterion table below (n of reviewers ' +
    'scoring each) with the criteria the panel would need to discuss (large spread) called out, the consensus strengths, the standing ' +
    'weaknesses in priority order each with its smallest fix (each was re-checked against the proposal), the UNVERIFIED weaknesses in their ' +
    'own clearly labelled list (raised by a reviewer, not yet checked against the proposal), the withdrawn weaknesses (already addressed — ' +
    'make that text easier to find), and a prioritized 5-item revision plan. Say plainly that this is an AI-simulated panel on the published ' +
    `criteria (${rubric.source}), not a funding prediction; that the reviewers are separate agents of the same model, so close scores are not ` +
    'independent agreement; and include an AI-assistance disclosure.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ reviewers: coverage.reviewers, scores: scoreStat, overall_scores: coverage.overall_scores, weakness_checks: checkStat })}\n` +
    `Scale: ${scale}\nOverall scores: ${JSON.stringify(overall)} (mean ${overallMean === null ? 'not available' : overallMean})\nPer criterion: ${JSON.stringify(perCriterion, null, 1)}\n` +
    `Strengths: ${JSON.stringify(panel.map((r) => ({ reviewer: r.role, strengths: r.strengths })), null, 1)}\n` +
    `Standing weaknesses: ${JSON.stringify(standing, null, 1)}\nUNVERIFIED weaknesses (check did not complete): ${JSON.stringify(unverified.map(brief), null, 1)}\n` +
    `Withdrawn: ${JSON.stringify(withdrawn.map((w) => ({ reviewer: w.reviewer, issue: w.issue, why: w.check.reason })), null, 1)}\n\n` +
    'Reply with a two-sentence summary.',
  'summary statement',
  workStatus,
  [],
  'high',
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
const result = {
  scale,
  overall_mean: overallMean,
  overall_scores: overall,
  criteria: perCriterion,
  reviewers: { requested: ROLES.length, completed: panel.length, missing: missingReviewers },
  weaknesses: { raised: majors.length, standing: standing.length, unverified: unverified.length, withdrawn: withdrawn.length },
  standing_weaknesses: standing.length,
  withdrawn_weaknesses: withdrawn.length,
  unverified_weaknesses: unverified.map(brief),
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', result)
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, ...result })
