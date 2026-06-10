# Adaptyv Foundry API Reference

This is a working reference for the public **Foundry API**. The API evolves, so treat the
machine-readable OpenAPI schema as authoritative and verify exact field names against it:

- OpenAPI: `https://foundry-api-public.adaptyvbio.com/api/v1/openapi.json`
- Docs: `https://docs.adaptyvbio.com`

Response JSON below is **illustrative** (shapes shown to orient parsing code), not a guaranteed
contract — confirm fields from the OpenAPI doc or a live response before depending on them.

## Base URL

```
https://foundry-api-public.adaptyvbio.com/api/v1
```

## Authentication

All requests use a bearer token:

```
Authorization: Bearer YOUR_API_TOKEN
```

Create and manage tokens in the Foundry portal at `https://foundry.adaptyvbio.com/` under
**Organization → Settings → Tokens**:
- **Role** — `Member` (read/write) or `Viewer` (read-only).
- **Expiry** — from 7 days up to 1 year.
- The token value is displayed **once** at creation — copy it before closing the dialog.

Store it as the `ADAPTYV_API_KEY` environment variable (also read by the official SDK), keep it
out of version control, and load it from a gitignored `.env` in local development.

## Experiment Lifecycle

Experiments move through a state machine, roughly:

```
Draft → WaitingForConfirmation → QuoteSent → WaitingForMaterials
      → InQueue → InProduction → DataAnalysis → InReview → Done
```

The typical programmatic flow:

1. `GET /targets` — find a `target_id` (only needed for binding-type assays).
2. `POST /experiments` — create a **draft** with the sequences + spec.
3. `GET /experiments/{id}/quote` (or `POST /experiments/cost-estimate`) — review cost.
4. `POST /experiments/{id}/submit` — submit to the lab. Nothing is charged before this.
5. Poll `GET /experiments/{id}` (or use a webhook) until `Done`.
6. `GET /experiments/{id}/results` — retrieve data.

## Endpoints

### Targets

#### Browse Target Catalog

`GET /targets`

Browse available target antigens. Filter by name, vendor, and self-service availability.
Targets with a calibrated self-service price support instant cost estimates and automated checkout.

Returns a list of targets each carrying a `target_id` (UUID) to reference when creating
binding (`screening` / `affinity`) experiments.

### Experiments

#### Create Experiment (draft)

`POST /experiments`

**Request Body:**
```json
{
  "name": "mini-binder round 1",
  "webhook_url": "https://your-server.com/adaptyv-webhook",
  "experiment_spec": {
    "experiment_type": "screening|affinity|thermostability|fluorescence|expression",
    "method": "bli|spr",
    "target_id": "<uuid, required for screening/affinity>",
    "sequences": {
      "design_a": "MKVLWALLGLLGAA...",
      "design_b": "MATGVLWALLG..."
    }
  }
}
```

Notes:
- `sequences` is a **map** of `label → amino_acid_string` (not a FASTA blob).
- **Multi-chain** constructs join chains with a colon, e.g. a Fab as `"HEAVY...:LIGHT..."`.
- `method` (`bli` / `spr`) applies to binding-type assays; non-binding assays
  (`thermostability`, `fluorescence`, `expression`) do not need a `target_id`.

**Response (illustrative):**
```json
{
  "experiment_id": "<uuid>",
  "experiment_code": "EXP-XXXX",
  "status": "draft",
  "costs": { "...": "..." }
}
```

#### Update Draft

`PATCH /experiments/{experiment_id}`

Edit a draft (name, sequences, spec) before submitting.

#### Cost Estimate

`POST /experiments/cost-estimate`

Accepts the same `experiment_spec` structure and returns an estimated price (USD cents),
typically broken into assay and material costs. Use this to budget before committing.

#### Submit Experiment

`POST /experiments/{experiment_id}/submit`

Submits a draft to the lab. After this the experiment advances through the lifecycle above.

#### Get Experiment Status

`GET /experiments/{experiment_id}`

Returns the experiment's current `status` (a lifecycle state above) and a `results_status`
field (`none` / `partial` / `all`) indicating how much result data is ready.

#### List Experiments

`GET /experiments`

Lists experiments for your organization. Supports pagination / filtering — check the OpenAPI
doc for the exact query parameters.

### Results

#### Get Experiment Results

`GET /experiments/{experiment_id}/results`

Returns the experimental data once the run completes. Contents depend on `experiment_type`:
binding classifications and kinetic constants (KD, kon, koff) for `screening`/`affinity`,
melting temperatures for `thermostability`, intensities for `fluorescence`, and yields for
`expression`. See `reference/experiments.md` for per-assay output details.

### Quotes

`GET /experiments/{experiment_id}/quote` — retrieve the quote for a draft.
`POST /quotes/{quote_id}/confirm` — confirm a quote (pricing / invoicing).

## Webhooks

Pass `webhook_url` when creating an experiment to receive a callback as the run progresses,
instead of polling. Use an HTTPS endpoint and acknowledge with `200 OK`. Verify the payload
shape and any signature scheme against the current docs before parsing in production.

## Error Handling

Errors are returned with appropriate HTTP status codes (e.g. `401` unauthorized, `404` not
found, `422` validation error) and a JSON body describing the problem. Implement retry with
exponential backoff for `429`/`5xx`, and surface `4xx` validation messages to the caller
rather than retrying. See `reference/examples.md` for a reusable retry wrapper.

## Best Practices

1. **Use the official SDK** (`adaptyvbio/adaptyv-sdk`) where possible; drop to raw `requests` only when needed.
2. **Review the quote** before `submit` — nothing is charged until you confirm.
3. **Use webhooks** for long-running experiments instead of tight polling.
4. **Validate sequences locally** (valid amino acids, correct colon-separated multi-chain format) before submission.
5. **Tag experiments** with a clear `name` and meaningful labels for traceability.
6. **Pre-filter computationally** (see `reference/protein_optimization.md`) so you only pay to test promising candidates.

## Support

- Email: support@adaptyvbio.com
- Docs: `https://docs.adaptyvbio.com`
- OpenAPI: `https://foundry-api-public.adaptyvbio.com/api/v1/openapi.json`
- Report bugs with the `experiment_code` / `experiment_id` and request details.
