#!/usr/bin/env node
// Dry-run validator for Claude Code dynamic-workflow scripts (skills/*/workflows/*.js,
// .claude/workflows/*.js).
//
// A workflow script can't be executed for real without spawning (and paying for) agents, so
// this harness checks everything short of that:
//   1. `export const meta = {...}` is the first statement and a PURE literal (no variables,
//      calls, spreads, or template interpolation) with a `name` and `description`; `name`
//      matches the file's basename (the plugin loader keys commands on it).
//   2. The body compiles as an async function (plain JS — no TypeScript, no import()).
//   3. The body avoids the runtime's forbidden calls (Date.now, Math.random, argless new Date).
//   4. The body RUNS end to end against a mocked runtime: agent() returns schema-conforming fake
//      objects, parallel()/pipeline() follow the documented semantics, and every phase used is
//      declared in meta.phases. Each script is run in several fake-data modes so both sides of
//      boolean branches execute.
//
//   5. Optionally, FAULT INJECTION: a scenario (4th argument) replaces or corrupts the results of
//      chosen agents so tests can check how a script accounts for failed, partial, and malformed
//      work (see "Scenario" below).
//
// Usage: node scripts/workflow_dryrun.mjs <script.js> [args-json] [mode] [scenario-json]
//   mode: a (booleans true, first enum), b (booleans false, last enum), mixed (alternating
//   booleans, cycling enums). Strings cycle through a small pool (s0, s1, s2) so ids produced by
//   different agents overlap the way real ids do and cross-referencing code paths run.
// Prints one JSON line: {"ok": true, "agents": N, "phases": [...], "calls": [...], "result": <the
// workflow's return value>, ...} and exits 0, or prints {"ok": false, "error": "..."} and exits 1.
//
// Scenario: {"rules": [rule, ...], "capture"?: "<regex>"}. Each rule has "match" (a regex tested
// against the agent's label, or its prompt when it has no label) and optionally "prompt" (a regex
// the prompt must also match), "skip" (ignore the first K matching calls) and "times" (apply to at
// most N matching calls after that). A rule either supplies a result — "return": <value>, which is
// checked against the call's schema like a real structured output; the first applicable "return"
// rule wins — or applies an "action" to the result (fake or returned), in rule order:
//   throw        agent() throws (message: "message")
//   null         agent() returns null (the runtime's skipped / died-after-retries result)
//   text         return "value" (for agents without a schema)
//   set          shallow-merge "values" into the result object
//   set_items    merge "values" into the items of an array field ("field", default: the first
//                array-valued key), optionally only items whose id is in "ids", or at "index"
//   drop         remove items from that array: those whose id is in "ids", else the last "count" (1)
//   duplicate    append copies of the first "count" (1) items, with "values" merged into the copies
//   unknown_id   append a copy of the first item whose id was never sent (string "UNKNOWN-ID", or
//                987654 for integer ids)
//   missing_id   delete the id from the first "count" (1) items
// The id key is "id_field", or "id"/"sid", whichever the item has. "capture" adds the label and
// prompt of every matching call to the output as "captured", so tests can assert what a stage was
// told (for example, that the report writer received the coverage numbers).

import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'

const [, , file, argsJson, mode = 'a', scenarioJson] = process.argv
const fail = (error) => {
  console.log(JSON.stringify({ ok: false, file, error: String(error && error.stack ? error.message : error) }))
  process.exit(1)
}
if (!file) fail('usage: workflow_dryrun.mjs <script.js> [args-json] [mode] [scenario-json]')
if (!['a', 'b', 'mixed'].includes(mode)) fail(`unknown mode "${mode}" (use a, b, or mixed)`)

const src = fs.readFileSync(file, 'utf8')

// ---- 1. meta -------------------------------------------------------------------------------
const lead = src.match(/^(?:\s*(?:\/\/[^\n]*|\/\*[\s\S]*?\*\/))*\s*export const meta = /)
if (!lead) fail('`export const meta = {...}` must be the first statement')
let i = lead[0].length
if (src[i] !== '{') fail('meta must be an object literal')
// Find the matching close brace, skipping string contents.
let depth = 0
let quote = null
let end = -1
for (let j = i; j < src.length; j++) {
  const c = src[j]
  if (quote) {
    if (c === '\\') { j++; continue }
    if (c === quote) quote = null
    continue
  }
  if (c === "'" || c === '"' || c === '`') { quote = c; continue }
  if (c === '{') depth++
  else if (c === '}' && --depth === 0) { end = j; break }
}
if (end < 0) fail('unbalanced meta literal')
const metaText = src.slice(i, end + 1)
const stripped = metaText.replace(/'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"/g, '""')
if (/`|\$\{|\.\.\.|\w\s*\(/.test(stripped)) fail('meta must be a pure literal (no template strings, spreads, or calls)')
let meta
try {
  meta = vm.runInNewContext(`(${metaText})`, Object.create(null))
} catch (e) {
  fail(`meta is not a valid literal: ${e.message}`)
}
if (!meta.name || !meta.description) fail('meta needs `name` and `description`')
const base = path.basename(file).replace(/\.m?js$/, '')
if (meta.name !== base) fail(`meta.name "${meta.name}" must equal the file basename "${base}"`)
const declared = new Set((meta.phases || []).map((p) => p.title))
if (meta.phases && declared.size !== meta.phases.length) fail('duplicate phase titles in meta.phases')

// ---- 2/3. body -----------------------------------------------------------------------------
const body = src.slice(end + 1)
for (const [re, what] of [
  [/\bDate\.now\s*\(/, 'Date.now()'],
  [/\bMath\.random\s*\(/, 'Math.random()'],
  [/\bnew Date\s*\(\s*\)/, 'argless new Date()'],
  [/\bimport\s*\(/, 'import()'],
  [/\brequire\s*\(/, 'require()'],
]) {
  if (re.test(body)) fail(`body uses ${what}, which the workflow runtime forbids`)
}
const AsyncFunction = (async () => {}).constructor
let fn
try {
  fn = new AsyncFunction('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'workflow', body)
} catch (e) {
  fail(`body does not compile: ${e.message}`)
}

// ---- 4. mocked run -------------------------------------------------------------------------
let boolToggle = false
let strCounter = 0
let enumCounter = 0
function fake(schema, where) {
  if (!schema || typeof schema !== 'object') fail(`${where}: missing/invalid schema node`)
  if (schema.enum) {
    if (!schema.enum.length) fail(`${where}: empty enum`)
    if (mode === 'b') return schema.enum[schema.enum.length - 1]
    if (mode === 'mixed') return schema.enum[enumCounter++ % schema.enum.length]
    return schema.enum[0]
  }
  if ('const' in schema) return schema.const
  const t = Array.isArray(schema.type) ? schema.type[0] : schema.type
  switch (t) {
    case 'object': {
      const props = schema.properties || {}
      for (const r of schema.required || []) {
        if (!(r in props)) fail(`${where}: required key "${r}" is not in properties`)
      }
      const o = {}
      for (const [k, s] of Object.entries(props)) o[k] = fake(s, `${where}.${k}`)
      return o
    }
    case 'array': {
      const n = Math.max(schema.minItems || 0, mode === 'b' ? 1 : 2)
      return Array.from({ length: n }, () => fake(schema.items, `${where}[]`))
    }
    case 'string':
      return `s${strCounter++ % 3}`
    case 'integer':
      return Math.max(schema.minimum ?? 3, 3)
    case 'number':
      return schema.minimum ?? 0.5
    case 'boolean':
      if (mode === 'mixed') return (boolToggle = !boolToggle)
      return mode !== 'b'
    case 'null':
      return null
    default:
      fail(`${where}: unsupported or missing type ${JSON.stringify(schema.type)}`)
  }
}

// ---- 5. fault-injection scenario ------------------------------------------------------------
let scenario = { rules: [] }
if (scenarioJson !== undefined && scenarioJson !== '') {
  try {
    scenario = JSON.parse(scenarioJson)
  } catch (e) {
    fail(`scenario-json is not valid JSON: ${e.message}`)
  }
  if (!scenario || typeof scenario !== 'object' || (scenario.rules !== undefined && !Array.isArray(scenario.rules))) {
    fail('scenario must be {"rules": [...], "capture"?: "<regex>"}')
  }
}
const ACTIONS = new Set(['throw', 'null', 'text', 'set', 'set_items', 'drop', 'duplicate', 'unknown_id', 'missing_id'])
const toRegExp = (s, where) => {
  try {
    return new RegExp(s)
  } catch (e) {
    return fail(`${where}: bad regex ${JSON.stringify(s)}: ${e.message}`)
  }
}
const rules = (scenario.rules || []).map((r, k) => {
  const where = `scenario rule ${k}`
  if (!r || typeof r !== 'object' || typeof r.match !== 'string') fail(`${where}: needs a "match" regex string`)
  const returns = Object.prototype.hasOwnProperty.call(r, 'return')
  if (returns === ('action' in r)) fail(`${where}: give exactly one of "return" or "action"`)
  if (!returns && !ACTIONS.has(r.action)) fail(`${where}: unknown action ${JSON.stringify(r.action)} (use ${[...ACTIONS].join(', ')})`)
  return { ...r, where, returns, re: toRegExp(r.match, where), promptRe: r.prompt ? toRegExp(r.prompt, where) : null, seen: 0, applied: 0 }
})
const captureRe = scenario.capture ? toRegExp(scenario.capture, 'scenario capture') : null
const captured = []
const clone = (v) => (v === undefined ? undefined : JSON.parse(JSON.stringify(v)))

// A fixture must look like a real structured output: the right types, required keys, enum values.
function conforms(schema, v, where) {
  if (!schema || typeof schema !== 'object') return
  if (schema.enum) {
    if (!schema.enum.includes(v)) fail(`${where}: fixture value ${JSON.stringify(v)} is not one of ${JSON.stringify(schema.enum)}`)
    return
  }
  const types = Array.isArray(schema.type) ? schema.type : [schema.type]
  const is = {
    object: (x) => x !== null && typeof x === 'object' && !Array.isArray(x),
    array: Array.isArray,
    string: (x) => typeof x === 'string',
    integer: Number.isInteger,
    number: (x) => typeof x === 'number' && Number.isFinite(x),
    boolean: (x) => typeof x === 'boolean',
    null: (x) => x === null,
  }
  if (!types.some((t) => is[t] && is[t](v))) fail(`${where}: fixture value ${JSON.stringify(v)} is not of type ${JSON.stringify(schema.type)}`)
  if (is.object(v) && schema.properties) {
    for (const r of schema.required || []) if (!(r in v)) fail(`${where}: fixture is missing required key "${r}"`)
    for (const [k, s] of Object.entries(schema.properties)) if (k in v) conforms(s, v[k], `${where}.${k}`)
  }
  if (Array.isArray(v) && schema.items) v.forEach((x, n) => conforms(schema.items, x, `${where}[${n}]`))
}

function arrayOf(result, rule, where) {
  if (!result || typeof result !== 'object') fail(`${where}: action "${rule.action}" needs an object result`)
  const key = rule.field || Object.keys(result).find((k) => Array.isArray(result[k]))
  if (!key || !Array.isArray(result[key])) fail(`${where}: action "${rule.action}" found no array field${rule.field ? ` "${rule.field}"` : ''}`)
  return result[key]
}
const idKey = (item, rule) => rule.id_field || (item && typeof item === 'object' && 'sid' in item && !('id' in item) ? 'sid' : 'id')

function applyAction(rule, result, label) {
  const where = `${rule.where} (${label})`
  const count = rule.count === undefined ? 1 : rule.count
  switch (rule.action) {
    case 'throw':
      throw new Error(rule.message || `injected fault: ${label} threw`)
    case 'null':
      return null
    case 'text':
      return rule.value === undefined ? 'injected text' : rule.value
    case 'set':
      if (!result || typeof result !== 'object') fail(`${where}: "set" needs an object result`)
      return Object.assign(result, clone(rule.values || {}))
    case 'set_items': {
      const arr = arrayOf(result, rule, where)
      const targets = rule.ids ? arr.filter((x) => rule.ids.includes(x[idKey(x, rule)])) : rule.index !== undefined ? [arr[rule.index]].filter(Boolean) : arr
      for (const x of targets) Object.assign(x, clone(rule.values || {}))
      return result
    }
    case 'drop': {
      const arr = arrayOf(result, rule, where)
      const keep = rule.ids ? arr.filter((x) => !rule.ids.includes(x[idKey(x, rule)])) : arr.slice(0, Math.max(0, arr.length - count))
      arr.splice(0, arr.length, ...keep)
      return result
    }
    case 'duplicate': {
      const arr = arrayOf(result, rule, where)
      arr.push(...arr.slice(0, count).map((x) => Object.assign(clone(x), clone(rule.values || {}))))
      return result
    }
    case 'unknown_id': {
      const arr = arrayOf(result, rule, where)
      if (!arr.length) fail(`${where}: "unknown_id" needs at least one item to copy`)
      for (let n = 0; n < count; n++) {
        const x = clone(arr[0])
        const k = idKey(x, rule)
        x[k] = typeof x[k] === 'number' ? 987654 + n : `UNKNOWN-ID${n ? `-${n + 1}` : ''}`
        arr.push(x)
      }
      return result
    }
    case 'missing_id': {
      const arr = arrayOf(result, rule, where)
      for (const x of arr.slice(0, count)) delete x[idKey(x, rule)]
      return result
    }
    default:
      return fail(`${where}: unknown action ${rule.action}`)
  }
}

const stats = { agents: 0, phases: new Set(), logs: 0, labels: [], calls: [], faults: 0 }
let currentPhase = null
const checkPhase = (title, where) => {
  if (meta.phases && !declared.has(title)) fail(`${where}: phase "${title}" is not declared in meta.phases`)
  stats.phases.add(title)
}

async function agent(prompt, opts = {}) {
  if (typeof prompt !== 'string' || prompt.trim().length < 20) fail('agent() needs a substantive prompt string')
  if (/undefined|\[object Object\]|NaN/.test(prompt)) fail(`agent prompt interpolated a bad value: ${prompt.slice(0, 160)}`)
  const known = new Set(['label', 'phase', 'schema', 'model', 'effort', 'isolation', 'agentType'])
  for (const k of Object.keys(opts)) if (!known.has(k)) fail(`agent(): unknown option "${k}"`)
  if (opts.effort && !['low', 'medium', 'high', 'xhigh', 'max'].includes(opts.effort)) fail(`agent(): bad effort ${opts.effort}`)
  if (opts.phase) checkPhase(opts.phase, 'agent({phase})')
  else if (currentPhase === null && meta.phases) fail('agent() called before any phase() and without opts.phase')
  stats.agents++
  if (stats.agents > 1000) fail('exceeded the 1000-agent runtime cap')
  if (opts.label) stats.labels.push(opts.label)
  const label = opts.label || prompt.slice(0, 80)
  stats.calls.push(label)
  if (captureRe && captureRe.test(label)) captured.push({ label, prompt })
  if (opts.schema && (opts.schema.type !== 'object' || !opts.schema.properties)) fail('schema root must be {type: "object", properties: {...}}')
  // Every rule counts the calls it matches, so "skip"/"times" do not depend on the other rules.
  const live = rules.filter((r) => {
    if (!r.re.test(label) || (r.promptRe && !r.promptRe.test(prompt))) return false
    r.seen++
    if (r.seen <= (r.skip || 0)) return false
    if (r.times !== undefined && r.applied >= r.times) return false
    r.applied++
    return true
  })
  const fixture = live.find((r) => r.returns)
  let result
  if (fixture) {
    result = clone(fixture.return)
    if (opts.schema) conforms(opts.schema, result, `${fixture.where} (${label})`)
  } else {
    result = opts.schema ? fake(opts.schema, opts.label || 'schema') : 'mock agent text'
  }
  for (const r of live.filter((x) => !x.returns)) {
    stats.faults++
    result = applyAction(r, result, label) // may throw: that is the injected fault
    if (result === null) break
  }
  return result
}

async function parallel(thunks) {
  if (!Array.isArray(thunks)) fail('parallel() takes an array of thunks')
  if (thunks.length > 4096) fail('parallel() over 4096 items')
  return Promise.all(thunks.map((t) => {
    if (typeof t !== 'function') fail('parallel() items must be functions (thunks), not promises')
    return Promise.resolve().then(t).catch((e) => { if (e && e.dryrunFatal) throw e; return null })
  }))
}

async function pipeline(items, ...stages) {
  if (!Array.isArray(items)) fail('pipeline() first argument must be an array')
  if (items.length > 4096) fail('pipeline() over 4096 items')
  return Promise.all(items.map(async (item, index) => {
    let prev = item
    for (const stage of stages) {
      try {
        prev = await stage(prev, item, index)
      } catch (e) {
        if (e && e.dryrunFatal) throw e
        return null
      }
    }
    return prev
  }))
}

function phase(title) {
  checkPhase(title, 'phase()')
  currentPhase = title
}
function log(message) {
  if (typeof message !== 'string') fail('log() takes a string')
  stats.logs++
}
const budget = { total: null, spent: () => 0, remaining: () => Infinity }
async function workflow() { fail('nested workflow() is not exercised by the dry run') }

// Make the runtime's forbidden globals throw here too, in case they are reached indirectly.
Date.now = () => fail('Date.now() is forbidden in workflow scripts')
Math.random = () => fail('Math.random() is forbidden in workflow scripts')

let runArgs
try {
  runArgs = argsJson === undefined || argsJson === '' ? undefined : JSON.parse(argsJson)
} catch (e) {
  fail(`args-json is not valid JSON: ${e.message}`)
}

try {
  const result = await fn(agent, parallel, pipeline, phase, log, runArgs, budget, workflow)
  if (result === undefined) fail('workflow returned undefined — return a result object')
  console.log(JSON.stringify({
    ok: true,
    file,
    name: meta.name,
    mode,
    agents: stats.agents,
    phases: [...stats.phases],
    logs: stats.logs,
    resultKeys: result && typeof result === 'object' ? Object.keys(result) : typeof result,
    faults: stats.faults,
    calls: stats.calls,
    ...(captureRe ? { captured } : {}),
    result,
  }))
} catch (e) {
  fail(e)
}
