export const meta = {
  name: 'claim-stress-test',
  description: "Stress-test a paper's headline claims: three skeptics per claim attack the evidence, the citations, and the inference, then each claim is rated and recalibrated",
  whenToUse: 'Before submission or a talk, or when refereeing: find which central claims survive disconfirming literature, citation checks, and inferential scrutiny. Args: a manuscript path, or {path?, claims?: [...], max_claims?, out?}.',
  phases: [
    { title: 'Claims', detail: 'extract the headline claims and the evidence offered for each' },
    { title: 'Attack', detail: 'three independent skeptics per claim, each with a different lens' },
    { title: 'Verdict', detail: 'rate each claim and write calibrated rewrites' },
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

// ---------------------------------------------------------------- 1. claims
phase('Claims')
let claims
if (given.length) {
  claims = given.slice(0, MAX).map((c, i) => ({ id: `C${i + 1}`, claim: c, evidence: input.path ? `see ${input.path}` : 'not supplied' }))
  if (given.length > MAX) log(`Testing the first ${MAX} of ${given.length} claims`)
} else {
  const found = await agent(
    `Read the manuscript at ${input.path} and list its headline claims — the ones in the title, abstract, and conclusions that the paper's ` +
      `contribution rests on — at most ${MAX}, most important first. For each, give the claim verbatim, the evidence the paper offers, and the design behind it.`,
    { schema: CLAIMS, label: 'extract headline claims' },
  )
  claims = (found && found.claims ? found.claims : []).slice(0, MAX)
  if (found && found.total_found > claims.length) log(`Testing ${claims.length} of ${found.total_found} claims found`)
}
if (!claims.length) return { report: null, message: 'No claims to test.' }

// ---------------------------------------------------------------- 2. attack
phase('Attack')
const attacked = await pipeline(claims, (c) =>
  parallel(LENSES.map((lens) => () =>
    agent(
      `You are a skeptical referee with one job: find out whether this claim survives the ${lens.key} lens.\n` +
        `Claim ${c.id}: "${c.claim}"\nEvidence offered: ${c.evidence}\n${c.design ? `Design: ${c.design}\n` : ''}` +
        `${input.path ? `Manuscript: ${input.path}\n` : ''}${lens.brief}\n` +
        'Set refuted=true only if the claim as stated does not hold up; severity is "fatal" if it cannot be rescued by rewording, ' +
        '"weakening" if it holds only in a narrower form. Cite only sources you retrieved.',
      { schema: ATTACK, effort: 'high', label: `${c.id} · ${lens.key}`, phase: 'Attack' },
    ).then((v) => (v ? { lens: lens.key, ...v } : null)),
  )).then((votes) => {
    const v = votes.filter(Boolean)
    const fatal = v.filter((x) => x.refuted && x.severity === 'fatal').length
    const weak = v.filter((x) => x.refuted).length
    // Majority rule across the three lenses; a single fatal finding still forces a closer look.
    const rating = fatal >= 2 ? 'refuted' : weak >= 2 ? 'weakened' : fatal === 1 ? 'contested' : 'survives'
    return { ...c, rating, attacks: v, lenses_reporting: v.length }
  }),
)
const results = attacked.filter(Boolean)
const partial = results.filter((r) => r.lenses_reporting < LENSES.length).length
if (partial) log(`${partial} claim(s) were judged with fewer than ${LENSES.length} lenses reporting`)

// ---------------------------------------------------------------- 3. verdict
phase('Verdict')
const tally = {}
for (const r of results) tally[r.rating] = (tally[r.rating] || 0) + 1
const summary = await agent(
  `Write a claim stress-test report to ${OUT} (Markdown). Start with a table: claim, rating (survives / contested / weakened / refuted), ` +
    'the decisive argument, and a calibrated rewrite that the evidence does support (keep "survives" claims as they are). Then one section per ' +
    'claim with each lens\'s argument and its retrieved evidence. End with the three changes that would most strengthen the paper and an ' +
    'AI-assistance disclosure. A contested claim had one fatal objection that the other lenses did not share — present both sides.\n\n' +
    `Ratings: ${JSON.stringify(tally)}\nResults: ${JSON.stringify(results, null, 1)}\n\nReply with a two-sentence summary.`,
  { effort: 'high', label: 'write report' },
)

return { report: OUT, ratings: tally, claims: results.map((r) => ({ id: r.id, rating: r.rating })), summary }
