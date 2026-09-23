export const meta = {
  name: 'grant-mock-panel',
  description: "Mock review panel for a grant proposal on the funder's own criteria and scoring scale: independent reviewers, a check of every major weakness, and a summary statement",
  whenToUse: "Weeks before a deadline (NIH, NSF, ERC, Horizon Europe, TÜBİTAK 1001/1002, or another funder): see how a panel is likely to read the proposal and what to fix first. A simulation, not a prediction. Args: {path, funder, mechanism?, out?}.",
  phases: [
    { title: 'Criteria', detail: "load the funder's review criteria and scoring scale" },
    { title: 'Review', detail: 'assigned reviewers plus a skeptical panelist, independently' },
    { title: 'Challenge', detail: 'each major weakness checked against the proposal' },
    { title: 'Summary', detail: 'score spread, discussion points, summary statement, fix list' },
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

// ---------------------------------------------------------------- 1. criteria
phase('Criteria')
const rubric = await agent(
  `Find the current peer-review criteria and scoring scale for ${program}. Use the alterlab-research-grants skill for US and other ` +
    'international funders and the alterlab-tubitak-proposal skill for TÜBİTAK programs when installed, and confirm against the funder\'s ' +
    'official call or review guidance (cite it with its date or version). Return the scale, its direction, and each scored criterion with ' +
    'the guidance reviewers receive. If the funder uses unscored criteria, include them with the scale noted in the guidance.',
  { schema: CRITERIA, label: 'funder criteria' },
)
if (!rubric || !rubric.criteria.length) throw new Error(`could not establish review criteria for ${program}`)
const scale = `${rubric.scale_min}–${rubric.scale_max}, ${rubric.lower_is_better ? 'lower is better' : 'higher is better'}`
const criteriaText = rubric.criteria.map((c) => `- ${c.key} · ${c.title}: ${c.guidance}`).join('\n')

// ---------------------------------------------------------------- 2. independent review
phase('Review')
const ROLES = [
  { key: 'primary', brief: 'You are the primary (assigned) reviewer: read everything closely, including the budget justification and appendices.' },
  { key: 'secondary', brief: 'You are the secondary reviewer: focus on feasibility, preliminary data, team, and whether the aims hang together.' },
  { key: 'tertiary', brief: 'You are the tertiary reviewer from an adjacent field: judge significance and clarity for a non-specialist panel.' },
  { key: 'skeptic', brief: 'You are the panel\'s most skeptical member: look for the fatal flaw, overreach, and missing alternatives.' },
]
const reviews = await parallel(ROLES.map((role) => () =>
  agent(
    `${role.brief}\nProposal: ${input.path}. Program: ${program}. Scale: ${scale}.\nCriteria:\n${criteriaText}\n\n` +
      'Score every criterion and give an overall score on that scale, with a rationale per score anchored in the proposal. List strengths ' +
      'and weaknesses; mark a weakness major only if it would move the overall score. Review independently — other panelists are reading ' +
      'the same proposal separately.',
    { schema: REVIEW, label: `${role.key} reviewer`, phase: 'Review' },
  ).then((r) => (r ? { role: role.key, ...r } : null)),
))
const panel = reviews.filter(Boolean)
if (!panel.length) throw new Error('no reviewer returned scores')

// ---------------------------------------------------------------- 3. challenge major weaknesses
phase('Challenge')
const majors = panel.flatMap((r) => r.weaknesses.filter((w) => w.severity === 'major').map((w) => ({ reviewer: r.role, ...w })))
const checked = await pipeline(majors, (w) =>
  agent(
    `A ${w.reviewer} reviewer flagged this major weakness in the proposal at ${input.path} (${program}): "${w.issue}" (${w.where}).\n` +
      'Re-read the proposal, including the approach, alternatives/pitfalls, preliminary data, and letters. Decide whether the weakness ' +
      'stands or the proposal already addresses it, quoting the text that settles it, and name the smallest change that would resolve it.',
    { schema: CHECK, effort: 'high', label: `check ${w.reviewer} ${w.id}`, phase: 'Challenge' },
  ).then((c) => ({ ...w, check: c })),
)
const standing = checked.filter(Boolean).filter((w) => !w.check || w.check.stands)
const withdrawn = checked.filter(Boolean).filter((w) => w.check && !w.check.stands)

// ---------------------------------------------------------------- 4. summary (spread computed here)
phase('Summary')
const span = rubric.scale_max - rubric.scale_min || 1
const perCriterion = rubric.criteria.map((c) => {
  const s = panel.map((r) => r.scores.find((x) => x.key === c.key)).filter(Boolean).map((x) => x.score)
  const mean = s.length ? Math.round((s.reduce((a, b) => a + b, 0) / s.length) * 10) / 10 : null
  const spread = s.length ? Math.max(...s) - Math.min(...s) : null
  // A spread of a third of the scale or more is where a real panel would argue.
  return { key: c.key, title: c.title, scores: s, mean, spread, discuss: spread !== null && spread / span >= 1 / 3 }
})
const overall = panel.map((r) => r.overall)
const overallMean = Math.round((overall.reduce((a, b) => a + b, 0) / overall.length) * 10) / 10
const summary = await agent(
  `Write the mock-panel summary statement for the proposal at ${input.path} (${program}) to ${OUT} (Markdown): overall impact and the mean ` +
    'score, the per-criterion table below with the criteria the panel would need to discuss (large spread) called out, the consensus ' +
    'strengths, the standing weaknesses in priority order each with its smallest fix, the withdrawn weaknesses (already addressed — make ' +
    'that text easier to find), and a prioritized 5-item revision plan. Say plainly that this is an AI-simulated panel on the published ' +
    `criteria (${rubric.source}), not a funding prediction, and include an AI-assistance disclosure.\n\n` +
    `Scale: ${scale}\nOverall scores: ${JSON.stringify(overall)} (mean ${overallMean})\nPer criterion: ${JSON.stringify(perCriterion, null, 1)}\n` +
    `Strengths: ${JSON.stringify(panel.map((r) => ({ reviewer: r.role, strengths: r.strengths })), null, 1)}\n` +
    `Standing weaknesses: ${JSON.stringify(standing, null, 1)}\nWithdrawn: ${JSON.stringify(withdrawn.map((w) => ({ reviewer: w.reviewer, issue: w.issue, why: w.check.reason })), null, 1)}\n\n` +
    'Reply with a two-sentence summary.',
  { effort: 'high', label: 'summary statement' },
)

return {
  report: OUT,
  program,
  scale,
  overall_mean: overallMean,
  criteria: perCriterion,
  standing_weaknesses: standing.length,
  withdrawn_weaknesses: withdrawn.length,
  summary,
}
