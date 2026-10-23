export const meta = {
  name: 'literature-map',
  description: 'Map a research field: parallel scholarly-database sweeps from several angles, merged and clustered into themes, with up to 12 proposed research gaps each searched for existing work before it is reported as open; unchecked gaps are listed as unchecked',
  whenToUse: 'Starting a project, proposal, or thesis chapter: find the themes, landmark and recent papers, methods, and open questions in a topic. Returns status complete / partial / blocked with requested-vs-completed sweep and gap-check counts. Args: a topic string, or {topic, seeds?: [DOIs], years?, out_dir?}.',
  phases: [
    { title: 'Plan', detail: 'search angles and database-native queries' },
    { title: 'Sweep', detail: 'one agent per angle across OpenAlex, PubMed, arXiv, and citation links' },
    { title: 'Cluster', detail: 'themes, landmark works, methods, open questions' },
    { title: 'Gaps', detail: 'each candidate gap searched for work that already fills it' },
    { title: 'Map', detail: 'the field map and research-question shortlist, then a read-back check that the file exists' },
  ],
}

const input = typeof args === 'string' ? { topic: args } : (args || {})
if (!input.topic) {
  throw new Error('literature-map needs a topic: /alterlab-workflows:literature-map "LLM-assisted qualitative coding" — or args {topic, seeds?, years?, out_dir?}')
}
const OUT_DIR = input.out_dir || 'alterlab-literature-map'
const OUT = `${OUT_DIR}/literature-map.md`
const YEARS = input.years || 'all years, with extra attention to the last five'
const seeds = Array.isArray(input.seeds) ? input.seeds : []
const MAX_ANGLES = 6
const MAX_CORPUS = 150
const MAX_GAPS = 12

const PLAN = {
  type: 'object',
  required: ['angles'],
  properties: {
    angles: {
      type: 'array',
      items: {
        type: 'object',
        required: ['key', 'rationale', 'query'],
        properties: {
          key: { type: 'string', description: 'short slug' },
          rationale: { type: 'string' },
          query: { type: 'string', description: 'an OpenAlex search string; add PubMed or arXiv syntax in the rationale when those databases matter' },
        },
      },
    },
  },
}

// Keyless OpenAlex list/search calls share a small per-IP daily budget and then answer HTTP 429
// (single-DOI lookups keep working). A rate-limited source was not searched; it is never evidence
// that no works exist.
const KEYLESS_SOURCES =
  'OpenAlex searches are often rate-limited without a key (HTTP 429; single-DOI lookups still work). If a source answers 429 or ' +
  'fails, continue with the other keyless public APIs: Crossref (api.crossref.org/works?query=...), Europe PMC ' +
  '(www.ebi.ac.uk/europepmc/webservices/rest/search), arXiv (export.arxiv.org/api/query), and name the unavailable source. A ' +
  'rate-limited source means not searched, never no works found.'

const SWEEP = {
  type: 'object',
  required: ['key', 'count', 'top'],
  properties: {
    key: { type: 'string' },
    count: { type: 'integer', description: 'records saved to the angle file' },
    top: {
      type: 'array',
      items: {
        type: 'object',
        required: ['title', 'year'],
        properties: {
          title: { type: 'string' },
          year: { type: 'integer' },
          doi: { type: 'string' },
          cited_by: { type: 'integer' },
          why: { type: 'string', description: 'one line on why it matters for the topic' },
        },
      },
    },
  },
}

const THEMES = {
  type: 'object',
  required: ['themes'],
  properties: {
    themes: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'summary', 'key_works', 'open_questions'],
        properties: {
          name: { type: 'string' },
          summary: { type: 'string' },
          key_works: { type: 'array', items: { type: 'string' }, description: 'DOIs or titles from the sweep' },
          methods: { type: 'string' },
          open_questions: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  },
}

const GAP = {
  type: 'object',
  required: ['open', 'evidence'],
  properties: {
    open: { type: 'boolean', description: 'false if you found work that already answers it' },
    searched: { type: 'boolean', description: 'false when no database could actually be searched (every source rate-limited or failing)' },
    evidence: { type: 'string', description: 'the works you found (DOIs) or the searches that came up empty' },
    sharpened: { type: 'string', description: 'the question, narrowed to what is genuinely still open' },
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
const RESERVED = 6 // held back so the map can always be written and read back
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
  `Open the map with its title, then the line "Status: ${s.toUpperCase()}", then a short coverage table built from the Coverage object ` +
  'below (angles swept and gaps checked: requested, dispatched, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This map is PARTIAL: say so plainly in the first paragraph and give the status reasons. ' : '') +
  'Never describe a gap as open or checked unless the data below shows its search completed.'

const norm = (w) => (w.doi ? w.doi.toLowerCase().replace(/^https?:\/\/(dx\.)?doi\.org\//, '') : `${(w.title || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()}|${w.year}`)

// ---------------------------------------------------------------- 1. plan
phase('Plan')
const plan = await withRetry(
  `Plan a literature map of: "${input.topic}" (${YEARS}).${seeds.length ? ` Seed papers: ${seeds.join(', ')}.` : ''}\n` +
    'Propose 4–6 search angles that together cover the field and would each surface different papers: core terminology and its synonyms, ' +
    'the main methods, key populations or application settings, adjacent fields that use other vocabulary, recent preprints, and (when ' +
    'seeds are given) their citation neighbourhood. Give each a database-native query and a distinct key.',
  { schema: PLAN, label: 'search plan' },
)
if (!plan) {
  reasons.push('the planning agent failed twice, so no search was run')
  return finish('blocked', { message: 'Could not plan search angles.' })
}
// Angle keys name the output files, so they must be unique.
const allAngles = []
const angleKeys = new Set()
for (const [k, a] of (Array.isArray(plan.angles) ? plan.angles : []).entries()) {
  if (!a || typeof a.query !== 'string' || !a.query.trim()) continue
  let key = (typeof a.key === 'string' && a.key.trim() ? a.key.trim() : `angle${k + 1}`).replace(/[^a-z0-9-]+/gi, '-')
  if (angleKeys.has(key)) {
    idIssues.duplicate++
    key = `${key}-${k + 1}`
  }
  angleKeys.add(key)
  allAngles.push({ ...a, key })
}
const angles = allAngles.slice(0, MAX_ANGLES)
if (!angles.length) {
  reasons.push('the plan contained no usable search angles')
  return finish('blocked', { message: 'Could not plan search angles.' })
}
if (allAngles.length > MAX_ANGLES) {
  reasons.push(`capped: ${MAX_ANGLES} of ${allAngles.length} planned angles were swept`)
  log(`Sweeping the first ${MAX_ANGLES} of ${allAngles.length} angles`)
}

// ---------------------------------------------------------------- 2. sweep (one agent per angle)
phase('Sweep')
const sweepStat = { requested: angles.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const sweeps = await pipeline(angles, async (a) => {
  if (!canSpawn()) return null
  sweepStat.dispatched++
  const s = await withRetry(
    `Search the literature for the "${a.key}" angle of "${input.topic}" (${YEARS}). Rationale: ${a.rationale}\nQuery: ${a.query}\n` +
      'Use the alterlab-openalex skill (and alterlab-pubmed, alterlab-arxiv, or alterlab-citation-graph where they fit) when installed, or ' +
      'the public APIs. ' + KEYLESS_SOURCES + ' Save up to 200 records to ' + `${OUT_DIR}/angle-${a.key}.jsonl ` +
      '(title, year, doi, authors, venue, cited_by, abstract) and return the 25 most important for the topic — landmark and highly cited ' +
      'works plus the strongest recent ones — with a line on why each matters. Report only works you retrieved.',
    { schema: SWEEP, label: `sweep: ${a.key}`, phase: 'Sweep' },
    sweepStat,
  )
  return s && Array.isArray(s.top) ? { ...s, key: a.key } : null
})
const doneSweeps = sweeps.filter(Boolean)
const failedAngles = angles.filter((_, i) => !sweeps[i]).map((a) => a.key)
sweepStat.completed = doneSweeps.length
sweepStat.failed = sweepStat.dispatched - sweepStat.completed
sweepStat.unresolved = sweepStat.requested - sweepStat.completed
coverage.sweeps = { ...sweepStat, failed_angles: failedAngles }
if (!doneSweeps.length) {
  reasons.push(`every search sweep failed (${failedAngles.join(', ')}), each after one retry`)
  return finish('blocked', { angles: angles.map((a) => a.key), message: 'No search sweep succeeded.' })
}
if (failedAngles.length) reasons.push(`${failedAngles.length} of ${angles.length} search angles returned nothing after one retry: ${failedAngles.join(', ')}`)
// Merge across angles in code: the de-duplicated union and how many angles surfaced each work.
const merged = new Map()
for (const s of doneSweeps) {
  for (const w of s.top) {
    if (!w || typeof w.title !== 'string') continue
    const k = norm(w)
    const prev = merged.get(k)
    if (prev && prev.angles.includes(s.key)) continue // the same work listed twice by one angle counts once
    merged.set(k, prev ? { ...prev, angles: [...prev.angles, s.key] } : { ...w, angles: [s.key] })
  }
}
const corpus = [...merged.values()].sort((x, y) => y.angles.length - x.angles.length || (y.cited_by || 0) - (x.cited_by || 0))
const clusterSet = corpus.slice(0, MAX_CORPUS)
coverage.works = { merged: corpus.length, clustered: clusterSet.length, cap: MAX_CORPUS }
if (corpus.length > MAX_CORPUS) reasons.push(`capped: the ${MAX_CORPUS} top-ranked of ${corpus.length} key works were clustered`)
log(`${corpus.length} distinct key works across ${doneSweeps.length} of ${angles.length} angles`)

// ---------------------------------------------------------------- 3. cluster (needs the whole corpus)
phase('Cluster')
const clustered = await withRetry(
  `Cluster these key works on "${input.topic}" into 4–8 themes. For each theme: a name, a paragraph on what it studies and where it ` +
    'stands, its key works (use the DOIs given), its dominant methods, and 1–3 open questions the works themselves point to (limitations, ' +
    'future-work sections, conflicting results). Works surfaced by several angles are likely central.\n\n' +
    JSON.stringify(clusterSet, null, 1),
  { schema: THEMES, effort: 'high', label: 'cluster themes' },
)
const themes = clustered && Array.isArray(clustered.themes) ? clustered.themes.filter((t) => t && typeof t.name === 'string') : []
coverage.clustering = { requested: 1, completed: clustered ? 1 : 0, themes: themes.length }
if (!clustered) reasons.push('the clustering agent failed twice: the map has no themes, and no candidate gap could be checked')
const allCandidates = themes.flatMap((t) => (Array.isArray(t.open_questions) ? t.open_questions : []).filter((q) => typeof q === 'string' && q.trim()).map((q) => ({ theme: t.name, question: q })))
const candidates = allCandidates.slice(0, MAX_GAPS)
const notChecked = allCandidates.slice(MAX_GAPS)
if (notChecked.length) {
  reasons.push(`capped: ${candidates.length} of ${allCandidates.length} candidate gaps were searched for existing answers; the rest are listed as unchecked`)
  log(`Checking the first ${candidates.length} of ${allCandidates.length} candidate gaps`)
}

// ---------------------------------------------------------------- 4. gaps (adversarial search)
phase('Gaps')
const gapStat = { requested: candidates.length, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const gapChecks = await pipeline(candidates, async (g) => {
  if (!canSpawn()) return null
  gapStat.dispatched++
  return withRetry(
    `Someone proposes this as an open research question in "${input.topic}" (theme: ${g.theme}): "${g.question}"\n` +
      'Try to show it is already answered: search for studies, reviews, and recent preprints that address it directly. Mark it open only ' +
      'if a real search finds nothing that answers it; if it is partly answered, narrow the question to what remains open. ' +
      KEYLESS_SOURCES + ' Set searched to false if no database could be searched at all.',
    { schema: GAP, effort: 'high', label: `gap: ${g.theme}`, phase: 'Gaps' },
    gapStat,
  )
})
// pipeline() keeps results aligned with its inputs, so a gap whose search failed is still here.
const open = []
const answered = []
const unchecked = [...notChecked.map((g) => ({ ...g, why: `beyond the ${MAX_GAPS}-gap cap` }))]
candidates.forEach((g, i) => {
  const v = gapChecks[i]
  if (!v || typeof v.open !== 'boolean') unchecked.push({ ...g, why: 'the search for existing answers did not complete' })
  else if (v.searched === false) unchecked.push({ ...g, why: 'no database could be searched (rate-limited or failing sources)' })
  else if (v.open) open.push({ ...g, ...v })
  else answered.push({ ...g, ...v })
})
gapStat.completed = open.length + answered.length
gapStat.failed = gapStat.dispatched - gapStat.completed
gapStat.unresolved = gapStat.requested - gapStat.completed
coverage.gaps = { ...gapStat, candidates: allCandidates.length, beyond_cap: notChecked.length }
if (gapStat.unresolved) reasons.push(`${gapStat.unresolved} of ${candidates.length} candidate gaps could not be searched (after one retry); they are listed as unchecked, not open`)

// ---------------------------------------------------------------- 5. map
phase('Map')
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `Write the literature map for "${input.topic}" to ${OUT}. ${statusBrief(workStatus)}\n` +
    'Then: an overview paragraph; a Mermaid diagram of the themes and how they connect; one section per theme with its key works (as ' +
    'formatted references with DOIs) and methods; a timeline of landmark works; the open questions that survived a search for existing ' +
    'answers, each turned into 1–2 candidate research questions; a short list of questions that looked open but are answered (with the ' +
    'answering works); a separate list of candidate gaps that were NOT checked, labelled as unchecked (never as open); and the search log ' +
    '(angles and queries, naming any angle whose sweep failed). Cite only works listed below. Note that the sweeps and gap checks are ' +
    'separate agents of the same model, so a gap no agent could fill is a lead to verify, not proof that none exists. Close with an ' +
    'AI-assistance disclosure and the date.' +
    (clustered ? '' : ' Clustering failed: say so, and present the key works by angle instead of by theme.') +
    `\n\nStatus reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ sweeps: coverage.sweeps, works: coverage.works, clustering: coverage.clustering, gaps: coverage.gaps })}\n` +
    `Angles: ${JSON.stringify(angles)}\nThemes: ${JSON.stringify(themes, null, 1)}\nKey works: ${JSON.stringify(clusterSet, null, 1)}\n` +
    `Open gaps (search completed, nothing found): ${JSON.stringify(open, null, 1)}\nAnswered: ${JSON.stringify(answered, null, 1)}\n` +
    `Unchecked candidate gaps: ${JSON.stringify(unchecked, null, 1)}\n\nReply with a two-sentence summary.`,
  'write map',
  workStatus,
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
const result = {
  angles: angles.map((a) => a.key),
  works: corpus.length,
  themes: themes.map((t) => t.name),
  open_gaps: open.map((g) => g.sharpened || g.question),
  answered_gaps: answered.length,
  unchecked_gaps: unchecked.map((g) => ({ theme: g.theme, question: g.question, why: g.why })),
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', result)
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, ...result })
