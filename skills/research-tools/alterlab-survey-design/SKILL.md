---
name: alterlab-survey-design
description: "Comprehensive survey and instrument design assistant supporting questionnaire construction, Likert scale design, question types (open/closed/matrix), response bias mitigation, sampling strategies (probability/non-probability), pilot testing, instrument validation (Cronbach's alpha, factor analysis), online survey tools (Qualtrics, REDCap, Google Forms), interview protocol development, focus group facilitation, mixed-mode surveys, and cultural adaptation of instruments. Use when designing a survey or questionnaire, building Likert scales, planning a sampling strategy, pilot testing, validating an instrument (Cronbach's alpha, factor analysis), developing an interview protocol, improving response rates, or working in Qualtrics or REDCap. For analyzing interview/focus-group data use alterlab-qualitative-methods; for qual+quant integration alterlab-mixed-methods; for test selection/power analysis alterlab-statistical-analysis; for IRB/consent alterlab-research-ethics. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read WebFetch WebSearch Bash(python:*)
compatibility: No API key required. Guidance-focused skill; uses WebFetch/WebSearch and optional Python helpers via `uv run python`.
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-03-18"
---

# Survey Design — Survey & Instrument Design Agent

A comprehensive survey and instrument design tool for faculty and researchers. Covers the full lifecycle of survey-based research: from construct definition and item writing through pilot testing, validation, deployment, and analysis of survey data.

## Overview

Survey research is one of the most widely used methods across social sciences, health sciences, education, and business. Despite its apparent simplicity, designing a valid and reliable survey instrument requires systematic attention to construct definition, item wording, response format, sampling, bias mitigation, and psychometric validation.

This skill treats survey design as a scientific process, not an art. Every design decision should be justified and documented.

## When to Use This Skill

This skill should be used when:
- Designing a new survey or questionnaire from scratch
- Adapting an existing instrument for a new population or context
- Writing Likert-scale items or other structured response formats
- Developing interview protocols or focus group guides
- Planning sampling strategies for survey research
- Conducting pilot tests and cognitive interviews
- Validating instruments (reliability and validity analysis)
- Selecting online survey platforms (Qualtrics, REDCap, Google Forms)
- Improving response rates and reducing bias
- Conducting cultural adaptation and translation of instruments
- Teaching research methods courses that include survey design

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Qualitative data analysis (coding, themes, focus group/interview analysis) | `alterlab-qualitative-methods` |
| Integrating qual + quant strands (convergent/sequential designs, joint displays) | `alterlab-mixed-methods` |
| Hypothesis-test selection, assumption checks, power analysis beyond validation | `alterlab-statistical-analysis` |
| Specialized social-science methods (Delphi, Q-methodology, QCA) | `alterlab-social-science-methods` |
| Writing the research paper | `alterlab-paper-writer` |
| Ethics/IRB applications, informed consent for survey research | `alterlab-research-ethics` |

---

## Core Capabilities

### 1. Survey Design Process

**The 10-Step Survey Design Framework:**

```
Step 1:  Define research objectives and constructs
         What do you want to measure? What are your research questions?
              │
Step 2:  Review existing instruments
         Has someone already validated an instrument for your construct?
              │
Step 3:  Define the target population and sampling frame
         Who will you survey? How will you reach them?
              │
Step 4:  Choose survey mode
         Online, paper, phone, in-person, mixed-mode?
              │
Step 5:  Write items and response options
         Craft questions that are clear, unambiguous, and aligned to constructs
              │
Step 6:  Design survey structure and flow
         Organize sections, add skip logic, manage survey length
              │
Step 7:  Expert review
         Subject matter experts and methodologists evaluate the instrument
              │
Step 8:  Cognitive interviews and pilot testing
         Test with a small sample from the target population
              │
Step 9:  Psychometric validation
         Reliability analysis, factor analysis, validity assessment
              │
Step 10: Deploy, monitor, and analyze
         Launch survey, track response rates, clean and analyze data
```

### 2. Construct Definition and Operationalization

Before writing a single item, define what you are measuring.

**Construct Mapping Template:**

```markdown
## Construct Map

### Construct: [Name]
### Definition: [Precise conceptual definition with citation]

### Dimensions/Facets:
1. [Dimension 1] — [Definition]
   - Indicators: [Observable behaviors or attitudes]
   - Example items: [Draft items]

2. [Dimension 2] — [Definition]
   - Indicators: [Observable behaviors or attitudes]
   - Example items: [Draft items]

3. [Dimension 3] — [Definition]
   - Indicators: [Observable behaviors or attitudes]
   - Example items: [Draft items]

### Related but Distinct Constructs:
- [Construct A] — How it differs from your construct
- [Construct B] — How it differs from your construct

### Nomological Network:
- Should correlate positively with: [Constructs]
- Should correlate negatively with: [Constructs]
- Should be unrelated to: [Constructs]
```

### 3. Item Writing

#### Question Types and When to Use Them

| Type | Format | Best For | Example |
|------|--------|----------|---------|
| Closed-ended (single choice) | Radio buttons | Mutually exclusive categories | "What is your highest degree? ( ) Bachelor's ( ) Master's ( ) Doctoral" |
| Closed-ended (multiple choice) | Checkboxes | Non-mutually exclusive categories | "Which tools do you use? [ ] Qualtrics [ ] REDCap [ ] Google Forms" |
| Likert scale | Rating scale | Attitudes, perceptions, frequency | "I feel confident using statistics: Strongly Disagree 1 2 3 4 5 Strongly Agree" |
| Semantic differential | Bipolar scale | Evaluative judgments | "The training was: Useless ___:___:___:___:___ Useful" |
| Ranking | Drag-and-drop or numbered | Forced prioritization | "Rank these factors from most to least important: ___" |
| Matrix/Grid | Likert items in table | Multiple items with same response scale | [See matrix example below] |
| Open-ended | Text box | Exploratory, rich responses | "What challenges do you face in your research?" |
| Numeric | Number input | Precise quantities | "How many publications do you have? ___" |
| Visual analog scale (VAS) | Slider | Continuous measurement | "Rate your pain: No pain |------●------| Worst pain" |

#### Likert Scale Design

**Number of Points:**

| Points | Pros | Cons | Use When |
|--------|------|------|----------|
| 4-point | Forces a choice (no midpoint) | May frustrate genuinely neutral respondents | You want to avoid social desirability midpoint clustering |
| 5-point | Most common; well-understood | Central tendency bias; midpoint ambiguity | Standard attitudinal measurement |
| 6-point | Forced choice with more granularity | Less familiar to respondents | You want to force direction with more options |
| 7-point | Greater discrimination; better for factor analysis | May exceed respondents' discriminative capacity | Established psychometric instruments; research contexts |

**Likert Scale Labeling:**

```
FULLY LABELED (recommended for clarity):
Strongly Disagree | Disagree | Neutral | Agree | Strongly Agree

END-ANCHORED ONLY (acceptable for experienced respondents):
Strongly Disagree | 2 | 3 | 4 | Strongly Agree

AGREEMENT:        Strongly Disagree → Strongly Agree
FREQUENCY:        Never → Always
IMPORTANCE:       Not at all Important → Extremely Important
SATISFACTION:     Very Dissatisfied → Very Satisfied
LIKELIHOOD:       Very Unlikely → Very Likely
QUALITY:          Very Poor → Excellent
```

#### Item Writing Rules

**DO:**
1. Use simple, clear language (avoid jargon, acronyms, technical terms unless your population uses them)
2. Ask about one thing per item (no double-barreled questions)
3. Use specific time frames ("In the past 30 days..." not "Do you ever...")
4. Match the response scale to the question stem
5. Include both positively and negatively worded items (with caution — see pitfalls)
6. Pilot test items with your target population
7. Write 2-3x more items than you need (expect to cut during validation)

**DO NOT:**
1. Use leading or loaded language ("Don't you agree that...")
2. Use double negatives ("How much do you disagree with not implementing...")
3. Assume knowledge ("Rate the effectiveness of the Delphi method" — respondent may not know it)
4. Use absolutes ("always," "never," "all," "none") unless measuring frequency
5. Create unnecessarily long items (aim for under 20 words per item)
6. Use hypothetical scenarios when asking about actual behavior

**Examples of Item Revisions:**

```
POOR: "How satisfied are you with the quality and timeliness of feedback?"
       (Double-barreled: quality AND timeliness)
FIX:  Item 1: "How satisfied are you with the quality of feedback you receive?"
      Item 2: "How satisfied are you with the timeliness of feedback you receive?"

POOR: "Students should not be required to not attend classes."
       (Double negative)
FIX:  "Class attendance should be mandatory."

POOR: "Do you agree that the new policy is beneficial?"
       (Leading — assumes the policy is beneficial)
FIX:  "The new policy has been beneficial to my work."
       (Neutral stem; let the Likert scale capture agreement/disagreement)

POOR: "Rate your teaching effectiveness." (1-5)
       (Socially desirable response; no reference frame)
FIX:  "In the past semester, how often did you use student feedback
       to modify your teaching?" (Never / Rarely / Sometimes / Often / Always)
```

### 4. Survey Structure and Flow

**Recommended Survey Organization:**

```markdown
## Survey Structure Template

### Page 1: Welcome and Consent
- Study title, purpose, estimated time
- Consent checkbox (mandatory before proceeding)
- Contact information for questions

### Page 2: Screening Questions (if applicable)
- Eligibility criteria
- Route ineligible respondents to end-of-survey message

### Page 3-N: Main Content Sections
- Group by topic/construct
- Progress bar visible
- Section headers with brief context
- Start with engaging, easy questions
- Place sensitive questions in the middle (after rapport, before fatigue)
- Use skip logic to hide irrelevant questions

### Page N+1: Demographics
- Place at the END (reduces dropout from sensitive questions early)
- Include only demographics you will actually analyze
- Provide "Prefer not to answer" option for sensitive items

### Final Page: Thank You
- Thank participant
- Provide debriefing information
- Share contact info for results
- Remind of withdrawal procedure
```

**Skip Logic Design:**

```
Q1: Do you supervise graduate students?
    ( ) Yes → Show Q2-Q5 (supervision questions)
    ( ) No  → Skip to Q6

Q3: How many students do you currently supervise?
    [Number input]
    If Q3 > 5 → Show Q4 (workload management question)
    If Q3 ≤ 5 → Skip to Q5

Q10: Would you like to participate in a follow-up interview?
     ( ) Yes → Show Q11 (contact information)
     ( ) No  → Skip to end
```

### 5. Sampling Strategies

**Probability Sampling (every member of population has a known, non-zero chance of selection):**

| Method | How It Works | Pros | Cons |
|--------|-------------|------|------|
| Simple random | Select randomly from complete list | Unbiased, generalizable | Requires complete sampling frame |
| Systematic | Select every kth element from list | Easy to implement | Periodicity risk if list has pattern |
| Stratified | Divide population into strata, then random sample within each | Ensures representation of subgroups | Requires knowledge of population characteristics |
| Cluster | Randomly select clusters (schools, hospitals), then sample within | Practical when no individual-level list exists | Higher sampling error than SRS |
| Multi-stage | Combine methods (e.g., cluster then stratified) | Flexible, practical for large populations | Complex to implement and analyze |

**Non-Probability Sampling (no guarantee of representativeness):**

| Method | How It Works | Pros | Cons |
|--------|-------------|------|------|
| Convenience | Recruit whoever is available | Fast, cheap | Not generalizable; strong bias |
| Purposive | Select participants based on specific criteria | Targets relevant subgroups | Researcher bias in selection |
| Snowball | Existing participants recruit others | Access to hard-to-reach populations | Biased toward connected individuals |
| Quota | Set quotas for subgroups, then convenience sample within | Ensures diversity on key dimensions | Not truly random within quotas |

**Sample Size Determination:**

```
For descriptive surveys (estimating proportions):
n = (Z² × p × (1-p)) / E²

Where:
  Z = Z-score for confidence level (1.96 for 95%)
  p = Expected proportion (use 0.5 if unknown — most conservative)
  E = Margin of error (e.g., 0.05 for ±5%)

Example: 95% confidence, 5% margin of error, unknown proportion
n = (1.96² × 0.5 × 0.5) / 0.05² = 384.16 → 385 respondents

Adjust for finite population:
n_adj = n / (1 + (n-1)/N)
Where N = population size

Adjust for expected response rate:
n_needed = n_adj / expected_response_rate
Example: 385 / 0.30 = 1,284 invitations needed for 30% response rate
```

**For comparative surveys (detecting differences between groups):**

```python
# Power analysis for two-group comparison
from scipy import stats
import numpy as np

def sample_size_two_groups(effect_size, alpha=0.05, power=0.80):
    """
    Calculate sample size per group for independent samples t-test.

    effect_size: Cohen's d (0.2=small, 0.5=medium, 0.8=large)
    alpha: significance level
    power: desired statistical power
    """
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n))

# Examples (normal approximation; exact noncentral-t values are ~1 larger:
# 394 / 64 / 26 — use statsmodels TTestIndPower for the exact figures)
print(f"Small effect (d=0.2):  {sample_size_two_groups(0.2)} per group")   # 393
print(f"Medium effect (d=0.5): {sample_size_two_groups(0.5)} per group")   # 63
print(f"Large effect (d=0.8):  {sample_size_two_groups(0.8)} per group")   # 25
```

### 6. Response Bias Mitigation

| Bias Type | Definition | Mitigation Strategies |
|-----------|-----------|----------------------|
| Social desirability | Respondents answer in ways they believe are socially acceptable | Anonymous data collection; indirect questioning; validated social desirability scales (e.g., Marlowe-Crowne) |
| Acquiescence | Tendency to agree with statements regardless of content | Mix positively and negatively worded items; use forced-choice formats |
| Central tendency | Tendency to select middle response options | Use even-point scales (no midpoint); provide behavioral anchors |
| Extreme responding | Tendency to select extreme endpoints | Use more response options (7-point); provide clear anchor descriptions |
| Order effects | Earlier questions influence responses to later questions | Randomize item order within sections; counterbalance across respondents |
| Nonresponse bias | Systematic differences between responders and non-responders | Follow-up reminders; analyze early vs. late responders; compare demographics to population |
| Recall bias | Inaccurate recall of past events | Use shorter recall periods; provide memory aids; use event-specific prompts |
| Common method bias | Inflated correlations due to same measurement method | Use different measurement methods; temporal separation; marker variables |

### 7. Pilot Testing

**Three-Phase Pilot Testing Protocol:**

```markdown
## Phase 1: Expert Review (n = 3-5 experts)

### Content Validity
- Do items adequately cover the construct?
- Are any important facets missing?
- Are items relevant to the target population?
- Content Validity Index (CVI): Rate each item as
  1 = Not relevant, 2 = Somewhat relevant, 3 = Quite relevant, 4 = Highly relevant
  Item-CVI = proportion of experts rating 3 or 4 (threshold: ≥ 0.78)
  Scale-CVI/Ave = mean of Item-CVIs (threshold: ≥ 0.90)

### Face Validity
- Do items appear to measure what they claim?
- Is the language clear and appropriate?
- Is the survey length reasonable?

---

## Phase 2: Cognitive Interviews (n = 5-10 from target population)

### Think-Aloud Protocol
"Please read each question out loud and tell me what you are thinking
as you decide on your answer."

### Probing Questions
- "What does [term] mean to you?"
- "How did you arrive at your answer?"
- "Was this question easy or difficult to answer? Why?"
- "Can you put this question in your own words?"
- "Is there anything confusing about this question?"
- "Would you change anything about this question?"

### Document
- Items that cause confusion or hesitation
- Items interpreted differently than intended
- Items where response options do not fit
- Suggested wording improvements
- Time to complete each section

---

## Phase 3: Quantitative Pilot (n = 30-50 from target population)

### Assess
- [ ] Completion rate and completion time
- [ ] Item-level missing data (flag items with >10% missing)
- [ ] Response distributions (flag items with >90% in one category)
- [ ] Internal consistency (Cronbach's alpha per subscale)
- [ ] Item-total correlations (flag items < 0.30)
- [ ] Inter-item correlations (flag pairs > 0.85 — redundancy)
- [ ] Open-ended feedback on survey experience
- [ ] Technical issues (display, skip logic, mobile compatibility)
```

### 8. Instrument Validation

#### Reliability

**Internal Consistency:**

```python
import pandas as pd
import numpy as np

def cronbachs_alpha(df):
    """
    Calculate Cronbach's alpha for a set of items.
    df: DataFrame where each column is an item and each row is a respondent.
    """
    n_items = df.shape[1]
    item_variances = df.var(axis=0, ddof=1)
    total_variance = df.sum(axis=1).var(ddof=1)

    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return alpha

# Example
data = pd.DataFrame({
    'item1': [4, 3, 5, 4, 3, 5, 4, 3, 2, 4],
    'item2': [3, 3, 4, 4, 2, 5, 4, 3, 3, 4],
    'item3': [4, 4, 5, 3, 3, 4, 5, 2, 3, 5],
    'item4': [3, 2, 4, 4, 3, 5, 4, 3, 2, 3],
})

alpha = cronbachs_alpha(data)
print(f"Cronbach's alpha: {alpha:.3f}")

# Interpretation:
# α ≥ 0.90  Excellent (but check for redundancy)
# 0.80 ≤ α < 0.90  Good
# 0.70 ≤ α < 0.80  Acceptable
# 0.60 ≤ α < 0.70  Questionable
# α < 0.60  Poor — revise items
```

**Item-Total Correlations:**

```python
def item_total_correlations(df):
    """Calculate corrected item-total correlations."""
    results = {}
    for col in df.columns:
        rest = df.drop(columns=col).sum(axis=1)
        corr = df[col].corr(rest)
        results[col] = round(corr, 3)
    return results

itc = item_total_correlations(data)
for item, corr in itc.items():
    flag = " ← REVIEW" if corr < 0.30 else ""
    print(f"  {item}: r = {corr}{flag}")
```

#### Validity

| Type | Question | Method |
|------|----------|--------|
| **Content validity** | Do items cover the construct adequately? | Expert review, CVI calculation |
| **Face validity** | Do items appear to measure the construct? | Target population review |
| **Construct validity** | Does the instrument measure the theoretical construct? | Factor analysis (EFA/CFA) |
| **Convergent validity** | Does it correlate with similar measures? | Correlation with established instruments (r > 0.50) |
| **Discriminant validity** | Is it distinct from different constructs? | Low correlation with theoretically unrelated measures (r < 0.30) |
| **Criterion validity (concurrent)** | Does it correlate with a current criterion? | Correlation with gold standard measured simultaneously |
| **Criterion validity (predictive)** | Does it predict a future outcome? | Correlation with criterion measured later |
| **Known-groups validity** | Can it distinguish groups known to differ? | Compare scores between groups that should differ |

**Exploratory Factor Analysis (EFA):**

```python
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo

# Check suitability for factor analysis
chi_square, p_value = calculate_bartlett_sphericity(data)
print(f"Bartlett's test: χ² = {chi_square:.2f}, p = {p_value:.4f}")
# p < 0.05 → suitable for factor analysis

kmo_all, kmo_model = calculate_kmo(data)
print(f"KMO: {kmo_model:.3f}")
# KMO > 0.60 → suitable; > 0.80 → good; > 0.90 → excellent

# Determine number of factors (parallel analysis)
fa = FactorAnalyzer(rotation=None, n_factors=data.shape[1])
fa.fit(data)
eigenvalues, _ = fa.get_eigenvalues()
print("Eigenvalues:", [f"{ev:.3f}" for ev in eigenvalues])
# Retain factors with eigenvalue > 1 (Kaiser criterion)
# Also use scree plot and parallel analysis

# Run EFA with chosen number of factors
fa = FactorAnalyzer(n_factors=2, rotation='oblimin', method='ml')
fa.fit(data)

# Factor loadings
loadings = pd.DataFrame(
    fa.loadings_,
    index=data.columns,
    columns=[f'Factor {i+1}' for i in range(2)]
)
print("\nFactor Loadings:")
print(loadings.round(3))
# Items should load ≥ 0.40 on one factor and < 0.30 on others
```

### 9. Online Survey Platform Comparison

| Feature | Qualtrics | REDCap | Google Forms | LimeSurvey |
|---------|-----------|--------|--------------|------------|
| Cost | Institutional license (expensive) | Free for institutions | Free | Free (open source) |
| Skip logic | Advanced | Advanced | Basic | Advanced |
| Randomization | Yes (items, blocks) | Limited | No | Yes |
| Piping | Yes | Yes | No | Yes |
| Offline data collection | Yes (app) | Yes (app) | No | Yes |
| HIPAA compliant | Yes (BAA available) | Yes (designed for it) | No | Self-hosted: yes |
| API access | Yes | Yes | Limited | Yes |
| Data export | CSV, SPSS, Excel | CSV, Excel, SPSS, SAS, R, Stata | CSV, Excel | CSV, Excel, SPSS, R |
| Multi-language | Yes | Yes | Manual | Yes |
| Panel integration | Yes (Prolific, MTurk) | No | No | Limited |
| Best for | Complex academic surveys | Clinical and health research | Simple surveys, course evaluations | Budget-conscious complex surveys |

### 10. Interview Protocol Development

**Semi-Structured Interview Guide Template:**

```markdown
## Interview Protocol

### Study: [Title]
### Interviewer: [Name]
### Participant ID: ___  Date: ___  Start Time: ___

---

### Opening (5 minutes)
- Thank participant for their time
- Review consent (confirm recording permission)
- Explain purpose: "I'm interested in understanding your experiences with [topic]"
- Explain format: "I have some questions prepared, but this is a conversation.
  There are no right or wrong answers. Please share as much or as little
  as you're comfortable with."

### Warm-Up Question (5 minutes)
1. "Can you tell me about your role and how you came to it?"
   - Probe: "How long have you been in this position?"

### Main Questions (30-40 minutes)

**Block A: [Topic/Construct 1]**
2. "Describe your experience with [topic]."
   - Probe: "Can you give me a specific example?"
   - Probe: "How did that make you feel?"
   - Probe: "What happened next?"

3. "What challenges have you encountered related to [topic]?"
   - Probe: "How did you handle that?"
   - Probe: "What support, if any, did you receive?"

**Block B: [Topic/Construct 2]**
4. "How has [topic] changed over time for you?"
   - Probe: "What prompted that change?"
   - Probe: "Looking back, what would you have done differently?"

5. "What factors have been most influential in shaping your [topic]?"
   - Probe: "Can you elaborate on [specific factor mentioned]?"

**Block C: [Topic/Construct 3]**
6. [Question]
   - Probes

### Closing (5 minutes)
7. "Is there anything else about [topic] that you think is important
   and that I haven't asked about?"
8. "Do you have any questions for me?"

### Post-Interview
- Thank participant; explain next steps and timeline
- Stop recording
- Write field notes immediately after:
  - Key impressions
  - Non-verbal observations
  - Reflections on the interview process
  - Emerging analytical ideas

End Time: ___  Total Duration: ___
```

### 11. Focus Group Facilitation

**Focus Group Design Checklist:**

```markdown
## Focus Group Planning

### Composition
- Participants per group: 6-10 (4-6 for complex topics)
- Number of groups: 3-5 per population segment (until saturation)
- Homogeneity within groups (shared experience/characteristic)
- Heterogeneity across groups (variation in perspectives)

### Roles
- Moderator: Facilitates discussion, manages dynamics
- Note-taker: Records non-verbal cues, group dynamics, key quotes
- Optional: Observer behind one-way glass or via video

### Environment
- Comfortable, neutral, private setting
- Circular or U-shaped seating (no head of table)
- Recording equipment tested before session
- Refreshments available
- Name tents (first names or pseudonyms)

### Facilitation Techniques
- Opening: Icebreaker or round-robin introduction
- Funnel approach: Broad → specific questions
- Manage dominant voices: "Let's hear from others..."
- Draw out quiet participants: "We haven't heard from everyone yet..."
- Handle conflict: "It sounds like there are different perspectives here,
  and that's valuable. Let's explore both views."
- Closing: "Of everything we've discussed, what stands out as most important?"
```

### 12. Cultural Adaptation of Instruments

**Brislin's (1970) Back-Translation Method:**

```
Original instrument (Source Language)
         │
         ▼
Forward translation by Translator A
(Source → Target language; bilingual with target as dominant)
         │
         ▼
Back-translation by Translator B
(Target → Source language; bilingual with source as dominant;
 has NOT seen original instrument)
         │
         ▼
Compare original and back-translation
(Research team + both translators)
         │
         ├── Discrepancies? → Revise target version → Re-translate → Compare again
         │
         └── Equivalent? → Proceed to expert review
                              │
                              ▼
                    Cultural review panel
                    (Experts familiar with target culture)
                              │
                              ▼
                    Cognitive interviews in target population
                              │
                              ▼
                    Pilot test and psychometric validation
                    in target population
```

**ISPOR Guidelines for Cross-Cultural Adaptation:**

1. Preparation (permissions, concept elaboration)
2. Forward translation (2 independent translators)
3. Reconciliation of forward translations
4. Back-translation
5. Back-translation review
6. Harmonization across language versions
7. Cognitive debriefing with target population
8. Review of cognitive debriefing results
9. Proofreading
10. Final report documenting all decisions

---

## Best Practices

1. **Start with constructs, not questions.** Define exactly what you are measuring before writing a single item. Each item should trace back to a specific construct or dimension.

2. **Use existing validated instruments when possible.** Do not reinvent the wheel. Search the literature for instruments with established psychometric properties.

3. **Pilot everything.** Every survey should go through cognitive interviews and a quantitative pilot before full deployment. There is no substitute for testing with your target population.

4. **Keep it short.** Every additional item increases dropout risk. Include only items you will actually analyze. A good survey is as short as possible and as long as necessary.

5. **Design for your weakest respondent.** Write at an appropriate reading level. Test on mobile devices. Consider accessibility (screen readers, color contrast). Provide translations if needed.

6. **Randomize item order within sections.** This reduces order effects and helps detect careless responding.

7. **Include attention checks.** Embed 1-2 instructed response items (e.g., "Please select 'Agree' for this item") to identify careless respondents.

8. **Plan your analysis before collecting data.** Every question should have a purpose in your analysis plan. If you cannot say how you will analyze an item, remove it.

9. **Document everything.** Keep a survey design log recording every decision: why items were added, removed, or revised; pilot test results; expert feedback.

10. **Protect respondent data.** Use anonymous links when possible; store data securely; minimize collection of identifiers; comply with IRB requirements.

---

## Common Pitfalls

| Pitfall | Why It Happens | How to Avoid |
|---------|---------------|--------------|
| Double-barreled questions | Trying to be efficient; asking two things at once | Split into separate items; one concept per item |
| Leading questions | Researcher's hypothesis influences wording | Have a colleague blind to your hypothesis review items |
| Response options that do not match the stem | Copy-pasting from another survey | Ensure stem and response scale are grammatically and logically matched |
| Too many open-ended questions | Wanting rich data | Limit to 2-3 open-ended items; save depth for interviews |
| No pilot testing | Time pressure; overconfidence in item clarity | Always pilot — even a quick cognitive interview with 3-5 people helps |
| Ignoring mobile respondents | Designing on desktop | Test on multiple devices; avoid matrix questions on mobile (they break) |
| Low response rate | No follow-up plan; survey too long; no incentive | Pre-notify; send reminders (3-4 contacts); shorten survey; offer incentive |
| Neglecting psychometric validation | Assuming items are valid because they "look right" | Run reliability and factor analysis; report results in your paper |
| Convenience sampling reported as representative | Not understanding sampling limitations | Be honest about sampling method in limitations section |
| Cultural insensitivity | Assuming instruments transfer across cultures | Use formal adaptation procedures (back-translation, cognitive interviews) |

---

## References

- DeVellis, R. F., & Thorpe, C. T. (2022). *Scale development: Theory and applications* (5th ed.). Sage.
- Dillman, D. A., Smyth, J. D., & Christian, L. M. (2014). *Internet, phone, mail, and mixed-mode surveys: The tailored design method* (4th ed.). Wiley.
- Fowler, F. J. (2014). *Survey research methods* (5th ed.). Sage.
- Groves, R. M., Fowler, F. J., Couper, M. P., Lepkowski, J. M., Singer, E., & Tourangeau, R. (2009). *Survey methodology* (2nd ed.). Wiley.
- Krosnick, J. A., & Presser, S. (2010). Question and questionnaire design. In P. V. Marsden & J. D. Wright (Eds.), *Handbook of survey research* (2nd ed., pp. 263-313). Emerald.
- Podsakoff, P. M., MacKenzie, S. B., Lee, J. Y., & Podsakoff, N. P. (2003). Common method biases in behavioral research. *Journal of Applied Psychology*, 88(5), 879-903.
- Willis, G. B. (2005). *Cognitive interviewing: A tool for improving questionnaire design*. Sage.

See also: `references/survey-methodology.md` for expanded methodology details.
