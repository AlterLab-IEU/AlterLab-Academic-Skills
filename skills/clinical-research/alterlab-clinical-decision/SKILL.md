---
name: alterlab-clinical-decision
description: Generates professional clinical decision support (CDS) documents for pharmaceutical and clinical research settings — biomarker-stratified patient cohort analyses with outcomes and evidence-based treatment recommendation reports with decision algorithms, supporting GRADE evidence grading, statistical analysis (hazard ratios, survival curves, waterfall plots), biomarker integration, and regulatory compliance, output as publication-ready LaTeX/PDF. Use when building a CDS document, cohort analysis, or treatment recommendation report for drug development, clinical research, or evidence synthesis, or when GRADE grading, hazard ratios, survival/waterfall plots, or biomarker stratification are requested. Part of the AlterLab Academic Skills suite.
allowed-tools: Read Write Edit Bash
license: MIT
compatibility: "Runs with Read/Write/Edit/Bash; producing PDF output requires a local LaTeX toolchain (e.g. pdflatex/xelatex). No API key required."
metadata:
    skill-author: AlterLab
    version: "1.0.0"
---

# Clinical Decision Support Documents

## Description

Generate professional clinical decision support (CDS) documents for pharmaceutical companies, clinical researchers, and medical decision-makers. This skill specializes in analytical, evidence-based documents that inform treatment strategies and drug development:

1. **Patient Cohort Analysis** - Biomarker-stratified group analyses with statistical outcome comparisons
2. **Treatment Recommendation Reports** - Evidence-based clinical guidelines with GRADE grading and decision algorithms

All documents are generated as publication-ready LaTeX/PDF files optimized for pharmaceutical research, regulatory submissions, and clinical guideline development.

**Note:** For individual patient treatment plans at the bedside, use the `alterlab-treatment-plans` skill instead. For single-patient case reports for journal submission (e.g. CARE-guideline cases), use `alterlab-clinical-reports`. This skill focuses on group-level analyses and evidence synthesis for pharmaceutical/research settings.

**Writing Style:** For publication-ready documents targeting medical journals, consult the `alterlab-venue-templates` skill's `medical_journal_styles.md` for guidance on structured abstracts, evidence language, and CONSORT/STROBE compliance.

## Capabilities

### Document Types

**Patient Cohort Analysis**
- Biomarker-based patient stratification (molecular subtypes, gene expression, IHC)
- Molecular subtype classification (e.g., GBM mesenchymal-immune-active vs proneural, breast cancer subtypes)
- Outcome metrics with statistical analysis (OS, PFS, ORR, DOR, DCR)
- Statistical comparisons between subgroups (hazard ratios, p-values, 95% CI)
- Survival analysis with Kaplan-Meier curves and log-rank tests
- Efficacy tables and waterfall plots
- Comparative effectiveness analyses
- Pharmaceutical cohort reporting (trial subgroups, real-world evidence)

**Treatment Recommendation Reports**
- Evidence-based treatment guidelines for specific disease states
- Strength of recommendation grading (GRADE system: 1A, 1B, 2A, 2B, 2C)
- Quality of evidence assessment (high, moderate, low, very low)
- Treatment algorithm flowcharts with TikZ diagrams
- Line-of-therapy sequencing based on biomarkers
- Decision pathways with clinical and molecular criteria
- Pharmaceutical strategy documents
- Clinical guideline development for medical societies

### Clinical Features

- **Biomarker Integration**: Genomic alterations (mutations, CNV, fusions), gene expression signatures, IHC markers, PD-L1 scoring
- **Statistical Analysis**: Hazard ratios, p-values, confidence intervals, survival curves, Cox regression, log-rank tests
- **Evidence Grading**: GRADE system (1A/1B/2A/2B/2C), Oxford CEBM levels, quality of evidence assessment
- **Clinical Terminology**: SNOMED-CT, LOINC, proper medical nomenclature, trial nomenclature
- **Regulatory Compliance**: HIPAA de-identification, confidentiality headers, ICH-GCP alignment
- **Professional Formatting**: Compact 0.5in margins, color-coded recommendations, publication-ready, suitable for regulatory submissions

## Pharmaceutical and Research Use Cases

This skill is specifically designed for pharmaceutical and clinical research applications:

**Drug Development**
- **Phase 2/3 Trial Analyses**: Biomarker-stratified efficacy and safety analyses
- **Subgroup Analyses**: Forest plots showing treatment effects across patient subgroups
- **Companion Diagnostic Development**: Linking biomarkers to drug response
- **Regulatory Submissions**: IND/NDA documentation with evidence summaries

**Medical Affairs**
- **KOL Education Materials**: Evidence-based treatment algorithms for thought leaders
- **Medical Strategy Documents**: Competitive landscape and positioning strategies
- **Advisory Board Materials**: Cohort analyses and treatment recommendation frameworks
- **Publication Planning**: Manuscript-ready analyses for peer-reviewed journals

**Clinical Guidelines**
- **Guideline Development**: Evidence synthesis with GRADE methodology for specialty societies
- **Consensus Recommendations**: Multi-stakeholder treatment algorithm development
- **Practice Standards**: Biomarker-based treatment selection criteria
- **Quality Measures**: Evidence-based performance metrics

**Real-World Evidence**
- **RWE Cohort Studies**: Retrospective analyses of patient cohorts from EMR data
- **Comparative Effectiveness**: Head-to-head treatment comparisons in real-world settings
- **Outcomes Research**: Long-term survival and safety in clinical practice
- **Health Economics**: Cost-effectiveness analyses by biomarker subgroup

## When to Use

Use this skill when you need to:

- **Analyze patient cohorts** stratified by biomarkers, molecular subtypes, or clinical characteristics
- **Generate treatment recommendation reports** with evidence grading for clinical guidelines or pharmaceutical strategies
- **Compare outcomes** between patient subgroups with statistical analysis (survival, response rates, hazard ratios)
- **Produce pharmaceutical research documents** for drug development, clinical trials, or regulatory submissions
- **Develop clinical practice guidelines** with GRADE evidence grading and decision algorithms
- **Document biomarker-guided therapy selection** at the population level (not individual patients)
- **Synthesize evidence** from multiple trials or real-world data sources
- **Create clinical decision algorithms** with flowcharts for treatment sequencing

**Do NOT use this skill for:**
- Individual patient treatment plans, bedside care documentation, or patient-specific protocols (use `alterlab-treatment-plans`)
- Single-patient case reports for journal submission, e.g. CARE-guideline cases (use `alterlab-clinical-reports`)

## Document Structure

**CRITICAL REQUIREMENT: All clinical decision support documents MUST begin with a complete executive summary on page 1 that spans the entire first page before any table of contents or detailed sections.**

### Page 1 Executive Summary Structure

The first page of every CDS document should contain ONLY the executive summary with the following components:

**Required Elements (all on page 1):**
1. **Document Title and Type**
   - Main title (e.g., "Biomarker-Stratified Cohort Analysis" or "Evidence-Based Treatment Recommendations")
   - Subtitle with disease state and focus
   
2. **Report Information Box** (using colored tcolorbox)
   - Document type and purpose
   - Date of analysis/report
   - Disease state and patient population
   - Author/institution (if applicable)
   - Analysis framework or methodology
   
3. **Key Findings Boxes** (3-5 colored boxes using tcolorbox)
   - **Primary Results** (blue box): Main efficacy/outcome findings
   - **Biomarker Insights** (green box): Key molecular subtype findings
   - **Clinical Implications** (yellow/orange box): Actionable treatment implications
   - **Statistical Summary** (gray box): Hazard ratios, p-values, key statistics
   - **Safety Highlights** (red box, if applicable): Critical adverse events or warnings

**Visual Requirements:**
- Use `\thispagestyle{empty}` to remove page numbers from page 1
- All content must fit on page 1 (before `\newpage`)
- Use colored tcolorbox environments with different colors for visual hierarchy
- Boxes should be scannable and highlight most critical information
- Use bullet points, not narrative paragraphs
- End page 1 with `\newpage` before table of contents or detailed sections

**Example First Page LaTeX Structure:**
```latex
\maketitle
\thispagestyle{empty}

% Report Information Box
\begin{tcolorbox}[colback=blue!5!white, colframe=blue!75!black, title=Report Information]
\textbf{Document Type:} Patient Cohort Analysis\\
\textbf{Disease State:} HER2-Positive Metastatic Breast Cancer\\
\textbf{Analysis Date:} \today\\
\textbf{Population:} 60 patients, biomarker-stratified by HR status
\end{tcolorbox}

\vspace{0.3cm}

% Key Finding #1: Primary Results
\begin{tcolorbox}[colback=blue!5!white, colframe=blue!75!black, title=Primary Efficacy Results]
\begin{itemize}
    \item Overall ORR: 72\% (95\% CI: 59-83\%)
    \item Median PFS: 18.5 months (95\% CI: 14.2-22.8)
    \item Median OS: 35.2 months (95\% CI: 28.1-NR)
\end{itemize}
\end{tcolorbox}

\vspace{0.3cm}

% Key Finding #2: Biomarker Insights
\begin{tcolorbox}[colback=green!5!white, colframe=green!75!black, title=Biomarker Stratification Findings]
\begin{itemize}
    \item HR+/HER2+: ORR 68\%, median PFS 16.2 months
    \item HR-/HER2+: ORR 78\%, median PFS 22.1 months
    \item HR status significantly associated with outcomes (p=0.041)
\end{itemize}
\end{tcolorbox}

\vspace{0.3cm}

% Key Finding #3: Clinical Implications
\begin{tcolorbox}[colback=orange!5!white, colframe=orange!75!black, title=Clinical Recommendations]
\begin{itemize}
    \item Strong efficacy observed regardless of HR status (Grade 1A)
    \item HR-/HER2+ patients showed numerically superior outcomes
    \item Treatment recommended for all HER2+ MBC patients
\end{itemize}
\end{tcolorbox}

\newpage
\tableofcontents  % TOC on page 2
\newpage  % Detailed content starts page 3
```

### Patient Cohort Analysis (Detailed Sections - Page 3+)
- **Cohort Characteristics**: Demographics, baseline features, patient selection criteria
- **Biomarker Stratification**: Molecular subtypes, genomic alterations, IHC profiles
- **Treatment Exposure**: Therapies received, dosing, treatment duration by subgroup
- **Outcome Analysis**: Response rates (ORR, DCR), survival data (OS, PFS), DOR
- **Statistical Methods**: Kaplan-Meier survival curves, hazard ratios, log-rank tests, Cox regression
- **Subgroup Comparisons**: Biomarker-stratified efficacy, forest plots, statistical significance
- **Safety Profile**: Adverse events by subgroup, dose modifications, discontinuations
- **Clinical Recommendations**: Treatment implications based on biomarker profiles
- **Figures**: Waterfall plots, swimmer plots, survival curves, forest plots
- **Tables**: Demographics table, biomarker frequency, outcomes by subgroup

### Treatment Recommendation Reports (Detailed Sections - Page 3+)

**Page 1 Executive Summary for Treatment Recommendations should include:**
1. **Report Information Box**: Disease state, guideline version/date, target population
2. **Key Recommendations Box** (green): Top 3-5 GRADE-graded recommendations by line of therapy
3. **Biomarker Decision Criteria Box** (blue): Key molecular markers influencing treatment selection
4. **Evidence Summary Box** (gray): Major trials supporting recommendations (e.g., KEYNOTE-189, FLAURA)
5. **Critical Monitoring Box** (orange/red): Essential safety monitoring requirements

**Detailed Sections (Page 3+):**
- **Clinical Context**: Disease state, epidemiology, current treatment landscape
- **Target Population**: Patient characteristics, biomarker criteria, staging
- **Evidence Review**: Systematic literature synthesis, guideline summary, trial data
- **Treatment Options**: Available therapies with mechanism of action
- **Evidence Grading**: GRADE assessment for each recommendation (1A, 1B, 2A, 2B, 2C)
- **Recommendations by Line**: First-line, second-line, subsequent therapies
- **Biomarker-Guided Selection**: Decision criteria based on molecular profiles
- **Treatment Algorithms**: TikZ flowcharts showing decision pathways
- **Monitoring Protocol**: Safety assessments, efficacy monitoring, dose modifications
- **Special Populations**: Elderly, renal/hepatic impairment, comorbidities
- **References**: Full bibliography with trial names and citations

## Output Format

**MANDATORY FIRST PAGE REQUIREMENT:**
- **Page 1**: Full-page executive summary with 3-5 colored tcolorbox elements
- **Page 2**: Table of contents (optional)
- **Page 3+**: Detailed sections with methods, results, figures, tables

**Document Specifications:**
- **Primary**: LaTeX/PDF with 0.5in margins for compact, data-dense presentation
- **Length**: Typically 5-15 pages (1 page executive summary + 4-14 pages detailed content)
- **Style**: Publication-ready, pharmaceutical-grade, suitable for regulatory submissions
- **First Page**: Always a complete executive summary spanning entire page 1 (see Document Structure section)

**Visual Elements:**
- **Colors**: 
  - Page 1 boxes: blue=data/information, green=biomarkers/recommendations, yellow/orange=clinical implications, red=warnings
  - Recommendation boxes (green=strong recommendation, yellow=conditional, blue=research needed)
  - Biomarker stratification (color-coded molecular subtypes)
  - Statistical significance (color-coded p-values, hazard ratios)
- **Tables**: 
  - Demographics with baseline characteristics
  - Biomarker frequency by subgroup
  - Outcomes table (ORR, PFS, OS, DOR by molecular subtype)
  - Adverse events by cohort
  - Evidence summary tables with GRADE ratings
- **Figures**: 
  - Kaplan-Meier survival curves with log-rank p-values and number at risk tables
  - Waterfall plots showing best response by patient
  - Forest plots for subgroup analyses with confidence intervals
  - TikZ decision algorithm flowcharts
  - Swimmer plots for individual patient timelines
- **Statistics**: Hazard ratios with 95% CI, p-values, median survival times, landmark survival rates
- **Compliance**: De-identification per HIPAA Safe Harbor, confidentiality notices for proprietary data

## Integration

This skill integrates with:
- **alterlab-scientific-writing**: Citation management, statistical reporting, evidence synthesis
- **alterlab-clinical-reports**: Medical terminology, HIPAA compliance, single-patient case reports
- **alterlab-scientific-schematics**: TikZ flowcharts for decision algorithms and treatment pathways
- **alterlab-treatment-plans**: Individual patient applications of cohort-derived insights (bidirectional)

## Routing: this skill vs. siblings

The discriminator is **unit of analysis**: this skill operates on **groups** (cohorts, subgroups, evidence bases); the siblings operate on a **single patient**.

| Ask | Skill |
| --- | --- |
| Cohort/subgroup analysis, biomarker stratification, GRADE-graded guideline, pharma/RWE strategy doc (group-level) | **this skill** |
| Individual patient care plan, SMART goals, patient-specific dosing/monitoring for the chart | `alterlab-treatment-plans` |
| Single-patient case report for journal submission (e.g. CARE-guideline) | `alterlab-clinical-reports` |

Example for this skill: "Analyze 60 HER2+ breast cancer patients by hormone receptor status with survival outcomes."

## Example Usage

### Patient Cohort Analysis

**Example 1: NSCLC Biomarker Stratification**
```
> Analyze a cohort of 45 NSCLC patients stratified by PD-L1 expression (<1%, 1-49%, ≥50%) 
> receiving pembrolizumab. Include outcomes: ORR, median PFS, median OS with hazard ratios 
> comparing PD-L1 ≥50% vs <50%. Generate Kaplan-Meier curves and waterfall plot.
```

**Example 2: GBM Molecular Subtype Analysis**
```
> Generate cohort analysis for 30 GBM patients classified into Cluster 1 (Mesenchymal-Immune-Active) 
> and Cluster 2 (Proneural) molecular subtypes. Compare outcomes including median OS, 6-month PFS rate, 
> and response to TMZ+bevacizumab. Include biomarker profile table and statistical comparison.
```

**Example 3: Breast Cancer HER2 Cohort**
```
> Analyze 60 HER2-positive metastatic breast cancer patients treated with trastuzumab-deruxtecan, 
> stratified by prior trastuzumab exposure (yes/no). Include ORR, DOR, median PFS with forest plot 
> showing subgroup analyses by hormone receptor status, brain metastases, and number of prior lines.
```

### Treatment Recommendation Report

**Example 1: HER2+ Metastatic Breast Cancer Guidelines**
```
> Create evidence-based treatment recommendations for HER2-positive metastatic breast cancer including 
> biomarker-guided therapy selection. Use GRADE system to grade recommendations for first-line 
> (trastuzumab+pertuzumab+taxane), second-line (trastuzumab-deruxtecan), and third-line options. 
> Include decision algorithm flowchart based on brain metastases, hormone receptor status, and prior therapies.
```

**Example 2: Advanced NSCLC Treatment Algorithm**
```
> Generate treatment recommendation report for advanced NSCLC based on PD-L1 expression, EGFR mutation, 
> ALK rearrangement, and performance status. Include GRADE-graded recommendations for each molecular subtype, 
> TikZ flowchart for biomarker-directed therapy selection, and evidence tables from KEYNOTE-189, FLAURA, 
> and CheckMate-227 trials.
```

**Example 3: Multiple Myeloma Line-of-Therapy Sequencing**
```
> Create treatment algorithm for newly diagnosed multiple myeloma through relapsed/refractory setting. 
> Include GRADE recommendations for transplant-eligible vs ineligible, high-risk cytogenetics considerations, 
> and sequencing of daratumumab, carfilzomib, and CAR-T therapy. Provide flowchart showing decision points 
> at each line of therapy.
```

## Evidence Grading

This skill uses two complementary axes (see `references/treatment_recommendations.md` and `assets/recommendation_strength_guide.md` for the full matrix):

- **Recommendation strength** — Strong (Grade 1, "we recommend": benefits clearly outweigh risks) vs. Conditional/Weak (Grade 2, "we suggest": trade-offs exist, patient values matter). A third "Research" tier flags insufficient evidence.
- **Certainty of evidence** — High / Moderate / Low / Very Low, per the GRADE Working Group's domains (downgrade for risk of bias, inconsistency, indirectness, imprecision, publication bias; upgrade observational data for large effect, dose-response, plausible confounding).

The compact letter codes used throughout (1A, 1B, 2A, 2B, 2C) are the **ACCP/Guyatt notation** (popularized by the ACCP/CHEST antithrombotic guidelines), which pairs the two axes into a single label. GRADE proper does not use these codes; report them as ACCP-style notation when both are cited, and never invent a grade not supported by the underlying evidence.

(Biomarker, outcome-metric, and statistical-method details are covered under **Capabilities** above and in the `references/` files.)

## Best Practices

### For Cohort Analyses

1. **Patient Selection Transparency**: Clearly document inclusion/exclusion criteria, patient flow, and reasons for exclusions
2. **Biomarker Clarity**: Specify assay methods, platforms (e.g., FoundationOne, Caris), cut-points, and validation status
3. **Statistical Rigor**: 
   - Report hazard ratios with 95% confidence intervals, not just p-values
   - Include median follow-up time for survival analyses
   - Specify statistical tests used (log-rank, Cox regression, Fisher's exact)
   - Account for multiple comparisons when appropriate
4. **Outcome Definitions**: Use standard criteria:
   - Response: RECIST 1.1, iRECIST for immunotherapy
   - Adverse events: CTCAE version 5.0
   - Performance status: ECOG or Karnofsky
5. **Survival Data Presentation**:
   - Median OS/PFS with 95% CI
   - Landmark survival rates (6-month, 12-month, 24-month)
   - Number at risk tables below Kaplan-Meier curves
   - Censoring clearly indicated
6. **Subgroup Analyses**: Pre-specify subgroups; clearly label exploratory vs pre-planned analyses
7. **Data Completeness**: Report missing data and how it was handled

### For Treatment Recommendation Reports

1. **Evidence Grading Transparency**: 
   - Use GRADE system consistently (1A, 1B, 2A, 2B, 2C)
   - Document rationale for each grade
   - Clearly state quality of evidence (high, moderate, low, very low)
2. **Comprehensive Evidence Review**: 
   - Include phase 3 randomized trials as primary evidence
   - Supplement with phase 2 data for emerging therapies
   - Note real-world evidence and meta-analyses
   - Cite trial names (e.g., KEYNOTE-189, CheckMate-227)
3. **Biomarker-Guided Recommendations**:
   - Link specific biomarkers to therapy recommendations
   - Specify testing methods and validated assays
   - Include FDA/EMA approval status for companion diagnostics
4. **Clinical Actionability**: Every recommendation should have clear implementation guidance
5. **Decision Algorithm Clarity**: TikZ flowcharts should be unambiguous with clear yes/no decision points
6. **Special Populations**: Address elderly, renal/hepatic impairment, pregnancy, drug interactions
7. **Monitoring Guidance**: Specify safety labs, imaging, and frequency
8. **Update Frequency**: Date recommendations and plan for periodic updates

### General Best Practices

1. **First Page Executive Summary (MANDATORY)**: 
   - ALWAYS create a complete executive summary on page 1 that spans the entire first page
   - Use 3-5 colored tcolorbox elements to highlight key findings
   - No table of contents or detailed sections on page 1
   - Use `\thispagestyle{empty}` and end with `\newpage`
   - This is the single most important page - it should be scannable in 60 seconds
2. **De-identification**: Remove all 18 HIPAA identifiers before document generation (Safe Harbor method)
3. **Regulatory Compliance**: Include confidentiality notices for proprietary pharmaceutical data
4. **Publication-Ready Formatting**: Use 0.5in margins, professional fonts, color-coded sections
5. **Reproducibility**: Document all statistical methods to enable replication
6. **Conflict of Interest**: Disclose pharmaceutical funding or relationships when applicable
7. **Visual Hierarchy**: Use colored boxes consistently (blue=data, green=biomarkers, yellow/orange=recommendations, red=warnings)

## References

See the `references/` directory for detailed guidance on:
- Patient cohort analysis and stratification methods
- Treatment recommendation development
- Clinical decision algorithms
- Biomarker classification and interpretation
- Outcome analysis and statistical methods
- Evidence synthesis and grading systems

## Templates

See the `assets/` directory for LaTeX templates:
- `cohort_analysis_template.tex` - Biomarker-stratified patient cohort analysis with statistical comparisons
- `treatment_recommendation_template.tex` - Evidence-based clinical practice guidelines with GRADE grading
- `clinical_pathway_template.tex` - TikZ decision algorithm flowcharts for treatment sequencing
- `biomarker_report_template.tex` - Molecular subtype classification and genomic profile reports

**Template Features:**
- 0.5in margins for compact presentation
- Color-coded recommendation boxes
- Professional tables for demographics, biomarkers, outcomes
- Built-in support for Kaplan-Meier curves, waterfall plots, forest plots
- GRADE evidence grading tables
- Confidentiality headers for pharmaceutical documents

## Scripts

See the `scripts/` directory for analysis and visualization tools:
- `generate_survival_analysis.py` - Kaplan-Meier curve generation with log-rank tests, hazard ratios, and 95% CIs (also covers the survival-statistics needs of cohort and subgroup analyses)
- `create_cohort_tables.py` - Demographics, biomarker frequency, and outcomes tables
- `build_decision_tree.py` - TikZ flowchart generation for treatment algorithms
- `biomarker_classifier.py` - Patient stratification algorithms by molecular subtype
- `validate_cds_document.py` - Quality and compliance checks (HIPAA, statistical reporting standards)


