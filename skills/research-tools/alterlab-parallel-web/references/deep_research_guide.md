# Deep Research Guide

How to run deep research with this skill's `research` command, plus reference material on Parallel's raw Task API for when you need processors, structured schemas, or async runs.

> **Scope — read first:** `scripts/parallel_web.py research` wraps the **Chat API** `core` model (override with `--model base`). It is synchronous and returns a markdown report with citations. It does NOT take `processor`, `description`, or `output_schema`, and there is NO `research_structured()` method. Everything below mentioning `processor=`, `description=`, `research_structured()`, or async `task_run` is the **raw Task API** (`POST /v1/tasks/runs`) — usable only by calling the SDK/HTTP API directly, not through `parallel_web.py`.

---

## Using the `research` command (Chat API)

```bash
# Default: core model, comprehensive report
python scripts/parallel_web.py research \
  "Comprehensive analysis of the global EV battery market: competitive landscape, market size, and growth projections through 2030." \
  -o sources/research_ev_battery_market.md

# Faster / cheaper pass with the base model
python scripts/parallel_web.py research "Latest funding rounds in AI startups (2025)" --model base \
  -o sources/research_ai_funding.md
```

To steer the report's focus or structure, write it into the query string itself (the Chat API has no separate `description` field):

```bash
python scripts/parallel_web.py research \
  "Electric-vehicle battery technology landscape. Focus on (1) solid-state progress, (2) charging-speed improvements, (3) cost-per-kWh trends, (4) key patents. Use clear section headers." \
  --model core -o sources/research_ev_battery_tech.md
```

`base` vs `core`: use `base` for quick factual synthesis (15-100s), `core` for deep multi-source reports (1-5min). See [API Reference](api_reference.md) for the full model table.

---

## Raw Task API (processors, schemas, async)

Everything in this section requires calling the Parallel SDK/HTTP API directly. The bundled script does not expose it.

### Processor Selection

For the raw Task API, choosing the right processor determines research depth, speed, and cost.

### Decision Matrix

| Scenario | Recommended Processor | Why |
|----------|----------------------|-----|
| Quick background for a paper section | `pro-fast` | Fast, good depth, low cost |
| Comprehensive market research report | `ultra-fast` | Deep multi-source synthesis |
| Simple fact lookup or metadata | `base-fast` | Fast, low cost |
| Competitive landscape analysis | `pro-fast` | Good balance of depth and speed |
| Background for grant proposal | `pro-fast` | Thorough but timely |
| State-of-the-art review for a topic | `ultra-fast` | Maximum source coverage |
| Quick question during writing | `core-fast` | Sub-2-minute response |
| Breaking news or very recent events | `pro` (standard) | Freshest data prioritized |
| Large-scale data enrichment | `base-fast` | Cost-effective at scale |

### Processor Tiers Explained

**`pro-fast`** (default, recommended for most tasks):
- Latency: 30 seconds to 5 minutes
- Depth: Explores 10-20+ web sources
- Best for: Section-level research, background gathering, comparative analysis
- Cost: $0.10 per query

**`ultra-fast`** (for comprehensive research):
- Latency: 1 to 10 minutes
- Depth: Explores 20-50+ web sources, multiple reasoning steps
- Best for: Full reports, market analysis, complex multi-faceted questions
- Cost: $0.30 per query

**`core-fast`** (quick cross-referenced answers):
- Latency: 15 seconds to 100 seconds
- Depth: Cross-references 5-10 sources
- Best for: Moderate complexity questions, verification tasks
- Cost: $0.025 per query

**`base-fast`** (simple enrichment):
- Latency: 15 to 50 seconds
- Depth: Standard web lookup, 3-5 sources
- Best for: Simple factual queries, metadata enrichment
- Cost: $0.01 per query

### Standard vs Fast

- **Fast processors** (`-fast`): 2-5x faster, very fresh data, ideal for interactive use
- **Standard processors** (no suffix): Highest data freshness, better for background jobs

**Rule of thumb:** Always use `-fast` variants unless you specifically need the freshest possible data (breaking news, live financial data, real-time events).

---

### Output Formats

These use the raw Task API SDK (`client.task_run`). For the skill's `research` command, you only get text output — fold focus/structure requests into the query string instead.

#### Text Mode (Markdown Reports)

Returns a comprehensive markdown report with inline citations. Best for human consumption and document integration.

```python
# raw Task API
from parallel import Parallel
from parallel.types import TaskSpecParam
client = Parallel()

run = client.task_run.create(
    input="Comprehensive analysis of mRNA vaccine platforms beyond COVID-19. "
          "Focus on clinical trials, approved applications, pipeline, key companies, and market size.",
    processor="pro-fast",
    task_spec=TaskSpecParam(output_schema={"type": "text"}),
)
result = client.task_run.result(run.run_id, api_timeout=3600)
print(result.output.content)  # markdown report
```

**When to use text mode:**
- Writing scientific documents (papers, reviews, reports)
- Background research for a topic
- When you need flowing prose, not structured data

#### Auto-Schema Mode (Structured JSON)

Lets the processor determine the best output structure automatically. Returns structured JSON with per-field citations (raw Task API only — omit `task_spec` for auto-schema):

```python
# raw Task API
run = client.task_run.create(
    input="Top 5 cloud computing companies: revenue, market share, key products, recent developments",
    processor="pro-fast",
)
result = client.task_run.result(run.run_id, api_timeout=3600)
print(result.output.content)  # structured dict
print(result.output.basis)    # per-field citations
```

**When to use auto-schema:**
- Data extraction and enrichment
- Comparative analysis with specific fields
- When you need programmatic access to individual data points
- Integration with databases or spreadsheets

#### Custom JSON Schema

Define exactly what fields you want returned (raw Task API):

```python
# raw Task API
schema = {
    "type": "object",
    "properties": {
        "market_size_2024": {
            "type": "string",
            "description": "Global market size in USD billions for 2024. Include source."
        },
        "growth_rate": {
            "type": "string",
            "description": "CAGR percentage for 2024-2030 forecast period."
        },
        "top_companies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Company name"},
                    "market_share": {"type": "string", "description": "Approximate market share percentage"},
                    "revenue": {"type": "string", "description": "Most recent annual revenue"}
                },
                "required": ["name", "market_share", "revenue"]
            },
            "description": "Top 5 companies by market share"
        },
        "key_trends": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top 3-5 industry trends driving growth"
        }
    },
    "required": ["market_size_2024", "growth_rate", "top_companies", "key_trends"],
    "additionalProperties": False
}

run = client.task_run.create(
    input="Global cybersecurity market analysis",
    processor="pro-fast",
    task_spec=TaskSpecParam(output_schema={"type": "json", "json_schema": schema}),
)
result = client.task_run.result(run.run_id, api_timeout=3600)
```

---

## Writing Effective Research Queries

### Query Construction Framework

Structure your query as: **[Topic] + [Specific Aspect] + [Scope/Time] + [Output Expectations]**

**Good queries:**
```
"Comprehensive analysis of the global lithium-ion battery recycling market,
including market size, key players, regulatory drivers, and technology
approaches. Focus on 2023-2025 developments."

"Compare the efficacy, safety profiles, and cost-effectiveness of GLP-1
receptor agonists (semaglutide, tirzepatide, liraglutide) for type 2
diabetes management based on recent clinical trial data."

"Survey of federated learning approaches for healthcare AI, covering
privacy-preserving techniques, real-world deployments, regulatory
compliance, and performance benchmarks from 2023-2025 publications."
```

**Poor queries:**
```
"Tell me about batteries"          # Too vague
"AI"                                # No specific aspect
"What's new?"                       # No topic at all
"Everything about quantum computing from all time"  # Too broad
```

### Tips for Better Results

1. **Be specific about what you need**: "market size" vs "tell me about the market"
2. **Include time bounds**: "2024-2025" narrows to relevant data
3. **Name entities**: "semaglutide vs tirzepatide" vs "diabetes drugs"
4. **Specify output expectations**: "Include statistics, key players, and growth projections"
5. **Keep under 15,000 characters**: Concise queries work better than massive prompts

---

## Working with Citations / Basis

Every research result includes citations (the Chat API "basis"): source URLs with excerpts.

### From the `research` command (Chat API)

```python
from parallel_web import ParallelDeepResearch
result = ParallelDeepResearch().research(query="...", model="core")

# Citations are deduplicated and include URLs + excerpts
for citation in result["citations"]:
    print(f"Source: {citation['title']}")
    print(f"URL: {citation['url']}")
    if citation.get("excerpts"):
        print(f"Excerpt: {citation['excerpts'][0][:200]}")
```

### Structured-Mode Basis (raw Task API)

When using the raw Task API with a schema, each field carries its own per-field basis with confidence and reasoning (`result.output.basis`). The Chat API used by this skill returns text + flat citations only, not per-field confidence.

### Confidence Levels (raw Task API basis)

| Level | Meaning | Action |
|-------|---------|--------|
| `high` | Multiple authoritative sources agree | Use directly |
| `medium` | Some supporting evidence, minor uncertainty | Use with caveat |
| `low` | Limited evidence, significant uncertainty | Verify independently |

---

## Advanced Patterns

These use the skill's `ParallelDeepResearch` / `ParallelExtract` classes (Chat + Extract APIs).

### Multi-Stage Research

Use `base` for a fast overview, then `core` for a deep dive, feeding context forward:

```python
from parallel_web import ParallelDeepResearch
researcher = ParallelDeepResearch()

# Stage 1: Quick overview with the base model
overview = researcher.research(
    query="What are the main approaches to quantum error correction?",
    model="base",
)

# Stage 2: Deep dive, carrying context forward
deep_dive = researcher.research(
    query=f"Detailed analysis of surface-code quantum error correction: "
          f"recent breakthroughs, implementation challenges, and leading research groups. "
          f"Context so far: {overview['response'][:500]}",
    model="core",
)
```

### Comparative Research

Fold the comparison structure into the query string (no separate `description` field on the Chat API):

```python
result = researcher.research(
    query="Compare three leading LLM architectures (GPT-4, Claude, Gemini): "
          "architecture differences, benchmark scores, pricing, context window, "
          "and unique capabilities. Present a summary comparison table with specific numbers.",
    model="core",
)
```

### Research with Follow-Up Extraction

```python
from parallel_web import ParallelDeepResearch, ParallelExtract
researcher = ParallelDeepResearch()
extractor = ParallelExtract()

# Step 1: Research to find relevant sources
research_result = researcher.research(
    query="Most influential papers on attention mechanisms in 2024",
    model="core",
)

# Step 2: Extract full content from the top cited sources
key_urls = [c["url"] for c in research_result["citations"][:5]]
for url in key_urls:
    extracted = extractor.extract(
        urls=[url],
        objective="Key methodology, results, and conclusions",
    )
```

---

## Performance and Cost

- **Pick the right model:** `base` for fast factual synthesis, `core` for deep multi-source reports. With the raw Task API, choose the cheapest processor that hits your depth (start at `base-fast`/`core-fast`, escalate to `pro-fast`/`ultra-fast` only when needed).
- **Be specific:** vague queries cost more exploration time for worse results.
- **Batch and cache:** one well-crafted query beats several shallow ones; save every result to `sources/` and reuse it across sections (see SKILL.md).
- **Verify critical findings:** cross-check key citations with `extract` before citing.

---

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Query too vague | Scattered, unfocused results | Add specific aspects and time bounds |
| Query too long | API rejection or degraded results | Summarize context, focus on key question |
| Using `base` for a deep report | Too shallow | Use `--model core` for comprehensive research |
| Folding nothing into the query | Report structure not aligned with needs | Write focus/structure requests into the query string |
| Not verifying citations | Risk of outdated or misattributed data | Cross-check key citations with `extract` |

---

## See Also

- [API Reference](api_reference.md) - Complete API parameter reference
- [Search Best Practices](search_best_practices.md) - For quick web searches
- [Extraction Patterns](extraction_patterns.md) - For reading specific URLs
- [Workflow Recipes](workflow_recipes.md) - Common multi-step patterns
