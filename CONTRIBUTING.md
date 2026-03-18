# Contributing to AlterLab Academic Skills

Thank you for your interest in contributing to AlterLab Academic Skills. This guide explains how to add new skills, submit changes, and maintain quality across the project.

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.

## How to Add a New Skill

### 1. Choose a Category

Skills must belong to one of the following categories:

| Category | Path | Description |
|----------|------|-------------|
| Core | `skills/core/` | Research, Write, Review, Publish pipeline |
| Databases | `skills/databases/` | Scientific database connectors |
| Bioinformatics | `skills/bioinformatics/` | Genomics, proteomics, molecular biology |
| Cheminformatics | `skills/cheminformatics/` | Chemistry, drug discovery |
| Clinical Research | `skills/clinical-research/` | Clinical decision support, medical tools |
| Data Science | `skills/data-science/` | ML, statistics, data analysis |
| Document Tools | `skills/document-tools/` | DOCX, PDF, PPTX, XLSX handling |
| Domain-Specific | `skills/domain-specific/` | Quantum, geospatial, materials science |
| Finance & Economics | `skills/finance-economics/` | Financial data and analysis |
| Lab Integrations | `skills/lab-integrations/` | Laboratory platform connectors |
| Research Tools | `skills/research-tools/` | Search, discovery, reference management |
| Visualization | `skills/visualization/` | Scientific plotting and graphics |
| Writing Tools | `skills/writing-tools/` | Scientific writing, citations, posters |

If your skill does not fit any existing category, open an issue to discuss adding a new one.

### 2. Naming Convention

- **Folder name**: `alterlab-{name}` (lowercase, hyphenated)
- **Examples**: `alterlab-blast`, `alterlab-pubmed`, `alterlab-r-stats`

### 3. Folder Structure

```
skills/{category}/alterlab-{name}/
  SKILL.md        # The skill definition (required)
  README.md       # Usage documentation (optional)
  examples/       # Example prompts and outputs (optional)
```

### 4. SKILL.md Template

Every skill must have a `SKILL.md` file with YAML frontmatter followed by the skill prompt content:

```markdown
---
name: "alterlab-{name}"
description: "One-line description of what the skill does."
version: "1.0"
license: "MIT"
metadata:
  skill-author: "AlterLab"
  category: "{category}"
  tags:
    - tag1
    - tag2
---

# alterlab-{name}

Part of the AlterLab Academic Skills suite.

## Purpose

Describe what the skill does and who it is for.

## Instructions

The full system prompt / instructions for the skill go here.
```

**Required frontmatter fields:**

- `name` -- must match `alterlab-{name}` pattern
- `description` -- concise, one-line summary
- `version` -- semver format
- `license` -- must be `MIT`
- `metadata.skill-author` -- must be `AlterLab`
- `metadata.category` -- must match the parent folder name

## Pull Request Process

1. **Fork the repository** and create a feature branch from `main`.
2. **Follow the naming conventions** described above.
3. **Include a clear PR description** explaining:
   - What the skill does
   - Which category it belongs to
   - Any external APIs or services it depends on
4. **One skill per PR** unless the skills are closely related.
5. **Test your skill** before submitting:
   - Verify the YAML frontmatter parses correctly
   - Confirm the skill works as intended with Claude
   - Check for prompt injection vulnerabilities in any user-facing input handling
6. **Wait for review** -- a maintainer will review your PR and may request changes.

## Commit Convention

Follow the project commit convention:

- `feat: add {skill-name}` -- new skill
- `improve: {skill-name} -- {what changed}` -- skill enhancement
- `fix: {skill-name} -- {what was wrong}` -- bug fix
- `docs: update {what}` -- documentation changes
- `chore: {description}` -- project maintenance

## Testing Guidelines

- Validate YAML frontmatter syntax (no tabs, proper quoting)
- Test the skill prompt with Claude to verify it produces expected behavior
- Check that the skill does not request or expose sensitive information (API keys, credentials)
- Verify the skill handles edge cases gracefully (empty input, malformed data)
- Review for prompt injection risks -- skills should not blindly pass untrusted user input into sensitive operations

## Modifying Existing Skills

- Bump the `version` field in the frontmatter
- Describe the change in your commit message using the `improve:` prefix
- If the change is a breaking modification to the skill's behavior, note it in the PR description

## Reporting Issues

Open a GitHub issue with:

- The skill name and category
- Steps to reproduce the problem
- Expected vs. actual behavior
- Claude model version used (if relevant)

## Questions?

Open a discussion or issue on the repository. We welcome suggestions for new categories, skill improvements, and documentation enhancements.
