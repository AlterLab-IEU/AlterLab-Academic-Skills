# Workflow Recipes

Common multi-step patterns combining the skill's `search`, `extract`, and `research` commands for scientific writing tasks.

> **Scope:** these recipes use `scripts/parallel_web.py`, which wraps the Chat API (`search`/`research`, models `base`/`core`) and the Extract API (`extract`). The script does NOT accept `--processor`, `--queries`, `--max-results`, `source_policy`, or `research_structured()` — those belong to the raw Search/Task APIs (see [api_reference.md](api_reference.md)). Where a recipe needs domain pinning or structured output, call the SDK directly.

---

## Recipe Index

| Recipe | APIs Used | Time | Use Case |
|--------|-----------|------|----------|
| [Section Research Pipeline](#recipe-1-section-research-pipeline) | Research + Search | 2-5 min | Writing a paper section |
| [Citation Verification](#recipe-2-citation-verification) | Search + Extract | 1-2 min | Verifying paper metadata |
| [Literature Survey](#recipe-3-literature-survey) | Research + Search + Extract | 5-15 min | Comprehensive lit review |
| [Market Intelligence Report](#recipe-4-market-intelligence-report) | Research (multi-stage) | 10-30 min | Market/industry analysis |
| [Competitive Analysis](#recipe-5-competitive-analysis) | Search + Extract + Research | 5-10 min | Comparing companies/products |
| [Fact-Check Pipeline](#recipe-6-fact-check-pipeline) | Search + Extract | 1-3 min | Verifying claims |
| [Current Events Briefing](#recipe-7-current-events-briefing) | Search + Research | 3-5 min | News synthesis |
| [Technical Documentation Gathering](#recipe-8-technical-documentation-gathering) | Search + Extract | 2-5 min | API/framework docs |
| [Grant Background Research](#recipe-9-grant-background-research) | Research + Search | 5-10 min | Grant proposal background |

---

## Recipe 1: Section Research Pipeline

**Goal:** Gather research and citations for writing a single section of a scientific paper.

**Commands:** `research` (core) + `search`

```bash
# Step 1: Deep research for comprehensive background
python scripts/parallel_web.py research \
  "Recent advances in federated learning for healthcare AI (2023-2025): privacy-preserving training methods, real-world deployments, and regulatory considerations. Structure as (1) key approaches, (2) clinical deployments, (3) regulatory landscape, (4) open challenges, with statistics." \
  --model core -o sources/research_federated_learning_health.md

# Step 2: Targeted search for specific citations
python scripts/parallel_web.py search \
  "Find recent peer-reviewed papers on federated learning deployed in hospital settings, preferring Nature, The Lancet, arXiv, and PubMed-indexed venues." \
  -o sources/search_federated_learning_papers.md
```

**Python version:**
```python
from parallel_web import ParallelDeepResearch, ParallelSearch

researcher = ParallelDeepResearch()
searcher = ParallelSearch()

# Step 1: Deep background research (fold structure into the query string)
background = researcher.research(
    query="Recent advances in federated learning for healthcare AI (2023-2025): "
          "privacy-preserving methods, real-world deployments, regulatory landscape. "
          "Structure as: (1) key approaches, (2) clinical deployments, "
          "(3) regulatory considerations, (4) open challenges. Include statistics.",
    model="core",
)

# Step 2: Find specific papers to cite (name source preferences in the objective)
papers = searcher.search(
    objective="Find recent peer-reviewed papers on federated learning deployed in hospital "
              "settings; prefer nature.com, thelancet.com, arxiv.org, and PubMed-indexed venues.",
)

# Combine: use background for writing, papers for citations
```

**When to use:** Before writing each major section of a research paper, literature review, or grant proposal.

---

## Recipe 2: Citation Verification

**Goal:** Verify that a citation is real and get complete metadata (DOI, volume, pages, year).

**APIs:** Search + Extract

```bash
# Option A: Search for the paper
python scripts/parallel_web.py search \
  "Find the exact citation details (DOI, venue, year) for 'Attention Is All You Need' by Vaswani et al., 2017 (NeurIPS)." \
  -o sources/search_attention_citation.md

# Option B: Extract metadata from a DOI
python scripts/parallel_web.py extract \
  "https://doi.org/10.48550/arXiv.1706.03762" \
  --objective "Complete citation: authors, title, venue, year, pages, DOI" \
  -o sources/extract_attention_doi.md
```

**Python version:**
```python
from parallel_web import ParallelSearch, ParallelExtract

searcher = ParallelSearch()
extractor = ParallelExtract()

# Step 1: Find the paper
result = searcher.search(
    objective="Find the exact citation details (DOI, venue, year) for the "
              "'Attention Is All You Need' paper by Vaswani et al., 2017.",
)

# Step 2: Extract full metadata from the paper's page (use a citation from the result)
paper_url = result["sources"][0]["url"]
metadata = extractor.extract(
    urls=[paper_url],
    objective="Complete BibTeX citation: all authors, title, conference/journal, year, pages, DOI, volume",
)
```

**When to use:** After writing a section, verify every citation in references.bib has correct and complete metadata.

---

## Recipe 3: Literature Survey

**Goal:** Comprehensive survey of a research field, identifying key papers, themes, and gaps.

**APIs:** Deep Research + Search + Extract

```python
from parallel_web import ParallelDeepResearch, ParallelSearch, ParallelExtract

researcher = ParallelDeepResearch()
searcher = ParallelSearch()
extractor = ParallelExtract()

topic = "CRISPR-based diagnostics for infectious diseases"

# Stage 1: Broad research overview
overview = researcher.research(
    query=f"Comprehensive review of {topic} (2020-2025): key developments, clinical "
          f"applications, regulatory status, commercial products, future directions. "
          f"Structure as a literature review: (1) historical development, (2) current "
          f"technologies, (3) clinical applications, (4) regulatory landscape, "
          f"(5) commercial products, (6) limitations and future directions. "
          f"Include key statistics and milestones.",
    model="core",
)

# Stage 2: Find specific landmark papers (name preferred venues in the objective)
key_papers = searcher.search(
    objective=f"Find the most cited and influential papers on {topic}; prefer "
              f"nature.com, science.org, cell.com, nejm.org, thelancet.com. "
              f"Include SHERLOCK/DETECTR point-of-care work and major reviews.",
    model="core",
)

# Stage 3: Extract detailed content from the top cited sources
top_urls = [s["url"] for s in key_papers["sources"][:5]]
detailed = extractor.extract(
    urls=top_urls,
    objective="Study design, key results, sensitivity/specificity data, and clinical implications",
)
```

**When to use:** Starting a literature review, systematic review, or comprehensive background section.

---

## Recipe 4: Market Intelligence Report

**Goal:** Generate a comprehensive market research report on an industry or product category.

**APIs:** Deep Research (multi-stage)

```python
researcher = ParallelDeepResearch()

industry = "AI-powered drug discovery"

# Stage 1: Market overview (core for maximum depth)
market_overview = researcher.research(
    query=f"Comprehensive market analysis of {industry}: market size, growth rate, "
          f"key segments, geographic distribution, and forecast through 2030. "
          f"Include specific dollar figures, CAGR percentages, and data sources; "
          f"break down by segment and geography.",
    model="core",
)

# Stage 2: Competitive landscape
# For structured JSON output, use the raw Task API (see deep_research_guide.md);
# the research command returns a markdown report.
competitors = researcher.research(
    query=f"Top 10 companies in {industry}: revenue, funding, key products, "
          f"partnerships, and market position. Present as a comparison table.",
    model="core",
)

# Stage 3: Technology and innovation trends
tech_trends = researcher.research(
    query=f"Technology trends and innovation landscape in {industry}: emerging "
          f"approaches, breakthrough technologies, patent landscape, and R&D investment. "
          f"Quantify R&D spending and identify emerging leaders.",
    model="core",
)

# Stage 4: Regulatory and risk analysis
regulatory = researcher.research(
    query=f"Regulatory landscape and risk factors for {industry}: "
          f"FDA guidance, EMA requirements, compliance challenges, and market risks",
    model="core",
)
```

**When to use:** Creating market research reports, investor presentations, or strategic analysis documents.

---

## Recipe 5: Competitive Analysis

**Goal:** Compare multiple companies, products, or technologies side-by-side.

**APIs:** Search + Extract + Research

```python
searcher = ParallelSearch()
extractor = ParallelExtract()
researcher = ParallelDeepResearch()

companies = ["OpenAI", "Anthropic", "Google DeepMind"]

# Step 1: Search for recent data on each company
for company in companies:
    result = searcher.search(
        objective=f"Latest (2025) product launches, funding, team size, and strategy "
                  f"for {company}. Prefer primary announcements from the past year.",
    )

# Step 2: Extract from company pages
company_pages = [
    "https://openai.com/about",
    "https://anthropic.com/company",
    "https://deepmind.google/about/",
]
company_data = extractor.extract(
    urls=company_pages,
    objective="Mission, key products, team size, founding date, and recent milestones",
)

# Step 3: Deep research for synthesis
comparison = researcher.research(
    query=f"Detailed comparison of {', '.join(companies)}: product portfolio, "
          f"technology approach, pricing, market position, strengths/weaknesses, "
          f"and future outlook. Include a summary comparison table.",
    model="core",
)
```

---

## Recipe 6: Fact-Check Pipeline

**Goal:** Verify specific claims or statistics before including in a document.

**APIs:** Search + Extract

```python
searcher = ParallelSearch()
extractor = ParallelExtract()

claim = "The global AI market is expected to reach $1.8 trillion by 2030"

# Step 1: Search for corroborating sources
result = searcher.search(
    objective=f"Verify this claim: '{claim}'. Find authoritative sources that confirm or "
              f"contradict this figure, with the forecast year, CAGR, and methodology.",
)

# Step 2: Extract specific figures from top sources
source_urls = [s["url"] for s in result["sources"][:3]]
details = extractor.extract(
    urls=source_urls,
    objective="Specific market size figures, forecast years, CAGR, and methodology of the projection",
)

# Analyze: Do multiple authoritative sources agree?
```

**When to use:** Before including any specific statistic, market figure, or factual claim in a paper or report.

---

## Recipe 7: Current Events Briefing

**Goal:** Get up-to-date synthesis of recent developments on a topic.

**APIs:** Search + Research

```python
searcher = ParallelSearch()
researcher = ParallelDeepResearch()

topic = "EU AI Act implementation"

# Step 1: Find the latest news
latest = searcher.search(
    objective=f"Latest news and developments on {topic} from the past month (2025), "
              f"covering key updates and official actions.",
)

# Step 2: Synthesize into a briefing
briefing = researcher.research(
    query=f"Summarize the latest developments in {topic} as of 2025: key milestones, "
          f"compliance deadlines, industry reactions, and implications. "
          f"Write a concise ~500-word executive briefing with a timeline of key events.",
    model="core",
)
```

---

## Recipe 8: Technical Documentation Gathering

**Goal:** Collect and synthesize technical documentation for a framework or API.

**APIs:** Search + Extract

```python
searcher = ParallelSearch()
extractor = ParallelExtract()

# Step 1: Find documentation pages
docs = searcher.search(
    objective="Find official PyTorch documentation for implementing custom attention "
              "mechanisms (e.g. MultiheadAttention); prefer pytorch.org.",
)

# Step 2: Extract full content from documentation pages
doc_urls = [s["url"] for s in docs["sources"][:3]]
full_docs = extractor.extract(
    urls=doc_urls,
    objective="Complete API reference, parameters, usage examples, and code snippets",
    full_content=True,
)
```

---

## Recipe 9: Grant Background Research

**Goal:** Build a comprehensive background section for a grant proposal with verified statistics.

**APIs:** Deep Research + Search

```python
researcher = ParallelDeepResearch()
searcher = ParallelSearch()

research_area = "AI-guided antibiotic discovery to combat antimicrobial resistance"

# Step 1: Significance and burden of disease
significance = researcher.research(
    query=f"Burden of antimicrobial resistance: mortality statistics, economic impact, "
          f"WHO priority pathogens, and projections. Provide specific numbers suitable "
          f"for an NIH Significance section: deaths per year, economic cost, resistance "
          f"trends, and urgency.",
    model="core",
)

# Step 2: Innovation landscape
innovation = researcher.research(
    query=f"Current approaches to {research_area}: successes (e.g. halicin), limitations "
          f"of current methods, and emerging novel approaches. Frame for an Innovation "
          f"section: what has been tried, what gaps remain, what is emerging.",
    model="core",
)

# Step 3: Find specific papers for preliminary data context
papers = searcher.search(
    objective="Find landmark papers on AI-discovered antibiotics and ML approaches to "
              "drug discovery (e.g. halicin); prefer nature.com, science.org, cell.com, pnas.org.",
)
```

**When to use:** Writing Significance, Innovation, or Background sections for NIH, NSF, or other grant proposals.

---

## Combining with Other Skills

### With `research-lookup` (Academic Papers)

```python
# Use parallel-web for general research
researcher.research("Current state of quantum computing applications")

# Use research-lookup for academic paper search (auto-routes to Perplexity)
# python research_lookup.py "find papers on quantum error correction in Nature and Science"
```

### With `citation-management` (BibTeX)

```python
# Step 1: Find paper with parallel search
result = searcher.search(objective="Vaswani et al Attention Is All You Need paper")

# Step 2: Get DOI from results
doi = "10.48550/arXiv.1706.03762"

# Step 3: Convert to BibTeX with citation-management skill
# python scripts/doi_to_bibtex.py 10.48550/arXiv.1706.03762
```

### With `scientific-schematics` (Diagrams)

```python
# Step 1: Research a process
result = researcher.research("How does the CRISPR-Cas9 gene editing mechanism work step by step")

# Step 2: Use the research to inform a schematic
# python scripts/generate_schematic.py "CRISPR-Cas9 gene editing workflow: guide RNA design -> Cas9 binding -> DNA cleavage -> repair pathway" -o figures/crispr_mechanism.png
```

---

## Command Cheat Sheet (this skill)

| Task | Command | Expected Time |
|------|---------|---------------|
| Quick fact lookup / web search | `search` (`base`) | ~15-100s |
| Heavier search | `search --model core` | ~1-5min |
| Section background | `research --model base` | ~15-100s |
| Comprehensive report | `research` (`core`, default) | ~1-5min |
| URL / citation verification | `extract` | seconds |

For raw Task API processor latency/cost (`base-fast` … `ultra8x-fast`), see [api_reference.md](api_reference.md).

---

## See Also

- [API Reference](api_reference.md) - Complete API parameter reference
- [Search Best Practices](search_best_practices.md) - Effective search queries
- [Deep Research Guide](deep_research_guide.md) - The `research` command, output formats, raw Task API
- [Extraction Patterns](extraction_patterns.md) - URL content extraction
