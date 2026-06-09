---
name: alterlab-market-research
description: Generates comprehensive market research reports (50+ pages) in the style of top consulting firms (McKinsey, BCG, Gartner), with professional LaTeX formatting, extensive visuals via scientific-schematics and generate-image, data gathering through research-lookup, and multi-framework strategic analysis (Porter Five Forces, PESTLE, SWOT, TAM/SAM/SOM, BCG Matrix). Use when producing a market analysis, competitive landscape, industry report, market-sizing study, or consulting-style strategic deliverable. NOT for a single focused, source-cited research question with no report/frameworks (use alterlab-deep-research) or for pulling raw financial data points from an API (use alterlab-alpha-vantage). Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: No API key of its own; orchestrates other AlterLab skills (research-lookup, generate-image) whose own credentials apply. Requires a LaTeX toolchain for PDF output.
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Market Research Reports

## Overview

Market research reports are comprehensive strategic documents that analyze industries, markets, and competitive landscapes to inform business decisions, investment strategies, and strategic planning. This skill generates **professional-grade reports of 50+ pages** with extensive visual content, modeled after deliverables from top consulting firms like McKinsey, BCG, Bain, Gartner, and Forrester.

**Key Features:**
- **Comprehensive length**: Reports are designed to be 50+ pages with no token constraints
- **Visual-rich content**: 5-6 key diagrams generated at start (more added as needed during writing)
- **Data-driven analysis**: Deep integration with research-lookup for market data
- **Multi-framework approach**: Porter's Five Forces, PESTLE, SWOT, BCG Matrix, TAM/SAM/SOM
- **Professional formatting**: Consulting-firm quality typography, colors, and layout
- **Actionable recommendations**: Strategic focus with implementation roadmaps

**Output Format:** LaTeX with professional styling, compiled to PDF. Uses the `market_research.sty` style package for consistent, professional formatting.

## When to Use This Skill

This skill should be used when:
- Creating comprehensive market analysis for investment decisions
- Developing industry reports for strategic planning
- Analyzing competitive landscapes and market dynamics
- Conducting market sizing exercises (TAM/SAM/SOM)
- Evaluating market entry opportunities
- Preparing due diligence materials for M&A activities
- Creating thought leadership content for industry positioning
- Developing go-to-market strategy documentation
- Analyzing regulatory and policy impacts on markets
- Building business cases for new product launches

## Visual Enhancement

Well-chosen visuals make a market research report far easier to navigate. Add figures where they clarify market structure, scale, competition, or risk — not as a quota. A handful of strong, accurate visuals beats a wall of decorative ones.

### Visual Generation Tools

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

**Diagrams/schematics work well for:**
- Market growth trajectory charts
- TAM/SAM/SOM breakdown diagrams (concentric circles)
- Porter's Five Forces diagrams
- Competitive positioning matrices
- Market segmentation charts
- Value chain diagrams
- Technology roadmaps
- Risk heatmaps
- Strategic prioritization matrices
- Implementation timelines/Gantt charts
- SWOT analysis diagrams
- BCG Growth-Share matrices

**Generated images work well for:**
- Executive summary hero infographics
- Industry/sector conceptual illustrations
- Abstract technology visualizations
- Cover page imagery

For ready-to-use generation prompts mapped to each section, see `references/visual_generation_guide.md`.

---

## Report Structure (50+ Pages)

The standard structure is front matter, eleven core chapters, and back matter. The per-page targets and framework assignments below drive the 50+ page length; the chosen frameworks (Porter, PESTLE, SWOT, TAM/SAM/SOM, BCG) are what distinguish this from a generic write-up.

| # | Section | Pages | Primary frameworks |
|---|---------|-------|--------------------|
| — | Front matter (cover, ToC/LoF/LoT, executive summary) | ~5 | Market snapshot, investment thesis |
| 1 | Market Overview & Definition | 4-5 | Ecosystem / value-chain mapping |
| 2 | Market Size & Growth | 6-8 | **TAM/SAM/SOM**, CAGR |
| 3 | Industry Drivers & Trends | 5-6 | **PESTLE**, driver impact matrix |
| 4 | Competitive Landscape | 6-8 | **Porter's Five Forces**, positioning matrix, strategic groups |
| 5 | Customer Analysis & Segmentation | 4-5 | Segmentation matrix, customer journey |
| 6 | Technology & Innovation Landscape | 4-5 | TRL, hype cycle, roadmap |
| 7 | Regulatory & Policy Environment | 3-4 | Regulatory timeline |
| 8 | Risk Analysis | 3-4 | Risk heatmap, mitigation matrix |
| 9 | Strategic Opportunities & Recommendations | 4-5 | Opportunity / priority matrices, **SWOT** |
| 10 | Implementation Roadmap | 3-4 | Phased Gantt, milestone tracker |
| 11 | Investment Thesis & Financial Projections | 3-4 | Scenario analysis, projections |
| — | Back matter (methodology, data tables, company profiles, bibliography) | ~5 | — |

For the full section-by-section content requirements, required visuals, and data points per chapter, load `references/report_structure_guide.md`. For market-data sourcing in Chapter 2 (and throughout), use the `research-lookup` skill to pull market-research reports (Gartner, Forrester, IDC), industry-association data, government statistics, and company financials — cite each figure.

---

## Workflow

### Phase 1: Research & Data Gathering

**Step 1: Define Scope**
- Clarify market definition
- Set geographic boundaries
- Determine time horizon
- Identify key questions to answer

**Step 2: Conduct Deep Research**

Use the companion `research-lookup` skill extensively to gather market data. Run focused
queries across each dimension of the analysis, for example:

- **Market size and growth**: "What is the current market size and projected growth rate
  for [MARKET] industry? Include TAM, SAM, SOM estimates and CAGR projections"
- **Competitive landscape**: "Who are the top 10 competitors in the [MARKET] market? What
  is their market share and competitive positioning?"
- **Industry trends**: "What are the major trends and growth drivers in the [MARKET]
  industry for 2024-2030?"
- **Regulatory environment**: "What are the key regulations and policy changes affecting
  the [MARKET] industry?"

**Step 3: Data Organization**
- Create `sources/` folder with research notes
- Organize data by section
- Identify data gaps
- Conduct follow-up research as needed

### Phase 2: Analysis & Framework Application

**Step 4: Apply Analysis Frameworks**

For each framework, conduct structured analysis:

- **Market Sizing**: TAM → SAM → SOM with clear assumptions
- **Porter's Five Forces**: Rate each force High/Medium/Low with rationale
- **PESTLE**: Analyze each dimension with trends and impacts
- **SWOT**: Internal strengths/weaknesses, external opportunities/threats
- **Competitive Positioning**: Define axes, plot competitors

**Step 5: Develop Insights**
- Synthesize findings into key insights
- Identify strategic implications
- Develop recommendations
- Prioritize opportunities

### Phase 3: Visuals

**Step 6: Plan and Generate Visuals**

Decide which figures genuinely aid the report, then generate them. Useful candidates and the kind of content each conveys:

- **Market growth trajectory** — bar chart of market size 2020–2034, historical vs. projected bars, with a CAGR annotation.
- **TAM/SAM/SOM breakdown** — concentric circles for Total / Serviceable Addressable / Serviceable Obtainable Market, each labeled.
- **Porter's Five Forces** — center "Competitive Rivalry" box with the four surrounding forces, color-coded by rating.
- **Competitive positioning matrix** — 2x2 with axes such as Market Focus (Niche↔Broad) and Solution Approach (Product↔Platform), competitors plotted as sized circles.
- **Risk heatmap** — Impact vs. Probability grid with risks plotted and color-graded.
- **Executive summary infographic** — a hero image synthesizing the report's headline metrics.

If a diagram or figure would aid comprehension, invoke the **alterlab-scientific-schematics** skill (diagrams/schematics) or the **alterlab-generate-image** skill (images). Figures are optional — add them only where they improve clarity.

### Phase 4: Report Writing

**Step 7: Initialize Project Structure**

Create the standard project structure:

```
writing_outputs/YYYYMMDD_HHMMSS_market_report_[topic]/
├── progress.md
├── drafts/
│   └── v1_market_report.tex
├── references/
│   └── references.bib
├── figures/
│   └── [all generated visuals]
├── sources/
│   └── [research notes]
└── final/
```

**Step 8: Write Report Using Template**

Use the `market_report_template.tex` as a starting point. Write each section following the structure guide, ensuring:

- **Comprehensive coverage**: Every subsection addressed
- **Data-driven content**: Claims supported by research
- **Visual integration**: Reference all generated figures
- **Professional tone**: Consulting-style writing
- **No token constraints**: Write fully, don't abbreviate

**Writing Guidelines:**
- Use active voice where possible
- Lead with insights, support with data
- Use numbered lists for recommendations
- Include data sources for all statistics
- Create smooth transitions between sections

### Phase 5: Compilation & Review

**Step 9: Compile LaTeX**

```bash
cd writing_outputs/[project_folder]/drafts/
xelatex v1_market_report.tex
bibtex v1_market_report
xelatex v1_market_report.tex
xelatex v1_market_report.tex
```

**Step 10: Quality Review**

Run the full **Checklist: 50+ Page Validation** (below) covering structure, visuals, content quality, and technical correctness before declaring the report done.

**Step 11: Peer Review**

Use the peer-review skill to evaluate the report:
- Assess comprehensiveness
- Verify data accuracy
- Check logical flow
- Evaluate recommendation quality

---

## Quality Standards

Summing the per-section page targets in the Report Structure table yields ~43 pages minimum and ~66 at target — comfortably clearing the 50+ page bar. If a draft falls short, expand appendix data tables, company profiles, and regional breakdowns rather than padding prose.

### Visual Quality Requirements

- **Resolution**: All images at 300 DPI minimum
- **Format**: PNG for raster, PDF for vector
- **Accessibility**: Colorblind-friendly palettes
- **Consistency**: Same color scheme throughout
- **Labeling**: All axes, legends, and data points labeled
- **Source Attribution**: Sources cited in figure captions

### Data Quality Requirements

- **Currency**: Data no older than 2 years (prefer current year)
- **Sourcing**: All statistics attributed to specific sources
- **Validation**: Cross-reference multiple sources when possible
- **Assumptions**: All projections state underlying assumptions
- **Limitations**: Acknowledge data limitations and gaps

### Writing Quality Requirements

- **Objectivity**: Present balanced analysis, acknowledge uncertainties
- **Clarity**: Avoid jargon, define technical terms
- **Precision**: Use specific numbers over vague qualifiers
- **Structure**: Clear headings, logical flow, smooth transitions
- **Actionability**: Recommendations are specific and implementable

---

## LaTeX Formatting

### Using the Style Package

The `market_research.sty` package provides professional formatting. Include it in your document:

```latex
\documentclass[11pt,letterpaper]{report}
\usepackage{market_research}
```

### Box Environments

Use colored boxes to highlight key content:

```latex
% Key insight box (blue)
\begin{keyinsightbox}[Key Finding]
The market is projected to grow at 15.3% CAGR through 2030.
\end{keyinsightbox}

% Market data box (green)
\begin{marketdatabox}[Market Snapshot]
\begin{itemize}
    \item Market Size (2024): \$45.2B
    \item Projected Size (2030): \$98.7B
    \item CAGR: 15.3%
\end{itemize}
\end{marketdatabox}

% Risk box (orange/warning)
\begin{riskbox}[Critical Risk]
Regulatory changes could impact 40% of market participants.
\end{riskbox}

% Recommendation box (purple)
\begin{recommendationbox}[Strategic Recommendation]
Prioritize market entry in the Asia-Pacific region.
\end{recommendationbox}

% Callout box (gray)
\begin{calloutbox}[Definition]
TAM (Total Addressable Market) represents the total revenue opportunity.
\end{calloutbox}
```

### Figure Formatting

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{../figures/market_growth.png}
\caption{Market Growth Trajectory (2020-2030). Source: Industry analysis, company data.}
\label{fig:market_growth}
\end{figure}
```

### Table Formatting

```latex
\begin{table}[htbp]
\centering
\caption{Market Size by Region (2024)}
\begin{tabular}{@{}lrrr@{}}
\toprule
\textbf{Region} & \textbf{Size (USD)} & \textbf{Share} & \textbf{CAGR} \\
\midrule
North America & \$18.2B & 40.3\% & 12.5\% \\
\rowcolor{tablealt} Europe & \$12.1B & 26.8\% & 14.2\% \\
Asia-Pacific & \$10.5B & 23.2\% & 18.7\% \\
\rowcolor{tablealt} Rest of World & \$4.4B & 9.7\% & 11.3\% \\
\midrule
\textbf{Total} & \textbf{\$45.2B} & \textbf{100\%} & \textbf{15.3\%} \\
\bottomrule
\end{tabular}
\label{tab:market_by_region}
\end{table}
```

For complete formatting reference, see `assets/FORMATTING_GUIDE.md`.

---

## Integration with Other Skills

This skill orchestrates several sibling skills:

- **alterlab-research-lookup**: gather market data, statistics, and competitive intelligence
- **alterlab-scientific-schematics**: generate diagrams, charts, matrices, and timelines
- **alterlab-generate-image**: create infographics and conceptual illustrations
- **alterlab-peer-review**: evaluate report quality and completeness
- **alterlab-citation-mgmt**: manage the BibTeX bibliography

Route elsewhere when the ask is narrower: a single source-cited research question → **alterlab-deep-research**; raw financial fundamentals from an API → **alterlab-alpha-vantage**.

---

## Example Prompts

### Market Overview Section

```
Write a comprehensive market overview section for the [Electric Vehicle Charging Infrastructure] market. Include:
- Clear market definition and scope
- Industry ecosystem with key stakeholders
- Value chain analysis
- Historical evolution of the market
- Current market dynamics

Generate 2 supporting visuals using scientific-schematics.
```

### Competitive Landscape Section

```
Analyze the competitive landscape for the [Cloud Computing] market. Include:
- Porter's Five Forces analysis with High/Medium/Low ratings
- Top 10 competitors with market share
- Competitive positioning matrix
- Strategic group mapping
- Barriers to entry analysis

Generate 4 supporting visuals including Porter's Five Forces diagram and positioning matrix.
```

### Strategic Recommendations Section

```
Develop strategic recommendations for entering the [Renewable Energy Storage] market. Include:
- 5-7 prioritized recommendations
- Opportunity sizing for each
- Implementation considerations
- Risk factors and mitigations
- Success criteria

Generate 3 supporting visuals including opportunity matrix and priority framework.
```

---

## Checklist: 50+ Page Validation

Before finalizing the report, verify:

### Structure Completeness
- [ ] Cover page with hero visual
- [ ] Table of contents (auto-generated)
- [ ] List of figures (auto-generated)
- [ ] List of tables (auto-generated)
- [ ] Executive summary (2-3 pages)
- [ ] All 11 core chapters present
- [ ] Appendix A: Methodology
- [ ] Appendix B: Data tables
- [ ] Appendix C: Company profiles
- [ ] References/Bibliography

### Visual Completeness (Core 5-6)
- [ ] Market growth trajectory chart (Priority 1)
- [ ] TAM/SAM/SOM diagram (Priority 2)
- [ ] Porter's Five Forces (Priority 3)
- [ ] Competitive positioning matrix (Priority 4)
- [ ] Risk heatmap (Priority 5)
- [ ] Executive summary infographic (Priority 6, optional)

### Additional Visuals (Generate as Needed)
- [ ] Market ecosystem diagram
- [ ] Regional breakdown chart
- [ ] Segment growth chart
- [ ] Industry trends/PESTLE diagram
- [ ] Market share chart
- [ ] Customer segmentation chart
- [ ] Technology roadmap
- [ ] Regulatory timeline
- [ ] Opportunity matrix
- [ ] Implementation timeline
- [ ] Financial projections chart
- [ ] Other section-specific visuals

### Content Quality
- [ ] All statistics have sources
- [ ] Projections include assumptions
- [ ] Frameworks properly applied
- [ ] Recommendations are actionable
- [ ] Writing is professional quality
- [ ] No placeholder or incomplete sections

### Technical Quality
- [ ] PDF compiles without errors
- [ ] All figures render correctly
- [ ] Cross-references work
- [ ] Bibliography complete
- [ ] Page count exceeds 50

---

## Resources

### Reference Files

Load these files for detailed guidance:

- **`references/report_structure_guide.md`**: Detailed section-by-section content requirements
- **`references/visual_generation_guide.md`**: Complete prompts for generating all visual types
- **`references/data_analysis_patterns.md`**: Templates for Porter's, PESTLE, SWOT, etc.

### Assets

- **`assets/market_research.sty`**: LaTeX style package
- **`assets/market_report_template.tex`**: Complete LaTeX template
- **`assets/FORMATTING_GUIDE.md`**: Quick reference for box environments and styling

---

## Troubleshooting

### Common Issues

**Problem**: Report is under 50 pages
- **Solution**: Expand data tables in appendices, add more detailed company profiles, include additional regional breakdowns

**Problem**: Visuals not rendering
- **Solution**: Check file paths in LaTeX, ensure images are in figures/ folder, verify file extensions

**Problem**: Bibliography missing entries
- **Solution**: Run bibtex after first xelatex pass, check .bib file for syntax errors

**Problem**: Table/figure overflow
- **Solution**: Use `\resizebox` or `adjustbox` package, reduce image width percentage

**Problem**: Poor visual quality from generation
- **Solution**: Pass `--doc-type report` for the report quality threshold, and `--iterations 2` (the scientific-schematics max) for an extra refinement pass

---

Use this skill to create comprehensive, visually-rich market research reports that rival top consulting firm deliverables. The combination of deep research, structured frameworks, and extensive visualization produces documents that inform strategic decisions and demonstrate analytical rigor.

