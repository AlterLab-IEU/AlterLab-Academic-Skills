# LabArchives Third-Party Integrations

## Overview

LabArchives integrates with numerous scientific software platforms to streamline research workflows. This document covers programmatic integration approaches, automation strategies, and best practices for each supported platform.

## Integration Categories

The programmatic examples below use `labapi` (PyPI, `uv pip install "labapi[dotenv]"`, Python >= 3.10), which signs requests and handles pages, entries, and attachments. Shared setup:

```python
import os
from labapi import Attachment, AttachmentEntry, Client, HeaderEntry, TextEntry

client = Client()  # API_URL, ACCESS_KEYID, ACCESS_PWD from the environment or .env
user = client.login(os.environ["LA_EMAIL"], os.environ["LA_APP_TOKEN"])  # "LA App authentication" token
notebook = user.notebooks["Lab Notebook"]

def attach(page, path):
    """Upload a local file as an attachment entry on a page."""
    return page.entries.create(AttachmentEntry, Attachment.from_file(path))
```

The raw API equivalents are `tree_tools/insert_node` (new page), `entries/add_entry` (text), and `entries/add_attachment` (file) — see `api_reference.md`. Entry comments are not covered by either Python client.

### 1. Protocol Management

#### Protocols.io Integration

Export protocols directly from Protocols.io to LabArchives notebooks.

**Use cases:**
- Standardize experimental procedures across lab notebooks
- Maintain version control for protocols
- Link protocols to experimental results

**Setup:**
1. Enable Protocols.io integration in LabArchives settings
2. Authenticate with Protocols.io account
3. Browse and select protocols to export

**Programmatic approach:**
```python
# Export Protocols.io protocol as HTML/PDF
# Then upload to LabArchives via API

def import_protocol_to_labarchives(page, protocol_id):
    """Record a protocols.io protocol on a LabArchives page"""
    # 1. Fetch the protocol (v4 API) with your protocols.io token
    protocol = fetch_protocol_from_protocolsio(protocol_id)  # see the alterlab-protocolsio skill

    # 2. Header + protocol body as a rich-text entry
    page.entries.create(HeaderEntry, f"Protocol: {protocol['title']}")
    page.entries.create(TextEntry, protocol["html_content"])

    # 3. Provenance as its own entry (the API has no client-supported comment call)
    page.entries.create(TextEntry, f"<p>protocols.io DOI: {protocol['doi']}; version {protocol['version']}</p>")
```

**Updated:** September 22, 2025

### 2. Data Analysis Tools

#### GraphPad Prism Integration (Version 8+)

Export analyses, graphs, and figures directly from Prism to LabArchives.

**Use cases:**
- Archive statistical analyses with raw data
- Document figure generation for publications
- Maintain analysis audit trail for compliance

**Setup:**
1. Install GraphPad Prism 8 or higher
2. Configure LabArchives connection in Prism preferences
3. Use "Export to LabArchives" option from File menu

**Programmatic approach:**
```python
# Upload Prism files to LabArchives via API

def upload_prism_analysis(page, prism_file_path):
    """Upload a GraphPad Prism project (and its exported figures) to a page"""
    return attach(page, prism_file_path)
```

**Supported file types:**
- .pzfx (Prism project files)
- .png, .jpg, .pdf (exported graphs)
- .xlsx (exported data tables)

**Updated:** September 8, 2025

### 3. Molecular Biology & Bioinformatics

#### SnapGene Integration

Direct integration for molecular biology workflows, plasmid maps, and sequence analysis.

**Use cases:**
- Document cloning strategies
- Archive plasmid maps with experimental records
- Link sequences to experimental results

**Setup:**
1. Install SnapGene software
2. Enable LabArchives export in SnapGene preferences
3. Use "Send to LabArchives" feature

**File format support:**
- .dna (SnapGene files)
- .gb, .gbk (GenBank format)
- .fasta (sequence files)
- .png, .pdf (plasmid map exports)

**Programmatic workflow:**
```python
def upload_snapgene_file(page, snapgene_file, preview_png=None):
    """Upload a SnapGene file, plus an exported map image if you have one"""
    attach(page, snapgene_file)
    if preview_png:  # e.g. a PNG exported from SnapGene
        attach(page, preview_png)
```

#### Geneious Integration

Bioinformatics analysis export from Geneious to LabArchives.

**Use cases:**
- Archive sequence alignments and phylogenetic trees
- Document NGS analysis pipelines
- Link bioinformatics workflows to wet-lab experiments

**Supported exports:**
- Sequence alignments
- Phylogenetic trees
- Assembly reports
- Variant calling results

**File formats:**
- .geneious (Geneious documents)
- .fasta, .fastq (sequence data)
- .bam, .sam (alignment files)
- .vcf (variant files)

### 4. Computational Notebooks

#### Jupyter Integration

Embed Jupyter notebooks as LabArchives entries for reproducible computational research.

**Use cases:**
- Document data analysis workflows
- Archive computational experiments
- Link code, results, and narrative

**Workflow:**

```python
def export_jupyter_to_labarchives(page, notebook_path):
    """Export an executed Jupyter notebook to a LabArchives page"""
    import nbformat
    from nbconvert import HTMLExporter

    with open(notebook_path, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    body, _resources = HTMLExporter(template_name='classic').from_notebook_node(nb)

    page.entries.create(HeaderEntry, f"Jupyter Notebook: {os.path.basename(notebook_path)}")
    page.entries.create(TextEntry, body)   # rendered notebook
    attach(page, notebook_path)            # original .ipynb
```

**Best practices:**
- Export with outputs included (Run All Cells before export)
- Include environment.yml or requirements.txt as attachment
- Add execution timestamp and system info as a text entry on the same page

### 5. Clinical Research

#### REDCap Integration

Clinical data capture integration with LabArchives for research compliance and audit trails.

**Use cases:**
- Link clinical data collection to research notebooks
- Maintain audit trails for regulatory compliance
- Document clinical trial protocols and amendments

**Integration approach:**
- REDCap API exports data to LabArchives entries
- Automated data synchronization for longitudinal studies
- HIPAA-compliant data handling

**Example workflow:**
```python
def sync_redcap_to_labarchives(page, redcap_api_token):
    """Record a de-identified REDCap export on a LabArchives page"""
    from datetime import datetime

    redcap_data = fetch_redcap_data(redcap_api_token)  # de-identify before it leaves REDCap
    page.entries.create(HeaderEntry, f"REDCap export {datetime.now():%Y-%m-%d}")
    return page.entries.create(TextEntry, format_redcap_data_html(redcap_data))
```

Only move identifiable participant data into a notebook that your IRB/privacy office has approved for it.

**Compliance features:**
- 21 CFR Part 11 compliance
- Audit trail maintenance
- Data integrity verification

### 6. Research Publishing

#### Qeios Integration

Research publishing platform integration for preprints and peer review.

**Use cases:**
- Export research findings to preprint servers
- Document publication workflows
- Link published articles to lab notebooks

**Workflow:**
- Export formatted entries from LabArchives
- Submit to Qeios platform
- Maintain bidirectional links between notebook and publication

#### SciSpace Integration

Literature management and citation integration.

**Use cases:**
- Link references to experimental procedures
- Maintain literature review in notebooks
- Generate bibliographies for reports

**Features:**
- Citation import from SciSpace to LabArchives
- PDF annotation synchronization
- Reference management

## OAuth Authentication for Integrations

LabArchives offers OAuth 2.0 for newer third-party integrations, alongside the signed-request API-key flow this skill uses for direct API access.

The standard OAuth 2.0 authorization-code shape applies (request an authorization code, then exchange it with `client_id`/`client_secret` for an access + refresh token), but the **authorization and token endpoint URLs, scopes, and registration process are not documented here** — obtain them from LabArchives developer support for your region rather than guessing endpoint paths.

**Why OAuth over API keys, when available:**
- Fine-grained, revocable permission scopes
- Token refresh for long-running integrations
- No long-lived shared secret embedded in clients

## Custom Integration Development

### General Workflow

For tools not officially supported, develop custom integrations:

1. **Export data** from source application (API or file export)
2. **Transform format** to HTML or supported file type
3. **Authenticate** with LabArchives API
4. **Create entry** or upload attachment on the target page
5. **Add metadata** as a text entry for traceability

### Example: Custom Integration Template

```python
class LabArchivesIntegration:
    """Template for custom LabArchives integrations (labapi)"""

    def __init__(self, email, app_token, notebook_name):
        from labapi import Client
        self.client = Client()  # API_URL, ACCESS_KEYID, ACCESS_PWD from the environment
        self.user = self.client.login(email, app_token)
        self.notebook = self.user.notebooks[notebook_name]

    def export_data(self, source_data, page_path, title):
        """Write transformed data to a page, e.g. page_path='Experiments/2026/Run-12'"""
        from labapi import HeaderEntry, TextEntry
        page = self.notebook.traverse(page_path)
        page.entries.create(HeaderEntry, title)
        return page.entries.create(TextEntry, self._transform_to_html(source_data))

    def _transform_to_html(self, data):
        """Transform data to HTML format"""
        raise NotImplementedError

    def close(self):
        self.client.close()
```

## Integration Best Practices

1. **Version control:** Track which software version generated the data
2. **Metadata preservation:** Include timestamps, user info, and processing parameters
3. **File format standards:** Use open formats when possible (CSV, JSON, HTML)
4. **Batch operations:** Implement rate limiting for bulk uploads
5. **Error handling:** Implement retry logic with exponential backoff
6. **Audit trails:** Log all API operations for compliance
7. **Testing:** Validate integrations in test notebooks before production use

## Troubleshooting Integrations

### Common Issues

**Integration not appearing in LabArchives:**
- Verify integration is enabled by administrator
- Check OAuth permissions if using OAuth
- Ensure compatible software version

**File upload failures:**
- Verify the file is within your account's per-file size limit (confirm the current limit with your LabArchives administrator)
- Check file format compatibility
- Ensure sufficient storage quota

**Authentication errors:**
- Verify API credentials are current
- Check if integration-specific tokens have expired
- Confirm user has necessary permissions

### Integration Support

For integration-specific issues:
- Check software vendor documentation (e.g., GraphPad, Protocols.io)
- Contact LabArchives support: support@labarchives.com
- Review LabArchives knowledge base: help.labarchives.com

## Future Integration Opportunities

Potential integrations for custom development:
- Electronic data capture (EDC) systems
- Laboratory information management systems (LIMS)
- Instrument data systems (chromatography, spectroscopy)
- Cloud storage platforms (Box, Dropbox, Google Drive)
- Project management tools (Asana, Monday.com)
- Grant management systems

For custom integration development, contact LabArchives for API partnership opportunities.
