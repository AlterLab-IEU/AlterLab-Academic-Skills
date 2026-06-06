# Scoping Spike: Per-domain plugin scoping from a single repo (ws-1a)

**Status:** RESOLVED — **GO** (single-repo, per-domain scoping is feasible; the current v1.2.0 manifest shape is broken and must change).
**Date:** 2026-06-06
**Branch:** `feat/v2.0`
**Question:** Can a single Claude Code `marketplace.json` scope one repo into 13 independently-installable domain plugins, so that installing ONE plugin loads ONLY that domain's skills — not all 180?

---

## TL;DR verdict

- **The current v1.2.0 shape (`source: "./"` on every plugin) does NOT scope.** Installing any one of the 13 plugins silently loads **all 180 skills** from every domain. This is a real defect, not a theoretical one.
- **Single-repo per-domain scoping IS achievable** without splitting into 13 repos or using `git-subdir`. The fix is to make each plugin's `source` point at its **own domain subdirectory** so the plugin root is the domain folder, and the default `skills/` auto-discovery can only see that one domain.
- Therefore: **GO.** v2.0 keeps one repo and one `marketplace.json`. Only the `source` paths and the on-disk layout (one `skills/` level per domain) change.

---

## Why the current shape is broken

Current v1.2.0 marketplace entry (every one of the 13 plugins is identical in this respect):

```json
{
  "name": "alterlab-databases",
  "source": "./",
  "strict": false,
  "skills": [
    "./skills/databases/alterlab-pubmed",
    "./skills/databases/alterlab-uniprot",
    "... 37 more ..."
  ]
}
```

Two independent facts from the official docs combine to make this load everything:

### Fact 1 — `source: "./"` makes the plugin root = the repo root

> Relative path … Local directory within the marketplace repo. Must start with `./`. **Resolved relative to the marketplace root**, not the `.claude-plugin/` directory.
> — [plugin-marketplaces, Plugin sources table](https://code.claude.com/docs/en/plugin-marketplaces#plugin-sources)

So `source: "./"` resolves the plugin's root to `<repo>/` — the same root for all 13 plugins.

### Fact 2 — the `skills` array is ADDITIVE for skills, and the default `skills/` dir is always auto-discovered

The plugins-reference is explicit that the `skills` component-path field is **additive**, while `commands`/`agents`/`outputStyles` are **replacing**:

> `skills` … Custom skill directories containing `<name>/SKILL.md` **(in addition to default `skills/`)**
> `commands` … Custom flat `.md` skill files or directories **(replaces default `commands/`)**
> `agents` … Custom agent files **(replaces default `agents/`)**
> — [plugins-reference, Component path fields](https://code.claude.com/docs/en/plugins-reference#component-path-fields)

And skills are auto-discovered from the plugin root:

> **Location**: `skills/` … directory in plugin root … Skills and commands are **automatically discovered** when the plugin is installed.
> — [plugins-reference, Skills](https://code.claude.com/docs/en/plugins-reference#skills)

**Consequence:** Because the plugin root is `<repo>/` (Fact 1), the default `skills/` directory under that root is `<repo>/skills/` — the whole 13-domain tree (180 `SKILL.md`). Auto-discovery walks all of it. The curated `skills` array does **not** narrow that set; for the `skills` field it only *adds* (and here it adds the same paths that are already auto-discovered). **Net result: every plugin loads all 180 skills.**

`strict: false` does not save this either — it governs whether `plugin.json` vs. the marketplace entry is authoritative for component *definitions*; it does not turn off default-location auto-discovery from the plugin root. (There is no `plugin.json` anywhere in this repo — verified — so `strict` is effectively inert.)

### Corroborating evidence from the issue tracker

- **anthropics/claude-code #39156** — "[BUG] Skill loader ignores installPath for string-source marketplace plugin." Confirms, with binary analysis, that **string `source` plugins are resolved by joining the marketplace install dir + `source` string** (`resolvedPath = path.join(baseDir, entry.source)`), i.e. the plugin root really is that resolved directory and skills load from it. This is exactly the resolution that, with `source: "./"`, points at the repo root. <https://github.com/anthropics/claude-code/issues/39156>
- **anthropics/claude-code #15439** — "[FEATURE] Support `ref` and `path` parameters in plugin source schema." A user asks for subdir/version control on plugin sources and notes the current workaround of per-component arrays is "verbose and repetitive" and "doesn't solve" the structural problems. Confirms the community is hitting the same single-repo-multi-plugin friction. <https://github.com/anthropics/claude-code/issues/15439>
- Issue #1087 (referenced in the task) is an unrelated startup-hang bug in the public repo; the task used it as "territory," not a literal match. The substantive issues are #39156 and #15439.

---

## The fix: make each plugin's root its own domain folder

The on-disk layout (verified) is:

```
skills/
  databases/
    alterlab-pubmed/SKILL.md
    alterlab-uniprot/SKILL.md
    ...
  bioinformatics/
    alterlab-scanpy/SKILL.md
    ...
  ...11 more domains
```

Domains have **no nested `skills/` subdirectory** — the skill folders sit directly under each domain. That detail decides which corrected shape works.

### Recommended shape (Option A): `source` = domain folder + a `skills` array

Point `source` at the domain directory, and use the explicit `skills` array (relative to the new plugin root) to enumerate that domain's skills. Because the domain folder has **no `skills/` subdirectory**, default `skills/` auto-discovery finds nothing under the new root, so the explicit array is the *only* thing loaded — and it only contains that one domain.

```json
{
  "name": "alterlab-databases",
  "source": "./skills/databases",
  "description": "Connectors to scientific databases (PubMed, ChEMBL, UniProt, GEO, and more) (39 skills)",
  "version": "2.0.0",
  "strict": false,
  "skills": [
    "./alterlab-pubmed",
    "./alterlab-uniprot",
    "./alterlab-chembl"
  ]
}
```

- `source: "./skills/databases"` → plugin root = `<repo>/skills/databases/`.
- `skills` paths are now **relative to that plugin root** (`./alterlab-pubmed`, not `./skills/databases/alterlab-pubmed`).
- No `skills/` subfolder exists under that root → no over-collection. Installing `alterlab-databases` loads exactly its 39 skills and nothing from the other 12 domains.

**Why keep the explicit `skills` array at all** (vs. relying on auto-discovery)? Two reasons: (1) it is defensive — if anyone later adds a `skills/` subfolder inside a domain, the explicit array still pins the set; (2) it makes the per-plugin contract reviewable in one file and survives the additive-vs-replacing subtlety. The array MUST use plugin-root-relative paths.

### Cleaner alternative (Option B): one nested `skills/` level per domain

Restructure on disk to `skills/<domain>/skills/<skill>/SKILL.md`, point `source: "./skills/<domain>"`, and drop the explicit `skills` array entirely — let default auto-discovery of the per-domain `skills/` handle it. This is the most idiomatic Claude Code layout, but it requires moving 180 skill folders down one level (a `git mv` per domain) and updating any tests that hardcode `skills/<domain>/<skill>` paths. **Recommend Option A for v2.0** (no mass file moves; the array does the scoping) and treat Option B as a later cleanup if desired.

### What NOT to ship

- `source: "./"` on multiple plugins (current bug — loads everything).
- Relying on the `skills` array alone with `source: "./"` to scope — it is additive, so it cannot subtract the auto-discovered repo-wide `skills/` tree.
- `git-subdir` per domain — works, but it is for pulling a subdir out of an *external* monorepo over a sparse clone; pointless when the marketplace and the plugins live in the same repo. Adds clone overhead and `ref`/`sha` bookkeeping for zero benefit here. Only needed if domains were split into separate repos (they are not).

---

## Exact `marketplace.json` shape v2.0 should emit

Top level is unchanged (name, owner, metadata). Each of the 13 plugin entries changes in exactly two ways: `source` becomes the domain path, and `skills` entries become plugin-root-relative. Bump versions to `2.0.0`. Skeleton (databases shown in full, others elided):

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "alterlab-academic-skills",
  "owner": {
    "name": "AlterLab @ Izmir University of Economics",
    "email": "alterlab.ieu@gmail.com"
  },
  "metadata": {
    "description": "180 Claude skills for academic research, organized by domain",
    "version": "2.0.0"
  },
  "plugins": [
    {
      "name": "alterlab-databases",
      "source": "./skills/databases",
      "description": "Connectors to scientific databases (PubMed, ChEMBL, UniProt, GEO, and more) (39 skills)",
      "version": "2.0.0",
      "author": { "name": "AlterLab @ Izmir University of Economics", "url": "https://github.com/AlterLab-IEU" },
      "homepage": "https://github.com/AlterLab-IEU/AlterLab-Academic-Skills",
      "license": "MIT",
      "category": "data",
      "keywords": ["database", "api", "pubmed", "uniprot", "chembl", "bioinformatics"],
      "strict": false,
      "skills": [
        "./alterlab-alphafold-db",
        "./alterlab-arxiv",
        "./alterlab-pubmed",
        "./alterlab-uniprot"
      ]
    }
  ]
}
```

Per-plugin `source` mapping (all 13):

| plugin | `source` | # skills |
| :-- | :-- | --: |
| alterlab-bioinformatics | `./skills/bioinformatics` | 25 |
| alterlab-cheminformatics | `./skills/cheminformatics` | 12 |
| alterlab-clinical-research | `./skills/clinical-research` | 7 |
| alterlab-core | `./skills/core` | 7 |
| alterlab-data-science | `./skills/data-science` | 22 |
| alterlab-databases | `./skills/databases` | 39 |
| alterlab-document-tools | `./skills/document-tools` | 2 |
| alterlab-domain-specific | `./skills/domain-specific` | 17 |
| alterlab-finance-economics | `./skills/finance-economics` | 7 |
| alterlab-lab-integrations | `./skills/lab-integrations` | 9 |
| alterlab-research-tools | `./skills/research-tools` | 12 |
| alterlab-visualization | `./skills/visualization` | 8 |
| alterlab-writing-tools | `./skills/writing-tools` | 13 |

Transform rule for the `skills` arrays (mechanical, per entry): strip the `./skills/<domain>/` prefix and replace with `./`. e.g. `./skills/databases/alterlab-pubmed` → `./alterlab-pubmed`.

---

## Validation plan (before merge)

The verdict above is derived from the documented resolution rules and corroborated by the loader internals in #39156, but the additive-vs-replacing behavior of the `skills` array should be confirmed empirically on the target Claude Code version, since loader behavior has changed across releases (see #39156 affecting v2.1.81–84):

1. Build a corrected `marketplace.json` (Option A) on a scratch branch.
2. `/plugin marketplace add <local path>` then `/plugin install alterlab-document-tools@alterlab-academic-skills` (smallest, 2 skills).
3. Run `/help` (or `claude plugin` listing) and confirm **only** `markitdown` and `open-notebook` appear under that plugin namespace — NOT all 180.
4. Repeat for one larger domain (databases) to confirm the count matches the table.
5. Run `claude plugin validate` against the manifest to catch any conflicting-manifest or missing-path errors.

GO is conditional on step 3 showing scoped loading; the design is sound, but the empirical check is cheap and removes the last uncertainty about the additive `skills` semantics on the installed CLI version.

---

## Evidence links

- Plugins reference (component path fields, skills auto-discovery, strict mode, error messages): <https://code.claude.com/docs/en/plugins-reference>
- Plugin marketplaces (source types table, relative-path resolution, strict mode, monorepo `git-subdir`): <https://code.claude.com/docs/en/plugin-marketplaces>
- Create plugins (skills/ layout, namespacing): <https://code.claude.com/docs/en/plugins>
- anthropics/claude-code #39156 — string-source skill-loader resolution (`path.join(baseDir, entry.source)`): <https://github.com/anthropics/claude-code/issues/39156>
- anthropics/claude-code #15439 — request for `ref`/`path` on plugin sources; documents single-repo-multi-plugin friction: <https://github.com/anthropics/claude-code/issues/15439>
