---
name: alterlab-literature-review
description: Conducts comprehensive, systematic literature reviews across multiple academic databases (PubMed, arXiv, bioRxiv, Semantic Scholar), with PRISMA 2020 flow tracking, study screening (title/abstract and full-text), evidence-table extraction, and risk-of-bias assessment (RoB 2, ROBINS-I, AMSTAR 2), producing professionally formatted markdown documents and PDFs with verified citations in multiple styles (APA, Nature, Vancouver). Use when running a systematic or scoping literature review, research synthesis, or broad literature search, building a PRISMA flow diagram, screening studies, extracting an evidence table, or assessing risk of bias across biomedical, scientific, and technical domains. For quantitative pooling of effect sizes (forest/funnel plots) use alterlab-meta-analysis; for an open-ended multi-agent investigation, fact-check, or Socratic research-question work use alterlab-deep-research. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: Needs network access to PubMed, arXiv, bioRxiv, and Semantic Scholar (searches follow the Entrez/Biopython and REST snippets in the references); verify_citations.py needs requests; PDF output requires pandoc and xelatex (check with --check-deps)
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Literature Review

## Overview

Conduct systematic, comprehensive literature reviews following rigorous academic methodology. Search multiple literature databases, synthesize findings thematically, verify all citations for accuracy, and generate professional output documents in markdown and PDF formats.

This skill integrates with sibling skills for database access (`alterlab-pubmed`, `alterlab-biorxiv`, `alterlab-arxiv`, `alterlab-openalex`, `alterlab-gget`, `alterlab-bioservices`, `alterlab-datacommons`) and provides its own scripts for citation verification, result aggregation, and document generation.

## When to Use This Skill

Use this skill when:
- Conducting a systematic literature review for research or publication
- Synthesizing current knowledge on a specific topic across multiple sources
- Performing meta-analysis or scoping reviews
- Writing the literature review section of a research paper or thesis
- Investigating the state of the art in a research domain
- Identifying research gaps and future directions
- Requiring verified citations and professional formatting

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Open-ended multi-agent investigation, a quick research brief, fact-checking claims, or Socratic help formulating the research question | `alterlab-deep-research` |
| Pooling effect sizes quantitatively (random-effects model, heterogeneity, forest/funnel plots, publication bias) | `alterlab-meta-analysis` |
| Writing the literature-review chapter of a thesis or dissertation with a supervisor-style workflow | `alterlab-thesis-supervisor` |
| Mapping the citation/co-citation network around seed papers | `alterlab-citation-graph` |
| Auditing whether every entry in a bibliography actually exists (hallucinated/retracted references) | `alterlab-citation-verifier` |

## Core Workflow

Literature reviews follow a structured, multi-phase workflow:

### Phase 1: Planning and Scoping

1. **Define Research Question**: Use PICO framework (Population, Intervention, Comparison, Outcome) for clinical/biomedical reviews
   - Example: "What is the efficacy of CRISPR-Cas9 (I) for treating sickle cell disease (P) compared to standard care (C)?"

2. **Establish Scope and Objectives**:
   - Define clear, specific research questions
   - Determine review type (narrative, systematic, scoping, meta-analysis)
   - Set boundaries (time period, geographic scope, study types)
   - For a systematic review, write a protocol (PRISMA-P) and register it before screening — PROSPERO for health-related reviews, OSF Registries otherwise — so the eligibility criteria and outcomes are fixed in advance

3. **Develop Search Strategy**:
   - Identify 2-4 main concepts from research question
   - List synonyms, abbreviations, and related terms for each concept
   - Plan Boolean operators (AND, OR, NOT) to combine terms
   - Select minimum 3 complementary databases

4. **Set Inclusion/Exclusion Criteria**:
   - Date range (e.g., last 10 years: 2015-2024)
   - Language (typically English, or specify multilingual)
   - Publication types (peer-reviewed, preprints, reviews)
   - Study designs (RCTs, observational, in vitro, etc.)
   - Document all criteria clearly

### Phase 2: Systematic Literature Search

1. **Multi-Database Search**:

   Select databases appropriate for the domain:

   **Biomedical & Life Sciences:**
   - Search PubMed/PMC via NCBI E-utilities (Entrez esearch/efetch) — see the Entrez/Biopython snippet in `references/database_search_guidance.md` (`scripts/search_databases.py` does not query databases; it aggregates, deduplicates, ranks, and formats exported results)
   - Search bioRxiv/medRxiv via the bioRxiv API (api.biorxiv.org) or Europe PMC
   - Use the `alterlab-bioservices` skill for ChEMBL, KEGG, UniProt, etc.

   **General Scientific Literature:**
   - Search arXiv via direct API (preprints in physics, math, CS, q-bio)
   - Search Semantic Scholar via API (200M+ papers, cross-disciplinary)
   - Use Google Scholar for comprehensive coverage (manual or careful scraping)

   **Specialized Databases:**
   - Use `alterlab-gget` (`gget alphafold`, `gget cosmic`) for protein structures and cancer genomics
   - Use `alterlab-datacommons` for demographic/statistical data
   - Use specialized databases as appropriate for the domain

2. **Document Search Parameters**:
   ```markdown
   ## Search Strategy

   ### Database: PubMed
   - **Date searched**: 2024-10-25
   - **Date range**: 2015-01-01 to 2024-10-25
   - **Search string**:
     ```
     ("CRISPR"[Title] OR "Cas9"[Title])
     AND ("sickle cell"[MeSH] OR "SCD"[Title/Abstract])
     AND 2015:2024[Publication Date]
     ```
   - **Results**: 247 articles
   ```

   Repeat for each database searched.

3. **Export and Aggregate Results**:
   - Export results in JSON format from each database
   - Combine all results into a single file
   - Use `scripts/search_databases.py` for post-processing:
     ```bash
     python scripts/search_databases.py combined_results.json \
       --deduplicate \
       --format markdown \
       --output aggregated_results.md
     ```

### Phase 3: Screening and Selection

1. **Deduplication**:
   ```bash
   python scripts/search_databases.py results.json --deduplicate --format json --output unique_results.json
   ```
   - Removes duplicates by DOI (primary) or title (fallback)
   - Document number of duplicates removed

2. **Title Screening**:
   - Review all titles against inclusion/exclusion criteria
   - Exclude obviously irrelevant studies
   - Document number excluded at this stage

3. **Abstract Screening**:
   - Read abstracts of remaining studies
   - Apply inclusion/exclusion criteria rigorously
   - Document reasons for exclusion

4. **Full-Text Screening**:
   - Obtain full texts of remaining studies
   - Conduct detailed review against all criteria
   - Document specific reasons for exclusion
   - Record final number of included studies

5. **Create PRISMA 2020 Flow Diagram** (Page et al., *BMJ* 2021;372:n71 — report counts at every stage and the reasons for full-text exclusions):
   ```
   Identification: records from databases (n per source) + registers
     └─ removed before screening: duplicates (n), other (n)
   Screening: records screened (n) → excluded (n)
     └─ reports sought for retrieval (n) → not retrieved (n)
     └─ reports assessed for eligibility (n) → excluded, with reasons (n per reason)
   Included: studies (n) and reports (n) in the review
   ```
   Report the full search strings per database following PRISMA-S; for scoping reviews use PRISMA-ScR.

### Phase 4: Data Extraction and Quality Assessment

1. **Extract Key Data** from each included study:
   - Study metadata (authors, year, journal, DOI)
   - Study design and methods
   - Sample size and population characteristics
   - Key findings and results
   - Limitations noted by authors
   - Funding sources and conflicts of interest

2. **Assess Risk of Bias** (per study, with the tool that matches its design):
   - **RCTs**: Cochrane RoB 2 — judgments per domain and overall: low risk / some concerns / high risk
   - **Non-randomized studies of interventions**: ROBINS-I (V2 at riskofbias.info) — low / moderate / serious / critical
   - **Other observational studies**: Newcastle-Ottawa Scale
   - **Diagnostic accuracy studies**: QUADAS-2
   - **Systematic reviews (umbrella reviews)**: AMSTAR 2
   - Then rate the **certainty of the body of evidence per outcome** with GRADE (high / moderate / low / very low) — GRADE grades outcomes across studies, not individual studies
   - Prefer sensitivity analyses over silently excluding high-risk studies, and report which studies were affected

3. **Organize by Themes**:
   - Identify 3-5 major themes across studies
   - Group studies by theme (studies may appear in multiple themes)
   - Note patterns, consensus, and controversies

### Phase 5: Synthesis and Analysis

1. **Create Review Document** from template:
   ```bash
   cp assets/review_template.md my_literature_review.md
   ```

2. **Write Thematic Synthesis** (NOT study-by-study summaries):
   - Organize Results section by themes or research questions
   - Synthesize findings across multiple studies within each theme
   - Compare and contrast different approaches and results
   - Identify consensus areas and points of controversy
   - Highlight the strongest evidence

   Example structure:
   ```markdown
   #### 3.3.1 Theme: CRISPR Delivery Methods

   Multiple delivery approaches have been investigated for therapeutic
   gene editing. Viral vectors (AAV) were used in 15 studies^1-15^ and
   showed high transduction efficiency (65-85%) but raised immunogenicity
   concerns^3,7,12^. In contrast, lipid nanoparticles demonstrated lower
   efficiency (40-60%) but improved safety profiles^16-23^.
   ```

3. **Critical Analysis**:
   - Evaluate methodological strengths and limitations across studies
   - Assess quality and consistency of evidence
   - Identify knowledge gaps and methodological gaps
   - Note areas requiring future research

4. **Write Discussion**:
   - Interpret findings in broader context
   - Discuss clinical, practical, or research implications
   - Acknowledge limitations of the review itself
   - Compare with previous reviews if applicable
   - Propose specific future research directions

### Phase 6: Citation Verification

Verify every citation before the review leaves your hands — a single wrong DOI or misattributed finding undermines the credibility of the whole synthesis.

1. **Verify All DOIs**:
   ```bash
   python scripts/verify_citations.py my_literature_review.md
   ```

   This script:
   - Extracts all DOIs from the document
   - Verifies each DOI resolves correctly
   - Retrieves metadata from CrossRef
   - Generates verification report
   - Outputs properly formatted citations

   It checks DOIs only; for references without DOIs, or to screen a whole bibliography for fabricated or retracted entries, run `alterlab-citation-verifier`.

2. **Review Verification Report**:
   - Check for any failed DOIs
   - Verify author names, titles, and publication details match
   - Correct any errors in the original document
   - Re-run verification until all citations pass

3. **Format Citations Consistently**:
   - Choose one citation style and use throughout (see `references/citation_styles.md`)
   - Common styles: APA, Nature, Vancouver, Chicago, IEEE
   - Use verification script output to format citations correctly
   - Ensure in-text citations match reference list format

### Phase 7: Document Generation

1. **Generate PDF**:
   ```bash
   python scripts/generate_pdf.py my_literature_review.md \
     --citation-style apa \
     --output my_review.pdf
   ```

   Options:
   - `--output` / `-o`: output PDF path (default: the markdown filename with `.pdf`)
   - `--citation-style`: a CSL style name such as apa, nature, ieee, chicago-author-date. It is applied only when a `.bib` with the same basename sits next to the markdown file, and pandoc must find `<style>.csl` (download it from the CSL styles repository at github.com/citation-style-language/styles into the working directory)
   - `--no-toc`: Disable table of contents
   - `--no-numbers`: Disable section numbering
   - `--check-deps`: Check if pandoc/xelatex are installed

2. **Review Final Output**:
   - Check PDF formatting and layout
   - Verify all sections are present
   - Ensure citations render correctly
   - Check that figures/tables appear properly
   - Verify table of contents is accurate

3. **Quality Checklist**:
   - [ ] All DOIs verified with verify_citations.py
   - [ ] Citations formatted consistently
   - [ ] PRISMA flow diagram included (for systematic reviews)
   - [ ] Search methodology fully documented
   - [ ] Inclusion/exclusion criteria clearly stated
   - [ ] Results organized thematically (not study-by-study)
   - [ ] Quality assessment completed
   - [ ] Limitations acknowledged
   - [ ] References complete and accurate
   - [ ] PDF generates without errors

## Database-Specific Search Guidance

Access patterns and search tips for each source — PubMed/PMC via **NCBI E-utilities (Entrez)** (with the Biopython snippet), bioRxiv/medRxiv via the **bioRxiv API / Europe PMC**, arXiv, Semantic Scholar, specialized biomedical databases, and forward/backward citation chaining — are in `references/database_search_guidance.md`. Broader cross-database strategy is in `references/database_strategies.md`.

## Citation Style and Source Quality

- **Citation style quick reference** (APA, Nature, Vancouver) and the rule to **prioritize high-impact papers** (citation-count thresholds, venue tiers, author reputation, identifying seminal work) → `references/source_quality_prioritization.md`.
- **Full formatting rules** (APA, Nature, Vancouver, Chicago, IEEE) → `references/citation_styles.md`.

**Always verify citations** with `scripts/verify_citations.py` before finalizing.

## Best Practices and Pitfalls

Best practices for search strategy, screening/selection, synthesis, reproducibility, and writing — plus the 10 common pitfalls to avoid — are in `references/example_workflow_and_practices.md`. Core rules: search ≥3 databases, document every search, organize thematically (not study-by-study), and verify all citations.

## Example Workflow, Integration, and Dependencies

- A complete end-to-end biomedical-review command sequence (template → search → aggregate → screen → write → verify → PDF) is in `references/example_workflow_and_practices.md`.
- That file also covers integration with database/analysis/visualization/writing skills and the Python-package + system-tool dependencies (pandoc, xelatex).

## Routing Guidance

- **Run the full review** → follow Core Workflow Phases 1-7 in order.
- **Pick/query a database** → `references/database_search_guidance.md` (+ `references/database_strategies.md`).
- **Format or prioritize citations** → `references/source_quality_prioritization.md` and `references/citation_styles.md`.
- **Best practices, the worked example, integrations, dependencies** → `references/example_workflow_and_practices.md`.

## References Index

**Scripts:**
- `scripts/verify_citations.py` — verify DOIs and generate formatted citations.
- `scripts/generate_pdf.py` — convert markdown to a professional PDF.
- `scripts/search_databases.py` — process, deduplicate, rank, and format search results.

**References:**
- `references/database_search_guidance.md` — per-database access patterns (Entrez/PubMed, bioRxiv API, arXiv, Semantic Scholar), search tips, citation chaining.
- `references/database_strategies.md` — comprehensive cross-database search strategies.
- `references/source_quality_prioritization.md` — citation-style quick reference plus high-impact prioritization (thresholds, venue tiers, seminal-paper identification).
- `references/citation_styles.md` — detailed citation formatting (APA, Nature, Vancouver, Chicago, IEEE).
- `references/example_workflow_and_practices.md` — end-to-end worked example, best practices, common pitfalls, skill integration, dependencies, external resources.

**Assets:**
- `assets/review_template.md` — complete literature review template with all sections.

## Summary

This literature-review skill provides:

1. **Systematic methodology** following academic best practices
2. **Multi-database integration** via existing scientific skills
3. **Citation verification** ensuring accuracy and credibility
4. **Professional output** in markdown and PDF formats
5. **Comprehensive guidance** covering the entire review process
6. **Quality assurance** with verification and validation tools
7. **Reproducibility** through detailed documentation requirements

Conduct thorough, rigorous literature reviews that meet academic standards and provide comprehensive synthesis of current knowledge in any domain.

Part of the AlterLab Academic Skills suite.

