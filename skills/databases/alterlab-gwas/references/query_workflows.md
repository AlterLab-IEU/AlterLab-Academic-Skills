# GWAS Catalog Query Workflows

Step-by-step workflows for disease-, variant-, and gene-centric queries, systematic reviews, and summary-statistics analysis, using REST API v2 (`https://www.ebi.ac.uk/gwas/rest/api/v2`). Web-interface search modes are listed at the end.

## Workflow 1: Exploring Genetic Associations for a Disease

1. **Identify the trait** using ontology terms or free text:
   - Search the web interface or `GET /v2/efo-traits?efo_trait=<name>` for the disease name
   - Note the current short-form (e.g., MONDO_0005148 for type 2 diabetes mellitus). Legacy IDs such as EFO_0001360 return an empty page — see the trait-ID gotcha in SKILL.md.
   - Decide whether descendant traits count (`show_child_trait=true`) and record that choice in your methods.

2. **Query associations via API:**
   ```python
   url = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
   params = {"efo_id": efo_id, "sort": "p_value", "direction": "asc", "size": 200}
   ```

3. **Filter by significance and population:**
   - Check p-values (genome-wide significant: p ≤ 5×10⁻⁸)
   - Review ancestry information in study metadata
   - Filter by sample size or discovery/replication status

4. **Extract variant details:** rs IDs, effect alleles and directions, effect sizes (odds ratios, beta coefficients), population allele frequencies.

5. **Cross-reference with other databases:** variant consequences in Ensembl, population frequencies in gnomAD, gene function and pathways.

## Workflow 2: Investigating a Specific Genetic Variant

1. **Query the variant:**
   ```python
   url = f"https://www.ebi.ac.uk/gwas/rest/api/v2/single-nucleotide-polymorphisms/{rs_id}"
   ```

2. **Retrieve all trait associations:**
   ```python
   url = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
   params = {"rs_id": rs_id, "sort": "p_value", "direction": "asc", "size": 200}
   ```

3. **Analyze pleiotropy:** identify all traits associated with this variant, review effect directions across traits, look for shared biological pathways.

4. **Check genomic context:** nearby genes, coding/regulatory regions, linkage disequilibrium with other variants.

## Workflow 3: Gene-Centric Association Analysis

1. **Search by gene symbol** in web interface or:
   ```python
   url = "https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
   params = {"mapped_gene": gene_symbol}          # add extended_geneset=true for all nearby genes
   ```

2. **Retrieve variants in gene region:** get the gene span from `/v2/genes/{gene_name}` (`location`, e.g. `10:112950015-113167678`), then query `/v2/single-nucleotide-polymorphisms?chromosome=10&bp_start=...&bp_end=...`, extending the boundaries to cover promoter/regulatory regions.

3. **Analyze association patterns:** identify traits associated with variants in this gene, look for consistent associations across studies, review effect sizes and directions.

4. **Functional interpretation:** determine variant consequences (missense, regulatory, etc.), check expression QTL (eQTL) data, review pathway and network context.

## Workflow 4: Systematic Review of Genetic Evidence

1. **Define research question:** specific trait/disease, population considerations, study design requirements.

2. **Comprehensive variant extraction:** query all associations for the trait, set significance threshold, note discovery and replication studies.

3. **Quality assessment:** review study sample sizes, check population diversity, assess heterogeneity across studies, identify potential biases.

4. **Data synthesis:** aggregate associations across studies, perform meta-analysis if applicable, create summary tables, generate Manhattan or forest plots.

5. **Export and documentation:** download full association data, export summary statistics if needed, document search strategy and date, create reproducible analysis scripts.

## Workflow 5: Accessing and Analyzing Summary Statistics

1. **Identify studies with summary statistics:** `GET /v2/studies?efo_id=<id>&full_pvalue_set=true`; each study's `full_summary_stats` field is its FTP directory. The nightly `harmonised_list.txt` on the FTP site lists every harmonised file.

2. **Download summary statistics:**
   ```bash
   # Harmonised GWAS-SSF file (directories are bucketed in ranges of 1,000 accessions)
   wget https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90475001-GCST90476000/GCST90475667/harmonised/GCST90475667.h.tsv.gz
   ```

3. **Query a region without downloading everything** (the Summary Statistics API is retired, HTTP 410):
   ```bash
   tabix -h https://ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/GCST90475001-GCST90476000/GCST90475667/harmonised/GCST90475667.h.tsv.gz 10:112900000-113200000
   ```

4. **Process and analyze:** filter by p-value thresholds, extract effect sizes and confidence intervals, perform downstream analyses (fine-mapping, colocalization, etc.).

## Web Interface Search Modes

The web interface at https://www.ebi.ac.uk/gwas/ supports multiple search modes:

**By Variant (rs ID):** `rs7903146` — returns all trait associations for this SNP.

**By Disease/Trait:** `type 2 diabetes`, `Parkinson disease`, `body mass index` — returns all associated genetic variants.

**By Gene:** `APOE`, `TCF7L2` — returns variants in or near the gene region.

**By Chromosomal Region:** `10:114000000-115000000` — returns variants in the specified genomic interval.

**By Publication:** `PMID:20581827`, `Author: McCarthy MI`, `GCST001234` — returns study details and all reported associations.
