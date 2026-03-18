<p align="center">
  <img src="https://img.shields.io/badge/Skills-186+-blueviolet?style=for-the-badge" alt="186+ Skills" />
  <img src="https://img.shields.io/badge/Domains-14-blue?style=for-the-badge" alt="14 Domains" />
  <img src="https://img.shields.io/badge/Claude-AI%20Powered-orange?style=for-the-badge" alt="Claude AI" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge" alt="PRs Welcome" />
</p>

<h1 align="center">AlterLab Academic Skills</h1>

<p align="center">
  <strong>186+ Claude AI skills for faculty members and academic researchers</strong><br />
  Research Pipeline | Scientific Databases | Bioinformatics | Data Science | Social Sciences | Visualization | and more
</p>

<p align="center">
  Built by <a href="https://github.com/AlterLab-IEU">AlterLab Creative Technologies Laboratory</a>
</p>

---

## What Is This?

A comprehensive suite of **186+ purpose-built Claude AI skills** for faculty members, academicians, and researchers — organized into **14 domain categories** spanning the full academic research lifecycle.

Each skill transforms Claude into a **domain-specific expert assistant** tailored to academic research, scientific computing, and scholarly publishing workflows.

**Not tied to any specific university.** These skills work for any researcher, anywhere.

> **How it works:** Each skill is a structured `.md` prompt file. Drop it into a Claude Project or Claude Code, and Claude instantly becomes your research expert — with real scientific frameworks, professional output templates, and deep domain knowledge.

---

## Table of Contents

- [Domain Overview](#domain-overview)
- [Quick Start](#quick-start)
- [Core Pipeline](#core-pipeline--4-skills)
- [All 186+ Skills](#all-186-skills)
- [Project Structure](#project-structure)
- [How Skills Work](#how-skills-work)
- [Contributing](#contributing)
- [License](#license)
- [Credits](#credits)

---

## Domain Overview

| Domain | Skills | Focus Areas |
|:-------|:------:|:------------|
| **Core Pipeline** | 6 | Multi-agent research -> write -> review -> publish pipeline + teaching + thesis |
| **Databases** | 39 | Connectors to 250+ scientific databases — PubMed, ChEMBL, UniProt, ClinicalTrials.gov, COSMIC, and more |
| **Bioinformatics** | 25 | Genomics, proteomics, molecular biology — Scanpy, BioPython, ESM, single-cell analysis |
| **Cheminformatics** | 12 | Chemistry and drug discovery — RDKit, molecular dynamics, docking, ADMET |
| **Clinical Research** | 10 | Clinical decision support, treatment planning, medical imaging, regulatory |
| **Data Science** | 22 | ML/statistics — scikit-learn, PyTorch Lightning, SHAP, transformers |
| **Visualization** | 8 | Scientific plotting — Matplotlib, Seaborn, Plotly, schematics, infographics |
| **Writing Tools** | 13 | Scientific writing, citations, grants, posters, academic career |
| **Lab Integrations** | 9 | Laboratory platforms — Benchling, DNAnexus, Opentrons, Protocols.io |
| **Domain-Specific** | 17 | Quantum computing, geospatial, materials science, social science methods, digital humanities |
| **Document Tools** | 6 | File format handling — DOCX, PDF, PPTX, XLSX, Markdown |
| **Research Tools** | 12 | Search, discovery, Zotero, qualitative methods, ethics, surveys, open science |
| **Finance & Economics** | 7 | FRED, Alpha Vantage, SEC EDGAR, market research |
| **Social Sciences & Humanities** | 10 | Teaching design, thesis supervision, mixed methods, digital humanities |

---

## Quick Start

### Option 1 — Claude Projects (Recommended)

```
1. Go to claude.ai -> Projects -> Create Project
2. Upload SKILL.md files from your domain folder into the project's Knowledge section
3. Start chatting — Claude now has your skills loaded
```

### Option 2 — Claude Code CLI

```bash
git clone https://github.com/AlterLab-IEU/AlterLab-Academic-Skills.git
cd AlterLab-Academic-Skills
claude "help me research the latest findings on CRISPR gene editing"
```

### Option 3 — Pick Individual Skills

Browse the [`skills/`](./skills) folder and download only the ones you need. Every skill is a standalone `.md` file.

---

## Core Pipeline — 6 Skills

The heart of the system — a **multi-agent research-to-publication pipeline** with 39 specialized agents, plus teaching and thesis supervision tools.

| # | Skill | Agents | What It Does |
|:-:|:------|:------:|:-------------|
| 1 | [Deep Research](./skills/core/alterlab-deep-research) | 13 | Multi-mode research with systematic review, Socratic dialogue, fact-checking |
| 2 | [Paper Writer](./skills/core/alterlab-paper-writer) | 12 | Academic paper authoring with LaTeX, bilingual support, 9 writing modes |
| 3 | [Paper Reviewer](./skills/core/alterlab-paper-reviewer) | 7 | Multi-perspective peer review with Devil's Advocate, 0-100 quality rubrics |
| 4 | [Research Pipeline](./skills/core/alterlab-research-pipeline) | 7 | 10-stage orchestrator with integrity verification and material passports |
| 5 | [Teaching Design](./skills/core/alterlab-teaching-design) | — | Course design, syllabi, rubrics, Bloom's taxonomy, backward design |
| 6 | [Thesis Supervisor](./skills/core/alterlab-thesis-supervisor) | — | Dissertation guidance, defense prep, committee management |

---

## All 186+ Skills

<details>
<summary><strong>Databases</strong> — Connectors to 250+ Scientific Databases (39 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [AlphaFold DB](./skills/databases/alterlab-alphafold-db) | Protein structure predictions from AlphaFold |
| 2 | [arXiv](./skills/databases/alterlab-arxiv) | Preprint search and discovery |
| 3 | [BindingDB](./skills/databases/alterlab-bindingdb) | Binding affinity data for drug-target interactions |
| 4 | [bioRxiv](./skills/databases/alterlab-biorxiv) | Biology preprint search and monitoring |
| 5 | [BRENDA](./skills/databases/alterlab-brenda) | Enzyme functional data |
| 6 | [cBioPortal](./skills/databases/alterlab-cbioportal) | Cancer genomics data exploration |
| 7 | [ChEMBL](./skills/databases/alterlab-chembl) | Bioactive molecules with drug-like properties |
| 8 | [ClinicalTrials.gov](./skills/databases/alterlab-clinicaltrials) | Clinical trial registry search |
| 9 | [ClinPGx](./skills/databases/alterlab-clinpgx) | Clinical pharmacogenomics data |
| 10 | [ClinVar](./skills/databases/alterlab-clinvar) | Genomic variation and human health |
| 11 | [COSMIC](./skills/databases/alterlab-cosmic) | Catalogue of somatic mutations in cancer |
| 12 | [Data Commons](./skills/databases/alterlab-datacommons) | Google's open knowledge graph |
| 13 | [DepMap](./skills/databases/alterlab-depmap) | Cancer dependency mapping |
| 14 | [DrugBank](./skills/databases/alterlab-drugbank) | Drug and drug target information |
| 15 | [ENA](./skills/databases/alterlab-ena) | European Nucleotide Archive |
| 16 | [Ensembl](./skills/databases/alterlab-ensembl) | Genome annotation and variation |
| 17 | [FDA](./skills/databases/alterlab-fda) | FDA drug and device data |
| 18 | [Gene DB](./skills/databases/alterlab-gene-db) | Gene-level data aggregation |
| 19 | [GEO](./skills/databases/alterlab-geo) | Gene Expression Omnibus datasets |
| 20 | [gnomAD](./skills/databases/alterlab-gnomad) | Genome aggregation and variant frequency |
| 21 | [GTEx](./skills/databases/alterlab-gtex) | Tissue-specific gene expression |
| 22 | [GWAS Catalog](./skills/databases/alterlab-gwas) | Genome-wide association studies |
| 23 | [HMDB](./skills/databases/alterlab-hmdb) | Human Metabolome Database |
| 24 | [Imaging Data Commons](./skills/databases/alterlab-imaging-data-commons) | Cancer imaging data |
| 25 | [InterPro](./skills/databases/alterlab-interpro) | Protein families and domains |
| 26 | [JASPAR](./skills/databases/alterlab-jaspar) | Transcription factor binding profiles |
| 27 | [KEGG](./skills/databases/alterlab-kegg) | Biological pathways and networks |
| 28 | [Metabolomics Workbench](./skills/databases/alterlab-metabolomics-wb) | Metabolomics data repository |
| 29 | [Monarch Initiative](./skills/databases/alterlab-monarch) | Disease-gene associations |
| 30 | [OpenAlex](./skills/databases/alterlab-openalex) | Open scholarly metadata |
| 31 | [Open Targets](./skills/databases/alterlab-opentargets) | Drug target identification |
| 32 | [PDB](./skills/databases/alterlab-pdb) | Protein 3D structure database |
| 33 | [PubChem](./skills/databases/alterlab-pubchem) | Chemical information database |
| 34 | [PubMed](./skills/databases/alterlab-pubmed) | Biomedical literature search |
| 35 | [Reactome](./skills/databases/alterlab-reactome) | Biological pathway database |
| 36 | [STRING](./skills/databases/alterlab-string-db) | Protein-protein interaction networks |
| 37 | [UniProt](./skills/databases/alterlab-uniprot) | Protein sequence and function |
| 38 | [USPTO](./skills/databases/alterlab-uspto) | Patent search and analysis |
| 39 | [ZINC](./skills/databases/alterlab-zinc-db) | Commercially-available compounds for docking |

</details>

<details>
<summary><strong>Bioinformatics</strong> — Genomics, Proteomics & Molecular Biology (25 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [AnnData](./skills/bioinformatics/alterlab-anndata) | Annotated data matrices for single-cell |
| 2 | [Arboreto](./skills/bioinformatics/alterlab-arboreto) | Gene regulatory network inference |
| 3 | [BioPython](./skills/bioinformatics/alterlab-biopython) | General-purpose bioinformatics toolkit |
| 4 | [BioServices](./skills/bioinformatics/alterlab-bioservices) | Programmatic access to biological web services |
| 5 | [CellxGene](./skills/bioinformatics/alterlab-cellxgene) | Interactive single-cell data exploration |
| 6 | [COBRApy](./skills/bioinformatics/alterlab-cobrapy) | Constraint-based metabolic modeling |
| 7 | [deepTools](./skills/bioinformatics/alterlab-deeptools) | NGS data analysis and visualization |
| 8 | [ESM](./skills/bioinformatics/alterlab-esm) | Protein language models |
| 9 | [ETE Toolkit](./skills/bioinformatics/alterlab-etetoolkit) | Phylogenetic tree analysis and visualization |
| 10 | [FlowIO](./skills/bioinformatics/alterlab-flowio) | Flow cytometry data handling |
| 11 | [gget](./skills/bioinformatics/alterlab-gget) | Query genomic databases from Python |
| 12 | [Glycoengineering](./skills/bioinformatics/alterlab-glycoengineering) | Glycan analysis and engineering |
| 13 | [HistoLab](./skills/bioinformatics/alterlab-histolab) | Computational histopathology |
| 14 | [LaminDB](./skills/bioinformatics/alterlab-lamindb) | Data lineage and biological data management |
| 15 | [Neuropixels](./skills/bioinformatics/alterlab-neuropixels) | Neural probe data processing |
| 16 | [PathML](./skills/bioinformatics/alterlab-pathml) | Machine learning for pathology |
| 17 | [Phylogenetics](./skills/bioinformatics/alterlab-phylogenetics) | Evolutionary tree construction |
| 18 | [PyDESeq2](./skills/bioinformatics/alterlab-pydeseq2) | Differential gene expression analysis |
| 19 | [pyOpenMS](./skills/bioinformatics/alterlab-pyopenms) | Mass spectrometry data analysis |
| 20 | [pysam](./skills/bioinformatics/alterlab-pysam) | SAM/BAM file manipulation |
| 21 | [Scanpy](./skills/bioinformatics/alterlab-scanpy) | Single-cell analysis in Python |
| 22 | [scikit-bio](./skills/bioinformatics/alterlab-scikit-bio) | Bioinformatics algorithms and data structures |
| 23 | [scVelo](./skills/bioinformatics/alterlab-scvelo) | RNA velocity analysis |
| 24 | [scvi-tools](./skills/bioinformatics/alterlab-scvi-tools) | Deep generative models for single-cell |
| 25 | [TileDB-VCF](./skills/bioinformatics/alterlab-tiledbvcf) | Population-scale genomic variant storage |

</details>

<details>
<summary><strong>Cheminformatics</strong> — Chemistry & Drug Discovery (12 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Datamol](./skills/cheminformatics/alterlab-datamol) | Molecular data manipulation |
| 2 | [DeepChem](./skills/cheminformatics/alterlab-deepchem) | Deep learning for chemistry |
| 3 | [DiffDock](./skills/cheminformatics/alterlab-diffdock) | Diffusion-based molecular docking |
| 4 | [matchms](./skills/cheminformatics/alterlab-matchms) | Mass spectra matching and similarity |
| 5 | [MedChem](./skills/cheminformatics/alterlab-medchem) | Medicinal chemistry analysis |
| 6 | [Molecular Dynamics](./skills/cheminformatics/alterlab-molecular-dynamics) | MD simulation setup and analysis |
| 7 | [MolFeat](./skills/cheminformatics/alterlab-molfeat) | Molecular featurization |
| 8 | [PrimeKG](./skills/cheminformatics/alterlab-primekg) | Precision medicine knowledge graph |
| 9 | [PyTDC](./skills/cheminformatics/alterlab-pytdc) | Therapeutics Data Commons access |
| 10 | [RDKit](./skills/cheminformatics/alterlab-rdkit) | Core cheminformatics toolkit |
| 11 | [Rowan](./skills/cheminformatics/alterlab-rowan) | Computational chemistry workflows |
| 12 | [TorchDrug](./skills/cheminformatics/alterlab-torchdrug) | Graph neural networks for drug discovery |

</details>

<details>
<summary><strong>Clinical Research</strong> — Clinical Decision Support & Medical Tools (10 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Clinical Decision](./skills/clinical-research/alterlab-clinical-decision) | Evidence-based clinical decision support |
| 2 | [Clinical Reports](./skills/clinical-research/alterlab-clinical-reports) | Structured clinical report generation |
| 3 | [Consciousness Council](./skills/clinical-research/alterlab-consciousness-council) | Multi-perspective medical ethics deliberation |
| 4 | [DHDNA Profiler](./skills/clinical-research/alterlab-dhdna-profiler) | Digital health DNA profiling |
| 5 | [ISO 13485](./skills/clinical-research/alterlab-iso13485) | Medical device quality management |
| 6 | [NeuroKit2](./skills/clinical-research/alterlab-neurokit2) | Neurophysiological signal processing |
| 7 | [PyDicom](./skills/clinical-research/alterlab-pydicom) | DICOM medical image handling |
| 8 | [PyHealth](./skills/clinical-research/alterlab-pyhealth) | Healthcare ML pipelines |
| 9 | [Treatment Plans](./skills/clinical-research/alterlab-treatment-plans) | Treatment planning and protocol design |
| 10 | [What-If Oracle](./skills/clinical-research/alterlab-what-if-oracle) | Counterfactual clinical reasoning |

</details>

<details>
<summary><strong>Data Science</strong> — ML, Statistics & Data Analysis (22 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Dask](./skills/data-science/alterlab-dask) | Parallel computing and out-of-core data |
| 2 | [EDA](./skills/data-science/alterlab-eda) | Exploratory data analysis |
| 3 | [NetworkX](./skills/data-science/alterlab-networkx) | Network/graph analysis |
| 4 | [Polars](./skills/data-science/alterlab-polars) | High-performance DataFrames |
| 5 | [PufferLib](./skills/data-science/alterlab-pufferlib) | Reinforcement learning environments |
| 6 | [PyMC](./skills/data-science/alterlab-pymc) | Bayesian statistical modeling |
| 7 | [pymoo](./skills/data-science/alterlab-pymoo) | Multi-objective optimization |
| 8 | [PyTorch Lightning](./skills/data-science/alterlab-pytorch-lightning) | Structured deep learning training |
| 9 | [scikit-learn](./skills/data-science/alterlab-scikit-learn) | Classical machine learning |
| 10 | [scikit-survival](./skills/data-science/alterlab-scikit-survival) | Survival analysis |
| 11 | [SHAP](./skills/data-science/alterlab-shap) | Model interpretability and feature importance |
| 12 | [SimPy](./skills/data-science/alterlab-simpy) | Discrete-event simulation |
| 13 | [Stable-Baselines3](./skills/data-science/alterlab-stable-baselines3) | Reinforcement learning algorithms |
| 14 | [Statistical Analysis](./skills/data-science/alterlab-statistical-analysis) | Classical statistical tests and methods |
| 15 | [statsmodels](./skills/data-science/alterlab-statsmodels) | Statistical models and econometrics |
| 16 | [SymPy](./skills/data-science/alterlab-sympy) | Symbolic mathematics |
| 17 | [TimesFM](./skills/data-science/alterlab-timesfm) | Foundation model for time series |
| 18 | [PyTorch Geometric](./skills/data-science/alterlab-torch-geometric) | Graph neural networks |
| 19 | [Transformers](./skills/data-science/alterlab-transformers) | Hugging Face transformer models |
| 20 | [UMAP](./skills/data-science/alterlab-umap) | Dimensionality reduction |
| 21 | [Vaex](./skills/data-science/alterlab-vaex) | Out-of-core DataFrames for big data |
| 22 | [Zarr](./skills/data-science/alterlab-zarr) | Chunked, compressed N-dimensional arrays |

</details>

<details>
<summary><strong>Visualization</strong> — Scientific Plotting & Graphics (8 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Generate Image](./skills/visualization/alterlab-generate-image) | AI image generation for research figures |
| 2 | [Infographics](./skills/visualization/alterlab-infographics) | Research infographic design |
| 3 | [Matplotlib](./skills/visualization/alterlab-matplotlib) | Publication-quality 2D plots |
| 4 | [Mermaid](./skills/visualization/alterlab-mermaid) | Diagrams and flowcharts as code |
| 5 | [Plotly](./skills/visualization/alterlab-plotly) | Interactive scientific visualizations |
| 6 | [Scientific Schematics](./skills/visualization/alterlab-scientific-schematics) | Technical diagrams and schematics |
| 7 | [Scientific Viz](./skills/visualization/alterlab-scientific-viz) | Advanced scientific visualization |
| 8 | [Seaborn](./skills/visualization/alterlab-seaborn) | Statistical data visualization |

</details>

<details>
<summary><strong>Writing Tools</strong> — Scientific Writing, Citations & Publishing (13 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Academic Career](./skills/writing-tools/alterlab-academic-career) | Academic CV, research statements, tenure dossier |
| 2 | [Citation Management](./skills/writing-tools/alterlab-citation-mgmt) | Reference formatting and management |
| 3 | [Hypothesis Generator](./skills/writing-tools/alterlab-hypothesis-gen) | Research hypothesis development |
| 4 | [LaTeX Posters](./skills/writing-tools/alterlab-latex-posters) | Conference poster design in LaTeX |
| 5 | [Literature Review](./skills/writing-tools/alterlab-literature-review) | Systematic literature review assistance |
| 6 | [Paper-to-Web](./skills/writing-tools/alterlab-paper-2-web) | Convert papers to web-friendly formats |
| 7 | [Peer Review](./skills/writing-tools/alterlab-peer-review) | Peer review writing assistance |
| 8 | [PPTX Posters](./skills/writing-tools/alterlab-pptx-posters) | Conference posters in PowerPoint |
| 9 | [Research Grants](./skills/writing-tools/alterlab-research-grants) | Grant proposal writing |
| 10 | [Scholar Eval](./skills/writing-tools/alterlab-scholar-eval) | Academic output evaluation |
| 11 | [Scientific Slides](./skills/writing-tools/alterlab-scientific-slides) | Research presentation creation |
| 12 | [Scientific Writing](./skills/writing-tools/alterlab-scientific-writing) | Academic writing style and structure |
| 13 | [Venue Templates](./skills/writing-tools/alterlab-venue-templates) | Journal/conference formatting templates |

</details>

<details>
<summary><strong>Lab Integrations</strong> — Laboratory Platform Connectors (9 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Benchling](./skills/lab-integrations/alterlab-benchling) | Molecular biology data platform |
| 2 | [DNAnexus](./skills/lab-integrations/alterlab-dnanexus) | Genomic data analysis platform |
| 3 | [Ginkgo Cloud](./skills/lab-integrations/alterlab-ginkgo-cloud) | Synthetic biology platform |
| 4 | [LabArchive](./skills/lab-integrations/alterlab-labarchive) | Electronic lab notebook |
| 5 | [LatchBio](./skills/lab-integrations/alterlab-latchbio) | Bioinformatics workflow platform |
| 6 | [OMERO](./skills/lab-integrations/alterlab-omero) | Biological image management |
| 7 | [Opentrons](./skills/lab-integrations/alterlab-opentrons) | Lab automation and robotics |
| 8 | [Protocols.io](./skills/lab-integrations/alterlab-protocolsio) | Protocol sharing and management |
| 9 | [PyLabRobot](./skills/lab-integrations/alterlab-pylabrobot) | Lab robotics programming |

</details>

<details>
<summary><strong>Domain-Specific</strong> — Quantum, Geospatial, Materials, Social Science & More (17 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Adaptyv](./skills/domain-specific/alterlab-adaptyv) | Adaptive experimental design |
| 2 | [Aeon](./skills/domain-specific/alterlab-aeon) | Time series classification |
| 3 | [AstroPy](./skills/domain-specific/alterlab-astropy) | Astronomy and astrophysics |
| 4 | [Cirq](./skills/domain-specific/alterlab-cirq) | Quantum circuit design (Google) |
| 5 | [FluidSim](./skills/domain-specific/alterlab-fluidsim) | Fluid dynamics simulation |
| 6 | [GeniML](./skills/domain-specific/alterlab-geniml) | Genomic interval ML |
| 7 | [GeoMaster](./skills/domain-specific/alterlab-geomaster) | Geospatial analysis mastery |
| 8 | [GeoPandas](./skills/domain-specific/alterlab-geopandas) | Geospatial data analysis |
| 9 | [GTARS](./skills/domain-specific/alterlab-gtars) | Genomic tool for annotation |
| 10 | [HypoGenic](./skills/domain-specific/alterlab-hypogenic) | Hypothesis generation from data |
| 11 | [Modal](./skills/domain-specific/alterlab-modal) | Cloud compute for research |
| 12 | [PennyLane](./skills/domain-specific/alterlab-pennylane) | Quantum machine learning |
| 13 | [Pymatgen](./skills/domain-specific/alterlab-pymatgen) | Materials science analysis |
| 14 | [Qiskit](./skills/domain-specific/alterlab-qiskit) | Quantum computing (IBM) |
| 15 | [QuTiP](./skills/domain-specific/alterlab-qutip) | Quantum dynamics simulation |
| 16 | [Social Science Methods](./skills/domain-specific/alterlab-social-science-methods) | Discourse analysis, QCA, Delphi, process tracing |
| 17 | [Digital Humanities](./skills/domain-specific/alterlab-digital-humanities) | Text mining, corpus linguistics, stylometry, OCR |

</details>

<details>
<summary><strong>Document Tools</strong> — File Format Handling (6 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [DOCX](./skills/document-tools/alterlab-docx) | Word document generation and manipulation |
| 2 | [MarkItDown](./skills/document-tools/alterlab-markitdown) | Convert documents to Markdown |
| 3 | [Open Notebook](./skills/document-tools/alterlab-open-notebook) | Open-format research notebooks |
| 4 | [PDF](./skills/document-tools/alterlab-pdf) | PDF generation and processing |
| 5 | [PPTX](./skills/document-tools/alterlab-pptx) | PowerPoint presentation creation |
| 6 | [XLSX](./skills/document-tools/alterlab-xlsx) | Excel spreadsheet handling |

</details>

<details>
<summary><strong>Research Tools</strong> — Search, Discovery, Methods & Reference Management (12 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [BGPT Search](./skills/research-tools/alterlab-bgpt-search) | AI-powered research search |
| 2 | [Mixed Methods](./skills/research-tools/alterlab-mixed-methods) | Mixed-methods research design and integration |
| 3 | [Open Science](./skills/research-tools/alterlab-open-science) | Preregistration, FAIR data, open access publishing |
| 4 | [Parallel Web](./skills/research-tools/alterlab-parallel-web) | Multi-source parallel web search |
| 5 | [Perplexity](./skills/research-tools/alterlab-perplexity) | Perplexity-powered research queries |
| 6 | [PyZotero](./skills/research-tools/alterlab-pyzotero) | Zotero reference manager integration |
| 7 | [Qualitative Methods](./skills/research-tools/alterlab-qualitative-methods) | Thematic analysis, grounded theory, IPA, coding |
| 8 | [Research Ethics](./skills/research-tools/alterlab-research-ethics) | IRB applications, informed consent, GDPR |
| 9 | [Research Lookup](./skills/research-tools/alterlab-research-lookup) | Quick research paper discovery |
| 10 | [Scientific Brainstorm](./skills/research-tools/alterlab-scientific-brainstorm) | Structured research ideation |
| 11 | [Scientific Thinking](./skills/research-tools/alterlab-scientific-thinking) | Critical scientific reasoning frameworks |
| 12 | [Survey Design](./skills/research-tools/alterlab-survey-design) | Questionnaire construction and validation |

</details>

<details>
<summary><strong>Finance & Economics</strong> — Financial Data & Analysis (7 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Alpha Vantage](./skills/finance-economics/alterlab-alpha-vantage) | Stock and financial market data |
| 2 | [Denario](./skills/finance-economics/alterlab-denario) | Financial data processing |
| 3 | [EDGAR Tools](./skills/finance-economics/alterlab-edgartools) | SEC filing search and analysis |
| 4 | [FRED](./skills/finance-economics/alterlab-fred) | Federal Reserve economic data |
| 5 | [Hedge Fund Monitor](./skills/finance-economics/alterlab-hedgefund-monitor) | Hedge fund tracking and analysis |
| 6 | [Market Research](./skills/finance-economics/alterlab-market-research) | Market analysis and intelligence |
| 7 | [US Fiscal Data](./skills/finance-economics/alterlab-usfiscaldata) | US government fiscal data |

</details>

<details>
<summary><strong>Social Sciences & Humanities</strong> — Teaching, Methods & Ethics (10 Skills)</summary>
<br />

| # | Skill | What It Does |
|:-:|:------|:-------------|
| 1 | [Teaching Design](./skills/core/alterlab-teaching-design) | Curriculum and course design for higher education |
| 2 | [Qualitative Methods](./skills/research-tools/alterlab-qualitative-methods) | Qualitative research methodology and analysis |
| 3 | [Research Ethics](./skills/research-tools/alterlab-research-ethics) | IRB, ethics review, and responsible research conduct |
| 4 | [Survey Design](./skills/research-tools/alterlab-survey-design) | Survey instrument design and validation |
| 5 | [Thesis Supervisor](./skills/core/alterlab-thesis-supervisor) | Graduate thesis and dissertation supervision |
| 6 | [Mixed Methods](./skills/research-tools/alterlab-mixed-methods) | Mixed-methods research design and integration |
| 7 | [Academic Career](./skills/writing-tools/alterlab-academic-career) | Academic career development, tenure, and promotion |
| 8 | [Open Science](./skills/research-tools/alterlab-open-science) | Open access, preregistration, and reproducibility |
| 9 | [Social Science Methods](./skills/domain-specific/alterlab-social-science-methods) | Social science research methodology |
| 10 | [Digital Humanities](./skills/domain-specific/alterlab-digital-humanities) | Computational approaches to humanities research |

</details>

---

## Project Structure

```
AlterLab-Academic-Skills/
├── skills/
│   ├── core/                  # 6 pipeline + teaching + thesis skills
│   ├── databases/             # 39 database connectors
│   ├── bioinformatics/        # 25 bio/genomics tools
│   ├── cheminformatics/       # 12 chemistry/drug discovery
│   ├── clinical-research/     # 10 clinical/medical tools
│   ├── data-science/          # 22 ML/statistics tools
│   ├── visualization/         # 8 plotting/charting tools
│   ├── writing-tools/         # 13 scientific writing & career tools
│   ├── lab-integrations/      # 9 lab platform connectors
│   ├── domain-specific/       # 17 specialized field tools
│   ├── document-tools/        # 6 file format tools
│   ├── research-tools/        # 12 search, methods & ethics tools
│   └── finance-economics/     # 7 financial/economic tools
├── .claude/
│   └── CLAUDE.md              # Project-level Claude config
├── README.md                  # This file
├── CLAUDE.md                  # Project instructions
├── CONTRIBUTING.md            # Contribution guidelines
└── LICENSE                    # MIT License
```

---

## How Skills Work

Each `.md` skill file follows a consistent structure:

```markdown
| name          | description                         |
|---------------|-------------------------------------|
| skill-name    | When to activate this skill...      |

# Skill Title

You are **RoleName**, a [role description]...

## Your Identity & Memory
## Your Core Mission
## Frameworks & Methods
## Output Templates
## Quality Standards
```

> **Pro tip:** Combine multiple skills in one Claude Project for a multi-expert team. For example, load Deep Research + Paper Writer + Paper Reviewer for a complete research-to-publication workflow.

---

## Usage Examples

Skills activate automatically based on user intent:

| You say... | Skill activated |
|:-----------|:----------------|
| "Help me research the latest findings on CRISPR gene editing" | `alterlab-deep-research` |
| "Write an academic paper on machine learning in education" | `alterlab-paper-writer` |
| "Review my manuscript for methodology issues" | `alterlab-paper-reviewer` |
| "Search PubMed for recent studies on Alzheimer's biomarkers" | `alterlab-pubmed` |
| "Analyze my RNA-seq data" | `alterlab-scanpy` + `alterlab-pydeseq2` |
| "Create a scientific poster for my conference" | `alterlab-latex-posters` |
| "Design a survey for my social science study" | `alterlab-survey-design` |
| "Help me with my IRB ethics application" | `alterlab-research-ethics` |
| "Build a Bayesian model for my clinical trial data" | `alterlab-pymc` |
| "Guide my PhD student's thesis writing" | `alterlab-thesis-supervisor` |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

**Quick ways to contribute:**

- Improve an existing skill with better frameworks or templates
- Create a new skill following the structure above
- Report issues or suggest improvements
- Add examples or use cases to documentation

---

## License

MIT License

Copyright (c) 2026 AlterLab Creative Technologies Laboratory

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Credits

Built by **AlterLab Creative Technologies Laboratory**.

> *186+ skills. 14 domains. 1 prompt away from expert-level research.*
>
> **[Star this repo](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills)** if you find it useful!
