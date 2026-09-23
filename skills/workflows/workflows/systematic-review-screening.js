export const meta = {
  name: 'systematic-review-screening',
  description: 'PRISMA 2020 title/abstract screening with two blinded screeners per record, third-reviewer adjudication, and Cohen kappa computed in code',
  whenToUse: 'Systematic or scoping reviews: turn a question into a screening codebook, optionally run the database searches, de-duplicate, and dual-screen every record. Args: {question, records?, include?, exclude?, databases?, max_per_database?, batch?, out_dir?}.',
  phases: [
    { title: 'Protocol', detail: 'eligibility codebook and per-database search strings' },
    { title: 'Search', detail: 'one agent per database (skipped when a records export is supplied)' },
    { title: 'Deduplicate', detail: 'merge exports and remove duplicates by DOI, PMID, and normalized title' },
    { title: 'Screen', detail: 'two independent screeners per batch' },
    { title: 'Adjudicate', detail: 'a third reviewer resolves every disagreement' },
    { title: 'Report', detail: 'PRISMA 2020 flow numbers, agreement, and the included set' },
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

const chunk = (xs, n) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n))
// Title/abstract screening is deliberately inclusive: "unsure" goes forward to full text.
const passes = (d) => d.decision !== 'exclude'

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
const protocol = await agent(
  `Draft a screening protocol for this systematic review question: "${input.question}".\n` +
    `${input.include ? `Inclusion criteria given by the review team: ${JSON.stringify(input.include)}\n` : ''}` +
    `${input.exclude ? `Exclusion criteria given by the review team: ${JSON.stringify(input.exclude)}\n` : ''}` +
    'Keep the team\'s criteria verbatim where given and operationalize each into a coded rule with a borderline example. Add the standard ' +
    'title/abstract rule: when a record cannot be excluded with confidence, it goes forward to full text. Write the codebook to ' +
    `${OUT_DIR}/codebook.md, and give one search string per database for: ${DATABASES.join(', ')} (Boolean syntax native to each; MeSH for PubMed).`,
  { schema: PROTOCOL, effort: 'high', label: 'protocol + codebook' },
)
if (!protocol || !protocol.criteria.length) throw new Error('could not draft a screening protocol')
const codebook = protocol.criteria.map((c) => `${c.code} (${c.kind}): ${c.rule}${c.examples ? ` — e.g. ${c.examples}` : ''}`).join('\n')

// ---------------------------------------------------------------- 2. search (optional)
phase('Search')
let searches = []
if (!input.records) {
  const wanted = protocol.queries.filter((q) => DATABASES.some((d) => q.database.toLowerCase().includes(d.toLowerCase())))
  const runs = await pipeline(wanted.length ? wanted : protocol.queries, (q) =>
    agent(
      `Run this search in ${q.database} and save the results: ${q.query}\n` +
        `Use the matching AlterLab skill when installed (alterlab-pubmed, alterlab-openalex, alterlab-arxiv, alterlab-biorxiv, alterlab-clinicaltrials) ` +
        'or the database\'s public API. Retrieve at most ' + `${PER_DB} records, most relevant first, and write them as JSON Lines to ` +
        `${OUT_DIR}/records-${q.database.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.jsonl with fields: source, source_id, title, abstract, ` +
        'authors, year, journal, doi, pmid. Report the exact query executed and the database\'s total hit count.',
      { schema: SEARCH, label: `search ${q.database}`, phase: 'Search' },
    ),
  )
  searches = runs.filter(Boolean)
  for (const s of searches.filter((x) => x.capped)) {
    log(`${s.database}: kept ${s.count} of ${s.total_hits || 'more'} hits (max_per_database=${PER_DB}) — raise it for a complete search`)
  }
  if (!searches.length) throw new Error('no database search succeeded')
} else {
  log(`Using the supplied records export: ${input.records}`)
}

// ---------------------------------------------------------------- 3. deduplicate
phase('Deduplicate')
const sources = input.records ? [input.records] : searches.map((s) => s.file)
const dedup = await agent(
  `Merge these record files into one de-duplicated set: ${sources.join(', ')} (formats may be RIS, BibTeX, PubMed nbib, CSV, or JSON Lines). ` +
    'Write a small script to do it deterministically: remove duplicates by DOI, then PMID, then normalized title (lowercase, no punctuation) ' +
    `plus year; keep the most complete copy. Write the result to ${OUT_DIR}/records.jsonl, numbering records sid 1..N in a stable order, ` +
    'with fields sid, title, abstract, authors, year, journal, doi, pmid, sources. Report how many records each source contributed.',
  { schema: DEDUP, label: 'merge + de-duplicate' },
)
if (!dedup || dedup.total < 1) throw new Error('no records to screen after de-duplication')
const total = Math.min(dedup.total, MAX_SCREEN)
if (dedup.total > MAX_SCREEN) log(`Screening the first ${MAX_SCREEN} of ${dedup.total} records in this run; re-run with a narrower search for the rest`)

// ---------------------------------------------------------------- 4. dual independent screening
phase('Screen')
const batches = chunk(Array.from({ length: total }, (_, i) => i + 1), BATCH).map((ids) => ({ from: ids[0], to: ids[ids.length - 1] }))
log(`${total} records in ${batches.length} batches, two screeners each`)
const screenPrompt = (b, who) =>
  `You are screener ${who} in a systematic review (title/abstract stage). Question: "${input.question}".\nPICO: ${protocol.pico}\n` +
  `Codebook:\n${codebook}\n\nRead records sid ${b.from} to ${b.to} from ${dedup.file}. Decide each one on its title and abstract alone: ` +
  'include, exclude (cite the E-code that applies), or unsure (goes forward to full text). Judge every record in the range; work alone — ' +
  'another screener is deciding the same records independently.'
const screened = await pipeline(batches, (b, _item, i) =>
  parallel(['A', 'B'].map((who) => () =>
    agent(screenPrompt(b, who), { schema: DECISIONS, label: `batch ${i + 1} · screener ${who}`, phase: 'Screen' }),
  )).then(([a, b2]) => ({ batch: b, a: a ? a.decisions : [], b: b2 ? b2.decisions : [] })),
)

// ---------------------------------------------------------------- 5. adjudication (computed conflicts)
phase('Adjudicate')
const byA = new Map()
const byB = new Map()
for (const s of screened.filter(Boolean)) {
  for (const d of s.a) if (d.sid >= s.batch.from && d.sid <= s.batch.to) byA.set(d.sid, d)
  for (const d of s.b) if (d.sid >= s.batch.from && d.sid <= s.batch.to) byB.set(d.sid, d)
}
const pairs = []
const final = new Map()
const conflicts = []
for (let sid = 1; sid <= total; sid++) {
  const a = byA.get(sid)
  const b = byB.get(sid)
  if (a && b) {
    pairs.push([passes(a), passes(b)])
    if (passes(a) === passes(b)) final.set(sid, { sid, decision: passes(a) ? 'include' : 'exclude', code: a.code, by: 'agreement' })
    else conflicts.push({ sid, a, b })
  } else {
    conflicts.push({ sid, a: a || null, b: b || null }) // a missing decision is never silently excluded
  }
}
const kappa = cohenKappa(pairs)
const agreement = pairs.length ? Math.round((pairs.filter(([x, y]) => x === y).length / pairs.length) * 1000) / 10 : null
log(`Screener agreement ${agreement}% (Cohen kappa ${kappa === null ? 'not defined' : kappa}); ${conflicts.length} record(s) to adjudicate`)
const adjudicated = await pipeline(chunk(conflicts, 15), (group, _item, i) =>
  agent(
    `You are the third reviewer resolving screening disagreements for: "${input.question}".\nCodebook:\n${codebook}\n\n` +
      `Read these records from ${dedup.file} and make the final title/abstract decision for each (include, exclude, or unsure — ` +
      'unsure goes forward). The two screeners\' decisions are shown; decide on the record, not on who said what.\n' +
      JSON.stringify(group, null, 1),
    { schema: DECISIONS, effort: 'high', label: `adjudication ${i + 1}`, phase: 'Adjudicate' },
  ),
)
for (const run of adjudicated.filter(Boolean)) {
  for (const d of run.decisions) {
    if (d.sid >= 1 && d.sid <= total && !final.has(d.sid)) {
      final.set(d.sid, { sid: d.sid, decision: passes(d) ? 'include' : 'exclude', code: d.code, by: 'adjudication' })
    }
  }
}
for (const c of conflicts) {
  if (!final.has(c.sid)) final.set(c.sid, { sid: c.sid, decision: 'include', code: 'UNRESOLVED', by: 'default-forward' })
}

// ---------------------------------------------------------------- 6. report
phase('Report')
const decided = [...final.values()]
const included = decided.filter((d) => d.decision === 'include').map((d) => d.sid)
const excludedBy = {}
for (const d of decided.filter((x) => x.decision === 'exclude')) excludedBy[d.code || 'unspecified'] = (excludedBy[d.code || 'unspecified'] || 0) + 1
const flow = {
  identified: dedup.identified,
  duplicates_removed: dedup.duplicates_removed,
  screened: total,
  excluded_title_abstract: decided.length - included.length,
  excluded_by_criterion: excludedBy,
  sought_for_retrieval: included.length,
  not_screened_this_run: dedup.total - total,
}
const summary = await agent(
  `Write the screening report to ${OUT_DIR}/prisma-screening.md and the included records (joined with their titles, DOIs, and PMIDs from ` +
    `${dedup.file}) to ${OUT_DIR}/included.jsonl. The report needs: the question and PICO; the codebook; the search strategy per database ` +
    '(exact strings and dates, for a PRISMA-S appendix); a PRISMA 2020 flow table (identification → screening → sought for retrieval) with ' +
    'the numbers below; inter-rater agreement (percent agreement and Cohen\'s kappa; kappa is not defined when a screener used ' +
    'only one category); exclusion reasons by criterion; and next steps — full-text eligibility, data extraction, risk of bias (e.g. with the ' +
    'alterlab-literature-review or alterlab-meta-analysis skills). State that screening used AI agents as two independent screeners and that ' +
    'the review team must verify decisions before publication.\n\n' +
    `Flow: ${JSON.stringify(flow)}\nAgreement: ${agreement}% ; kappa: ${kappa}\nSearches: ${JSON.stringify(searches)}\n` +
    `Included sids: ${JSON.stringify(included)}\n\nReply with a two-sentence summary.`,
  { label: 'PRISMA report' },
)

return { report: `${OUT_DIR}/prisma-screening.md`, flow, agreement_percent: agreement, kappa, summary }
