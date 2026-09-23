# Tier 1 — Config

Goal: eliminate CI-level false positives with a single reviewable commit that introduces three artefacts at the repo root.

## Files to create

1. `.lychee.toml` — lychee's config file. lychee only auto-loads `lychee.toml` (no leading dot) from the working directory, so pass this one with `--config`.
2. `.lycheeignore` — regex-per-line exclusion list.
3. `.github/workflows/check-links.yml` — hardened workflow.

## `.lychee.toml` template

```toml
# .lychee.toml — pass it explicitly with `--config .lychee.toml` (see workflow below).

# HTTP status codes treated as success. Both this key and the CLI `--accept`
# flag REPLACE lychee's default set (100..=103, 200..=299) rather than extending
# it — a common footgun — so the 2xx range is listed explicitly.
accept = ["200..=299", "301", "302", "304", "308", "403", "429"]

# Cache results between scheduled runs. lychee writes `.lycheecache`.
cache = true
# Drop cached results after a day so a transient outage is not pinned as OK/ERROR.
max_cache_age = "1d"

# Per-request timeout (lychee default: 20). 30 gives slow academic mirrors a fair chance.
timeout = 30

# Back-off before retrying a failed request (default: 1).
retry_wait_time = 5

# Retry transient failures (5xx, network errors, 429) up to this many times
# (default: 3). 5 absorbs most DOI / publisher flakes without bloating CI time.
max_retries = 5

# Follow redirect chains common to DOIs and archive.org links (default: 10).
max_redirects = 10

# Paths to skip entirely. Entries are REGULAR EXPRESSIONS matched against the
# path, not literal paths: a bare ".git" would also match "digital-humanities"
# (any character + "git"). Anchor and escape them.
exclude_path = ["(^|/)node_modules/", "(^|/)\\.git/", "(^|/)\\.github/ISSUE_TEMPLATE/"]

# Placeholder / example DOIs deliberately included in templates.
exclude = [
  "^https?://doi\\.org/x+$",
  "^https?://doi\\.org/10\\.x+",
  "^https?://doi\\.org/xx\\.",
  "^https?://doi\\.org/10\\.xxx/yyy",
  "^https?://doi\\.org/10\\.xxxx/yyyy",
  "^https?://doi\\.org/xx\\.xxx/yyyy",
  "^https?://your-tenant\\.benchling\\.com/.*",
]
```

### Why each `accept` code

- `200..=299` — normal success.
- `301, 302, 304, 308` — redirects; combined with `max_redirects = 10` covers DOI → publisher chains.
- `403` — academic / publisher sites (BMJ, Oxford Academic, Sage, OECD, Ensembl) bot-block automated requests from CI runners even when the content is public.
- `429` — rate-limited responses on retry are transient, not broken links.

**Do not** accept `400`. A 400 means the host actively rejected the request, and accepting it globally hides genuinely broken or moved API endpoints and malformed URLs — exactly the rot the check exists to surface. If one specific endpoint (for example a GraphQL URL that only answers POST) returns 400 to a GET probe, exclude that exact URL in `.lycheeignore` with a comment. This repo's source audit originally accepted 400 for such endpoints and later removed it after re-probing showed nothing relied on it.

**Do not** blanket-accept `500..=504`. Those indicate upstream infrastructure problems. Handle per-host in `.lycheeignore` with a comment.

lychee sends `GET` by default. Hosts that reject bot traffic sometimes accept a different method; current lychee (v0.24.x) accepts `--method head,get` to try each in turn, but prefer a per-host exclusion over widening methods globally.

## `.lycheeignore` starter

```
# Badge / shield services — always 200 but noisy.
^https?://img\.shields\.io/.*
^https?://shields\.io/.*
^https?://awesome\.re/.*
^https?://capsule-render\.vercel\.app/.*

# Anti-bot / auth-walled hosts.
^https?://([a-z0-9-]+\.)?linkedin\.com/.*
^https?://(twitter\.com|x\.com|t\.co)/.*

# gitter.im 301s to matrix.to and trips max-redirects.
^https?://gitter\.im/.*
```

Add host-specific entries during Tier 4 (see `tier4-exclusions.md`) with a `#` comment above each group explaining why the host is excluded.

## Workflow (`.github/workflows/check-links.yml`)

```yaml
name: Check Links

on:
  schedule:
    - cron: "0 9 * * 1"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  check-links:
    name: Check for Dead Links
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Restore lychee cache
        uses: actions/cache@v6
        with:
          path: .lycheecache
          key: cache-lychee-${{ github.sha }}
          restore-keys: cache-lychee-

      # lychee writes its cache to .lycheecache itself (cache = true in the config).
      # `output` is the Markdown REPORT path — never point it at the cache file,
      # or each run overwrites the cache with the report.
      - name: Check links in Markdown files
        uses: lycheeverse/lychee-action@v2
        with:
          args: --config .lychee.toml --no-progress "**/*.md"
          output: ./lychee/out.md
          jobSummary: true
          fail: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Hardening checklist

- Current majors as of 2026-09: `actions/checkout@v7`, `actions/cache@v6`, `lycheeverse/lychee-action@v2` (v2.9.x, which installs lychee v0.24.2 by default). Pin to a commit SHA if your org requires it, and re-check majors when you touch the workflow.
- `actions/cache` keyed on SHA — consecutive scheduled runs reuse already-verified results (bounded by `max_cache_age`).
- `output` is the report path (default `lychee/out.md`), distinct from `.lycheecache`; `jobSummary: true` puts the report in the run summary.
- Args reference `.lychee.toml` via `--config` — keep inline args to the glob only.
- `fail: true` — CI fails on residual errors so regressions are visible.
- `permissions: contents: read` — least privilege; the workflow doesn't need write.
- `GITHUB_TOKEN` exposed — lychee authenticates github.com URLs (higher rate limit).

## The gotcha that motivated this tier

The original workflow passed `args: --verbose --no-progress --accept 403 "**/*.md"`. The `--accept` flag **replaces** the default accept set instead of extending it — so every `200 OK` was reclassified as a failure. That single line accounted for the bulk of the 1208 baseline errors. Moving the config to `.lychee.toml` makes the accepted-status set explicit and reviewable, and survives future CLI-flag drift.

**Write the root cause into the PR body**, not just the commit message: "the `--accept 403` flag on the lychee CLI replaces the default accept set rather than extending it — every 200 OK was rejected as a result." That one sentence saves the next person from rediscovering the footgun in six months.
