# Repository Structure

Layout of the upstream `hypothesis-generation` repository and what each directory holds.

Understanding the repository layout:

```
hypothesis-generation/
├── hypogenic/              # Core package code
├── hypogenic_cmd/          # CLI entry points
├── hypothesis_agent/       # HypoRefine agent framework
├── literature/            # Literature processing utilities
├── modules/               # GROBID and preprocessing modules
├── examples/              # Example scripts
│   ├── generation.py      # Basic HypoGeniC generation
│   ├── union_generation.py # HypoRefine/Union generation
│   ├── inference.py       # Single hypothesis inference
│   ├── multi_hyp_inference.py # Multiple hypothesis inference
│   └── pdf_preprocess.py  # Literature PDF processing
├── data/                  # Example datasets (clone separately)
├── tests/                 # Unit tests
└── IO_prompting/          # Prompt templates and experiments
```

**Key directories:**
- **hypogenic/**: Main package with BaseTask and generation logic
- **examples/**: Reference implementations for common workflows
- **literature/**: Tools for PDF processing and literature extraction
- **modules/**: External tool integrations (GROBID, etc.)
