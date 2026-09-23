export const meta = {
  name: 'citation-audit',
  description: 'Audit every reference and cited claim in a manuscript: existence, metadata, and claim support, with two independent re-checks of every flag',
  whenToUse: 'Before submission, after an AI-assisted draft, or when reviewing a thesis: catches fabricated, corrupted, hijacked, placeholder, and unsupportive citations across the whole document. Args: a manuscript path, or {path, mailto?, out?}.',
  phases: [
    { title: 'Extract', detail: 'parse the reference list and the claim-citation pairs' },
    { title: 'Verify', detail: 'resolve reference batches against Crossref, OpenAlex, Semantic Scholar, and arXiv' },
    { title: 'Faithfulness', detail: 'check each cited claim against what its sources say' },
    { title: 'Challenge', detail: 'two independent re-checks of every flagged item' },
    { title: 'Report', detail: 'integrity report in the TF/PAC/IH/PH/SH taxonomy' },
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
const CONTACT = input.mailto ? ` Pass ${input.mailto} as the polite-pool contact (--mailto).` : ''

const TOOLING =
  'Use the alterlab-citation-verifier skill (alterlab-core plugin): scripts/verify_citations.py for existence and ' +
  'metadata, scripts/claim_faithfulness.py for claim support. If that skill is not installed, query the Crossref, ' +
  'OpenAlex, Semantic Scholar, and arXiv public APIs directly. Judge only from what those sources return, never from ' +
  'memory: the model that may have invented a citation shares its training data with you, so a plausible fabrication ' +
  'would pass a memory check.' + CONTACT

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

const chunk = (xs, n) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n))

// ---------------------------------------------------------------- 1. extract
phase('Extract')
const doc = await agent(
  `Read the manuscript at ${input.path}. For LaTeX, also read the .bib file(s) it uses; for Word, convert it first (e.g. with MarkItDown). ` +
    'Extract: (1) every entry of the reference list, each with a stable id (the citekey if there is one) and, when present, its DOI or arXiv id; ' +
    '(2) every sentence that makes a factual, quantitative, or causal claim and cites one or more references — keep the sentence verbatim and ' +
    'map its in-text citations to reference ids; (3) every unresolved citation placeholder, verbatim. ' +
    'If there are more than 150 citing sentences, keep the 150 most consequential (quantitative results, causal claims, abstract and discussion) ' +
    'and report the uncapped count in claims_total. Do not verify anything yet.',
  { schema: EXTRACT, label: 'extract references and claims' },
)
if (!doc || !doc.references.length) {
  return { report: null, message: `No reference list found in ${input.path}; nothing to audit.` }
}
if (doc.claims_total > doc.claims.length) {
  log(`Checking ${doc.claims.length} of ${doc.claims_total} citing sentences (capped at the most consequential)`)
}

// ---------------------------------------------------------------- 2. verify existence + metadata
phase('Verify')
const refBatches = chunk(doc.references, REF_BATCH)
const refRuns = await pipeline(refBatches, (batch, _item, i) =>
  agent(
    `${TOOLING}\n\nVerify these ${batch.length} references. For each, return VERIFIED (matches an authoritative record), ` +
      'PAC (real work, but a metadata field is wrong — give the corrected reference), IH (the DOI/arXiv id resolves to a different work), ' +
      'NOT_FOUND (no source has it after a title search, an author+year search, and identifier resolution), or UNVERIFIED (the lookup ' +
      'itself failed — network error or rate limit — which is not evidence of fabrication). Flag retractions.\n\n' +
      JSON.stringify(batch, null, 1),
    { schema: REF_VERDICTS, label: `references ${i * REF_BATCH + 1}-${i * REF_BATCH + batch.length}` },
  ),
)
const refIds = new Set(doc.references.map((r) => r.id))
const refVerdict = new Map()
for (const run of refRuns.filter(Boolean)) for (const r of run.results) if (refIds.has(r.id)) refVerdict.set(r.id, r)
const missingRefs = doc.references.filter((r) => !refVerdict.has(r.id))
for (const r of missingRefs) refVerdict.set(r.id, { id: r.id, verdict: 'UNVERIFIED', evidence: 'verification agent did not return a result' })

// ---------------------------------------------------------------- 3. claim faithfulness
phase('Faithfulness')
// Only claims whose sources exist can be checked for support; claims citing a missing source are
// already problems and are reported with that source.
const bad = new Set(['NOT_FOUND', 'IH'])
const checkable = doc.claims.filter((c) => c.refs.length && c.refs.every((id) => refVerdict.has(id) && !bad.has(refVerdict.get(id).verdict)))
const claimRuns = await pipeline(chunk(checkable, CLAIM_BATCH), (batch, _item, i) =>
  agent(
    `${TOOLING}\n\nFor each claim below, read what its cited sources actually say (full text when open access, otherwise the abstract) ` +
      'and judge whether they support the claim at the strength stated: SUPPORTED, PARTIAL (weaker, narrower, or different population/measure), ' +
      'UNSUPPORTED (the source does not say this), CONTRADICTED (the source says the opposite), or UNCHECKABLE (no accessible text). ' +
      'Quote the source verbatim as evidence, and for anything short of SUPPORTED propose a calibrated rewrite of the claim.\n\n' +
      JSON.stringify(batch.map((c) => ({ ...c, sources: c.refs.map((id) => refVerdict.get(id)) })), null, 1),
    { schema: CLAIM_VERDICTS, label: `claims batch ${i + 1}` },
  ),
)
const checkableIds = new Set(checkable.map((c) => c.id))
const claimVerdict = new Map()
for (const run of claimRuns.filter(Boolean)) for (const r of run.results) if (checkableIds.has(r.id)) claimVerdict.set(r.id, r)

// ---------------------------------------------------------------- 4. adversarial re-check of flags
phase('Challenge')
// A flag accuses an author of a fabricated or misused citation, so each one must survive two
// independent attempts to overturn it before it is reported.
const flags = [
  ...[...refVerdict.values()].filter((r) => ['PAC', 'IH', 'NOT_FOUND', 'UNVERIFIED'].includes(r.verdict)).map((r) => ({ kind: 'reference', r })),
  ...[...claimVerdict.values()].filter((r) => ['UNSUPPORTED', 'CONTRADICTED'].includes(r.verdict)).map((r) => ({ kind: 'claim', r })),
]
const refText = new Map(doc.references.map((r) => [r.id, r.text]))
const claimText = new Map(doc.claims.map((c) => [c.id, c]))
const describe = (f) =>
  f.kind === 'reference'
    ? `Reference ${f.r.id}: "${refText.get(f.r.id)}" was judged ${f.r.verdict} (${f.r.evidence}).`
    : `Claim ${f.r.id}: "${claimText.get(f.r.id).claim}" citing ${claimText.get(f.r.id).refs.join(', ')} was judged ${f.r.verdict} (${f.r.evidence}).`
const strategies = [
  'Search by exact title in Crossref and OpenAlex, then by first author plus year, then resolve any identifier directly.',
  "Search the first author's publication list (ORCID, Google Scholar profile, institutional page) and the venue's table of contents for that year.",
]
const challenged = await pipeline(flags, (f, _item, i) =>
  parallel(strategies.map((how, k) => () =>
    agent(
      `${TOOLING}\n\nTry to overturn this integrity flag. ${describe(f)}\n${how}\n` +
        'Set overturned=true only with concrete evidence (a URL or DOI plus a verbatim quote) that the reference exists as cited or that ' +
        'the source supports the claim; otherwise leave it false and list the searches you ran.',
      { schema: RECHECK, effort: 'high', label: `recheck ${f.r.id} (${k + 1}/2)`, phase: 'Challenge' },
    ),
  )).then((votes) => {
    const overturns = votes.filter(Boolean).filter((v) => v.overturned)
    return { ...f, overturned: overturns.length > 0, recheck: votes.filter(Boolean), index: i }
  }),
)
const survived = challenged.filter(Boolean).filter((f) => !f.overturned)
const overturned = challenged.filter(Boolean).filter((f) => f.overturned)

// ---------------------------------------------------------------- 5. report
phase('Report')
const count = (pred) => survived.filter(pred).length
const counts = {
  references: doc.references.length,
  claims_checked: checkable.length,
  TF: count((f) => f.kind === 'reference' && f.r.verdict === 'NOT_FOUND'),
  PAC: count((f) => f.kind === 'reference' && f.r.verdict === 'PAC'),
  IH: count((f) => f.kind === 'reference' && f.r.verdict === 'IH'),
  PH: doc.placeholders.length,
  SH: count((f) => f.kind === 'claim'),
  unverified: count((f) => f.kind === 'reference' && f.r.verdict === 'UNVERIFIED'),
  retracted: [...refVerdict.values()].filter((r) => r.retracted).length,
  flags_overturned_on_recheck: overturned.length,
}
const summary = await agent(
  `Write a citation-integrity report for ${input.path} to ${OUT} (Markdown). Structure: a summary table of the counts below; then one ` +
    'table per category — TF (fabricated: NOT_FOUND after two independent re-checks), PAC (corrupted metadata, with the corrected reference), ' +
    'IH (identifier points elsewhere), PH (placeholders), SH (claims the cited source does not support or contradicts, with the verbatim ' +
    'evidence and the calibrated rewrite), UNVERIFIED (lookup failed — re-run, not an accusation), retractions — each row with its ' +
    'evidence and a concrete fix; then a short "overturned on re-check" section so authors can see what was cleared. Close with the method ' +
    '(sources queried, today\'s date) and an AI-assistance disclosure. Keep the tone factual: these are findings to check, not verdicts on intent.\n\n' +
    `Counts: ${JSON.stringify(counts)}\n\nSurviving flags: ${JSON.stringify(survived.map(({ kind, r, recheck }) => ({ kind, ...r, recheck })), null, 1)}\n\n` +
    `Placeholders: ${JSON.stringify(doc.placeholders)}\n\nOverturned flags: ${JSON.stringify(overturned.map(({ kind, r, recheck }) => ({ kind, id: r.id, recheck })), null, 1)}\n\n` +
    'Reply with a three-sentence summary of the findings.',
  { label: 'write integrity report' },
)

return { report: OUT, counts, summary }
