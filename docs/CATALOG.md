# AlterLab Academic Skills — Catalog

All 242 skills by domain (v3.0.1). Each skill is a `SKILL.md` instruction file, often with
reference documents and helper scripts. A listing here means the skill exists and ships a
structurally valid eval file; it does **not** mean the skill was evaluated behaviorally — see
[`docs/evals.md`](evals.md) and [`docs/benchmark-results.md`](benchmark-results.md) for what has been measured.
The machine-readable index is [`skills.json`](../skills.json); the browsable site is generated from it.

## ⚡ Core Pipeline — 10 Skills

> *The heart of the system — a multi-agent research-to-publication pipeline with 35 specialized agents, plus teaching and thesis supervision tools.*

| # | Skill | Agents | What It Does |
|:---:|:---|:---:|:---|
| 1 | **🔬 Deep Research** | 13 | Multi-mode research with systematic review, Socratic dialogue, fact-checking |
| 2 | **📝 Paper Writer** | 12 | Academic paper authoring with LaTeX, bilingual support, 9 writing modes |
| 3 | **🔍 Paper Reviewer** | 7 | Multi-perspective peer review with Devil's Advocate, 0–100 quality rubrics |
| 4 | **🔄 Research Pipeline** | 3 | 10-stage orchestrator with integrity verification and material passports |
| 5 | **🔎 Citation Verifier** | — | Deterministic citation-existence gate over Crossref / OpenAlex / Semantic Scholar / arXiv |
| 6 | **🎓 Teaching Design** | — | Course design, syllabi, rubrics, Bloom's taxonomy, backward design |
| 7 | **📋 Thesis Supervisor** | — | Dissertation guidance, defense prep, committee management |
| 8 | **🔗 Link Health** | — | Repo link-health audit meta-skill |
| 9 | **🧩 Workflow Orchestration** | — | Composes AlterLab skills into multi-agent workflows: subagent fan-out, pipelines, judge panels, adversarial verification |
| 10 | **🧭 Skill Finder** | — | Front-door router — turns *"use AlterLab skills"* into the right skill(s); the **`alterflow`** keyword clarifies the goal then launches a dynamic multi-agent workflow |

<br>

---

## 📚 All 242 Skills

### 🗄️ Databases — Scientific Database Connectors (39 Skills)

<details>
<summary><b>Click to expand full database skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **AlphaFold DB** | Protein structure predictions from AlphaFold |
| 2 | **arXiv** | Preprint search and discovery |
| 3 | **BindingDB** | Binding affinity data for drug-target interactions |
| 4 | **bioRxiv** | Biology preprint search and monitoring |
| 5 | **BRENDA** | Enzyme functional data |
| 6 | **cBioPortal** | Cancer genomics data exploration |
| 7 | **ChEMBL** | Bioactive molecules with drug-like properties |
| 8 | **ClinicalTrials.gov** | Clinical trial registry search |
| 9 | **ClinPGx** | Clinical pharmacogenomics data |
| 10 | **ClinVar** | Genomic variation and human health |
| 11 | **COSMIC** | Catalogue of somatic mutations in cancer |
| 12 | **Data Commons** | Google's open knowledge graph |
| 13 | **DepMap** | Cancer dependency mapping |
| 14 | **DrugBank** | Drug and drug target information |
| 15 | **ENA** | European Nucleotide Archive |
| 16 | **Ensembl** | Genome annotation and variation |
| 17 | **FDA** | FDA drug and device data |
| 18 | **Gene DB** | Gene-level data aggregation |
| 19 | **GEO** | Gene Expression Omnibus datasets |
| 20 | **gnomAD** | Genome aggregation and variant frequency |
| 21 | **GTEx** | Tissue-specific gene expression |
| 22 | **GWAS Catalog** | Genome-wide association studies |
| 23 | **HMDB** | Human Metabolome Database |
| 24 | **Imaging Data Commons** | Cancer imaging data |
| 25 | **InterPro** | Protein families and domains |
| 26 | **JASPAR** | Transcription factor binding profiles |
| 27 | **KEGG** | Biological pathways and networks |
| 28 | **Metabolomics Workbench** | Metabolomics data repository |
| 29 | **Monarch Initiative** | Disease-gene associations |
| 30 | **OpenAlex** | Open scholarly metadata |
| 31 | **Open Targets** | Drug target identification |
| 32 | **PDB** | Protein 3D structure database |
| 33 | **PubChem** | Chemical information database |
| 34 | **PubMed** | Biomedical literature search |
| 35 | **Reactome** | Biological pathway database |
| 36 | **STRING** | Protein-protein interaction networks |
| 37 | **UniProt** | Protein sequence and function |
| 38 | **USPTO** | Patent search and analysis |
| 39 | **ZINC** | Commercially-available compounds for docking |

</details>

### 🧬 Bioinformatics — Genomics, Proteomics & Molecular Biology (38 Skills)

<details>
<summary><b>Click to expand full bioinformatics skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **AnnData** | Annotated data matrices for single-cell |
| 2 | **Arboreto** | Gene regulatory network inference |
| 3 | **BioPython** | General-purpose bioinformatics toolkit |
| 4 | **BioServices** | Programmatic access to biological web services |
| 5 | **CellxGene** | Interactive single-cell data exploration |
| 6 | **COBRApy** | Constraint-based metabolic modeling |
| 7 | **deepTools** | NGS data analysis and visualization |
| 8 | **ESM** | Protein language models |
| 9 | **ETE Toolkit** | Phylogenetic tree analysis and visualization |
| 10 | **FlowIO** | Flow cytometry data handling |
| 11 | **gget** | Query genomic databases from Python |
| 12 | **Glycoengineering** | Glycan analysis and engineering |
| 13 | **HistoLab** | Computational histopathology |
| 14 | **LaminDB** | Data lineage and biological data management |
| 15 | **Neuropixels** | Neural probe data processing |
| 16 | **PathML** | Machine learning for pathology |
| 17 | **Phylogenetics** | Evolutionary tree construction |
| 18 | **PyDESeq2** | Differential gene expression analysis |
| 19 | **pyOpenMS** | Mass spectrometry data analysis |
| 20 | **pysam** | SAM/BAM file manipulation |
| 21 | **Scanpy** | Single-cell analysis in Python |
| 22 | **scikit-bio** | Bioinformatics algorithms and data structures |
| 23 | **scVelo** | RNA velocity analysis |
| 24 | **scvi-tools** | Deep generative models for single-cell |
| 25 | **TileDB-VCF** | Population-scale genomic variant storage |
| 26 | **BLAST** | NCBI BLAST+ command-line sequence similarity searches |
| 27 | **nf-core/sarek** | FASTQ-to-VCF germline & somatic variant-calling pipeline |
| 28 | **QIIME 2 Amplicon** | 16S/ITS microbiome amplicon analysis |
| 29 | **RNA-seq Quant** | Transcript abundance with salmon & kallisto |
| 30 | **Squidpy Spatial** | Spatial transcriptomics on AnnData/SpatialData |

</details>

### ⚗️ Cheminformatics — Chemistry & Drug Discovery (12 Skills)

<details>
<summary><b>Click to expand full cheminformatics skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Datamol** | Molecular data manipulation |
| 2 | **DeepChem** | Deep learning for chemistry |
| 3 | **DiffDock** | Diffusion-based molecular docking |
| 4 | **matchms** | Mass spectra matching and similarity |
| 5 | **MedChem** | Medicinal chemistry analysis |
| 6 | **Molecular Dynamics** | MD simulation setup and analysis |
| 7 | **MolFeat** | Molecular featurization |
| 8 | **PrimeKG** | Precision medicine knowledge graph |
| 9 | **PyTDC** | Therapeutics Data Commons access |
| 10 | **RDKit** | Core cheminformatics toolkit |
| 11 | **Rowan** | Computational chemistry workflows |
| 12 | **TorchDrug** | Graph neural networks for drug discovery |

</details>

### 🏥 Clinical Research — Clinical Decision Support & Medical Tools (7 Skills)

<details>
<summary><b>Click to expand full clinical research skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Clinical Decision** | Evidence-based clinical decision support |
| 2 | **Clinical Reports** | Structured clinical report generation |
| 3 | **ISO 13485** | Medical device quality management |
| 4 | **NeuroKit2** | Neurophysiological signal processing |
| 5 | **PyDicom** | DICOM medical image handling |
| 6 | **PyHealth** | Healthcare ML pipelines |
| 7 | **Treatment Plans** | Treatment planning and protocol design |

</details>

### 📊 Data Science — ML, Statistics & Data Analysis (22 Skills)

<details>
<summary><b>Click to expand full data science skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Dask** | Parallel computing and out-of-core data |
| 2 | **EDA** | Exploratory data analysis |
| 3 | **NetworkX** | Network/graph analysis |
| 4 | **Polars** | High-performance DataFrames |
| 5 | **PufferLib** | Reinforcement learning environments |
| 6 | **PyMC** | Bayesian statistical modeling |
| 7 | **pymoo** | Multi-objective optimization |
| 8 | **PyTorch Lightning** | Structured deep learning training |
| 9 | **scikit-learn** | Classical machine learning |
| 10 | **scikit-survival** | Survival analysis |
| 11 | **SHAP** | Model interpretability and feature importance |
| 12 | **SimPy** | Discrete-event simulation |
| 13 | **Stable-Baselines3** | Reinforcement learning algorithms |
| 14 | **Statistical Analysis** | Classical statistical tests and methods |
| 15 | **statsmodels** | Statistical models and econometrics |
| 16 | **SymPy** | Symbolic mathematics |
| 17 | **TimesFM** | Foundation model for time series |
| 18 | **PyTorch Geometric** | Graph neural networks |
| 19 | **Transformers** | Hugging Face transformer models |
| 20 | **UMAP** | Dimensionality reduction |
| 21 | **Vaex** | Out-of-core DataFrames for big data |
| 22 | **Zarr** | Chunked, compressed N-dimensional arrays |

</details>

### 📈 Visualization — Scientific Plotting & Graphics (9 Skills)

<details>
<summary><b>Click to expand full visualization skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Generate Image** | AI image generation for research figures |
| 2 | **Infographics** | Research infographic design |
| 3 | **Matplotlib** | Publication-quality 2D plots |
| 4 | **Mermaid** | Diagrams and flowcharts as code |
| 5 | **Plotly** | Interactive scientific visualizations |
| 6 | **Scientific Schematics** | Technical diagrams and schematics |
| 7 | **Scientific Viz** | Advanced scientific visualization |
| 8 | **Seaborn** | Statistical data visualization |

</details>

### ✍️ Writing Tools — Scientific Writing, Citations & Publishing (14 Skills)

<details>
<summary><b>Click to expand full writing tools skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Academic Career** | Academic CV, research statements, tenure dossier |
| 2 | **AI-Use Disclosure** | Generative-AI disclosure statements for manuscripts, grants, peer review & theses, per publisher, funder & YÖK/TÜBİTAK policy |
| 3 | **Citation Management** | Reference formatting and management |
| 4 | **Hypothesis Generator** | Research hypothesis development |
| 5 | **LaTeX Posters** | Conference poster design in LaTeX |
| 6 | **Literature Review** | Systematic literature review assistance |
| 7 | **Paper-to-Web** | Convert papers to web-friendly formats |
| 8 | **Peer Review** | Peer review writing assistance |
| 9 | **PPTX Posters** | Conference posters in PowerPoint |
| 10 | **Research Grants** | Grant proposal writing |
| 11 | **Scholar Eval** | Academic output evaluation |
| 12 | **Scientific Slides** | Research presentation creation |
| 13 | **Scientific Writing** | Academic writing style and structure |
| 14 | **Venue Templates** | Journal/conference formatting templates |

</details>

### 🔧 Lab Integrations — Laboratory Platform Connectors (9 Skills)

<details>
<summary><b>Click to expand full lab integration skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Benchling** | Molecular biology data platform |
| 2 | **DNAnexus** | Genomic data analysis platform |
| 3 | **Ginkgo Cloud** | Synthetic biology platform |
| 4 | **LabArchive** | Electronic lab notebook |
| 5 | **LatchBio** | Bioinformatics workflow platform |
| 6 | **OMERO** | Biological image management |
| 7 | **Opentrons** | Lab automation and robotics |
| 8 | **Protocols.io** | Protocol sharing and management |
| 9 | **PyLabRobot** | Lab robotics programming |

</details>

### 🌍 Domain-Specific — Quantum, Geospatial, Materials, Social Science & More (18 Skills)

<details>
<summary><b>Click to expand full domain-specific skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Adaptyv** | Adaptive experimental design |
| 2 | **Aeon** | Time series classification |
| 3 | **AstroPy** | Astronomy and astrophysics |
| 4 | **Cirq** | Quantum circuit design (Google) |
| 5 | **FluidSim** | Fluid dynamics simulation |
| 6 | **GeniML** | Genomic interval ML |
| 7 | **GeoMaster** | Geospatial analysis mastery |
| 8 | **GeoPandas** | Geospatial data analysis |
| 9 | **GTARS** | Genomic tool for annotation |
| 10 | **HypoGenic** | Hypothesis generation from data |
| 11 | **Modal** | Cloud compute for research |
| 12 | **PennyLane** | Quantum machine learning |
| 13 | **Pymatgen** | Materials science analysis |
| 14 | **Qiskit** | Quantum computing (IBM) |
| 15 | **QuTiP** | Quantum dynamics simulation |
| 16 | **Social Science Methods** | Discourse analysis, QCA, Delphi, process tracing |
| 17 | **Digital Humanities** | Text mining, corpus linguistics, stylometry, OCR |

</details>

### 📄 Document Tools — Markdown & Document Conversion (3 Skills)

<details>
<summary><b>Click to expand full document tools skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **MarkItDown** | Convert documents to Markdown |
| 2 | **Open Notebook** | Open-format research notebooks |

</details>

### 🔍 Research Tools — Search, Discovery, Methods & Reference Management (14 Skills)

<details>
<summary><b>Click to expand full research tools skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **BGPT Search** | AI-powered research search |
| 2 | **Citation Graph** | Keyless ResearchRabbit analog — citation & co-citation graphs over OpenAlex |
| 3 | **Mixed Methods** | Mixed-methods research design and integration |
| 4 | **Open Science** | Preregistration, FAIR data, open access publishing |
| 5 | **Parallel Web** | Multi-source parallel web search |
| 6 | **PDF Extract** | Elicit-columns analog — per-paper evidence tables from PDFs |
| 7 | **Perplexity** | Perplexity-powered research queries |
| 8 | **PyZotero** | Zotero reference manager integration |
| 9 | **Qualitative Methods** | Thematic analysis, grounded theory, IPA, coding |
| 10 | **Research Ethics** | IRB applications, informed consent, GDPR |
| 11 | **Research Lookup** | Quick research paper discovery |
| 12 | **Scientific Brainstorm** | Structured research ideation |
| 13 | **Scientific Thinking** | Critical scientific reasoning frameworks |
| 14 | **Survey Design** | Questionnaire construction and validation |

</details>

### 💰 Finance & Economics — Financial Data & Analysis (7 Skills)

<details>
<summary><b>Click to expand full finance & economics skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Alpha Vantage** | Stock and financial market data |
| 2 | **Denario** | Financial data processing |
| 3 | **EDGAR Tools** | SEC filing search and analysis |
| 4 | **FRED** | Federal Reserve economic data |
| 5 | **Hedge Fund Monitor** | Hedge fund tracking and analysis |
| 6 | **Market Research** | Market analysis and intelligence |
| 7 | **US Fiscal Data** | US government fiscal data |

</details>

### 🇹🇷 Turkish Academia — National Platforms & Scholarly Workflow (13 Skills)

<details>
<summary><b>Click to expand full Turkish academia skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **DergiPark** | Harvest metadata, abstracts & PDFs from DergiPark via OAI-PMH |
| 2 | **TR Dizin** | Search TR Dizin & verify a journal's national-index status |
| 3 | **YÖK Tez** | Search the national graduate-thesis archive for review & originality checks |
| 4 | **YÖK Akademik** | Look up a Turkish academic's YÖKSİS profile, title & affiliation |
| 5 | **YÖKATLAS** | Higher-education program & admission statistics (kontenjan, taban puan) |
| 6 | **TÜBİTAK Proposal** | Scaffold TÜBİTAK 1001, 1002-A & 3501 national research proposals |
| 7 | **TÜBİTAK BİDEB** | Match & prepare BİDEB fellowships and travel support (2219, 2218, 2221, 2232-A/B, 2236-A, 2224-A, 2223-B) |
| 8 | **Doçentlik Eligibility** | Pre-screen a publication list against ÜAK doçentlik criteria for all 12 temel alanlar |
| 9 | **Akademik Teşvik** | Compute the annual academic-incentive (teşvik) score |
| 10 | **TR Academic Style** | Turkish-journal & TR-Dizin formatting + Turkish APA-7 |
| 11 | **TR Research Ethics** | Turkish etik kurul applications & consent-form routing |
| 12 | **KVKK DMP** | KVKK-compliant data-management plans for Turkish research |
| 13 | **Aperta** | TÜBİTAK open-science compliance & deposition into Aperta |

</details>

### 🎓 Faculty Life — Teaching, Service & the Academic Career (6 Skills)

<details>
<summary><b>Click to expand full faculty life skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Syllabus AI Policy** | Course-level generative-AI use policies & syllabus statements |
| 2 | **Grant Reporting** | Post-award reports — NIH RPPR, NSF, Horizon Europe / ERC |
| 3 | **Recommendation Letters** | Evidence-anchored reference & recommendation letters |
| 4 | **Accreditation (AoL)** | AACSB / ABET assurance-of-learning documentation |
| 5 | **REDCap / CDISC** | Validated data-capture instruments mapped to CDISC standards |
| 6 | **Preprint Deposition** | Deposit preprints to arXiv, bioRxiv, medRxiv, SSRN, OSF |

</details>

### 🧪 Methodology — Research Rigor & Discipline Gates (3 Skills)

<details>
<summary><b>Click to expand full methodology skills list</b></summary>
<br>

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **Pre-registration Discipline** | No analysis without a frozen, pre-registered plan |
| 2 | **Test-Selection Guard** | No statistical test chosen after seeing the p-value |
| 3 | **Results Transparency** | No results claim without reporting every analysis run |

</details>

### 🧭 Social-Science Workflow — Stage-Gated Methods Spine (17 Skills)

<details>
<summary><b>Click to expand full social-science workflow skills list</b></summary>
<br>

A stage-gated methods spine: an orchestrator holds a **Design Passport**, five gates each refuse to advance until their discipline is satisfied, and eleven analysis modules are dispatched by the design/data. The measurement stage is paradigm-selected (quantitative measurement gate vs qualitative reflexivity gate). Every module's library was web-verified to its current API; the gates and modules *route to* the existing qualitative-methods, survey-design, statistics, statsmodels, and networkx skills rather than reimplementing them.

| # | Skill | What It Does |
|:---:|:---|:---|
| 1 | **SSci Orchestrator** | Thin pipeline coordinator — holds the Design Passport, enforces gate order with PASS / WARN / BLOCK, dispatches the right module (does no analysis itself) |
| 2 | **SSci Design Gate** | Routes the study to its design family and **pins the identifying assumption** the causal claim rests on before any analysis |
| 3 | **SSci Measurement Gate** | Enforces *reliability ≠ validity* — omega (not alpha alone), the four validities, and measurement invariance before group comparison |
| 4 | **SSci Sampling Gate** | Matches the **sizing logic to the inference** (power / precision / saturation) and the generalization claim to the sample type |
| 5 | **SSci Reflexivity Gate** | The **qualitative analog** of the measurement gate — positionality + Lincoln & Guba trustworthiness, fail-closed against ungrounded interpretivist claims |
| 6 | **SSci Inference Gate** | The terminal auditor — no causal claim beyond the design, no p-value/CI misreading, no generalization beyond the frame |
| 7 | **Causal Inference** | DiD / IV / RDD / panel FE / PSM / CATE via statsmodels, linearmodels, pyfixest, DoWhy, EconML, rdrobust — names the assumption, estimates, then refutes |
| 8 | **Survey Analysis** | Design-based inference for complex-sample surveys (weights/strata/PSU/FPC, replicate SEs, raking) — svy (samplics is archived) or R survey+srvyr |
| 9 | **SEM & Psychometrics** | CFA / SEM / EFA / IRT / measurement invariance via semopy & factor_analyzer, with a stdlib McDonald's-omega calculator |
| 10 | **Multilevel Models** | Mixed-effects / hierarchical (statsmodels MixedLM, R lme4/glmmTMB/brms) enforcing the under-reported LMM reporting checklist |
| 11 | **QCA** | csQCA / mvQCA / fsQCA (calibrate → truth table → minimize) — **shells to R's QCA package** since no maintained Python library exists |
| 12 | **SNA** | Centrality, community detection (Louvain/Leiden), and ERGM — SNA method discipline over networkx / igraph / R statnet |
| 13 | **ABM (Mesa)** | Agent-based modeling on the **current Mesa 3 AgentSet API**, with replication + parameter-sweep + pattern-oriented validation |
| 14 | **Text-as-Data** | Topic modeling (BERTopic / LDA), embeddings, dictionary methods — chosen by goal, with a topic-reliability procedure |
| 15 | **Qualitative Analysis** | Intercoder reliability (Krippendorff's α + bootstrap CI), codebook-vs-reflexive branch, human↔LLM double-coding |
| 16 | **Meta-Analysis** | Random-effects pooling, I²/τ² heterogeneity, forest/funnel, Egger + trim-and-fill (statsmodels / R metafor), PRISMA |
| 17 | **Missing Data** | MCAR/MAR/MNAR + MICE with **Rubin's-rules pooling** / FIML (statsmodels, R mice); flags the single-imputation trap |

</details>

### 🧩 Research Workflows — Runnable Multi-Agent Jobs (1 Skill + 7 Workflows)

<details>
<summary><b>Click to expand the research workflows</b></summary>
<br>

Claude Code **dynamic workflows** are scripts that orchestrate many subagents and keep their intermediate results out of your conversation. The `alterlab-workflows` plugin ships seven, each composing existing AlterLab skills with the independence and adversarial checks its task needs; counts, votes, κ, and score spreads are computed in code. On claude.ai and other surfaces, the **`alterlab-research-workflows`** skill runs the same stages as staged playbooks. Install: `/plugin install alterlab-workflows@alterlab-academic-skills` (also installs `alterlab-core`).

| # | Command | What It Does |
|:---:|:---|:---|
| 1 | `/alterlab-workflows:citation-audit` | Every reference resolved against Crossref / OpenAlex / Semantic Scholar / arXiv, every cited claim checked against its source; each flag counts only after **two completed re-checks** by separate agents (TF / PAC / IH / PH / SH report); up to 150 cited claims, with coverage reported |
| 2 | `/alterlab-workflows:review-panel` | 4–6 **blind** reviewers chosen for the paper's field and design; every major concern re-read against the manuscript before the editor decides |
| 3 | `/alterlab-workflows:claim-stress-test` | Three skeptics per headline claim (counter-evidence, citation support, inference); majority rating and calibrated rewrites |
| 4 | `/alterlab-workflows:systematic-review-screening` | PRISMA 2020 title/abstract screening — codebook, optional database search, de-duplication, **two blinded screeners per record**, adjudication, Cohen's κ |
| 5 | `/alterlab-workflows:rebuttal` | Point-by-point response to reviewers with a cross-response consistency pass; `[AUTHORS: …]` placeholders instead of invented results |
| 6 | `/alterlab-workflows:grant-mock-panel` | Mock study section on the funder's own criteria and scale (NIH, NSF, ERC, Horizon Europe, TÜBİTAK 1001/1002); score spread computed; summary statement |
| 7 | `/alterlab-workflows:literature-map` | Parallel scholarly-database sweeps → themes, landmark works, and research gaps that survive a search for existing answers |

</details>

<br>
