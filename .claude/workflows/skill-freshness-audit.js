export const meta = {
  name: 'skill-freshness-audit',
  description: 'Maintainer audit: find stale library versions, removed APIs, moved endpoints, and retired model IDs across the AlterLab skill corpus, each finding re-verified before it is reported',
  whenToUse: 'Quarterly, or after a major release of a library the corpus teaches. Report-only: it never edits skills. Args: {domains?: ["databases", ...], out?}.',
  phases: [
    { title: 'Inventory', detail: 'list domains and skills to audit' },
    { title: 'Audit', detail: 'one agent per batch of skills checks versions, APIs, endpoints, and model IDs' },
    { title: 'Verify', detail: 'every finding independently re-checked against its primary source' },
    { title: 'Report', detail: 'confirmed drift grouped by domain, with suggested edits' },
  ],
}

const input = args || {}
const OUT = input.out || 'freshness-report.md'
const BATCH = 10

const INVENTORY = {
  type: 'object',
  required: ['domains'],
  properties: {
    domains: {
      type: 'array',
      items: {
        type: 'object',
        required: ['domain', 'skills'],
        properties: { domain: { type: 'string' }, skills: { type: 'array', items: { type: 'string' } } },
      },
    },
  },
}

const FINDINGS = {
  type: 'object',
  required: ['findings', 'checked'],
  properties: {
    checked: { type: 'array', items: { type: 'string' }, description: 'skills fully checked' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['skill', 'file', 'kind', 'stale', 'current', 'source', 'severity'],
        properties: {
          skill: { type: 'string' },
          file: { type: 'string', description: 'path relative to the repo root' },
          kind: { type: 'string', enum: ['version', 'removed_api', 'renamed_api', 'endpoint', 'auth_or_limits', 'model_id', 'dead_link', 'policy', 'other'] },
          stale: { type: 'string', description: 'what the skill says now, quoted' },
          current: { type: 'string', description: 'what is true today' },
          source: { type: 'string', description: 'primary source URL (PyPI/CRAN/npm JSON, changelog, official docs)' },
          severity: { type: 'string', enum: ['breaks', 'misleads', 'cosmetic'] },
        },
      },
    },
  },
}

const VERDICT = {
  type: 'object',
  required: ['confirmed', 'note'],
  properties: {
    confirmed: { type: 'boolean' },
    note: { type: 'string', description: 'what the primary source says, quoted' },
    suggested_edit: { type: 'string', description: 'the minimal text change for the skill' },
  },
}

const chunk = (xs, n) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n))

// ---------------------------------------------------------------- 1. inventory
phase('Inventory')
const inv = await agent(
  'List the AlterLab skill domains under skills/ in this repository and the skill directories in each (directories containing a ' +
    `SKILL.md). ${Array.isArray(input.domains) && input.domains.length ? `Only these domains: ${input.domains.join(', ')}.` : 'All domains.'}`,
  { schema: INVENTORY, effort: 'low', label: 'inventory' },
)
const work = (inv && inv.domains ? inv.domains : []).flatMap((d) => chunk(d.skills, BATCH).map((skills) => ({ domain: d.domain, skills })))
if (!work.length) throw new Error('no skills found to audit')
log(`${work.reduce((n, w) => n + w.skills.length, 0)} skills in ${work.length} batches`)

// ---------------------------------------------------------------- 2. audit + 3. verify, pipelined per batch
phase('Audit')
const audited = await pipeline(
  work,
  (w, _item, i) =>
    agent(
      `Audit these skills in skills/${w.domain}/ for factual drift: ${w.skills.join(', ')}.\n` +
        'For each, read SKILL.md and grep its references/ and scripts/ for version-sensitive content. Check against primary sources: ' +
        'current releases (PyPI/CRAN/npm/bioconda JSON), removed or renamed functions and parameters (release notes, migration guides), ' +
        'API base URLs and versions (official docs; a quick request to the endpoint), auth and rate-limit rules, dead links, and model IDs ' +
        '(Claude IDs follow skills/core/shared/model_env.md; third-party IDs against the provider\'s live model list). Report only drift ' +
        'you confirmed at a primary source, quoting the stale text. Do not edit files.',
      { schema: FINDINGS, label: `${w.domain} batch ${i + 1}`, phase: 'Audit' },
    ),
  (found, w) =>
    parallel((found ? found.findings : []).map((f) => () =>
      agent(
        `Independently verify this suspected drift in the AlterLab skill ${f.skill} (${f.file}): the skill says "${f.stale}", and the ` +
          `claim is that today "${f.current}" (source: ${f.source}). Fetch the primary source yourself. Confirm only if it clearly shows the ` +
          'skill is out of date, and give the minimal edit that would fix it.',
        { schema: VERDICT, effort: 'low', label: `verify ${f.skill}: ${f.kind}`, phase: 'Verify' },
      ).then((v) => ({ ...f, domain: w.domain, verdict: v })),
    )).then((checked) => ({ domain: w.domain, checked: found ? found.checked : [], findings: checked.filter(Boolean) })),
)

// ---------------------------------------------------------------- 4. report
phase('Report')
const results = audited.filter(Boolean)
const confirmed = results.flatMap((r) => r.findings.filter((f) => f.verdict && f.verdict.confirmed))
const rejected = results.flatMap((r) => r.findings.filter((f) => !f.verdict || !f.verdict.confirmed))
const unchecked = work.filter((w, i) => !audited[i]).map((w) => `${w.domain}: ${w.skills.join(', ')}`)
if (unchecked.length) log(`${unchecked.length} batch(es) did not complete and are listed as unchecked`)
const bySeverity = {}
for (const f of confirmed) bySeverity[f.severity] = (bySeverity[f.severity] || 0) + 1
const summary = await agent(
  `Write ${OUT} (Markdown): a summary table of confirmed drift by domain and severity; then per domain, each confirmed finding with the ` +
    'file, the stale text, what is current, the primary source, and the suggested edit ("breaks" first); then the findings the verifier ' +
    'rejected (one line each, so a maintainer can spot a verifier mistake); then any unchecked batches. End with the commands to validate ' +
    'after fixing: python scripts/audit_skills.py, uv run pytest tests/, uv run python scripts/run_evals.py --strict.\n\n' +
    `Severity counts: ${JSON.stringify(bySeverity)}\nConfirmed: ${JSON.stringify(confirmed, null, 1)}\n` +
    `Rejected: ${JSON.stringify(rejected.map((f) => ({ skill: f.skill, kind: f.kind, stale: f.stale, note: f.verdict ? f.verdict.note : 'verifier failed' })), null, 1)}\n` +
    `Unchecked: ${JSON.stringify(unchecked)}\n\nReply with a two-sentence summary.`,
  { effort: 'low', label: 'write report' },
)

return { report: OUT, confirmed: confirmed.length, rejected: rejected.length, by_severity: bySeverity, unchecked, summary }
