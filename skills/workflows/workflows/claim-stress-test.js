export const meta = {
  name: 'claim-stress-test',
  description: "Stress-test a paper's headline claims: three separate skeptic agents per claim attack the evidence, the citations, and the inference; each claim is rated only when the lenses that completed settle it, and recalibrated",
  whenToUse: 'Before submission or a talk, or when refereeing: find which central claims survive disconfirming literature, citation checks, and inferential scrutiny. Returns status complete / partial / blocked with requested-vs-completed lens counts. Args: a manuscript path, or {path?, claims?: [...], max_claims?, out?}.',
  phases: [
    { title: 'Claims', detail: 'extract the headline claims and the evidence offered for each' },
    { title: 'Attack', detail: 'three separate skeptics per claim, each with a different lens' },
    { title: 'Verdict', detail: 'rate each claim, write calibrated rewrites, then a read-back check that the file exists' },
  ],
}

const input = typeof args === 'string' ? { path: args } : (args || {})
const given = Array.isArray(input.claims) ? input.claims.filter((c) => typeof c === 'string' && c.trim()) : []
if (!input.path && !given.length) {
  throw new Error('claim-stress-test needs a manuscript path or a list of claims: args {path} or {claims: ["...", "..."]}')
}
const OUT = input.out || 'alterlab-claim-stress-test.md'
const MAX = Math.min(Math.max(Number(input.max_claims) || 8, 1), 20)

const CLAIMS = {
  type: 'object',
  required: ['claims'],
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'claim', 'evidence'],
        properties: {
          id: { type: 'string' },
          claim: { type: 'string', description: 'the claim as the paper states it, verbatim' },
          evidence: { type: 'string', description: 'the data, analysis, or citations the paper offers for it' },
          design: { type: 'string', description: 'the study design behind it' },
        },
      },
    },
    total_found: { type: 'integer' },
  },
}

const ATTACK = {
  type: 'object',
  required: ['refuted', 'severity', 'argument'],
  properties: {
    refuted: { type: 'boolean', description: 'true if the claim, as stated, does not survive your lens' },
    severity: { type: 'string', enum: ['none', 'weakening', 'fatal'] },
    argument: { type: 'string' },
    evidence: {
      type: 'array',
      items: {
        type: 'object',
        required: ['source', 'finding'],
        properties: {
          source: { type: 'string', description: 'DOI or URL you actually retrieved' },
          finding: { type: 'string', description: 'what it shows, quoted where possible' },
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
  `Open the report with its title, then the line "Status: ${s.toUpperCase()}", then a coverage table built from the Coverage object ` +
  'below (claims and lens attacks: requested, dispatched, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This stress test is PARTIAL: say so plainly in the first paragraph and give the status reasons. ' : '') +
  'Never describe a lens as having checked a claim unless the data below shows that lens completed.'

// Distinct lenses catch distinct failure modes; three identical skeptics would mostly repeat each other.
const LENSES = [
  {
    key: 'counter-evidence',
    brief:
      'Search the literature for disconfirming, null, or failed-replication findings and for systematic reviews or meta-analyses on the ' +
      'question (use the alterlab-openalex, alterlab-pubmed, or alterlab-deep-research skills when installed). Weigh them by the evidence ' +
      'hierarchy: meta-analyses and RCTs outweigh single observational studies.',
  },
  {
    key: 'citation-support',
    brief:
      'Check whether the sources the paper cites for this claim actually support it at the strength stated — right population, measure, ' +
      'direction, and effect size (use the alterlab-citation-verifier skill when installed). Retrieve the sources; never judge them from memory.',
  },
  {
    key: 'inference',
    brief:
      'Check whether the design and analysis license the claim: causal language from correlational data, generalization beyond the sample ' +
      'frame, multiplicity or optional stopping, effect size versus significance, confounding, and whether the uncertainty is reported.',
  },
]

// Majority rule across the three lenses; a single fatal finding still forces a closer look.
const rate = (votes) => {
  const fatal = votes.filter((x) => x.refuted && x.severity === 'fatal').length
  const weak = votes.filter((x) => x.refuted).length
  return fatal >= 2 ? 'refuted' : weak >= 2 ? 'weakened' : fatal === 1 ? 'contested' : 'survives'
}
// With a lens missing, a rating stands only if every answer the missing lens could have given leads
// to the same rating; otherwise the claim is "unrated". A missing lens never counts as "no objection".
const OUTCOMES = [{ refuted: false, severity: 'none' }, { refuted: true, severity: 'weakening' }, { refuted: true, severity: 'fatal' }]
function settle(votes, missing) {
  let fills = [[]]
  for (let k = 0; k < missing; k++) fills = fills.flatMap((f) => OUTCOMES.map((o) => [...f, o]))
  const ratings = new Set(fills.map((f) => rate([...votes, ...f])))
  return ratings.size === 1 ? [...ratings][0] : 'unrated'
}

// ---------------------------------------------------------------- 1. claims
phase('Claims')
let claims
let found = given.length
if (given.length) {
  claims = given.slice(0, MAX).map((c, i) => ({ id: `C${i + 1}`, claim: c, evidence: input.path ? `see ${input.path}` : 'not supplied' }))
} else {
  const extracted = await withRetry(
    `Read the manuscript at ${input.path} and list its headline claims — the ones in the title, abstract, and conclusions that the paper's ` +
      `contribution rests on — at most ${MAX}, most important first. For each, give the claim verbatim, the evidence the paper offers, and the design behind it.`,
    { schema: CLAIMS, label: 'extract headline claims' },
  )
  if (!extracted) {
    reasons.push('the claim-extraction agent failed twice, so no claim was tested')
    return finish('blocked', { message: `Could not extract claims from ${input.path}.` })
  }
  const list = (Array.isArray(extracted.claims) ? extracted.claims : []).filter((c) => c && typeof c.claim === 'string' && c.claim.trim())
  found = Math.max(Number.isInteger(extracted.total_found) ? extracted.total_found : 0, list.length)
  // Claims are numbered here so a missing or repeated extractor id cannot merge two claims.
  claims = list.slice(0, MAX).map((c, i) => ({ ...c, id: `C${i + 1}` }))
}
coverage.claims = { found, requested: claims.length, cap: MAX, not_tested: found - claims.length }
if (!claims.length) {
  reasons.push('no headline claims were found, so there was nothing to test')
  return finish('blocked', { message: 'No claims to test.' })
}
if (found > claims.length) {
  reasons.push(`capped: ${claims.length} of ${found} claims were tested (max_claims=${MAX})`)
  log(`Testing ${claims.length} of ${found} claims`)
}

// ---------------------------------------------------------------- 2. attack
phase('Attack')
// Three separate agents with different briefs. They are agents of the same model, so their
// agreement is not independent verification; the lenses exist to cover different failure modes.
const lensStat = { requested: claims.length * LENSES.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const attacked = await pipeline(claims, (c) =>
  parallel(LENSES.map((lens) => async () => {
    if (!canSpawn()) return null
    lensStat.dispatched++
    const v = await withRetry(
      `You are a skeptical referee with one job: find out whether this claim survives the ${lens.key} lens.\n` +
        `Claim ${c.id}: "${c.claim}"\nEvidence offered: ${c.evidence}\n${c.design ? `Design: ${c.design}\n` : ''}` +
        `${input.path ? `Manuscript: ${input.path}\n` : ''}${lens.brief}\n` +
        'Set refuted=true only if the claim as stated does not hold up; severity is "fatal" if it cannot be rescued by rewording, ' +
        '"weakening" if it holds only in a narrower form. Cite only sources you retrieved.',
      { schema: ATTACK, effort: 'high', label: `${c.id} · ${lens.key}`, phase: 'Attack' },
      lensStat,
    )
    return v && typeof v.refuted === 'boolean' ? { lens: lens.key, ...v } : null
  })),
)
// pipeline() keeps results aligned with its inputs, so a claim whose lenses all failed is still here.
const results = claims.map((c, i) => {
  const votes = (Array.isArray(attacked[i]) ? attacked[i] : []).filter(Boolean)
  lensStat.completed += votes.length
  const missingLenses = LENSES.map((l) => l.key).filter((k) => !votes.some((v) => v.lens === k))
  return { ...c, rating: settle(votes, missingLenses.length), lenses_completed: votes.length, lenses_missing: missingLenses, attacks: votes }
})
lensStat.failed = lensStat.dispatched - lensStat.completed
lensStat.unresolved = lensStat.requested - lensStat.completed
coverage.lenses = lensStat
const incomplete = results.filter((r) => r.lenses_completed < LENSES.length)
const unrated = results.filter((r) => r.rating === 'unrated')
coverage.claims.rated = results.length - unrated.length
coverage.claims.unrated = unrated.length
if (incomplete.length) {
  reasons.push(`${incomplete.length} of ${results.length} claims were judged with fewer than ${LENSES.length} completed lenses (${plural(lensStat.unresolved, 'lens attack')} missing after one retry)`)
  log(`${incomplete.length} claim(s) were judged with fewer than ${LENSES.length} lenses reporting`)
}
if (unrated.length) reasons.push(`${unrated.length} claim(s) are unrated: the lenses that completed do not settle a rating`)

// ---------------------------------------------------------------- 3. verdict
phase('Verdict')
const tally = {}
for (const r of results) tally[r.rating] = (tally[r.rating] || 0) + 1
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `Write a claim stress-test report to ${OUT} (Markdown). ${statusBrief(workStatus)}\n` +
    'Then a table: claim, rating (survives / contested / weakened / refuted / unrated), lenses completed (of 3), the decisive argument, and ' +
    'a calibrated rewrite that the evidence does support (keep "survives" claims as they are). A rating is computed from the lenses that ' +
    'completed and stands only if the missing lenses could not have changed it; an "unrated" claim had too few lenses complete — say which ' +
    'are missing and do not imply it survived. Then one section per claim with each completed lens\'s argument and its retrieved evidence, ' +
    'naming any lens that did not report. End with the three changes that would most strengthen the paper, a note that the three skeptics ' +
    'are separate agents of the same model (their agreement is not independent verification), and an AI-assistance disclosure. A ' +
    'contested claim had one fatal objection that the other lenses did not share — present both sides.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ claims: coverage.claims, lenses: lensStat })}\n` +
    `Ratings: ${JSON.stringify(tally)}\nResults: ${JSON.stringify(results, null, 1)}\n\nReply with a two-sentence summary.`,
  'write report',
  workStatus,
  [],
  'high',
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
const result = {
  ratings: tally,
  claims: results.map((r) => ({ id: r.id, rating: r.rating, lenses_completed: r.lenses_completed, lenses_missing: r.lenses_missing })),
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', result)
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, ...result })
