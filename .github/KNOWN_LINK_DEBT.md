# Known Link Debt

URLs excluded from link checking that warrant future review. Each entry explains *why* the exclusion exists so maintainers do not need to reconstruct context. Keep this file in sync with `.lycheeignore` — if you add or remove an exclusion pattern, update the corresponding row here (or add a new one with rationale).

## Categories

### Infrastructure hostility (permanent)

URLs where the host systematically blocks or fails for CI runners, regardless of any fix on our side. Rows are permanent unless the host changes policy.

| URL pattern | Reason | Date excluded | Revisit trigger |
| --- | --- | --- | --- |
| `unicarbkb.org/*` | Invalid request format on HEAD from CI; probe-dependent 405 on desktop too. | 2026-04-21 | Host announces support for HEAD / link-checker bots |
| `dicom.nema.org/*` | TCP connection reset when requested from GitHub Actions (Azure) runners; pages load in browser. | 2026-04-21 | GitHub runner network policy changes |
| `console.cloud.google.com/marketplace/*` | HTTP/2 handshake errors against GCP marketplace pages from CI. | 2026-04-21 | lychee HTTP/2 behaviour improves |
| `gnomad.broadinstitute.org/api` (GraphQL) | GraphQL endpoints return 400 on GET (accepted via `accept=[..., "400", ...]` but included here for traceability). | 2026-04-21 | — |
| `linkedin.com/*`, `x.com/*`, `twitter.com/*`, `t.co/*` | Aggressive anti-bot (999/403/451) regardless of accept config. | 2026-04-21 | — |
| `iqtree.org/workshop/molevol2022*` | SSL certificate expired; content still useful as prose citation. | 2026-04-21 | Cert renewal |
| `*.stlouisfed.org/*` | HTTP/2 handshake fails from GH Actions runners; alive from desktop. | 2026-04-21 | lychee / curl HTTP/2 improvements |
| `docking.org` (wiki/files/cartblanche22) | TCP resets from CI; live in browser. | 2026-04-21 | Host network policy changes |
| `modal.com/{apps,secrets}` | Return 500 without authenticated session. | 2026-04-21 | — |
| `asterweb.jpl.nasa.gov/*` | Connection reset from CI. | 2026-04-21 | — |
| `charmm-gui.org/*` | 20s timeouts from both CI and desktop. | 2026-04-21 | Host responsiveness improves |
| `na-mic.org/*` | SSL OCSP revocation check fails (schannel + curl). | 2026-04-21 | Cert / CRL infrastructure fixed |
| `flowcyt.org/*`, `prisma.thetacollaborative.ca/*` | Dead / DNS-blocked from CI. | 2026-04-21 | — |
| `fda.gov/{animal-veterinary,food/compliance-enforcement-food/*,safety/recalls-market-withdrawals-safety-alerts}` | Bot-blocked even with accept=403; pages are live in browser. | 2026-04-21 | FDA relaxes bot policy |
| `jra.kishou.go.jp/*` | DNS resolution fails from CI runners. | 2026-04-21 | — |
| `fosteropenscience.eu/*` | FOSTER project ended 2019; kept in archive.org form in prose. | 2026-04-21 | — |
| `spikeinterface.readthedocs.io/.../qualitymetrics.html` | Upstream moved; no redirect. | 2026-04-21 | Upstream doc refactor |
| `www.atcc.org/resources/cell-line-authentication-testing-service` | Page dropped without redirect; every reasonable substitute also 404s. | 2026-04-21 | ATCC restores a canonical page |

### Upstream migrations (temporary)

Exclusions expected to be removed once upstream projects finish doc restructures. Each row tracks an issue to reassess.

| URL pattern | Reason | Date excluded | Tracking issue |
| --- | --- | --- | --- |
| `docs.pylabrobot.org/*` | Entire pylabrobot docs site is mid-migration to MyST; individual page-level substitutions keep 404ing. | 2026-04-21 | #2 |

### Pedagogical placeholders (deliberate)

URLs that are intentional filler in template or example files. They demonstrate a citation FORMAT, not real resources. These should stay excluded indefinitely.

| URL pattern | Reason |
| --- | --- |
| `doi.org/x+`, `doi.org/10.x+`, `doi.org/xx.*`, `doi.org/10.xxx/yyy`, `doi.org/10.xxxx/yyyy`, `doi.org/xx.xxx/yyyy` | Placeholder DOI patterns used in citation templates. |
| `doi.org/10.1038/nrd.2023.001`, `doi.org/10.1101/2024.01.001`, `doi.org/10.1057/s41307-023-00318-5`, `doi.org/10.1080/17439884.2023.2141509` | Illustrative example citations in writing-tool templates (not registered with their prefixes). |
| `your-tenant.benchling.com/*` | Tenant-placeholder hostname used in authentication examples. |
| `join.slack.com/t/*` | Ephemeral Slack invite URLs; treat as placeholder content. |
| `localhost(:port)/*` | Example dev-server references in skill docs; never reachable from CI. |

### Chinese-language journal DOIs (needs native reader review)

Six DOIs excluded pending source-citation verification. Two have suspicious parentheses in the suffix that look like transcription errors. A reader fluent in the source language should cross-check each against the original citation and either correct the DOI or confirm it is indeed unregistered.

- `doi.org/10.6152/jce.2022.0303.04`
- `doi.org/10.6152/jhe.2022.1302.02`
- `doi.org/10.6542/TERSS.202312_23(2).0002`  ← suspicious parentheses
- `doi.org/10.6773/JALE.202206_(38).0001`     ← suspicious parentheses
- `doi.org/10.3966/102887082023126904001`
- `doi.org/10.3966/156082982022032501001`

### Dead substitutions (review for replacement)

URLs where the original target is dead and no verified replacement has been committed. Empty state is the goal — populating this section means somebody guessed and left a breadcrumb for future verification.

No current entries.

## Maintenance

- When adding to `.lycheeignore`, add a row here with reason + date.
- When removing an entry from `.lycheeignore` (because upstream fixed the issue), delete the corresponding row here.
- Entries in "Upstream migrations" should link a tracking issue; close the entry when the issue resolves.
