# InterPro Domain Analysis Reference

## Entry Types

| Type | Description | Example |
|------|-------------|---------|
| `family` | Group of related proteins sharing common evolutionary origin | IPR002117: p53 tumour suppressor family |
| `domain` | Distinct structural/functional unit that can exist independently | IPR010991: p53, tetramerisation domain |
| `homologous_superfamily` | Proteins related by structure but not necessarily sequence | IPR009003: Peptidase S1, PA clan |
| `repeat` | Short sequence unit that occurs in multiple copies | IPR002110: Ankyrin repeat |
| `site` | Parent category for the functional-site types below | (see subtypes) |
| `conserved_site` | Conserved sequence motif (functional) | IPR000047: Helix-turn-helix motif |
| `active_site` | Catalytic residues | IPR000169: Cysteine peptidase, cysteine active site |
| `binding_site` | Residues involved in binding | IPR000048: IQ motif, EF-hand binding site |
| `ptm` | Post-translational modification site | IPR000152: EGF-type aspartate/asparagine hydroxylation site |

## Common Domain Accessions

### Signaling Domains

| Accession | Name | Function |
|-----------|------|---------|
| IPR000719 | Protein kinase domain | ATP-dependent phosphorylation |
| IPR001245 | Serine-threonine/tyrosine-protein kinase | Kinase catalytic domain |
| IPR000980 | SH2 domain | Phosphotyrosine binding |
| IPR001452 | SH3 domain | Proline-rich sequence binding |
| IPR011993 | PH domain | Phosphoinositide binding |
| IPR000048 | IQ motif | Calmodulin binding |
| IPR000008 | C2 domain | Ca2+/phospholipid binding |
| IPR001849 | PH domain | Pleckstrin homology |

### DNA Binding Domains

| Accession | Name | Function |
|-----------|------|---------|
| IPR013087 | Zinc finger C2H2-type | DNA binding |
| IPR000571 | Zinc finger, CCCH-type | RNA binding |
| IPR036388 | Winged helix-like DNA-binding domain superfamily | Transcription factor DNA binding |
| IPR036578 | SMAD MH1 domain superfamily | SMAD DNA binding |
| IPR001606 | ARID DNA-binding domain | AT-rich DNA binding |
| IPR000679 | Zinc finger, GATA-type | DNA binding (GATA TFs) |

### Structural Domains

| Accession | Name | Function |
|-----------|------|---------|
| IPR001357 | BRCT domain | DNA repair protein interaction |
| IPR000536 | Nuclear hormone receptor, ligand-binding | Hormone binding |
| IPR001628 | Zinc finger, nuclear hormone receptor | DNA binding (NHR) |
| IPR003961 | Fibronectin type III | Cell adhesion |
| IPR000742 | EGF-like domain | Receptor-ligand interaction |

## Domain Architecture Patterns

Common multi-domain architectures and their biological meanings:

### Receptor Tyrosine Kinases
```
[EGF domain]... - [TM] - [Kinase domain]
e.g., EGFR: IPR000742 (EGF) + IPR000719 (kinase)
```

### Adapter Proteins
```
[SH3] - [SH2] - [SH3]
e.g., Grb2, Crk — signaling adapters
```

### Nuclear Receptors
```
[DBD/C2H2 zinc finger] - [Ligand binding domain]
e.g., ERα (ESR1)
```

### Kinases
```
[N-lobe] - [Activation loop] - [C-lobe]
Standard protein kinase fold (IPR000719)
```

## GO Term Categories

InterPro GO annotations use three ontologies:

| Code | Ontology | Examples |
|------|----------|---------|
| P | Biological Process | GO:0006468 (protein phosphorylation) |
| F | Molecular Function | GO:0004672 (protein kinase activity) |
| C | Cellular Component | GO:0005886 (plasma membrane) |

## InterProScan for Novel Sequences

For protein sequences not in UniProt (novel/predicted sequences), run InterProScan:

```bash
# Command-line (install InterProScan locally)
./interproscan.sh -i my_proteins.fasta -f tsv,json -dp

# Options:
# -i: input FASTA
# -f: output formats (tsv, json, xml, gff3, html)
# -dp: disable precalculation lookup (use for non-UniProt sequences)
# --goterms: include GO term mappings
# --pathways: include pathway mappings

# Or use the web service:
# https://www.ebi.ac.uk/interpro/search/sequence/
```

**Output fields (TSV):**
1. Protein accession
2. Sequence MD5
3. Sequence length
4. Analysis (e.g., Pfam, SMART)
5. Signature accession (e.g., PF00397)
6. Signature description
7. Start
8. Stop
9. Score
10. Status (T = true)
11. Date
12. InterPro accession (if integrated)
13. InterPro description

## Useful Entry ID Collections

### Human Disease-Relevant Domains

```python
# Names/types verified against the InterPro entry endpoint.
DISEASE_DOMAINS = {
    # Cancer
    "IPR011615": "p53, DNA-binding domain",
    "IPR012346": "p53/RUNT-type transcription factor, DNA-binding domain superfamily",
    "IPR000719": "Protein kinase domain",
    "IPR004827": "Basic-leucine zipper domain",

    # Neurodegenerative
    "IPR003527": "Mitogen-activated protein (MAP) kinase, conserved site",
    "IPR016024": "Armadillo-type fold",

    # Metabolic
    "IPR001764": "Glycoside hydrolase, family 3, N-terminal",
    "IPR006047": "Glycosyl hydrolase family 13, catalytic domain",
}
```

### Commonly Referenced Pfam IDs

| Pfam ID | Domain Name |
|---------|-------------|
| PF00069 | Pkinase (protein kinase) |
| PF00076 | RRM_1 (RNA recognition motif) |
| PF00096 | zf-C2H2 (zinc finger) |
| PF00397 | WW domain |
| PF00400 | WD40 repeat (WD domain, G-beta repeat) |
| PF00415 | RCC1 repeat (regulator of chromosome condensation) |
| PF00018 | SH3 domain (SH3_1) |
| PF00017 | SH2 domain |
| PF00097 | zf-C3HC4 (RING finger) |
