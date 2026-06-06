# Citation Integrity Gate

AlterLab's loudest credibility objection used to be *"academic skills are just prompts —
they will happily cite papers that do not exist."* That objection is real: independent
audits put LLM citation fabrication anywhere from **18%** (GPT-4) to **56%** (Deakin 2025,
GPT-4o) of references, with an estimated **~147k hallucinated citations** circulating in 2025.

The **citation integrity gate** is the deterministic, network-backed answer. It is a shared
core capability living in [`skills/core/alterlab-citation-verifier/`](../skills/core/alterlab-citation-verifier/),
called by the corpus's integrity-sensitive agents
([`integrity_verification_agent`](../skills/core/alterlab-research-pipeline/agents/integrity_verification_agent.md),
[`bibliography_agent`](../skills/core/alterlab-deep-research/agents/bibliography_agent.md))
instead of a generic, same-model WebSearch that is prone to confirming its own hallucinations.

The gate has **two halves**, run in order:

1. **Existence + metadata** — *does the cited work exist, and does its metadata match?*
   Handled by `verify_citations.py` (Crossref + OpenAlex + Semantic Scholar + arXiv existence
   check, title/author similarity, DOI/arXiv-ID resolution, Retraction Watch flag).
2. **Claim faithfulness** — *does the cited work actually support the claim attached to it?*
   Handled by [`claim_faithfulness.py`](../skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py),
   documented here.

This document is the source of truth for the **claim-faithfulness half** — its tiers, its
verdict vocabulary, how those verdicts map onto the corpus claim taxonomy, and — critically —
**what it cannot do.** Honesty about limits is the whole point: a faithfulness checker that
over-claims is worse than none, because it launders fabrications behind a green check.

---

## The five-type fabrication taxonomy

The corpus already ships the best prose taxonomy in the field (GPTZero × NeurIPS 2025; Ansari,
2026), defined in `integrity_verification_agent.md`. The gate maps to it directly:

| Type | Code | Share | Caught by |
|------|------|-------|-----------|
| Total Fabrication | **TF** | 66% | `verify_citations.py` (existence) |
| Partial Attribute Corruption | **PAC** | 27% | `verify_citations.py` (metadata cross-check) |
| Identifier Hijacking | **IH** | 4% | `verify_citations.py` (DOI/arXiv resolution vs title+authors) |
| Placeholder Hallucination | **PH** | 2% | `verify_citations.py` (placeholder/stub detection) |
| **Semantic Hallucination** | **SH** | 1% | **`claim_faithfulness.py` (this tool)** |

`claim_faithfulness.py` owns the **SH** row: the citation resolves to a real paper with
correct metadata, but the paper *does not say what the citing text claims it says*. SH is the
hardest class — existence checks pass — and it is the only one that requires reading content,
not just resolving identifiers.

---

## `claim_faithfulness.py`

### What it does

Given one or more `(claim, DOI)` pairs, it:

1. **Fetches the cited work's abstract** — Crossref first (JATS-XML, stripped to plain text),
   falling back to OpenAlex (reconstructing plain text from the `abstract_inverted_index`).
2. **Scores claim support** as one of three verdicts — `support`, `contradict`, or
   `unsupported` — using one of two tiers.
3. **Returns a structured result** with the verdict, a confidence, the tier used, a rationale,
   the lexical signals behind the call, and the `abstract_only` / `abstract_found` / `source`
   flags so no downstream consumer can mistake an abstract-level pass for full-text proof.

It is **standard-library only** (`urllib`/`json`/`re`) — no `requests`, no third-party deps —
so it runs under `uv run python` with no extra installs. The polite-pool contact defaults to
`alterlab.ieu@gmail.com` and is override-able via `ALTERLAB_CONTACT_EMAIL`.

### The two scoring tiers

#### Tier 1 — `heuristic` (default; deterministic, offline once the abstract is in hand)

A transparent **keyword-overlap + entailment-lite** scorer. It computes content-term overlap
between claim and abstract, plus a lightweight **polarity signal**: stemmed antonym pairs
(`increas`/`decreas`, `outperform`/`underperform`, `support`/`refut`, …) and a negation-count
delta. Decision logic is deliberately conservative:

| Condition | Verdict | Confidence cap |
|-----------|---------|----------------|
| overlap ≥ 0.30 **and** an antonym/polarity flip | `contradict` | ≤ 0.55 |
| overlap ≥ 0.60 **and** no flip **and** no negation mismatch | `support` | ≤ 0.60 |
| otherwise | `unsupported` (abstain) | ≤ 0.30 |

The key design choice: **the heuristic is biased toward abstaining.** When it is not sure, it
returns `unsupported` rather than a false `support`. Its `support` confidence is hard-capped at
**0.60** precisely because lexical overlap is *not* semantic entailment — a high cap would
imply a rigor the method does not have.

#### Tier 2 — `llm` (optional; opt-in via `--tier llm`)

An LLM-judge tier that asks the model configured by the **`ALTERLAB_MODEL` convention** (see
[`skills/core/shared/model_env.md`](../skills/core/shared/model_env.md)) to classify the pair.
The prompt instructs the judge that it sees **only the abstract**, that non-coverage is
`unsupported` (not `contradict`), and to return a single minified JSON object.

- **No model id is ever hardcoded.** The only literal lives in the one `DEFAULT_MODEL` constant
  (reviewed 2026-06-06, currently `claude-opus-4-8`), per `model_env.md` rule 1. Override at
  runtime with `ALTERLAB_MODEL`; an empty value is treated as unset.
- **Graceful degradation.** If the `claude` CLI is absent, the call fails, or the model returns
  unparseable output, the tier **falls back to the heuristic** and relabels the result's tier as
  `llm->heuristic-fallback` with the reason prepended to the rationale — never a silent failure
  (closes the #1154 silent-fallback class).

### Verdict → corpus taxonomy mapping

This tool's three verdicts map onto the Phase-E **Claim Verdict Taxonomy** in
`integrity_verification_agent.md`:

| `claim_faithfulness.py` | Corpus verdict | Severity | Meaning |
|-------------------------|----------------|----------|---------|
| `support` | `VERIFIED` | none | Abstract is consistent with the claim |
| `contradict` | `MAJOR_DISTORTION` / **SH** | SERIOUS | Abstract asserts the opposite (polarity flip) |
| `unsupported` | `UNVERIFIABLE` (abstain) | — | Abstract does not establish the claim — **non-coverage, not refutation** |

When **no abstract** can be fetched at all, the result is `unsupported` with
`abstract_found: false`, which corresponds to the corpus's **`UNVERIFIABLE_ACCESS`** (MEDIUM):
the verifier could not read the source and the agent must fall back to full-text / WebSearch.

### Usage

```bash
# single pair
uv run python skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py \
    --claim "Transformers outperform RNNs on translation" \
    --doi 10.48550/arXiv.1706.03762

# batch from JSON ([{"claim": "...", "doi": "..."}, ...]) -> JSON report
uv run python .../claim_faithfulness.py --input pairs.json --json

# LLM-judge tier (uses $ALTERLAB_MODEL)
uv run python .../claim_faithfulness.py --input pairs.json --tier llm --json

# offline, deterministic self-test on a toy pair (no network)
uv run python .../claim_faithfulness.py --self-test
```

The process exits **non-zero if any pair is `contradict`**, so it can be wired directly into a
CI gate.

---

## Honest limitations

These are real and load-bearing. Treat the gate as a **high-recall triage filter**, not an
oracle. A clean pass means "no integrity problem was *detected at the abstract level*," not
"this citation is verified."

1. **Abstract ceiling.** The tool sees only the abstract, never the full text. A claim drawn
   from a paper's results section that is not mentioned in the abstract reads as `unsupported`
   even when the full text fully supports it. `abstract_only: true` is always set so this is
   never forgotten downstream. Abstract silence is **non-coverage, not contradiction.**

2. **The heuristic is bag-of-words, not entailment.** It is invariant to word order, so
   **subject–object role reversal** ("A outperforms B" vs "B outperforms A") is invisible and
   reads as `support`. It also misses numeric mismatches (it does not compare figures), scope
   and qualifier changes ("in mice" vs "in humans"), hedging, and sarcasm. Use `--tier llm` or
   full-text verification when role or number fidelity matters.

3. **Crude stemming.** The antonym/polarity check uses a hand-rolled suffix stripper, not a
   lemmatizer. It catches common inflections (`increase`/`increasing`/`increased`) but will
   miss irregular forms and antonyms not in the hand-curated list.

4. **English-only signals.** The stopword list, antonym pairs, and negation tokens are English.
   Non-English abstracts degrade to overlap-only scoring and will mostly abstain.

5. **Coverage gaps.** Some DOIs have no abstract in either Crossref or OpenAlex (notably many
   DataCite/arXiv-form DOIs and older or paywalled records). These return `abstract_found:
   false` and **must** be escalated to full-text/WebSearch verification, not passed.

6. **The LLM tier shares the corpus's same-source-hallucination risk.** If the judge model and
   the drafting model share training data, a plausible-but-wrong claim can be judged `support`.
   The abstract-grounding constraint and the heuristic cross-check mitigate but do not eliminate
   this; the existence half of the gate (`verify_citations.py`) is the independent backstop.

The design rule throughout: **when uncertain, abstain (`unsupported`) and escalate.** The gate
exists to stop fabricated and distorted citations from passing silently — not to manufacture
false confidence that they are correct.

---

## References

- Ansari, S. (2026). *Compound Deception in Elite Peer Review: A Failure Mode Taxonomy of 100
  Fabricated Citations at NeurIPS 2025.* arXiv:2602.05930.
- Walters, W. H., & Wilder, E. I. (2023). Fabrication and errors in the bibliographic citations
  generated by ChatGPT. *Scientific Reports, 13*, 14045. https://doi.org/10.1038/s41598-023-41032-5
- Deakin University (2025). GPT-4o citation accuracy audit (56% fabricated/erroneous).
