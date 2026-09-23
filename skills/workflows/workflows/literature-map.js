export const meta = {
  name: 'literature-map',
  description: 'Map a research field: parallel scholarly-database sweeps from several angles, merged and clustered into themes, with every proposed research gap checked for existing work before it is reported',
  whenToUse: 'Starting a project, proposal, or thesis chapter: find the themes, landmark and recent papers, methods, and genuinely open questions in a topic. Args: a topic string, or {topic, seeds?: [DOIs], years?, out_dir?}.',
  phases: [
    { title: 'Plan', detail: 'search angles and database-native queries' },
    { title: 'Sweep', detail: 'one agent per angle across OpenAlex, PubMed, arXiv, and citation links' },
    { title: 'Cluster', detail: 'themes, landmark works, methods, open questions' },
    { title: 'Gaps', detail: 'each candidate gap searched for work that already fills it' },
    { title: 'Map', detail: 'the field map and research-question shortlist' },
  ],
}

const input = typeof args === 'string' ? { topic: args } : (args || {})
if (!input.topic) {
  throw new Error('literature-map needs a topic: /alterlab-workflows:literature-map "LLM-assisted qualitative coding" — or args {topic, seeds?, years?, out_dir?}')
}
const OUT_DIR = input.out_dir || 'alterlab-literature-map'
const YEARS = input.years || 'all years, with extra attention to the last five'
const seeds = Array.isArray(input.seeds) ? input.seeds : []

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
    evidence: { type: 'string', description: 'the works you found (DOIs) or the searches that came up empty' },
    sharpened: { type: 'string', description: 'the question, narrowed to what is genuinely still open' },
  },
}

const norm = (w) => (w.doi ? w.doi.toLowerCase().replace(/^https?:\/\/(dx\.)?doi\.org\//, '') : `${(w.title || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()}|${w.year}`)

// ---------------------------------------------------------------- 1. plan
phase('Plan')
const plan = await agent(
  `Plan a literature map of: "${input.topic}" (${YEARS}).${seeds.length ? ` Seed papers: ${seeds.join(', ')}.` : ''}\n` +
    'Propose 4–6 search angles that together cover the field and would each surface different papers: core terminology and its synonyms, ' +
    'the main methods, key populations or application settings, adjacent fields that use other vocabulary, recent preprints, and (when ' +
    'seeds are given) their citation neighbourhood. Give each a database-native query.',
  { schema: PLAN, label: 'search plan' },
)
const angles = plan && plan.angles ? plan.angles.slice(0, 6) : []
if (!angles.length) throw new Error('could not plan search angles')

// ---------------------------------------------------------------- 2. sweep (one agent per angle)
phase('Sweep')
const sweeps = await pipeline(angles, (a) =>
  agent(
    `Search the literature for the "${a.key}" angle of "${input.topic}" (${YEARS}). Rationale: ${a.rationale}\nQuery: ${a.query}\n` +
      'Use the alterlab-openalex skill (and alterlab-pubmed, alterlab-arxiv, or alterlab-citation-graph where they fit) when installed, or ' +
      'the public APIs. Save up to 200 records to ' + `${OUT_DIR}/angle-${a.key.replace(/[^a-z0-9-]+/gi, '-')}.jsonl ` +
      '(title, year, doi, authors, venue, cited_by, abstract) and return the 25 most important for the topic — landmark and highly cited ' +
      'works plus the strongest recent ones — with a line on why each matters. Report only works you retrieved.',
    { schema: SWEEP, label: `sweep: ${a.key}`, phase: 'Sweep' },
  ),
)
// Merge across angles in code: the de-duplicated union and how many angles surfaced each work.
const merged = new Map()
for (const s of sweeps.filter(Boolean)) {
  for (const w of s.top) {
    const k = norm(w)
    const prev = merged.get(k)
    merged.set(k, prev ? { ...prev, angles: [...prev.angles, s.key] } : { ...w, angles: [s.key] })
  }
}
const corpus = [...merged.values()].sort((x, y) => y.angles.length - x.angles.length || (y.cited_by || 0) - (x.cited_by || 0))
log(`${corpus.length} distinct key works across ${sweeps.filter(Boolean).length} angles`)

// ---------------------------------------------------------------- 3. cluster (needs the whole corpus)
phase('Cluster')
const clustered = await agent(
  `Cluster these key works on "${input.topic}" into 4–8 themes. For each theme: a name, a paragraph on what it studies and where it ` +
    'stands, its key works (use the DOIs given), its dominant methods, and 1–3 open questions the works themselves point to (limitations, ' +
    'future-work sections, conflicting results). Works surfaced by several angles are likely central.\n\n' +
    JSON.stringify(corpus.slice(0, 150), null, 1),
  { schema: THEMES, effort: 'high', label: 'cluster themes' },
)
const themes = clustered && clustered.themes ? clustered.themes : []
const candidates = themes.flatMap((t) => t.open_questions.map((q) => ({ theme: t.name, question: q }))).slice(0, 12)
if (themes.reduce((n, t) => n + t.open_questions.length, 0) > candidates.length) log(`Checking the first ${candidates.length} candidate gaps`)

// ---------------------------------------------------------------- 4. gaps (adversarial search)
phase('Gaps')
const gaps = await pipeline(candidates, (g) =>
  agent(
    `Someone proposes this as an open research question in "${input.topic}" (theme: ${g.theme}): "${g.question}"\n` +
      'Try to show it is already answered: search for studies, reviews, and recent preprints that address it directly. Mark it open only ' +
      'if a real search finds nothing that answers it; if it is partly answered, narrow the question to what remains open.',
    { schema: GAP, effort: 'high', label: `gap: ${g.theme}`, phase: 'Gaps' },
  ).then((v) => (v ? { ...g, ...v } : null)),
)
const open = gaps.filter(Boolean).filter((g) => g.open)
const closed = gaps.filter(Boolean).filter((g) => !g.open)

// ---------------------------------------------------------------- 5. map
phase('Map')
const summary = await agent(
  `Write the literature map for "${input.topic}" to ${OUT_DIR}/literature-map.md: an overview paragraph; a Mermaid diagram of the themes ` +
    'and how they connect; one section per theme with its key works (as formatted references with DOIs) and methods; a timeline of ' +
    'landmark works; the verified open questions, each turned into 1–2 candidate research questions; a short list of questions that ' +
    'looked open but are answered (with the answering works); and the search log (angles and queries). Cite only works listed below. ' +
    'Close with an AI-assistance disclosure and the date.\n\n' +
    `Angles: ${JSON.stringify(angles)}\nThemes: ${JSON.stringify(themes, null, 1)}\nKey works: ${JSON.stringify(corpus.slice(0, 150), null, 1)}\n` +
    `Open gaps: ${JSON.stringify(open, null, 1)}\nAnswered: ${JSON.stringify(closed, null, 1)}\n\nReply with a two-sentence summary.`,
  { label: 'write map' },
)

return {
  report: `${OUT_DIR}/literature-map.md`,
  angles: angles.map((a) => a.key),
  works: corpus.length,
  themes: themes.map((t) => t.name),
  open_gaps: open.map((g) => g.sharpened || g.question),
  summary,
}
