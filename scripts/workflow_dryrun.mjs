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
// Usage: node scripts/workflow_dryrun.mjs <script.js> [args-json] [mode]
//   mode: a (booleans true, first enum), b (booleans false, last enum), mixed (alternating
//   booleans, cycling enums). Strings cycle through a small pool (s0, s1, s2) so ids produced by
//   different agents overlap the way real ids do and cross-referencing code paths run.
// Prints one JSON line: {"ok": true, "agents": N, "phases": [...], ...} and exits 0, or
// prints {"ok": false, "error": "..."} and exits 1.

import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'

const [, , file, argsJson, mode = 'a'] = process.argv
const fail = (error) => {
  console.log(JSON.stringify({ ok: false, file, error: String(error && error.stack ? error.message : error) }))
  process.exit(1)
}
if (!file) fail('usage: workflow_dryrun.mjs <script.js> [args-json] [mode]')

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

const stats = { agents: 0, phases: new Set(), logs: 0, labels: [] }
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
  if (opts.schema) {
    if (opts.schema.type !== 'object' || !opts.schema.properties) fail('schema root must be {type: "object", properties: {...}}')
    return fake(opts.schema, opts.label || 'schema')
  }
  return 'mock agent text'
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
  }))
} catch (e) {
  fail(e)
}
