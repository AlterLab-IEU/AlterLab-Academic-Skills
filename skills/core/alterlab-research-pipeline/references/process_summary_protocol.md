# Stage 6: Process Summary Protocol (v2.4) — Full Detail

Complete workflow, required content, and the mandatory Collaboration Quality Evaluation for the post-pipeline "Paper Creation Process Record," summarized in SKILL.md.

## Stage 6: Process Summary Protocol (Added in v2.4)

**Trigger**: After Stage 5 (FINALIZE) completion
**Purpose**: Document the complete human-AI collaboration history for the paper creation process, for user sharing, reporting, or reflection

### Workflow

```
1. Ask user language preference:
   "Which language version of the process record would you like to generate first?"
   - Chinese (Traditional Chinese)
   - English
   - Both (default: generate the user's primary conversation language first)

2. Review session history and compile the following:
   - User's initial instructions (verbatim quote)
   - Key decision points and user interventions at each stage
   - Direction correction moments and reasons
   - Iteration count and review result summaries
   - Intellectual insights raised by the user (e.g., questions that spawned new chapters)
   - Quality requirement evolution (e.g., formatting, tone adjustments)
   - Pipeline statistics (stage count, review rounds, integrity verification count, etc.)

3. Generate Markdown version (paper_creation_process.md / paper_creation_process_en.md)

4. Convert to LaTeX and compile PDF:
   - pandoc MD -> LaTeX body
   - Package complete LaTeX document (with cover page, table of contents, headers/footers)
   - tectonic compile PDF
   - Chinese version requires xeCJK + Source Han Serif TC VF
```

### Required Content in Process Record

| Section | Content |
|---------|---------|
| Paper Information | Title, final deliverables list |
| Stage-by-Stage Process | Input/output/key decisions for each stage, with verbatim user quotes |
| Iteration Details | Review comment summaries, revision items, re-review results |
| Interaction Pattern Summary | User role, Claude role, intervention count, key turning points — statistics table |
| User Key Decisions | Chronological list of every important decision made by the user |
| Key Lessons | Reusable lessons learned from the process |
| **Collaboration Quality Evaluation** | **Final chapter: 1-100 score + dimensional analysis + improvement suggestions** (see below) |

### Collaboration Quality Evaluation (Final Chapter, Mandatory)

The final chapter of the process record is a "Collaboration Quality Evaluation" that honestly and constructively assesses the user's performance in the human-AI collaboration. Format follows the Claude Code CLI `/insight` feature.

#### Scoring Dimensions (each 1-100, weighted average for overall score)

```
+--------------------------------------------------+
|  Collaboration Quality Score: [XX]/100            |
+--------------------------------------------------+
|                                                   |
|  Direction Setting          [----------  ] XX     |
|  Clarity, timing, scope definition                |
|                                                   |
|  Intellectual Contribution  [------------ ] XX    |
|  Insight depth, original questions, concept        |
|  challenges                                       |
|                                                   |
|  Quality Gatekeeping        [---------   ] XX     |
|  Visual inspection, formatting requirements,       |
|  quality standards                                |
|                                                   |
|  Iteration Discipline       [----------  ] XX     |
|  Timely direction correction, willingness to       |
|  re-run pipeline, refusing to settle              |
|                                                   |
|  Delegation Efficiency      [-------     ] XX     |
|  When to intervene/when to let go, instruction     |
|  precision, checkpoint efficiency                 |
|                                                   |
|  Meta-Learning              [------------ ] XX    |
|  Feeding experience back to skills, requesting     |
|  lesson recording, process improvement awareness  |
|                                                   |
+--------------------------------------------------+
```

#### Scoring Criteria

| Score Range | Meaning |
|------------|---------|
| 90-100 | Exceptional — User intervention significantly elevated the paper's intellectual quality beyond what AI could produce independently |
| 75-89 | Excellent — User made correct directional decisions and effectively leveraged the pipeline's iteration capabilities |
| 60-74 | Good — User completed necessary decisions but some opportunities were missed |
| 40-59 | Basic — User primarily served as a "continue" button with little substantive intervention |
| 1-39 | Needs Improvement — User intervention may have disrupted the workflow or lacked critical quality gatekeeping |

#### Required Subsections

1. **Overall Score**: Total score + one-sentence evaluation
2. **What Worked Well**: 2-4 specific behaviors, with verbatim user quotes
3. **Missed Opportunities**: 1-3 things the user could have done but didn't
4. **Recommendations for Next Time**: 3-5 specific, actionable improvement suggestions
5. **Human vs AI Value-Add**: Clearly identify which aspects of the final paper quality came from user intervention (not achievable by AI independently)

#### Evaluation Principles

- **Honesty first**: No inflation, no pleasantries. If the user only pressed "continue," reflect that truthfully
- **Evidence-based**: Every score is supported by specific behaviors or conversation records
- **Constructive**: Every criticism must include actionable improvement suggestions
- **Acknowledge uncertainty**: If certain dimensions cannot be evaluated (e.g., mid-entry skipped the research stage), mark as N/A
- **Bidirectional reflection**: Also candidly point out Claude's shortcomings during the process (e.g., areas requiring multiple corrections)

### Output Specifications

- **Filename**: `paper_creation_process.md` (Chinese) / `paper_creation_process_en.md` (English)
- **PDF**: `paper_creation_process_zh.pdf` / `paper_creation_process_en.pdf`
- **LaTeX template**: `article` class, 12pt, A4, Times New Roman + Source Han Serif TC VF
- **Includes table of contents**: `\tableofcontents`
- **Header**: left = document title (italic), right = date
- **Compilation**: tectonic (same toolchain as Stage 5)
