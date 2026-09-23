export const meta = {
  name: 'review-panel',
  description: 'Independent multi-reviewer peer review of a manuscript, with every major concern checked against the text before the editor decides',
  whenToUse: 'Before submitting a paper, thesis chapter, or preprint, when you want reviewers who cannot anchor on each other and no concern that misreads the manuscript. Args: a manuscript path, or {path, venue?, field?, lenses?, out?}.',
  phases: [
    { title: 'Profile', detail: 'detect field, design, venue norms, and reporting guideline; choose reviewer lenses' },
    { title: 'Review', detail: 'blind, independent reviewers — one per lens' },
    { title: 'Verify', detail: 'each major concern re-read against the manuscript' },
    { title: 'Decide', detail: 'editor synthesis, decision letter, revision roadmap' },
  ],
}

const input = typeof args === 'string' ? { path: args } : (args || {})
if (!input.path) {
  throw new Error('review-panel needs a manuscript: /alterlab-workflows:review-panel paper.pdf — or args {path, venue?, field?, lenses?, out?}')
}
const OUT = input.out || 'alterlab-review-panel.md'
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

// ---------------------------------------------------------------- 1. profile
phase('Profile')
const profile = await agent(
  `Read the manuscript at ${input.path}. ${context} Identify its field, paper type, study design, and the reporting guideline that applies ` +
    '(or "none"). Then choose 4–5 reviewer lenses for THIS paper: always a methodology lens, a domain-contribution lens, a statistics and ' +
    'reproducibility lens (or an analytic-rigor lens for qualitative work), and a devil\'s-advocate lens that attacks the central claim; add an ' +
    'ethics and reporting-standards lens when there are human or animal participants or a reporting guideline applies. Make each focus specific ' +
    'to this manuscript. If the alterlab-paper-reviewer skill is installed, its field-analyst guidance applies.',
  { schema: PROFILE, label: 'field analyst' },
)
if (!profile) throw new Error('could not profile the manuscript')
const lenses = Array.isArray(input.lenses) && input.lenses.length
  ? input.lenses.map((l, i) => (typeof l === 'string' ? { key: `lens${i + 1}`, title: l, focus: l } : l))
  : profile.lenses
if (lenses.length > 6) log(`Using the first 6 of ${lenses.length} lenses`)
const panel = lenses.slice(0, 6)

// ---------------------------------------------------------------- 2. independent review
phase('Review')
// Reviewers run in separate contexts and never see each other's reports: independence is the point.
const reviews = await parallel(panel.map((lens) => () =>
  agent(
    `You are the ${lens.title} on a peer-review panel for the manuscript at ${input.path}. ${context}\n` +
      `Paper profile: ${profile.field}; ${profile.paper_type}; ${profile.design}. Reporting guideline: ${profile.reporting_guideline}.\n` +
      `Your focus: ${lens.focus}\n` +
      'Read the whole manuscript and write your own review. Anchor every concern to a location and, where possible, a verbatim quote; say ' +
      'what would resolve it. Mark a concern major only if it threatens a main conclusion. Recommend accept, minor_revision, major_revision, ' +
      'or reject. Be specific and constructive; do not invent content the paper lacks or cite literature you have not verified.',
    { schema: REVIEW, label: lens.title, phase: 'Review' },
  ).then((r) => (r ? { lens, ...r } : null)),
))
const done = reviews.filter(Boolean)
if (!done.length) throw new Error('no reviewer returned a report')

// ---------------------------------------------------------------- 3. verify major concerns
phase('Verify')
const majors = done.flatMap((r) => r.concerns.filter((c) => c.severity === 'major').map((c) => ({ reviewer: r.lens.title, ...c })))
const checked = await pipeline(majors, (c) =>
  agent(
    `A reviewer (${c.reviewer}) raised this major concern about the manuscript at ${input.path}:\n` +
      `"${c.issue}" (location: ${c.location}${c.quote ? `; quoted text: "${c.quote}"` : ''}).\n` +
      'Re-read the relevant parts of the manuscript, including the methods, supplementary material it references, and limitations. Decide ' +
      'whether the concern is valid as stated. It is not valid if the manuscript already addresses it or the reviewer misread the text; quote ' +
      'the passage that settles it either way.',
    { schema: CHECK, effort: 'high', label: `check: ${c.reviewer} ${c.id}`, phase: 'Verify' },
  ).then((v) => ({ ...c, check: v })),
)
const validMajors = checked.filter(Boolean).filter((c) => !c.check || c.check.valid)
const dropped = checked.filter(Boolean).filter((c) => c.check && !c.check.valid)
if (dropped.length) log(`${dropped.length} major concern(s) dropped after re-reading the manuscript`)

// ---------------------------------------------------------------- 4. editor decision
phase('Decide')
const tally = {}
for (const r of done) tally[r.recommendation] = (tally[r.recommendation] || 0) + 1
const letter = await agent(
  `You are the handling editor. Write the decision package for the manuscript at ${input.path} to ${OUT} (Markdown): ` +
    '(1) the editorial decision with a short rationale; (2) where reviewers agree and where they disagree, and how you weigh the disagreement; ' +
    '(3) a revision roadmap — the validated major concerns first, grouped by theme, each with what would resolve it, then minor points; ' +
    '(4) each reviewer\'s report, lightly edited; (5) a note listing concerns withdrawn after re-reading the manuscript, so authors are not ' +
    'asked to fix what is already there; (6) an AI-assistance disclosure stating this is a simulated panel, not a journal decision.\n\n' +
    `Recommendation tally: ${JSON.stringify(tally)}\nProfile: ${JSON.stringify(profile)}\n` +
    `Reviews: ${JSON.stringify(done.map((r) => ({ reviewer: r.lens.title, recommendation: r.recommendation, summary: r.summary, strengths: r.strengths, minor: r.concerns.filter((c) => c.severity === 'minor'), questions: r.questions_for_authors || [] })), null, 1)}\n` +
    `Validated major concerns: ${JSON.stringify(validMajors, null, 1)}\nWithdrawn concerns: ${JSON.stringify(dropped.map((c) => ({ reviewer: c.reviewer, issue: c.issue, why: c.check.reason })), null, 1)}\n\n` +
    'Reply with the decision in one word (accept, minor_revision, major_revision, or reject) followed by a two-sentence rationale.',
  { effort: 'high', label: 'editor-in-chief' },
)

return {
  report: OUT,
  recommendations: tally,
  major_concerns: validMajors.length,
  withdrawn_concerns: dropped.length,
  decision: letter,
}
