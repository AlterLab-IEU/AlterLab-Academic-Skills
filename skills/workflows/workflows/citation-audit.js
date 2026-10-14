export const meta = {
  name: 'citation-audit',
  description: 'Audit the reference list and up to 150 cited claims in a manuscript: existence, metadata, and claim support, with two separate re-checks of every flag and a coverage account of what was and was not checked',
  whenToUse: 'Before submission, after an AI-assisted draft, or when reviewing a thesis: catches fabricated, corrupted, hijacked, placeholder, and unsupportive citations. Returns status complete / partial / blocked with requested-vs-completed counts. Args: a manuscript path, or {path, mailto?, out?}.',
  phases: [
    { title: 'Extract', detail: 'parse the reference list and up to 150 claim-citation pairs' },
    { title: 'Verify', detail: 'resolve reference batches against Crossref, OpenAlex, Semantic Scholar, and arXiv' },
    { title: 'Faithfulness', detail: 'check each checkable cited claim against what its sources say' },
    { title: 'Challenge', detail: 'two separate re-checks of every flagged item' },
    { title: 'Report', detail: 'integrity report with coverage, then a read-back check that the file exists' },
  ],
}

// ---------------------------------------------------------------- inputs
const input = typeof args === 'string' ? { path: args } : (args || {})
if (!input.path) {
  throw new Error('citation-audit needs a manuscript: /alterlab-workflows:citation-audit paper.md — or args {path, mailto?, out?}')
}
const OUT = input.out || 'alterlab-citation-audit.md'
const REF_BATCH = 12
const CLAIM_BATCH = 8
const CLAIM_CAP = 150
const CONTACT = input.mailto ? ` Pass ${input.mailto} as the Crossref polite-pool contact (--mailto).` : ''

const TOOLING =
  'Use the alterlab-citation-verifier skill (alterlab-core plugin): scripts/verify_citations.py for existence and ' +
  'metadata, scripts/claim_faithfulness.py for claim support. If that skill is not installed, query the Crossref, ' +
  'OpenAlex, Semantic Scholar, and arXiv public APIs directly. Judge only from what those sources return, never from ' +
  'memory: the model that may have invented a citation shares its training data with you, so a plausible fabrication ' +
  'would pass a memory check. The verifier uses OPENALEX_API_KEY and S2_API_KEY from the environment when they are ' +
  'set; keyless OpenAlex and Semantic Scholar calls share a small per-IP budget. If verify_citations.py reports ' +
  'status "partial" (exit code 3), the entries it lists under input_accounting as rejected or unsupported were not ' +
  'checked: give those references UNVERIFIED, never VERIFIED. claim_faithfulness.py never verifies a claim: its ' +
  'LEXICAL_MATCH_REQUIRES_REVIEW and MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW labels are leads, so read the source ' +
  'passage before judging a claim SUPPORTED.' + CONTACT

// ---------------------------------------------------------------- schemas
const EXTRACT = {
  type: 'object',
  required: ['references', 'claims', 'claims_total', 'placeholders'],
  properties: {
    references: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'text'],
        properties: {
          id: { type: 'string', description: 'stable key such as R12 or the BibTeX citekey' },
          text: { type: 'string', description: 'the full reference as written' },
          doi: { type: 'string' },
          arxiv: { type: 'string' },
        },
      },
    },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'claim', 'refs'],
        properties: {
          id: { type: 'string', description: 'C1, C2, ...' },
          claim: { type: 'string', description: 'the citing sentence, verbatim' },
          refs: { type: 'array', items: { type: 'string' }, description: 'reference ids the sentence cites' },
          location: { type: 'string', description: 'section or line' },
        },
      },
    },
    claims_total: { type: 'integer', description: 'citing sentences found before any cap' },
    placeholders: {
      type: 'array',
      items: { type: 'string' },
      description: 'unresolved stubs verbatim: [CITATION NEEDED], (Author, YYYY), ??, [?], TODO',
    },
  },
}

const REF_VERDICTS = {
  type: 'object',
  required: ['results'],
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'verdict', 'evidence'],
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['VERIFIED', 'PAC', 'IH', 'NOT_FOUND', 'UNVERIFIED'] },
          evidence: { type: 'string', description: 'which source matched or failed, with the resolved DOI/URL and match score' },
          corrected: { type: 'string', description: 'the corrected reference when the verdict is PAC or IH' },
          retracted: { type: 'boolean' },
        },
      },
    },
  },
}

const CLAIM_VERDICTS = {
  type: 'object',
  required: ['results'],
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'verdict', 'evidence'],
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTRADICTED', 'UNCHECKABLE'] },
          evidence: { type: 'string', description: 'verbatim quote from the source, or what was missing' },
          fix: { type: 'string', description: 'a calibrated rewrite of the claim when not SUPPORTED' },
        },
      },
    },
  },
}

const RECHECK = {
  type: 'object',
  required: ['overturned', 'evidence'],
  properties: {
    overturned: { type: 'boolean', description: 'true only if you found concrete evidence that the flag is wrong' },
    new_verdict: { type: 'string', description: 'the verdict the evidence supports, when overturned' },
    evidence: { type: 'string', description: 'URL/DOI and verbatim quote, or the searches that came up empty' },
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
// bounded: no call, batch item, or re-check is attempted more than twice.
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
  (s === 'partial' ? 'This audit is PARTIAL: say so plainly in the first paragraph, give the status reasons, and say what was not checked. ' : '') +
  'Never describe an item as checked, verified, or confirmed unless the data below shows its check completed.'

// ---------------------------------------------------------------- 1. extract
phase('Extract')
const doc = await withRetry(
  `Read the manuscript at ${input.path}. For LaTeX, also read the .bib file(s) it uses; for Word, convert it first (e.g. with MarkItDown). ` +
    'Extract: (1) every entry of the reference list, each with a stable id (the citekey if there is one) and, when present, its DOI or arXiv id; ' +
    '(2) every sentence that makes a factual, quantitative, or causal claim and cites one or more references — keep the sentence verbatim and ' +
    'map its in-text citations to reference ids; (3) every unresolved citation placeholder, verbatim. ' +
    `If there are more than ${CLAIM_CAP} citing sentences, keep the ${CLAIM_CAP} most consequential (quantitative results, causal claims, abstract and discussion) ` +
    'and report the uncapped count in claims_total. Do not verify anything yet.',
  { schema: EXTRACT, label: 'extract references and claims' },
)
if (!doc) {
  reasons.push('the extraction agent failed twice, so nothing was audited')
  return finish('blocked', { message: `Could not extract references and claims from ${input.path}.` })
}

// References keep their ids (claims cite them). An entry without an id gets one; a repeated id is
// suffixed so both entries are still verified, and the repetition is reported.
const references = []
const refIndex = new Map()
const extraction = { reference_ids_missing: 0, reference_ids_duplicated: [] }
for (const [k, r] of (Array.isArray(doc.references) ? doc.references : []).entries()) {
  if (!r || typeof r !== 'object') continue
  let id = typeof r.id === 'string' ? r.id.trim() : ''
  if (!id) {
    extraction.reference_ids_missing++
    id = `ref#${k + 1}`
  }
  if (refIndex.has(id)) {
    extraction.reference_ids_duplicated.push(id)
    id = `${id}#${k + 1}`
  }
  const ref = { ...r, id, text: typeof r.text === 'string' ? r.text : '' }
  refIndex.set(id, ref)
  references.push(ref)
}
// Claims are numbered here (C1, C2, ...) so a missing or repeated extractor id cannot merge two claims.
const allClaims = (Array.isArray(doc.claims) ? doc.claims : [])
  .filter((c) => c && typeof c.claim === 'string' && c.claim.trim())
  .map((c, k) => ({
    id: `C${k + 1}`,
    claim: c.claim,
    refs: [...new Set((Array.isArray(c.refs) ? c.refs : []).filter((x) => typeof x === 'string' && x.trim()).map((x) => x.trim()))],
    location: c.location || '',
  }))
const claims = allClaims.slice(0, CLAIM_CAP)
const claimsTotal = Math.max(Number.isInteger(doc.claims_total) ? doc.claims_total : 0, allClaims.length)
const placeholders = Array.isArray(doc.placeholders) ? doc.placeholders : []
Object.assign(extraction, {
  references_listed: references.length,
  claims_total: claimsTotal,
  claims_extracted: claims.length,
  claim_cap: CLAIM_CAP,
  claims_not_extracted: claimsTotal - claims.length,
  placeholders: placeholders.length,
})
coverage.extraction = extraction
if (!references.length) {
  reasons.push(`no reference list was found in ${input.path}, so there is nothing to audit`)
  return finish('blocked', { message: `No reference list found in ${input.path}; nothing to audit.` })
}
if (claimsTotal > claims.length) {
  reasons.push(`capped: ${claims.length} of ${claimsTotal} citing sentences were extracted for checking (cap ${CLAIM_CAP}); the rest were not checked`)
  log(`Checking ${claims.length} of ${claimsTotal} citing sentences (capped at the most consequential)`)
}

// ---------------------------------------------------------------- 2. verify existence + metadata
phase('Verify')
const refRun = await batched(
  references,
  REF_BATCH,
  'id',
  'results',
  (batch, i) => `references ${i * REF_BATCH + 1}-${i * REF_BATCH + batch.length}`,
  (batch, label) =>
    tryAgent(
      `${TOOLING}\n\nVerify these ${batch.length} references. For each, return VERIFIED (matches an authoritative record), ` +
        'PAC (real work, but a metadata field is wrong — give the corrected reference), IH (the DOI/arXiv id resolves to a different work), ' +
        'NOT_FOUND (no source has it after a title search, an author+year search, and identifier resolution), or UNVERIFIED (the lookup ' +
        'itself failed — network error or rate limit — which is not evidence of fabrication). Flag retractions. Return exactly one result ' +
        'per reference, using the id given.\n\n' +
        JSON.stringify(batch, null, 1),
      { schema: REF_VERDICTS, label },
    ),
  (a, b) => a.verdict === b.verdict,
)
const refVerdict = refRun.answers
coverage.references = refRun.stat
if (refRun.stat.unresolved) {
  reasons.push(`${refRun.stat.unresolved} of ${references.length} references have no verification verdict (agent failure or omission after one retry)`)
  log(`${refRun.stat.unresolved} reference(s) could not be verified; they are listed as unchecked`)
}

// ---------------------------------------------------------------- 3. claim faithfulness
phase('Faithfulness')
// Only claims whose sources were not judged missing can be checked for support. Claims citing a
// NOT_FOUND or IH source are reported with that source; claims citing an id that is not in the
// reference list (or no id) are listed as not checkable. A claim citing a reference that could not be
// verified is still checked: the checker looks the source up itself.
const bad = new Set(['NOT_FOUND', 'IH'])
const checkable = []
const notCheckable = []
for (const c of claims) {
  const unknown = c.refs.filter((id) => !refIndex.has(id))
  if (!c.refs.length) notCheckable.push({ id: c.id, reason: 'cites no reference id' })
  else if (unknown.length) notCheckable.push({ id: c.id, reason: `cites ${unknown.join(', ')}, not in the reference list` })
  else if (c.refs.some((id) => refVerdict.has(id) && bad.has(refVerdict.get(id).verdict))) notCheckable.push({ id: c.id, reason: 'cites a reference judged NOT_FOUND or IH (reported with that reference)' })
  else checkable.push(c)
}
const claimRun = await batched(
  checkable,
  CLAIM_BATCH,
  'id',
  'results',
  (_batch, i) => `claims batch ${i + 1}`,
  (batch, label) =>
    tryAgent(
      `${TOOLING}\n\nFor each claim below, read what its cited sources actually say (full text when open access, otherwise the abstract) ` +
        'and judge whether they support the claim at the strength stated: SUPPORTED, PARTIAL (weaker, narrower, or different population/measure), ' +
        'UNSUPPORTED (the source does not say this), CONTRADICTED (the source says the opposite), or UNCHECKABLE (no accessible text). ' +
        'Quote the source verbatim as evidence, and for anything short of SUPPORTED propose a calibrated rewrite of the claim. Return exactly ' +
        'one result per claim, using the id given.\n\n' +
        JSON.stringify(batch.map((c) => ({ ...c, sources: c.refs.map((id) => refVerdict.get(id) || { id, verdict: 'UNCHECKED' }) })), null, 1),
      { schema: CLAIM_VERDICTS, label },
    ),
  (a, b) => a.verdict === b.verdict,
)
const claimVerdict = claimRun.answers
coverage.claims = {
  total_in_manuscript: claimsTotal,
  extracted: claims.length,
  not_checkable: notCheckable.length,
  ...claimRun.stat,
}
if (claimRun.stat.unresolved) {
  reasons.push(`${claimRun.stat.unresolved} of ${checkable.length} checkable claims have no faithfulness verdict (agent failure or omission after one retry)`)
}

// ---------------------------------------------------------------- 4. adversarial re-check of flags
phase('Challenge')
// A flag accuses an author of a fabricated or misused citation, so it is reported only after two
// separate attempts to overturn it have both completed and failed. Fewer than two completed re-checks
// leave the flag provisional. Separate agents of the same model share its blind spots, so surviving
// both re-checks is a stronger screen, not independent proof.
const flags = [
  ...references.filter((r) => refVerdict.has(r.id) && ['PAC', 'IH', 'NOT_FOUND', 'UNVERIFIED'].includes(refVerdict.get(r.id).verdict)).map((r) => ({ kind: 'reference', r: refVerdict.get(r.id) })),
  ...checkable.filter((c) => claimVerdict.has(c.id) && ['UNSUPPORTED', 'CONTRADICTED'].includes(claimVerdict.get(c.id).verdict)).map((c) => ({ kind: 'claim', r: claimVerdict.get(c.id) })),
]
const claimById = new Map(claims.map((c) => [c.id, c]))
const describe = (f) =>
  f.kind === 'reference'
    ? `Reference ${f.r.id}: "${refIndex.get(f.r.id).text}" was judged ${f.r.verdict} (${f.r.evidence}).`
    : `Claim ${f.r.id}: "${claimById.get(f.r.id).claim}" citing ${claimById.get(f.r.id).refs.join(', ')} was judged ${f.r.verdict} (${f.r.evidence}).`
const strategies = [
  'Search by exact title in Crossref and OpenAlex, then by first author plus year, then resolve any identifier directly.',
  "Search the first author's publication list (ORCID, Google Scholar profile, institutional page) and the venue's table of contents for that year.",
]
const recheck = { flags: flags.length, requested: flags.length * strategies.length, dispatched: 0, completed: 0, failed: 0, retried: 0 }
const challenged = await pipeline(flags, (f) =>
  parallel(strategies.map((how, k) => async () => {
    if (!canSpawn()) return null
    recheck.dispatched++
    return withRetry(
      `${TOOLING}\n\nTry to overturn this integrity flag. ${describe(f)}\n${how}\n` +
        'Set overturned=true only with concrete evidence (a URL or DOI plus a verbatim quote) that the reference exists as cited or that ' +
        'the source supports the claim; otherwise leave it false and list the searches you ran.',
      { schema: RECHECK, effort: 'high', label: `recheck ${f.kind} ${f.r.id} (${k + 1}/${strategies.length})`, phase: 'Challenge' },
      recheck,
    )
  })),
)
const judged = flags.map((f, i) => {
  const votes = (Array.isArray(challenged[i]) ? challenged[i] : []).filter(Boolean)
  recheck.completed += votes.length
  const state = votes.some((v) => v.overturned) ? 'overturned' : votes.length === strategies.length ? 'stood' : 'recheck_incomplete'
  return { ...f, votes, rechecks_completed: votes.length, state }
})
recheck.failed = recheck.dispatched - recheck.completed
const stood = judged.filter((f) => f.state === 'stood')
const overturned = judged.filter((f) => f.state === 'overturned')
const provisional = judged.filter((f) => f.state === 'recheck_incomplete')
Object.assign(recheck, { flags_stood: stood.length, flags_overturned: overturned.length, flags_recheck_incomplete: provisional.length })
coverage.rechecks = recheck
if (provisional.length) {
  reasons.push(`${provisional.length} of ${flags.length} flags have fewer than ${strategies.length} completed re-checks; they are provisional and excluded from the TF/PAC/IH/SH counts`)
}

// ---------------------------------------------------------------- 5. report
phase('Report')
const category = (f) => (f.kind === 'claim' ? 'SH' : { NOT_FOUND: 'TF', PAC: 'PAC', IH: 'IH', UNVERIFIED: 'unverified' }[f.r.verdict])
const tally = (list, cat) => list.filter((f) => category(f) === cat).length
const counts = {
  references: references.length,
  references_with_verdict: refRun.stat.completed,
  claims_total: claimsTotal,
  claims_extracted: claims.length,
  claims_checkable: checkable.length,
  claims_checked: claimRun.stat.completed, // claims with a returned verdict, not claims dispatched
  TF: tally(stood, 'TF'),
  PAC: tally(stood, 'PAC'),
  IH: tally(stood, 'IH'),
  PH: placeholders.length,
  SH: tally(stood, 'SH'),
  unverified: tally(stood, 'unverified'),
  retracted: [...refVerdict.values()].filter((r) => r.retracted).length,
  claims_uncheckable: [...claimVerdict.values()].filter((v) => v.verdict === 'UNCHECKABLE').length,
  flags_overturned_on_recheck: overturned.length,
  flags_recheck_incomplete: provisional.length,
}
// UNVERIFIED (the lookup failed) and UNCHECKABLE (no accessible text) are answers, but the check they
// stand for did not happen, so they keep the audit partial.
const stillUnverified = judged.filter((f) => f.state !== 'overturned' && f.kind === 'reference' && f.r.verdict === 'UNVERIFIED').length
if (stillUnverified) reasons.push(`${plural(stillUnverified, 'reference')} remain UNVERIFIED (the lookup failed, also on re-check); re-run to complete the existence check`)
if (counts.claims_uncheckable) reasons.push(`${counts.claims_uncheckable} of ${checkable.length} checkable claims are UNCHECKABLE (no accessible source text)`)
const unchecked = {
  references_without_verdict: references.filter((r) => !refVerdict.has(r.id)).map((r) => r.id),
  claims_without_verdict: checkable.filter((c) => !claimVerdict.has(c.id)).map((c) => c.id),
  claims_not_checkable: notCheckable,
  claims_not_extracted: claimsTotal - claims.length,
  flags_recheck_incomplete: provisional.map((f) => ({ kind: f.kind, id: f.r.id, verdict: f.r.verdict, category: category(f), rechecks_completed: f.rechecks_completed })),
}
const flagRows = (list) => list.map(({ kind, r, votes, rechecks_completed }) => ({ kind, category: category({ kind, r }), ...r, rechecks_completed, recheck: votes }))
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `Write a citation-integrity report for ${input.path} to ${OUT} (Markdown). ${statusBrief(workStatus)}\n` +
    'Then a summary table of the counts below; claims_checked is the number of claims that received a verdict, of which ' +
    'claims_uncheckable had no accessible source text. Then one table per ' +
    'category, each row with its evidence and a concrete fix: TF (NOT_FOUND, and both separate re-checks completed without finding the ' +
    'work), PAC (corrupted metadata, with the corrected reference), IH (identifier points elsewhere), PH (placeholders), SH (claims the ' +
    'cited source does not support or contradicts, with the verbatim evidence and the calibrated rewrite), UNVERIFIED (lookup failed — re-run, ' +
    'not an accusation), and retractions flagged by the verification stage. Then "Provisional flags — re-check incomplete": each flag with ' +
    'fewer than two completed re-checks and how many completed; do not count these in TF/PAC/IH/SH or call them confirmed. Then "Not checked": ' +
    'references without a verdict, claims without a verdict, claims that could not be checked and why, and how many citing sentences were ' +
    `never extracted because of the ${CLAIM_CAP}-claim cap. Then "Overturned on re-check" so authors can see what was cleared. Close with ` +
    "the method (sources queried, today's date); a note that the re-checks are separate passes by agents of the same model, so their " +
    'agreement is not independent verification and a human should confirm each finding; and an AI-assistance disclosure. Keep the tone ' +
    'factual: these are findings to check, not verdicts on intent.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ extraction, references: refRun.stat, claims: coverage.claims, rechecks: recheck })}\n` +
    `Counts: ${JSON.stringify(counts)}\n\nFlags that stood after two completed re-checks: ${JSON.stringify(flagRows(stood), null, 1)}\n\n` +
    `Provisional flags (re-check incomplete): ${JSON.stringify(flagRows(provisional), null, 1)}\n\n` +
    `Placeholders: ${JSON.stringify(placeholders)}\n\nNot checked: ${JSON.stringify(unchecked, null, 1)}\n\n` +
    `Overturned flags: ${JSON.stringify(overturned.map(({ kind, r, votes }) => ({ kind, id: r.id, verdict: r.verdict, recheck: votes })), null, 1)}\n\n` +
    'Reply with a three-sentence summary of the findings that states the coverage.',
  'write integrity report',
  workStatus,
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', { counts, unchecked, summary: delivered.summary })
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, counts, unchecked, summary: delivered.summary })
