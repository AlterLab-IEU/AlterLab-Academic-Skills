export const meta = {
  name: 'systematic-review-screening',
  description: 'PRISMA 2020 title/abstract screening with two separate blinded screener agents per record, third-reviewer adjudication, Cohen kappa computed in code, and every record whose screening or adjudication did not complete retained as UNRESOLVED',
  whenToUse: 'Systematic or scoping reviews: turn a question into a screening codebook, optionally run the database searches, de-duplicate, and dual-screen every record. Returns status complete / partial / blocked; unresolved records are never counted as screened, included, or excluded. Args: {question, records?, include?, exclude?, databases?, max_per_database?, batch?, out_dir?}.',
  phases: [
    { title: 'Protocol', detail: 'eligibility codebook and per-database search strings' },
    { title: 'Search', detail: 'one agent per database (skipped when a records export is supplied)' },
    { title: 'Deduplicate', detail: 'merge exports and remove duplicates by DOI, PMID, and normalized title' },
    { title: 'Screen', detail: 'two separate screeners per batch' },
    { title: 'Adjudicate', detail: 'a third reviewer resolves every disagreement and stands in for a failed screener' },
    { title: 'Report', detail: 'PRISMA 2020 flow numbers with unresolved records shown separately, agreement, the included set, and a read-back check' },
  ],
}

const input = typeof args === 'string' ? { question: args } : (args || {})
if (!input.question) {
  throw new Error('systematic-review-screening needs a review question: args {question, records?, include?, exclude?, databases?, out_dir?}')
}
const OUT_DIR = input.out_dir || 'alterlab-screening'
const BATCH = Math.min(Math.max(Number(input.batch) || 25, 5), 60)
const PER_DB = Math.min(Math.max(Number(input.max_per_database) || 300, 20), 2000)
const DATABASES = Array.isArray(input.databases) && input.databases.length ? input.databases : ['pubmed', 'openalex']
const MAX_SCREEN = 2000
const ADJ_GROUP = 15
const FIRST_PASS_AGENTS = 700 // keep two screeners per batch under this so retries and adjudication fit the cap

const PROTOCOL = {
  type: 'object',
  required: ['pico', 'criteria', 'queries'],
  properties: {
    pico: { type: 'string', description: 'population, intervention/exposure, comparator, outcomes, study designs' },
    criteria: {
      type: 'array',
      items: {
        type: 'object',
        required: ['code', 'kind', 'rule'],
        properties: {
          code: { type: 'string', description: 'I1, I2 ... for inclusion; E1, E2 ... for exclusion' },
          kind: { type: 'string', enum: ['include', 'exclude'] },
          rule: { type: 'string' },
          examples: { type: 'string' },
        },
      },
    },
    queries: {
      type: 'array',
      items: {
        type: 'object',
        required: ['database', 'query'],
        properties: { database: { type: 'string' }, query: { type: 'string' } },
      },
    },
  },
}

const SEARCH = {
  type: 'object',
  required: ['database', 'query_run', 'count', 'capped', 'file'],
  properties: {
    database: { type: 'string' },
    query_run: { type: 'string', description: 'the exact query string executed, for the PRISMA-S appendix' },
    count: { type: 'integer', description: 'records written to the file' },
    total_hits: { type: 'integer', description: 'hits the database reported, before the cap' },
    capped: { type: 'boolean' },
    file: { type: 'string' },
  },
}

const DEDUP = {
  type: 'object',
  required: ['identified', 'duplicates_removed', 'total', 'file'],
  properties: {
    identified: {
      type: 'array',
      items: {
        type: 'object',
        required: ['source', 'n'],
        properties: { source: { type: 'string' }, n: { type: 'integer' } },
      },
    },
    duplicates_removed: { type: 'integer' },
    total: { type: 'integer', description: 'unique records written, numbered sid 1..total' },
    file: { type: 'string' },
  },
}

const DECISIONS = {
  type: 'object',
  required: ['decisions'],
  properties: {
    decisions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['sid', 'decision', 'code', 'reason'],
        properties: {
          sid: { type: 'integer' },
          decision: { type: 'string', enum: ['include', 'exclude', 'unsure'] },
          code: { type: 'string', description: 'the codebook criterion that decided it (e.g. E2), or I for include' },
          reason: { type: 'string', description: 'one sentence' },
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
// bounded: no call, batch item, or record is attempted more than twice per stage.
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
const chunk = (xs, n) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n))
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

// Keep only answers whose id was sent in this call. Duplicates that agree count once; duplicates that
// disagree are discarded (so the item is retried); answers with a missing or unknown id are ignored.
function collect(list, expected, key, same) {
  const got = new Map()
  const conflicted = new Set()
  for (const r of Array.isArray(list) ? list : []) {
    const id = r && typeof r === 'object' ? r[key] : undefined
    if (id === undefined || id === null || id === '') {
      idIssues.missing++
    } else if (!expected.has(id)) {
      idIssues.unknown++
    } else if (got.has(id) || conflicted.has(id)) {
      idIssues.duplicate++
      if (got.has(id) && !same(got.get(id), r)) {
        got.delete(id)
        conflicted.add(id)
        idIssues.conflicting++
      }
    } else {
      got.set(id, r)
    }
  }
  return got
}

// Batched calls with per-item accounting. Items and answers share an id `key`; answers are read from
// `field` of each result. A batch that fails is re-sent once, and so are the items a batch omitted
// or answered inconsistently.
async function batched(items, size, key, field, labelOf, send, same) {
  const stat = { requested: items.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
  const answers = new Map()
  await pipeline(chunk(items, size), async (batch, _item, i) => {
    let todo = batch
    for (let attempt = 0; attempt < 2 && todo.length && canSpawn(); attempt++) {
      if (attempt) {
        retries++
        stat.retried++
      } else {
        stat.dispatched += batch.length
      }
      const out = await send(todo, attempt ? `${labelOf(batch, i)} (retry)` : labelOf(batch, i))
      const got = collect(out && out[field], new Set(todo.map((x) => x[key])), key, same)
      for (const [id, r] of got) answers.set(id, r)
      todo = todo.filter((x) => !got.has(x[key]))
    }
  })
  stat.completed = answers.size
  stat.failed = stat.dispatched - stat.completed
  stat.unresolved = stat.requested - stat.completed
  return { answers, stat }
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
  'below (for each stage: requested, dispatched, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This screening run is PARTIAL: say so plainly in the first paragraph, give the status reasons, and say which records are unresolved. ' : '') +
  'Never describe a record as screened, included, or excluded unless the data below gives it a resolved decision.'

// Title/abstract screening is deliberately inclusive: "unsure" goes forward to full text.
const passes = (d) => d.decision !== 'exclude'
const sameCall = (a, b) => passes(a) === passes(b)

function cohenKappa(pairs) {
  const n = pairs.length
  if (!n) return null
  let agree = 0
  let aYes = 0
  let bYes = 0
  for (const [a, b] of pairs) {
    if (a === b) agree++
    if (a) aYes++
    if (b) bYes++
  }
  const po = agree / n
  const pe = (aYes / n) * (bYes / n) + (1 - aYes / n) * (1 - bYes / n)
  if (pe === 1) return null // both screeners used a single category: kappa is undefined
  return Math.round(((po - pe) / (1 - pe)) * 1000) / 1000
}

// ---------------------------------------------------------------- 1. protocol
phase('Protocol')
const protocol = await withRetry(
  `Draft a screening protocol for this systematic review question: "${input.question}".\n` +
    `${input.include ? `Inclusion criteria given by the review team: ${JSON.stringify(input.include)}\n` : ''}` +
    `${input.exclude ? `Exclusion criteria given by the review team: ${JSON.stringify(input.exclude)}\n` : ''}` +
    'Keep the team\'s criteria verbatim where given and operationalize each into a coded rule with a borderline example. Add the standard ' +
    'title/abstract rule: when a record cannot be excluded with confidence, it goes forward to full text. Write the codebook to ' +
    `${OUT_DIR}/codebook.md, and give one search string per database for: ${DATABASES.join(', ')} (Boolean syntax native to each; MeSH for PubMed).`,
  { schema: PROTOCOL, effort: 'high', label: 'protocol + codebook' },
)
if (!protocol || !Array.isArray(protocol.criteria) || !protocol.criteria.length) {
  reasons.push(protocol ? 'the protocol agent returned no eligibility criteria' : 'the protocol agent failed twice')
  return finish('blocked', { message: 'Could not draft a screening protocol, so nothing was screened.' })
}
const codebook = protocol.criteria.map((c) => `${c.code} (${c.kind}): ${c.rule}${c.examples ? ` — e.g. ${c.examples}` : ''}`).join('\n')

// ---------------------------------------------------------------- 2. search (optional)
phase('Search')
let searches = []
if (!input.records) {
  const queries = (Array.isArray(protocol.queries) ? protocol.queries : []).filter((q) => q && typeof q.database === 'string' && typeof q.query === 'string')
  const covers = (q, d) => q.database.toLowerCase().includes(String(d).toLowerCase())
  const withoutQuery = DATABASES.filter((d) => !queries.some((q) => covers(q, d)))
  const wanted = queries.filter((q) => DATABASES.some((d) => covers(q, d)))
  const toRun = wanted.length ? wanted : queries
  if (withoutQuery.length) reasons.push(`no search string was drafted for ${withoutQuery.join(', ')}, so ${withoutQuery.length === 1 ? 'it was' : 'they were'} not searched`)
  const searchStat = { requested: toRun.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0, databases_requested: DATABASES, databases_without_query: withoutQuery }
  const runs = await pipeline(toRun, async (q) => {
    if (!canSpawn()) return null
    searchStat.dispatched++
    return withRetry(
      `Run this search in ${q.database} and save the results: ${q.query}\n` +
        `Use the matching AlterLab skill when installed (alterlab-pubmed, alterlab-openalex, alterlab-arxiv, alterlab-biorxiv, alterlab-clinicaltrials) ` +
        'or the database\'s public API. Retrieve at most ' + `${PER_DB} records, most relevant first, and write them as JSON Lines to ` +
        `${OUT_DIR}/records-${q.database.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.jsonl with fields: source, source_id, title, abstract, ` +
        'authors, year, journal, doi, pmid. Report the exact query executed and the database\'s total hit count.',
      { schema: SEARCH, label: `search ${q.database}`, phase: 'Search' },
      searchStat,
    )
  })
  searches = runs.filter(Boolean)
  const failedSearches = toRun.filter((_, i) => !runs[i]).map((q) => q.database)
  searchStat.completed = searches.length
  searchStat.failed = searchStat.dispatched - searchStat.completed
  searchStat.unresolved = searchStat.requested - searchStat.completed
  searchStat.failed_databases = failedSearches
  coverage.searches = searchStat
  for (const s of searches.filter((x) => x.capped)) {
    const hits = Number.isInteger(s.total_hits) ? `${s.total_hits}` : 'more'
    reasons.push(`capped: ${s.database} returned ${hits} hits but only ${s.count} were retrieved (max_per_database=${PER_DB}); identification is incomplete`)
    log(`${s.database}: kept ${s.count} of ${hits} hits (max_per_database=${PER_DB}) — raise it for a complete search`)
  }
  if (!searches.length) {
    reasons.push(toRun.length ? `every database search failed (${failedSearches.join(', ')}), each after one retry` : 'the protocol gave no search strings')
    return finish('blocked', { message: 'No database search succeeded, so nothing was screened.' })
  }
  if (failedSearches.length) reasons.push(`the search failed for ${failedSearches.join(', ')} after one retry; identification is incomplete`)
} else {
  log(`Using the supplied records export: ${input.records}`)
}

// ---------------------------------------------------------------- 3. deduplicate
phase('Deduplicate')
const sources = input.records ? [input.records] : searches.map((s) => s.file)
const dedup = await withRetry(
  `Merge these record files into one de-duplicated set: ${sources.join(', ')} (formats may be RIS, BibTeX, PubMed nbib, CSV, or JSON Lines). ` +
    'Write a small script to do it deterministically: remove duplicates by DOI, then PMID, then normalized title (lowercase, no punctuation) ' +
    `plus year; keep the most complete copy. Write the result to ${OUT_DIR}/records.jsonl, numbering records sid 1..N in a stable order, ` +
    'with fields sid, title, abstract, authors, year, journal, doi, pmid, sources. Report how many records each source contributed.',
  { schema: DEDUP, label: 'merge + de-duplicate' },
)
if (!dedup) {
  reasons.push('the de-duplication agent failed twice, so nothing was screened')
  return finish('blocked', { message: 'De-duplication failed.' })
}
if (!Number.isInteger(dedup.total) || dedup.total < 1) {
  reasons.push('no records remained after de-duplication, so there was nothing to screen')
  return finish('blocked', { message: 'No records to screen after de-duplication.' })
}
const total = Math.min(dedup.total, MAX_SCREEN)
if (dedup.total > MAX_SCREEN) {
  reasons.push(`capped: this run screens the first ${MAX_SCREEN} of ${dedup.total} records; ${dedup.total - MAX_SCREEN} were not screened`)
  log(`Screening the first ${MAX_SCREEN} of ${dedup.total} records in this run; re-run with a narrower search for the rest`)
}

// ---------------------------------------------------------------- 4. dual screening by separate agents
phase('Screen')
const size = Math.max(BATCH, Math.ceil((2 * total) / FIRST_PASS_AGENTS))
if (size > BATCH) log(`Batch size raised from ${BATCH} to ${size} so ${total} records fit the agent cap`)
const records = Array.from({ length: total }, (_, i) => ({ sid: i + 1 }))
log(`${total} records in ${Math.ceil(total / size)} batches, two screeners each`)
const span = (ids) => (ids.length > 1 && ids[ids.length - 1] - ids[0] === ids.length - 1 ? `sid ${ids[0]} to ${ids[ids.length - 1]}` : `sid ${ids.join(', ')}`)
const screenPrompt = (ids, who) =>
  `You are screener ${who} in a systematic review (title/abstract stage). Question: "${input.question}".\nPICO: ${protocol.pico}\n` +
  `Codebook:\n${codebook}\n\nRead records ${span(ids)} from ${dedup.file}. Decide each one on its title and abstract alone: ` +
  'include, exclude (cite the E-code that applies), or unsure (goes forward to full text). Judge every record listed, once each, using its ' +
  'sid; work alone — another screener decides the same records separately, and you must not look at their decisions.'
const screen = (who) =>
  batched(
    records,
    size,
    'sid',
    'decisions',
    (_batch, i) => `batch ${i + 1} · screener ${who}`,
    (batch, label) => tryAgent(screenPrompt(batch.map((r) => r.sid), who), { schema: DECISIONS, label, phase: 'Screen' }),
    sameCall,
  )
const [runA, runB] = await parallel([() => screen('A'), () => screen('B')])
const byA = runA ? runA.answers : new Map()
const byB = runB ? runB.answers : new Map()
const screenerStat = {
  requested: 2 * total,
  dispatched: (runA ? runA.stat.dispatched : 0) + (runB ? runB.stat.dispatched : 0),
  completed: byA.size + byB.size,
  retried: (runA ? runA.stat.retried : 0) + (runB ? runB.stat.retried : 0),
}
screenerStat.failed = screenerStat.dispatched - screenerStat.completed
screenerStat.unresolved = screenerStat.requested - screenerStat.completed

// ---------------------------------------------------------------- 5. adjudication (computed conflicts)
phase('Adjudicate')
// Resolution rules (conservative; nothing is silently excluded):
//   both screeners decided and agree       -> their decision
//   both decided and disagree              -> the adjudicator's decision
//   only one screener decided              -> the adjudicator reviews it as the second reviewer; the
//                                             decision stands only if the two agree
//   neither screener decided               -> UNRESOLVED (not sent to adjudication)
//   adjudication needed but did not finish -> UNRESOLVED
// UNRESOLVED records are retained for the review team and not counted as screened, included, or excluded.
const final = new Map()
const unresolved = new Map()
const toAdjudicate = []
const pairs = []
const tallyBy = { agreement: 0, adjudication: 0, second_review: 0 }
for (const { sid } of records) {
  const a = byA.get(sid)
  const b = byB.get(sid)
  if (a && b) {
    pairs.push([passes(a), passes(b)])
    if (passes(a) === passes(b)) final.set(sid, { sid, decision: passes(a) ? 'include' : 'exclude', code: a.code, by: 'agreement' })
    else toAdjudicate.push({ sid, need: 'conflict', a, b })
  } else if (a || b) {
    toAdjudicate.push({ sid, need: 'second_review', a: a || null, b: b || null })
  } else {
    unresolved.set(sid, 'neither screener returned a decision (each was retried once)')
  }
}
const kappa = cohenKappa(pairs)
const agreement = pairs.length ? Math.round((pairs.filter(([x, y]) => x === y).length / pairs.length) * 1000) / 10 : null
log(`Screener agreement ${agreement === null ? 'not defined' : `${agreement}%`} on ${plural(pairs.length, 'record')} (Cohen kappa ${kappa === null ? 'not defined' : kappa}); ${toAdjudicate.length} record(s) to adjudicate`)
const adjRun = await batched(
  toAdjudicate,
  ADJ_GROUP,
  'sid',
  'decisions',
  (_group, i) => `adjudication ${i + 1}`,
  (group, label) =>
    tryAgent(
      `You are the third reviewer for title/abstract screening on: "${input.question}".\nCodebook:\n${codebook}\n\n` +
        `Read these records from ${dedup.file} and make a title/abstract decision for each (include, exclude, or unsure — unsure goes ` +
        'forward). For need=conflict the two screeners disagreed: yours is the final decision. For need=second_review one screener\'s ' +
        'decision is missing: decide the record yourself as the second reviewer. Decide on the record, not on who said what. Return one ' +
        'decision per sid listed.\n' +
        JSON.stringify(group, null, 1),
      { schema: DECISIONS, effort: 'high', label, phase: 'Adjudicate' },
    ),
  sameCall,
)
for (const c of toAdjudicate) {
  const d = adjRun.answers.get(c.sid)
  if (!d) {
    unresolved.set(c.sid, c.need === 'conflict' ? 'the screeners disagreed and adjudication did not complete' : 'one screener failed and the second review did not complete')
  } else if (c.need === 'conflict') {
    final.set(c.sid, { sid: c.sid, decision: passes(d) ? 'include' : 'exclude', code: d.code, by: 'adjudication' })
  } else if (passes(d) === passes(c.a || c.b)) {
    final.set(c.sid, { sid: c.sid, decision: passes(d) ? 'include' : 'exclude', code: d.code, by: 'second_review' })
  } else {
    unresolved.set(c.sid, 'one screener failed, and that screener and the second reviewer disagree')
  }
}
for (const d of final.values()) tallyBy[d.by]++
coverage.screening = {
  records: total,
  screener_decisions: screenerStat,
  records_with_both_screeners: pairs.length,
  records_with_one_screener: toAdjudicate.filter((c) => c.need === 'second_review').length,
  records_with_no_screener: [...unresolved.values()].filter((r) => r.startsWith('neither')).length,
}
coverage.adjudication = { ...adjRun.stat, conflicts: toAdjudicate.filter((c) => c.need === 'conflict').length, second_reviews: coverage.screening.records_with_one_screener }
coverage.records = { requested: total, resolved: final.size, unresolved: unresolved.size, resolved_by: tallyBy }
if (screenerStat.unresolved) {
  reasons.push(`${screenerStat.unresolved} of ${screenerStat.requested} screener decisions are missing after one retry, so not every record was dual-screened`)
}
if (unresolved.size) {
  reasons.push(`${unresolved.size} of ${total} records are UNRESOLVED (screening or adjudication did not complete); they are retained for the review team and not counted as screened, included, or excluded`)
  log(`${unresolved.size} record(s) unresolved`)
}

// ---------------------------------------------------------------- 6. report
phase('Report')
const decided = [...final.values()].sort((x, y) => x.sid - y.sid)
const included = decided.filter((d) => d.decision === 'include').map((d) => d.sid)
const excludedBy = {}
for (const d of decided.filter((x) => x.decision === 'exclude')) excludedBy[d.code || 'unspecified'] = (excludedBy[d.code || 'unspecified'] || 0) + 1
const unresolvedList = [...unresolved].map(([sid, reason]) => ({ sid, reason })).sort((x, y) => x.sid - y.sid)
const flow = {
  identified: dedup.identified,
  duplicates_removed: dedup.duplicates_removed,
  records_after_deduplication: dedup.total,
  submitted_for_screening: total,
  screened: decided.length, // records with a resolved title/abstract decision
  unresolved: unresolvedList.length, // retained; not screened, included, or excluded
  excluded_title_abstract: decided.length - included.length,
  excluded_by_criterion: excludedBy,
  sought_for_retrieval: included.length,
  not_screened_this_run: dedup.total - total,
}
const INCLUDED_FILE = `${OUT_DIR}/included.jsonl`
const UNRESOLVED_FILE = `${OUT_DIR}/unresolved.jsonl`
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  `${OUT_DIR}/prisma-screening.md`,
  `Write the screening report to ${OUT_DIR}/prisma-screening.md, the included records (joined with their titles, DOIs, and PMIDs from ` +
    `${dedup.file}) to ${INCLUDED_FILE} (one JSON object per line), and the UNRESOLVED records with their reasons to ${UNRESOLVED_FILE} ` +
    `(one per line; leave the file empty when there are none). ${statusBrief(workStatus)}\n` +
    'The report needs: the question and PICO; the codebook; the search strategy per database (exact strings and dates, for a PRISMA-S ' +
    'appendix), naming any database whose search failed or was capped; a PRISMA 2020 flow table (identification → screening → sought for ' +
    'retrieval) with the numbers below, where "screened" counts only records with a resolved decision and UNRESOLVED records appear on their ' +
    'own row — never fold them into screened, included, or excluded; until the review team screens them the flow is provisional. Then ' +
    'how each record was resolved (agreement, adjudication, or second review standing in for a failed screener); inter-rater agreement ' +
    '(percent agreement and Cohen\'s kappa with the number of dual-screened records they are computed on; kappa is not defined when a ' +
    'screener used only one category); exclusion reasons by criterion; and next steps — screening the unresolved records, full-text ' +
    'eligibility, data extraction, risk of bias (e.g. with the alterlab-literature-review or alterlab-meta-analysis skills). State that ' +
    'screening used two separate AI screener agents of the same model, so their agreement and kappa measure consistency between two runs ' +
    'of one model, not agreement between independent human screeners, and that the review team must verify decisions before publication.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ searches: coverage.searches || 'records export supplied', screening: coverage.screening, adjudication: coverage.adjudication, records: coverage.records })}\n` +
    `Flow: ${JSON.stringify(flow)}\nAgreement: ${agreement === null ? 'not defined' : `${agreement}%`} on ${pairs.length} dual-screened records; kappa: ${kappa === null ? 'not defined' : kappa}\n` +
    `Searches: ${JSON.stringify(searches)}\nIncluded sids: ${JSON.stringify(included)}\nUNRESOLVED records: ${JSON.stringify(unresolvedList)}\n\n` +
    'Reply with a two-sentence summary that states how many records are unresolved.',
  'PRISMA report',
  workStatus,
  [INCLUDED_FILE, UNRESOLVED_FILE],
)
coverage.report = { path: `${OUT_DIR}/prisma-screening.md`, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check, files: delivered.others }
const result = {
  flow,
  agreement_percent: agreement,
  kappa,
  kappa_records: pairs.length,
  included_sids: included,
  unresolved: unresolvedList,
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', { files: { included: null, unresolved: null }, ...result })
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
// The record files count only when read back with the expected number of lines.
const fileOk = (p, n) => delivered.others[p] && delivered.others[p].exists && delivered.others[p].lines === n
if (!fileOk(INCLUDED_FILE, included.length)) reasons.push(`${INCLUDED_FILE} was not read back with ${plural(included.length, 'line')}`)
if (!fileOk(UNRESOLVED_FILE, unresolvedList.length)) reasons.push(`${UNRESOLVED_FILE} was not read back with ${plural(unresolvedList.length, 'line')}`)
return finish(reasons.length ? 'partial' : 'complete', {
  report: delivered.report,
  files: { included: fileOk(INCLUDED_FILE, included.length) ? INCLUDED_FILE : null, unresolved: fileOk(UNRESOLVED_FILE, unresolvedList.length) ? UNRESOLVED_FILE : null },
  ...result,
})
