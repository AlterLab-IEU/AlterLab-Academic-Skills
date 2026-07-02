# Social-Science Workflow — the methods spine

The `social-science-workflow` domain is not a bag of tools; it is a **stage-gated pipeline** of
four discipline-enforcing gates that a study passes through *in order*, before it is analyzed or
written. Each gate refuses to advance until its one discipline is satisfied, and each writes to a
shared **Design Passport** that the next gate reads. The gates deliberately *route to* the suite's
existing analysis skills rather than reimplementing them.

## The four gates

| Order | Skill | The one rule it enforces |
|:----:|-------|--------------------------|
| 1 | [`alterlab-ssci-design-gate`](../skills/social-science-workflow/alterlab-ssci-design-gate/) | A causal claim is only as good as its **identifying assumption** — name it first. |
| 2 | [`alterlab-ssci-measurement-gate`](../skills/social-science-workflow/alterlab-ssci-measurement-gate/) | A reliable measure of the wrong construct is still wrong — **reliability ≠ validity**. |
| 3 | [`alterlab-ssci-sampling-gate`](../skills/social-science-workflow/alterlab-ssci-sampling-gate/) | Sizing logic follows the inference — **power / precision / saturation**, never a rule of thumb. |
| 4 | [`alterlab-ssci-inference-gate`](../skills/social-science-workflow/alterlab-ssci-inference-gate/) | A claim may not exceed its **design, sample, or uncertainty**. |

## The Design Passport

The Passport is a small YAML document threaded through the gates. Each gate appends the fields it
owns; the inference gate audits the final claims against everything upstream.

```yaml
# design-gate writes:
research_question: <the question>
design_type: <experiment | did | iv | rdd | its | fe | observational | qualitative | mixed>
identifying_assumption: <the named assumption + why it is defensible — or "not defended">
claim_type: <causal | associational | descriptive>

# measurement-gate appends (per construct):
constructs:
  - name: <construct>
    reliability: <omega + alpha with tau-equivalence caveat>
    validity_evidence: <which of content/criterion/convergent/discriminant are shown>
    dimensionality: <CFA fit>
    invariance: <none | configural | metric | scalar | strict>

# sampling-gate appends:
target_population: <who the claim is about>
sampling_frame: <what was actually drawn from> + coverage_gap
sampling_method: <SRS | stratified | cluster | systematic | quota | convenience | snowball | purposive>
size_logic: <power | precision | saturation> + inputs + n
generalization: <statistical | analytical>

# inference-gate reads all of the above and audits every claim sentence against it.
```

## What the gates do NOT do

They do not run models. Execution is routed to existing suite skills:

- Design depth / qualitative mechanics → `alterlab-qualitative-methods`, `alterlab-mixed-methods`
- Instrument construction → `alterlab-survey-design`
- CFA / SEM / invariance → the psychometrics skill (phase 2)
- Test choice → `alterlab-test-selection-guard`
- Computation → `alterlab-statistical-analysis`

This is by design: the gates add **methodological discipline**, and delegate **computation** to the
skills that already do it well. Each gate ships a stdlib helper (`design_router.py`,
`sample_size.py`, `claim_audit.py`) that enforces the gate's rule without any third-party
dependency, plus a loaded-on-demand reference and vignette-in / routing-out evals.

## Relationship to the `methodology` domain

The `methodology` domain (`alterlab-test-selection-guard`, pre-registration discipline, results
transparency) supplies **general** research-rigor gates. `social-science-workflow` is the
**social-science-specific spine** that sequences design → measurement → sampling → inference and
carries the Design Passport between them. The two compose: the sampling gate hands test choice to
`alterlab-test-selection-guard`, and the inference gate's transparency checks echo the
methodology domain's reporting discipline.

## Roadmap

Phase 1 (shipped) is the four **validity gates** above — the eval-first showcase. Phase 2 adds the
thin **orchestrator** and six pluggable **analysis modules** (causal-inference, SEM/psychometrics,
QCA, social-network analysis, agent-based modeling, text-as-data), each web-verified against its
library's current API before shipping.
