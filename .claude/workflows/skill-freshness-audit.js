export const meta = {
  name: 'skill-freshness-audit',
  description: 'Maintainer audit: find stale library versions, removed APIs, moved endpoints, and retired model IDs across the AlterLab skill corpus; each finding is separately re-verified against its primary source before it is reported as confirmed, and unverified findings and unchecked skills are listed',
  whenToUse: 'Quarterly, or after a major release of a library the corpus teaches. Report-only: it never edits skills. Returns status complete / partial / blocked with requested-vs-completed skill and verification counts. Args: {domains?: ["databases", ...], out?}.',
  phases: [
    { title: 'Inventory', detail: 'list domains and skills to audit' },
    { title: 'Audit', detail: 'one agent per batch of skills checks versions, APIs, endpoints, and model IDs' },
    { title: 'Verify', detail: 'every finding separately re-checked against its primary source' },
    { title: 'Report', detail: 'confirmed drift grouped by domain, with suggested edits, then a read-back check that the file exists' },
  ],
}

const input = args || {}
const OUT = input.out || 'freshness-report.md'
const BATCH = 10
const WANTED = Array.isArray(input.domains) ? input.domains.filter((d) => typeof d === 'string' && d.trim()).map((d) => d.trim()) : []

// When domains are requested, the inventory may only name those (an enum the structured output enforces).
const INVENTORY = {
  type: 'object',
  required: ['domains'],
  properties: {
    domains: {
      type: 'array',
      items: {
        type: 'object',
        required: ['domain', 'skills'],
        properties: { domain: WANTED.length ? { type: 'string', enum: WANTED } : { type: 'string' }, skills: { type: 'array', items: { type: 'string' } } },
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
// bounded: no call, batch item, or verification is attempted more than twice.
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
  'below (skills audited and findings verified: requested, dispatched, completed, failed, unresolved, retried). ' +
  (s === 'partial' ? 'This audit is PARTIAL: say so plainly in the first paragraph, give the status reasons, and list what was not checked. ' : '') +
  'Never describe a finding as confirmed or rejected, or a skill as checked, unless the data below shows that check completed.'

// ---------------------------------------------------------------- 1. inventory
phase('Inventory')
const inv = await withRetry(
  'List the AlterLab skill domains under skills/ in this repository and the skill directories in each (directories containing a ' +
    `SKILL.md). ${WANTED.length ? `Only these domains: ${WANTED.join(', ')}.` : 'All domains.'}`,
  { schema: INVENTORY, effort: 'low', label: 'inventory' },
)
if (!inv) {
  reasons.push('the inventory agent failed twice, so no skill was audited')
  return finish('blocked', { message: 'Could not list the skills to audit.' })
}
// One entry per skill: a domain listed twice is merged, a skill listed twice is audited once, and a
// domain that was not asked for is ignored. Every adjustment is counted.
const skillsByDomain = new Map()
let duplicateSkills = 0
for (const d of Array.isArray(inv.domains) ? inv.domains : []) {
  if (!d || typeof d.domain !== 'string' || !d.domain.trim()) {
    idIssues.missing++
    continue
  }
  const domain = d.domain.trim()
  if (WANTED.length && !WANTED.includes(domain)) {
    idIssues.unknown++
    continue
  }
  const set = skillsByDomain.get(domain) || new Set()
  for (const s of Array.isArray(d.skills) ? d.skills : []) {
    if (typeof s !== 'string' || !s.trim()) continue
    if (set.has(s.trim())) duplicateSkills++
    else set.add(s.trim())
  }
  skillsByDomain.set(domain, set)
}
idIssues.duplicate += duplicateSkills
const missingDomains = WANTED.filter((d) => !skillsByDomain.has(d) || !skillsByDomain.get(d).size)
const work = [...skillsByDomain].flatMap(([domain, set]) => chunk([...set], BATCH).map((skills) => ({ domain, skills })))
const totalSkills = work.reduce((n, w) => n + w.skills.length, 0)
coverage.inventory = { domains_requested: WANTED.length ? WANTED : 'all', domains_found: skillsByDomain.size, domains_missing: missingDomains, skills: totalSkills, duplicate_skills: duplicateSkills, batches: work.length }
if (!work.length) {
  reasons.push(`no skills were found to audit${WANTED.length ? ` in ${WANTED.join(', ')}` : ''}`)
  return finish('blocked', { message: 'No skills found to audit.' })
}
if (missingDomains.length) reasons.push(`no skills were found for the requested domain(s) ${missingDomains.join(', ')}; they were not audited`)
log(`${totalSkills} skills in ${work.length} batches`)

// ---------------------------------------------------------------- 2. audit + 3. verify, pipelined per batch
phase('Audit')
const auditStat = { requested: totalSkills, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const verifyStat = { requested: 0, dispatched: 0, completed: 0, failed: 0, unresolved: 0, retried: 0 }
const auditPrompt = (domain, skills) =>
  `Audit these skills in skills/${domain}/ for factual drift: ${skills.join(', ')}.\n` +
  'For each, read SKILL.md and grep its references/ and scripts/ for version-sensitive content. Check against primary sources: ' +
  'current releases (PyPI/CRAN/npm/bioconda JSON), removed or renamed functions and parameters (release notes, migration guides), ' +
  'API base URLs and versions (official docs; a quick request to the endpoint), auth and rate-limit rules, dead links, and model IDs ' +
  '(Claude IDs follow skills/core/shared/model_env.md; third-party IDs against the provider\'s live model list). Report only drift ' +
  'you confirmed at a primary source, quoting the stale text, and list in `checked` exactly the skills you checked completely. Do not edit files.'
// A batch that fails is re-sent once, and so are the skills a batch did not list as checked. A
// finding about a skill that was not sent is ignored; the same finding reported twice counts once.
async function auditBatch(w, i) {
  const label = `${w.domain} batch ${i + 1}`
  const checked = new Set()
  const findings = []
  const seen = new Set()
  let todo = w.skills
  for (let attempt = 0; attempt < 2 && todo.length && canSpawn(); attempt++) {
    if (attempt) {
      retries++
      auditStat.retried++
    } else {
      auditStat.dispatched += w.skills.length
    }
    const out = await tryAgent(auditPrompt(w.domain, todo), { schema: FINDINGS, label: attempt ? `${label} (retry)` : label, phase: 'Audit' })
    if (!out) continue
    const sent = new Set(todo)
    for (const s of Array.isArray(out.checked) ? out.checked : []) {
      if (typeof s !== 'string' || !s) idIssues.missing++
      else if (!sent.has(s)) idIssues.unknown++
      else if (checked.has(s)) idIssues.duplicate++
      else checked.add(s)
    }
    for (const f of Array.isArray(out.findings) ? out.findings : []) {
      if (!f || typeof f.skill !== 'string' || !f.skill) {
        idIssues.missing++
        continue
      }
      if (!w.skills.includes(f.skill)) {
        idIssues.unknown++
        continue
      }
      const sig = `${f.skill}\u0000${f.file}\u0000${f.kind}\u0000${f.stale}`
      if (seen.has(sig)) {
        idIssues.duplicate++
        continue
      }
      seen.add(sig)
      findings.push({ ...f, domain: w.domain })
    }
    todo = todo.filter((s) => !checked.has(s))
  }
  return { domain: w.domain, checked: [...checked], unchecked: todo, findings }
}
const audited = await pipeline(
  work,
  (w, _item, i) => auditBatch(w, i),
  (batch) =>
    parallel(batch.findings.map((f) => async () => {
      if (!canSpawn()) return null
      verifyStat.dispatched++
      return withRetry(
        `Separately verify this suspected drift in the AlterLab skill ${f.skill} (${f.file}): the skill says "${f.stale}", and the ` +
          `claim is that today "${f.current}" (source: ${f.source}). Fetch the primary source yourself — do not rely on the auditor's ` +
          'reading. Confirm only if it clearly shows the skill is out of date, and give the minimal edit that would fix it.',
        { schema: VERDICT, effort: 'low', label: `verify ${f.skill}: ${f.kind}`, phase: 'Verify' },
        verifyStat,
      )
    })).then((verdicts) => ({ ...batch, findings: batch.findings.map((f, k) => ({ ...f, verdict: verdicts[k] || null })) })),
)

// ---------------------------------------------------------------- 4. report
phase('Report')
// pipeline() keeps results aligned with its inputs, so a batch whose stages failed is still accounted for.
const batches = work.map((w, i) => audited[i] || { domain: w.domain, checked: [], unchecked: w.skills, findings: [] })
const findings = batches.flatMap((b) => b.findings)
// A verifier that did not complete leaves its finding UNVERIFIED — neither confirmed nor rejected.
const verified = (f) => f.verdict && typeof f.verdict.confirmed === 'boolean'
const confirmed = findings.filter((f) => verified(f) && f.verdict.confirmed)
const rejected = findings.filter((f) => verified(f) && !f.verdict.confirmed)
const unverified = findings.filter((f) => !verified(f))
const unchecked = batches.flatMap((b) => b.unchecked.map((s) => `${b.domain}/${s}`))
auditStat.completed = batches.reduce((n, b) => n + b.checked.length, 0)
auditStat.failed = auditStat.dispatched - auditStat.completed
auditStat.unresolved = auditStat.requested - auditStat.completed
verifyStat.requested = findings.length
verifyStat.completed = confirmed.length + rejected.length
verifyStat.failed = verifyStat.dispatched - verifyStat.completed
verifyStat.unresolved = verifyStat.requested - verifyStat.completed
coverage.skills = auditStat
coverage.verification = { ...verifyStat, confirmed: confirmed.length, rejected: rejected.length, unverified: unverified.length }
if (unchecked.length) {
  reasons.push(`${unchecked.length} of ${totalSkills} skills were not fully checked (audit failure or omission after one retry); they are listed as unchecked`)
  log(`${unchecked.length} skill(s) were not fully checked and are listed as unchecked`)
}
if (unverified.length) {
  reasons.push(`${unverified.length} of ${findings.length} findings have no completed verification (after one retry); they are listed as UNVERIFIED, not rejected`)
}
const bySeverity = {}
for (const f of confirmed) bySeverity[f.severity] = (bySeverity[f.severity] || 0) + 1
const brief = (f) => ({ domain: f.domain, skill: f.skill, file: f.file, kind: f.kind, stale: f.stale, current: f.current, source: f.source, severity: f.severity })
const workStatus = reasons.length ? 'partial' : 'complete'
const delivered = await deliver(
  OUT,
  `Write ${OUT} (Markdown). ${statusBrief(workStatus)}\n` +
    'Then a summary table of confirmed drift by domain and severity; then per domain, each confirmed finding with the file, the stale ' +
    'text, what is current, the primary source, and the suggested edit ("breaks" first); then the findings the verifier rejected (one ' +
    'line each, so a maintainer can spot a verifier mistake); then the UNVERIFIED findings in their own list — the verifier did not ' +
    'complete, so they are neither confirmed nor rejected and need a manual check; then the skills that were not fully checked. Note that ' +
    'the auditor and the verifier are separate agents of the same model, so their agreement is not independent verification: a maintainer ' +
    'confirms each edit at the primary source before applying it. End with the commands to validate after fixing: python ' +
    'scripts/audit_skills.py, uv run pytest tests/, uv run python scripts/run_evals.py --strict.\n\n' +
    `Status reasons: ${JSON.stringify(reasons)}\nCoverage: ${JSON.stringify({ inventory: coverage.inventory, skills: auditStat, verification: coverage.verification })}\n` +
    `Severity counts (confirmed only): ${JSON.stringify(bySeverity)}\nConfirmed: ${JSON.stringify(confirmed, null, 1)}\n` +
    `Rejected: ${JSON.stringify(rejected.map((f) => ({ skill: f.skill, kind: f.kind, stale: f.stale, note: f.verdict.note })), null, 1)}\n` +
    `UNVERIFIED (verifier did not complete): ${JSON.stringify(unverified.map(brief), null, 1)}\n` +
    `Unchecked skills: ${JSON.stringify(unchecked)}\n\nReply with a two-sentence summary.`,
  'write report',
  workStatus,
  [],
  'low',
)
coverage.report = { path: OUT, confirmed: Boolean(delivered.report), attempts: delivered.attempts, read_back: delivered.check }
const result = {
  confirmed: confirmed.length,
  rejected: rejected.length,
  unverified: unverified.length,
  by_severity: bySeverity,
  unchecked,
  unverified_findings: unverified.map(brief),
  summary: delivered.summary,
}
if (!delivered.report) {
  reasons.push(delivered.reason)
  return finish('blocked', result)
}
if (delivered.mismatch) reasons.push(delivered.mismatch)
return finish(reasons.length ? 'partial' : 'complete', { report: delivered.report, ...result })
