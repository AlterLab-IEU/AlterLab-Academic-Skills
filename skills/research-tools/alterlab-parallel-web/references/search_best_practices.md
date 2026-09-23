# Search Best Practices

How to get the best results from this skill's `search`/`research` commands, plus the raw Search API params for when you call the HTTP/SDK API directly.

> **Scope:** `scripts/parallel_web.py search` wraps the **Chat API** (`base`/`core` models). Its only inputs are the `objective` string and `--model`. The `search_queries`, `max_results`, `source_policy`, and `mode` parameters in this doc belong to the **raw Search API** (`POST /v1/search`, GA since Nov 2025; `parallel-web` ≥ 1.0 exposes it as `client.search()`) and are not accepted by the script — examples using them are labeled "raw Search API". The objective-writing advice applies to both.

---

## Core Concepts

Both the Chat API (this skill) and the raw Search API return LLM-optimized, citation-backed results from web sources based on a natural-language objective, ranked for reasoning utility rather than engagement. A single well-scoped objective often resolves a complex, multi-topic question in one request.

---

## Crafting Effective Objectives

A strong `objective` is the single biggest lever on result quality for the Chat API search/research commands. State your broader task, source preferences, freshness, and content type in one natural-language string.

**Good (works with `parallel_web.py search "<objective>"`):**
```bash
python scripts/parallel_web.py search \
  "I'm writing a literature review on Alzheimer's treatments. Find peer-reviewed research and clinical-trial results from the past 2 years on amyloid-beta targeted therapies (e.g. lecanemab, donanemab) with outcome data." \
  -o sources/search_alzheimer_amyloid.md
```

**Poor:**
```bash
# Too vague - no context about intent or scope
python scripts/parallel_web.py search "Alzheimer's treatment"
```

**Raw Search API** (direct SDK call, not the script) pairs the objective with explicit keyword queries — in v1, `search_queries` is required (2-3 short queries of 3-6 words work best):
```python
# raw Search API — requires calling the SDK directly, not parallel_web.py
from parallel import Parallel
client = Parallel()  # reads PARALLEL_API_KEY
result = client.search(
    objective="Find peer-reviewed clinical-trial results on amyloid-beta therapies (2024-2025).",
    search_queries=[
        "amyloid beta clinical trials 2024-2025",
        "lecanemab donanemab trial outcomes",
    ],
    mode="fast",
    advanced_settings={"max_results": 10},
)
for r in result.results:
    print(r.title, r.url, r.publish_date)
```

### Objective Writing Tips

1. **State your broader task**: "I'm writing a research paper on...", "I'm analyzing the market for...", "I'm preparing a presentation about..."
2. **Be specific about source preferences**: "Prefer official government websites", "Focus on peer-reviewed journals", "From major news outlets"
3. **Include freshness requirements**: "From the past 6 months", "Published in 2024-2025", "Most recent data available"
4. **Specify content type**: "Technical documentation", "Clinical trial results", "Market analysis reports", "Product announcements"

### Example Objectives by Use Case

**Academic Research:**
```
"I'm writing a literature review on CRISPR gene editing applications in cancer therapy.
Find peer-reviewed papers from Nature, Science, Cell, and other high-impact journals
published in 2023-2025. Prefer clinical trial results and systematic reviews."
```

**Market Intelligence:**
```
"I'm preparing Q1 2025 investor materials for a fintech startup.
Find recent announcements from the Federal Reserve and SEC about digital asset
regulations and banking partnerships with crypto firms. Past 3 months only."
```

**Technical Documentation:**
```
"I'm designing a machine learning course. Find technical documentation and API guides
that explain how transformer attention mechanisms work, preferably from official
framework documentation like PyTorch or Hugging Face."
```

**Current Events:**
```
"I'm tracking AI regulation developments. Find official policy announcements,
legislative actions, and regulatory guidance from the EU, US, and UK governments
from the past month."
```

---

## Search Modes (raw Search API only)

The `mode`, `source_policy`, and `max_results` features belong to the raw Search API (`POST /v1/search`). They are not available through `parallel_web.py`; use them only when calling the SDK/HTTP API directly. v1 has four modes (checked 2026-09 against docs.parallel.ai; the Beta `one-shot`/`agentic` modes map to `fast`/`advanced`):

| Mode | What it does | Latency | Cost per 1,000 requests |
|------|--------------|---------|-------------------------|
| `turbo` | Lowest latency and cost; English and Japanese queries only | ~200 ms | $1 |
| `fast` | High-quality, sub-second search; Parallel's recommended starting point for agents | ~700 ms | $1 |
| `basic` | Extended snippets per result; works best with 2-3 good `search_queries` | ~1 s | $5 |
| `advanced` (default) | Advanced retrieval and compression for multi-hop, quality-first work | ~3 s | $5 |

Start with `fast`; use `advanced` for background research where depth matters more than latency, and `basic` when you want longer excerpts per source in one call.

---

## Source Policy (raw Search API only)

Control which domains are included or excluded from results (direct SDK call, not `parallel_web.py`). In v1 the policy lives inside `advanced_settings`:

```python
# raw Search API
client.search(
    objective="Find clinical trial results for new cancer immunotherapy drugs",
    search_queries=["checkpoint inhibitor clinical trials 2025"],
    advanced_settings={
        "source_policy": {
            "include_domains": ["clinicaltrials.gov", "nejm.org", "thelancet.com", "nature.com"],
            "exclude_domains": ["reddit.com", "quora.com"],
            "after_date": "2024-01-01",
        }
    },
)
```

### Source Policy Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_domains` | list[str] | Hard allow-list: only these domains (or domain/path prefixes; a bare extension such as `.gov` also works) are searched |
| `exclude_domains` | list[str] | Block these domains or path prefixes |
| `after_date` | str (YYYY-MM-DD) | Only include content published on or after this date |

`include_domains` and `exclude_domains` together may list at most 200 entries. Parallel warns that `include_domains` can sharply reduce result quality because the rest of the web is not searched; when you only want to steer toward good sources, say so in the `objective` ("prefer peer-reviewed journals") and reserve `include_domains` for tasks that must come from specific publishers.

### Domain Lists by Use Case

**Academic Research:**
```python
include_domains = [
    "nature.com", "science.org", "cell.com", "thelancet.com",
    "nejm.org", "bmj.com", "pnas.org", "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov", "scholar.google.com"
]
```

**Technology/AI:**
```python
include_domains = [
    "arxiv.org", "openai.com", "anthropic.com", "deepmind.google",
    "huggingface.co", "pytorch.org", "tensorflow.org",
    "proceedings.neurips.cc", "proceedings.mlr.press"
]
```

**Market Intelligence:**
```python
exclude_domains = [
    "reddit.com", "quora.com", "medium.com",
    "wikipedia.org"  # Good for facts, not for market data
]
```

**Government/Policy:**
```python
include_domains = [
    ".gov", "europa.eu", "who.int", "worldbank.org",
    "imf.org", "oecd.org", "un.org"
]
```

---

## Controlling Result Volume (raw Search API only)

These knobs apply to the raw Search API, not `parallel_web.py`.

### `max_results` (inside `advanced_settings`)

- Default 10; public modes cap it at 20 (larger values are reduced with a warning), and the API may return fewer
- More results = broader coverage but more tokens to process
- Fewer results = more focused but may miss relevant sources

**Recommendations:**
- Quick fact check: `max_results=3`
- Standard research: `max_results=10` (default)
- Comprehensive survey: `max_results=20`

### Excerpt Length Control

```python
# raw Search API
client.search(
    objective="...",
    search_queries=["..."],
    max_chars_total=50000,  # cap on excerpt characters across all results
    advanced_settings={"excerpt_settings": {"max_chars_per_result": 10000}},
)
```

- **Short excerpts (1000-3000)**: Quick summaries, metadata extraction
- **Medium excerpts (5000-10000)**: Standard research, balanced depth
- **Long excerpts (10000-50000)**: Full article content, deep analysis

---

## Common Patterns

These use this skill's `search` command. The pattern is the same every time: pack the intent, scope, and freshness into one objective string and save to `sources/`.

### Pattern 1: Research Before Writing

```bash
python scripts/parallel_web.py search \
  "Find recent advances in transformer attention mechanisms (2024-2025) for a NeurIPS paper introduction: efficient-attention variants, key results, and benchmarks." \
  -o sources/search_attention_advances.md
```

### Pattern 2: Fact Verification

```bash
python scripts/parallel_web.py search \
  "Verify whether GPT-4 achieved 86.4% on the MMLU benchmark. Cite the primary source and note the evaluation setting." \
  -o sources/search_gpt4_mmlu.md
```

### Pattern 3: Competitive Intelligence

```bash
python scripts/parallel_web.py search \
  "Find recent (2025) product launches and funding announcements for AI coding assistants. Prefer primary announcements and reputable tech press." \
  --model core -o sources/search_ai_coding_tools.md
```

### Pattern 4: Multi-Language Research

The Chat API returns multilingual sources automatically — just name the regions in the objective:

```bash
python scripts/parallel_web.py search \
  "Find global perspectives on AI regulation, covering the EU AI Act, China's AI policy, and US executive actions, with 2025 updates." \
  --model core -o sources/search_ai_regulation_global.md
```

To pin specific authoritative domains or a date floor, use `source_policy` via the raw Search API (see above).

---

## Troubleshooting

### Few or No Results

- **Broaden your objective**: Remove overly specific constraints
- **Add more search queries**: Different phrasings of the same concept
- **Remove source policy**: Domain restrictions may be too narrow
- **Check date filters**: `after_date` may be too recent

### Irrelevant Results

- **Make objective more specific**: Add context about your task
- **Use source policy**: Allow only authoritative domains
- **Add negative context**: "Not about [unrelated topic]"
- **Refine search queries**: Use more precise keywords

### Too Many Tokens in Results

- **Reduce `max_results`**: From 10 to 5 or 3
- **Reduce excerpt length**: Lower `max_chars_total` or `excerpt_settings.max_chars_per_result`
- **Avoid `basic` mode**: it returns extended snippets; `fast` or `turbo` keep excerpts shorter

---

## See Also

- [API Reference](api_reference.md) - Complete API parameter reference
- [Deep Research Guide](deep_research_guide.md) - For comprehensive research tasks
- [Extraction Patterns](extraction_patterns.md) - For reading specific URLs
- [Workflow Recipes](workflow_recipes.md) - Common multi-step patterns
