export const meta = {
  name: 'rebuttal',
  description: 'Point-by-point response to reviewers: split the reviews into atomic comments, draft a response and a manuscript change for each in parallel, then reconcile them into one consistent letter',
  whenToUse: 'After receiving a revise-and-resubmit decision. Drafts the response letter, change log, and the list of analyses only the authors can run — it never invents results. Args: {manuscript, reviews, out_dir?, tone?}.',
  phases: [
    { title: 'Parse', detail: 'split every review into atomic, numbered comments' },
    { title: 'Respond', detail: 'one agent per comment drafts the stance, response, and change' },
    { title: 'Reconcile', detail: 'check all responses together for contradictions and over-promising' },
    { title: 'Compile', detail: 'response letter, change log, author action list' },
  ],
}

const input = args || {}
if (!input.manuscript || !input.reviews) {
  throw new Error('rebuttal needs {manuscript: "paper.docx", reviews: "decision-letter.pdf" (or an array of files)}')
}
const reviewFiles = Array.isArray(input.reviews) ? input.reviews : [input.reviews]
const OUT_DIR = input.out_dir || 'alterlab-rebuttal'
const TONE = input.tone || 'appreciative, direct, and specific'

const PARSE = {
  type: 'object',
  required: ['comments'],
  properties: {
    comments: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'reviewer', 'text', 'kind', 'asks_for'],
        properties: {
          id: { type: 'string', description: 'R1.1, R1.2, R2.1, ... (E.1 for the editor)' },
          reviewer: { type: 'string' },
          text: { type: 'string', description: 'the comment, verbatim' },
          kind: { type: 'string', enum: ['major', 'minor', 'editorial', 'question', 'praise'] },
          asks_for: { type: 'string', enum: ['new_analysis', 'new_data', 'clarification', 'citation', 'rewrite', 'restructure', 'none'] },
        },
      },
    },
  },
}

const RESPONSE = {
  type: 'object',
  required: ['id', 'stance', 'response', 'change', 'author_action'],
  properties: {
    id: { type: 'string' },
    stance: { type: 'string', enum: ['agree_changed', 'partly_agree', 'clarified', 'respectfully_disagree'] },
    response: { type: 'string', description: 'the reply to the reviewer, in the requested tone' },
    change: {
      type: 'object',
      required: ['location', 'description'],
      properties: {
        location: { type: 'string', description: 'section / paragraph / figure, or "none"' },
        description: { type: 'string' },
        new_text: { type: 'string', description: 'proposed revised text, when it is a wording change' },
      },
    },
    author_action: { type: 'string', description: 'what only the authors can do (run an analysis, collect data, confirm a fact), or "none"' },
  },
}

const RECONCILE = {
  type: 'object',
  required: ['issues'],
  properties: {
    issues: {
      type: 'array',
      items: {
        type: 'object',
        required: ['ids', 'problem', 'fix'],
        properties: {
          ids: { type: 'array', items: { type: 'string' } },
          problem: { type: 'string', description: 'contradiction, duplicated change, promise not backed by a change, tone, factual risk' },
          fix: { type: 'string' },
        },
      },
    },
  },
}

// ---------------------------------------------------------------- 1. parse
phase('Parse')
const parsed = await agent(
  `Read the decision letter and reviews in ${reviewFiles.join(', ')}. Split them into atomic comments — one request or point each — ` +
    'numbered by reviewer (R1.1, R1.2, ...; editor comments as E.1, ...). Keep each comment verbatim, classify it, and say what it asks for. ' +
    'Keep praise items too, so the letter can thank reviewers specifically.',
  { schema: PARSE, label: 'split reviews' },
)
const comments = parsed && parsed.comments ? parsed.comments : []
if (!comments.length) throw new Error('no reviewer comments found')
const actionable = comments.filter((c) => c.kind !== 'praise')
log(`${comments.length} comments (${actionable.length} needing a response) from ${new Set(comments.map((c) => c.reviewer)).size} reviewer(s)`)

// ---------------------------------------------------------------- 2. respond (one agent per comment)
phase('Respond')
const drafts = await pipeline(actionable, (c) =>
  agent(
    `Draft the response to reviewer comment ${c.id} (${c.kind}; asks for ${c.asks_for}) on the manuscript at ${input.manuscript}:\n"${c.text}"\n\n` +
      'Read the parts of the manuscript it concerns. Choose a stance on the merits — agree and change, partly agree, clarify, or respectfully ' +
      'disagree with evidence. Write the reply in a tone that is ' + `${TONE}, ` +
      'and specify the manuscript change (location, what changes, and new text for wording changes). Never invent results, statistics, ' +
      'references, or data: where a response depends on an analysis or fact only the authors have, write a placeholder like ' +
      '[AUTHORS: report the sensitivity analysis excluding site 3] and describe it in author_action. The alterlab-paper-writer skill\'s ' +
      'revision mode has guidance on response style.',
    { schema: RESPONSE, label: c.id, phase: 'Respond' },
  ).then((r) => (r ? { ...r, id: c.id, comment: c } : null)),
)
const responses = drafts.filter(Boolean)
const missing = actionable.filter((c) => !responses.some((r) => r.id === c.id))
if (missing.length) log(`No draft for ${missing.map((c) => c.id).join(', ')} — they are listed for the authors to answer`)

// ---------------------------------------------------------------- 3. reconcile (needs every draft at once)
phase('Reconcile')
const review = await agent(
  'Review this full set of draft responses to reviewers as one document. Find: responses that contradict each other; the same manuscript ' +
    'change promised twice or described differently; responses that claim a change the change field does not actually make; stances that ' +
    'will read as dismissive; and any sentence that states a result or fact the authors have not supplied (those must become placeholders). ' +
    'Propose a concrete fix for each issue.\n\n' +
    JSON.stringify(responses.map(({ comment, ...r }) => ({ comment: comment.text, ...r })), null, 1),
  { schema: RECONCILE, effort: 'high', label: 'consistency pass' },
)
const issues = review && review.issues ? review.issues : []

// ---------------------------------------------------------------- 4. compile
phase('Compile')
const actions = responses.filter((r) => r.author_action && r.author_action.toLowerCase() !== 'none').map((r) => ({ id: r.id, action: r.author_action }))
const summary = await agent(
  `Assemble the revision package in ${OUT_DIR}/: (1) response-letter.md — a short cover note to the editor, then every comment in order, ` +
    'quoted, followed by the response and where the manuscript changed (thank reviewers for the praise items specifically); ' +
    '(2) change-log.md — every manuscript change by location, with new text where given; (3) author-actions.md — every placeholder and ' +
    'analysis the authors must supply before submitting. Apply each consistency fix below while assembling. Do not edit the manuscript ' +
    'itself. Add a line to the cover note disclosing AI assistance in drafting the response, per the journal\'s policy.\n\n' +
    `All comments: ${JSON.stringify(comments, null, 1)}\n\nDrafts: ${JSON.stringify(responses.map(({ comment, ...r }) => r), null, 1)}\n\n` +
    `Consistency fixes: ${JSON.stringify(issues, null, 1)}\n\nComments without a draft: ${JSON.stringify(missing.map((c) => c.id))}\n\n` +
    'Reply with a two-sentence summary.',
  { label: 'assemble letter' },
)

return {
  out_dir: OUT_DIR,
  comments: comments.length,
  responded: responses.length,
  consistency_issues: issues.length,
  author_actions: actions,
  summary,
}
