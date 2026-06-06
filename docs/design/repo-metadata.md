<div align="center">

# 🏷️ Repo Metadata — GitHub Discovery

<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills"><img src="https://img.shields.io/badge/Repo-AlterLab--Academic--Skills-8B5CF6?style=for-the-badge&logo=github&logoColor=white" alt="Repo"></a>
<a href="https://alterlab-ieu.github.io/AlterLab-Academic-Skills/"><img src="https://img.shields.io/badge/Pages-Live-0EA5E9?style=for-the-badge&logo=githubpages&logoColor=white" alt="Pages"></a>

<p><em>Canonical description, topics, homepage, and the exact <code>gh</code> commands to apply them.</em></p>

</div>

<br>

## 📝 Repository description

> 183 evaluated academic Claude/agent skills across 13 research domains — bioinformatics, cheminformatics, data science, databases, clinical & more. Every skill ships an executable eval (agentskills.io schema). Deterministic citation verifier + research→write→review→publish pipeline. Works in Claude Code, Cursor, Codex, Gemini CLI & Copilot.

<sub>341 characters (under GitHub's 350 cap). Leads with **183 evaluated academic Claude/agent skills**; every claim is grounded in `skills.json` (`summary.total = 183`, `summary.eval_coverage = 183/183`, 13 domains) and `CHANGELOG.md` `[2.0.0]`.</sub>

<br>

## 🏷️ Topics (exactly 20)

All lowercase-kebab, ordered by discovery value. Anchored in the suite's real domains (`skills.json` `summary.per_domain`) and ecosystem.

<div align="center">

| # | Topic | Why it surfaces the repo |
|:---:|:---|:---|
| 1 | `claude` | Primary platform — searched constantly |
| 2 | `claude-skills` | Exact category of this artifact |
| 3 | `agent-skills` | The open [agentskills.io](https://agentskills.io) standard this conforms to |
| 4 | `anthropic` | Vendor namespace |
| 5 | `claude-code` | Plugin marketplace target |
| 6 | `llm-agents` | Broad agent-tooling discovery |
| 7 | `academic-research` | Core audience intent |
| 8 | `research-tools` | Real domain (14 skills) + generic search term |
| 9 | `scientific-computing` | Cross-domain umbrella for the corpus |
| 10 | `bioinformatics` | Largest scientific domain (25 skills) |
| 11 | `cheminformatics` | Real domain (12 skills) |
| 12 | `data-science` | Real domain (22 skills) |
| 13 | `clinical-research` | Real domain (7 skills) |
| 14 | `data-visualization` | Real domain (8 skills) |
| 15 | `scientific-writing` | Writing-tools domain (13 skills) |
| 16 | `model-context-protocol` | Bundled academic MCP (`.mcp.json`) |
| 17 | `reproducible-research` | Evals + provenance + figure-stamp positioning |
| 18 | `citation` | Headline deterministic citation verifier |
| 19 | `prompt-engineering` | High-traffic adjacent discovery term |
| 20 | `turkish-academia` | Maintainer/audience niche (EN/TR parity) |

</div>

<br>

## 🌐 Homepage

```
https://alterlab-ieu.github.io/AlterLab-Academic-Skills/
```

<sub>Served by the static site at `docs/site/index.html`, published via `.github/workflows/gh-pages.yml`.</sub>

<br>

## ⚙️ Apply it all with `gh`

> [!NOTE]
> Run from a clone authenticated against `AlterLab-IEU`. These are **additive** metadata edits — they touch repo settings only, not the tree.

### 1 — Description, homepage & 20 topics

```bash
REPO="AlterLab-IEU/AlterLab-Academic-Skills"

gh repo edit "$REPO" \
  --description "183 evaluated academic Claude/agent skills across 13 research domains — bioinformatics, cheminformatics, data science, databases, clinical & more. Every skill ships an executable eval (agentskills.io schema). Deterministic citation verifier + research→write→review→publish pipeline. Works in Claude Code, Cursor, Codex, Gemini CLI & Copilot." \
  --homepage "https://alterlab-ieu.github.io/AlterLab-Academic-Skills/" \
  --add-topic claude \
  --add-topic claude-skills \
  --add-topic agent-skills \
  --add-topic anthropic \
  --add-topic claude-code \
  --add-topic llm-agents \
  --add-topic academic-research \
  --add-topic research-tools \
  --add-topic scientific-computing \
  --add-topic bioinformatics \
  --add-topic cheminformatics \
  --add-topic data-science \
  --add-topic clinical-research \
  --add-topic data-visualization \
  --add-topic scientific-writing \
  --add-topic model-context-protocol \
  --add-topic reproducible-research \
  --add-topic citation \
  --add-topic prompt-engineering \
  --add-topic turkish-academia
```

> [!TIP]
> To set the topic list **authoritatively** (replacing whatever is there with exactly these 20), use the topics API instead of `--add-topic`:
>
> ```bash
> gh api -X PUT "repos/$REPO/topics" \
>   -H "Accept: application/vnd.github+json" \
>   -f names[]=claude -f names[]=claude-skills -f names[]=agent-skills \
>   -f names[]=anthropic -f names[]=claude-code -f names[]=llm-agents \
>   -f names[]=academic-research -f names[]=research-tools -f names[]=scientific-computing \
>   -f names[]=bioinformatics -f names[]=cheminformatics -f names[]=data-science \
>   -f names[]=clinical-research -f names[]=data-visualization -f names[]=scientific-writing \
>   -f names[]=model-context-protocol -f names[]=reproducible-research -f names[]=citation \
>   -f names[]=prompt-engineering -f names[]=turkish-academia
> ```

### 2 — Enable GitHub Pages from the Actions workflow

The site is published by `.github/workflows/gh-pages.yml`, so Pages must be in **workflow** build mode (not legacy branch mode):

```bash
# Create the Pages site in Actions/workflow build mode:
gh api -X POST "repos/$REPO/pages" \
  -H "Accept: application/vnd.github+json" \
  -f build_type=workflow

# If Pages already exists, switch it to workflow mode instead:
gh api -X PUT "repos/$REPO/pages" \
  -H "Accept: application/vnd.github+json" \
  -f build_type=workflow
```

### 3 — Verify

```bash
gh repo view "$REPO" --json description,homepageUrl,repositoryTopics
gh api "repos/$REPO/pages" --jq '{status, html_url, build_type}'
```

Expected: description set, `homepageUrl` = the Pages URL, exactly 20 topics, and `build_type: "workflow"`.

<br>

<div align="center">

<sub>Grounded in <code>skills.json</code>, <code>CHANGELOG.md</code> <code>[2.0.0]</code>, and <code>.github/workflows/gh-pages.yml</code> · AlterLab Creative Technologies Laboratory</sub>

</div>
