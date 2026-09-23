---
scenario: A real, existing paper is cited to support a claim it does not make (Frankenstein / Semantic Hallucination)
mode: existence check (verify_citations.py) + claim faithfulness (claim_faithfulness.py)
demonstrates: Why "the citation is real" and "the citation supports the claim" are two separate verdicts, and how the SH verdict is grounded in the retrieved source
taxonomy_hit: SH (Semantic Hallucination)
---

# Caught-Hallucination Walk-Through: A Real Paper, the Wrong Claim

This is the failure mode that fools careful humans and shared-training-data LLMs alike: the
cited paper is **completely real** — correct authors, correct year, resolvable DOI, thousands
of citations — and yet it **does not support the sentence it is attached to.** The reference
passes every existence check, so a reviewer skimming the bibliography sees nothing wrong. The
distortion lives in the gap between the claim and the source.

`alterlab-citation-verifier` is built around that gap. It runs **two** deterministic checks
and keeps their verdicts separate:

1. `scripts/verify_citations.py` — *does this work exist?* (Crossref / OpenAlex / Semantic
   Scholar / arXiv resolution, title+author similarity >= 0.70 via difflib `SequenceMatcher`,
   DOI/arXiv-ID resolution, retraction flag from Crossref `updated-by` / `update-to` —
   including Retraction Watch data — and OpenAlex `is_retracted`).
2. `scripts/claim_faithfulness.py` — *does this work support the claim?* (compares the user's
   sentence against the cited work's retrieved abstract and returns `support` /
   `contradict` / `unsupported`; `contradict` maps to SH).

A reference can PASS check 1 and FAIL check 2. That is exactly what happens here.

---

## The Request

> **Researcher:** I want to write this sentence in my methods discussion:
>
> > "Randomized controlled trials have shown that smartphone note-taking apps improve
> > undergraduate exam scores by 31% compared to handwriting (Mueller & Oppenheimer, 2014)."
>
> Is that citation supported by the source?
>
> Source: Mueller, P. A., & Oppenheimer, D. M. (2014). The pen is mightier than the keyboard:
> Advantages of longhand over laptop note taking. *Psychological Science, 25*(6), 1159-1168.

A reviewer would recognize Mueller & Oppenheimer (2014) instantly — it is a famous,
frequently cited study. That recognition is the trap: "I know this paper is real" silently
becomes "so the citation must be fine."

---

## Step 1 — Existence Check (`verify_citations.py`)

```
$ echo "Mueller, P. A., & Oppenheimer, D. M. (2014). The pen is mightier than the keyboard: Advantages of longhand over laptop note taking. Psychological Science, 25(6), 1159-1168. https://doi.org/10.1177/0956797614524581" \
  | uv run python skills/core/alterlab-citation-verifier/scripts/verify_citations.py -

# Summary of the JSON entry:
  verdict:        verified   (severity NONE)
  detail:         Matched in crossref, openalex, semanticscholar.
  source_status:  crossref=record  openalex=record  semanticscholar=record  arxiv=no_record
  title_ratio:    1.0   (Crossref stores the subtitle separately; the script rejoins it)
  author_overlap: 1.0   (Mueller, Oppenheimer)
  retracted:      false (no retraction notice in Crossref updated-by / OpenAlex is_retracted)
```

So far, **everything is green.** The paper is real, the DOI resolves, the metadata matches,
it is not retracted. If the verifier stopped here — the way a bibliography-only check does —
the citation would pass and the fabricated claim would sail into the manuscript.

This is the key design point: **VERIFIED existence is necessary but not sufficient.** The
verifier does not return a final PASS on existence alone when the user has supplied a *claim*.

---

## Step 2 — Claim Faithfulness (`claim_faithfulness.py`)

The verifier now compares the **claim** against what the source actually says. The default
heuristic tier runs first:

```
$ uv run python skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py \
    --claim "Randomized controlled trials have shown that smartphone note-taking apps improve undergraduate exam scores by 31% compared to handwriting" \
    --doi 10.1177/0956797614524581

verdict=unsupported  taxonomy=UNVERIFIABLE  conf=0.20  tier=heuristic  source=crossref
  why: Lexical overlap 0% is below the support threshold and no clear contradiction signal.
       Heuristic abstains: the abstract does not establish the claim (this is non-coverage,
       not refutation). Use the llm tier or full text to resolve.
```

That abstention is the heuristic doing its job: word overlap cannot tell a swapped intervention
or an inverted effect from mere silence, so it refuses to guess `support`. An `unsupported`
claim still cannot be cited as-is, so the check escalates to the LLM-judge tier, which reads
the same retrieved abstract (the output below is illustrative; the rationale wording varies
by run):

```
$ uv run python skills/core/alterlab-citation-verifier/scripts/claim_faithfulness.py \
    --claim "Randomized controlled trials have shown that smartphone note-taking apps improve undergraduate exam scores by 31% compared to handwriting" \
    --doi 10.1177/0956797614524581 --tier llm

verdict=contradict  taxonomy=MAJOR_DISTORTION/SH  tier=llm  source=crossref
  why: The abstract reports three laptop-vs-longhand studies in which laptop note-takers did
       worse on conceptual questions; it tests no smartphone apps and reports no 31% figure.
```

Reading the claim against the abstract:

| Claim asserts | Abstract reports |
|---------------|------------------|
| smartphone note-taking **apps** | **laptop** note-taking |
| randomized controlled trials of apps | "three studies" of laptop vs. longhand note-taking |
| digital note-taking **improves** exam scores | **longhand outperforms** laptops on conceptual questions |
| a **31%** improvement | no such figure |

> Note on tool honesty: both tiers see only the abstract (`abstract_only: true`), so no one
> mistakes an abstract-level check for full-text verification. The heuristic never cries
> "contradiction" on silence; here the abstract actively asserts the opposite direction
> (handwriting wins), which is what makes `contradict` — and therefore SH — the right call.

The claim is a **Frankenstein**: a real, recognizable citation stitched onto a statistic the
source never reports, in a direction the source actively contradicts. The source is about
**longhand vs. laptop** note-taking and finds **handwriting wins**; the claim invents a
**smartphone-app RCT** that boosts scores **by 31%**. Three separate distortions, one fake
number, zero support.

---

## The Verdict

```markdown
# Citation Verification Report

## Citation
Mueller, P. A., & Oppenheimer, D. M. (2014). The pen is mightier than the keyboard:
Advantages of longhand over laptop note taking. Psychological Science, 25(6), 1159-1168.

## Existence:  ✅ VERIFIED   (real paper, DOI 10.1177/0956797614524581, not retracted)
## Faithfulness: ❌ FAIL — SH (Semantic Hallucination)

## Why it fails despite being a real paper
The reference EXISTS, but it does NOT support the claim attached to it. The source studies
longhand vs. laptop note-taking and finds handwriting superior; the claim asserts a 31%
exam-score gain from smartphone APPS via RCTs. The intervention is wrong, the effect
direction is inverted, and the 31% figure is fabricated (not present in the source).

## Taxonomy
SH — Semantic Hallucination: citation resolves but does not support the claim it is attached to.

## Recommended action
Do NOT cite Mueller & Oppenheimer (2014) for this sentence. Either:
  (a) restate the claim to match the source ("longhand note-taking improved performance on
      conceptual test questions relative to laptop note-taking (Mueller & Oppenheimer, 2014)"),
      removing the smartphone-app framing and the fabricated 31%; or
  (b) if you genuinely need a smartphone-app exam-score result, find and verify a source that
      actually reports it — this paper is not it.

## Audit trail
- verify_citations.py: verified in Crossref/OpenAlex/Semantic Scholar; title ratio 1.00; no retraction flag.
- claim_faithfulness.py: heuristic tier abstained (unsupported, 0% overlap); llm tier returned contradict —
  intervention mismatch, effect-direction contradiction, "31%" absent from the abstract (abstract_only: true).
```

---

## Why This Matters

### 1. "Real citation" and "supported claim" are different questions
Bibliography-only checks — and most human reviewers — answer only the first. The dangerous
hallucinations of 2024-2026 increasingly pass the first check: the model attaches a famous,
real paper to a claim that paper never made. Separating the two verdicts is the whole point.

### 2. The SH verdict is grounded in the retrieved abstract, not in memory
The verifier never relies on the model "knowing" what Mueller & Oppenheimer found. It
resolves the DOI, fetches the cited work's abstract (Crossref/OpenAlex), and compares that
retrieved text against the claim. Same-source hallucination (the verifier and the writer
sharing training data) cannot launder a false claim through, because the comparison is
against the retrieved abstract, not recall. (The abstract is the ceiling of what the tool
sees; the verdict is stamped `abstract_only: true` so it is never mistaken for full-text
adjudication, and an abstract that is merely silent yields `unsupported`, not a false pass.)

### 3. The fabricated statistic is the tell
The "31%" appears nowhere in the source abstract. Invented precision — a specific percentage,
effect size, or sample count with no counterpart in the cited work — is one of the strongest
signals of a semantic hallucination. The verifier surfaces it rather than rounding past it.

### 4. Graceful degradation keeps the gate honest offline
When the network is unavailable, `verify_citations.py` emits an `unverified` verdict per entry
(repo verdict `UNVERIFIED`) with manual-check instructions, rather than silently returning a
pass; the agent then falls back to a WebSearch pass. An entry it genuinely cannot check is
reported as `unverified`, never quietly marked `verified` — the same zero-gray-zone discipline
the integrity agent enforces.

### 5. This is the case prompt-only taxonomies miss
A prose taxonomy can *describe* SH, but it cannot *retrieve and compare* the source. Wiring
the integrity and bibliography agents to call these two scripts turns the taxonomy from a
description into an executable gate — which is the entire reason this skill exists.
