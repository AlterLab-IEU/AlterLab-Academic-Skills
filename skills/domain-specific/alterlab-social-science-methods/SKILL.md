---
name: alterlab-social-science-methods
description: "Guides advanced social science research methods — discourse analysis (Fairclough CDA, Gee), conversation analysis, quantitative content analysis, Qualitative Comparative Analysis (QCA), process tracing, archival research, participatory/community-based research (PAR, CBPR), Delphi and Q methodology, social network analysis (SNA), bibliometrics and scientometrics, systematic mapping reviews, and program/policy evaluation. Use when designing or conducting any of these studies — choosing a specialized method, building a coding scheme, establishing causal mechanisms in case studies, mapping relational or subjective data, or applying an evaluation framework. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*)
metadata:
  skill-author: AlterLab
  version: "1.0.0"
  last_updated: "2026-03-18"
---

# Social Science Research Methods

## Overview

Social science research encompasses a remarkably diverse methodological landscape. Beyond the familiar quantitative-qualitative divide lie specialized methods that have been refined over decades within particular disciplinary traditions -- methods that carry specific epistemological commitments, analytical procedures, and quality criteria. This skill covers advanced and specialized social science research methods that go beyond introductory methods courses: discourse analysis in its multiple traditions, conversation analysis, quantitative content analysis, comparative methods including Qualitative Comparative Analysis (QCA), process tracing for causal inference in case studies, archival research, participatory and community-based research, the Delphi method and Q methodology, social network analysis, bibliometrics and scientometrics, systematic mapping reviews, and program evaluation and policy analysis.

Each method section explains the intellectual origins of the approach, its core analytical procedures, the types of research questions it can address, practical implementation guidance with examples, and the quality criteria by which work using the method is evaluated. The goal is to provide enough depth that a researcher can determine whether a method is appropriate for their question and begin implementing it, while knowing where to find the canonical references for full methodological training.

This skill is designed for faculty and researchers working across the social sciences -- sociology, political science, education, public health, communication, public policy, social work, and interdisciplinary fields. Many of these methods are also used in the humanities and in applied fields such as management, urban planning, and international development.

## When to Use This Skill

Use this skill when you need to:

- Conduct or design a discourse analysis study using Fairclough's Critical Discourse Analysis (CDA) or Gee's discourse analysis framework
- Analyze naturally occurring talk-in-interaction using conversation analysis (CA)
- Design a quantitative content analysis with reliable coding schemes
- Apply Qualitative Comparative Analysis (QCA) or Mill's methods for cross-case comparison
- Use process tracing to establish causal mechanisms in case study research
- Plan and conduct archival research with primary historical sources
- Design a participatory action research (PAR) or community-based participatory research (CBPR) project
- Implement a Delphi study to build expert consensus
- Conduct a Q methodology study to map subjective viewpoints
- Perform social network analysis (SNA) on relational data
- Conduct bibliometric or scientometric analysis of scholarly literatures
- Design a systematic mapping review (as distinct from a systematic review)
- Plan a program evaluation using established frameworks
- Conduct policy analysis using structured analytical approaches

## Core Capabilities

### Discourse Analysis

Discourse analysis is not a single method but a family of approaches that examine how language constructs social reality. The two most influential traditions in social science are Fairclough's Critical Discourse Analysis and Gee's discourse analysis.

#### Fairclough's Critical Discourse Analysis (CDA)

Norman Fairclough's CDA examines the relationship between language, power, and ideology through a three-dimensional framework:

**Dimension 1: Text analysis (description)**
- Vocabulary choices (overwording, rewording, ideologically contested terms)
- Grammar (transitivity, modality, agency, nominalization)
- Text structure and cohesion
- Turn-taking and interactional control

**Dimension 2: Discursive practice (interpretation)**
- Production (who created the text, under what institutional conditions)
- Distribution (how the text circulates and to whom)
- Consumption (how audiences interpret and use the text)
- Intertextuality (how the text draws on and transforms other texts)
- Interdiscursivity (how the text mixes different discourses, genres, styles)

**Dimension 3: Social practice (explanation)**
- Situational context (immediate social situation)
- Institutional context (organizational norms and power relations)
- Societal context (broader political, economic, cultural structures)

**Example: CDA analysis of a university policy document**

```
Text: "Students are expected to demonstrate professional behaviors
consistent with the values of the institution."

Text analysis:
- Passive voice ("are expected") obscures who does the expecting
- Nominalization ("behaviors") converts actions into countable objects
- "Professional" is an ideologically loaded term that normalizes
  particular class and cultural norms
- "Values of the institution" presupposes shared values and
  positions the institution as a moral agent

Discursive practice:
- Genre: institutional policy (authoritative, impersonal)
- Intertextuality: draws on corporate/professional discourse,
  displacing educational discourse
- Production: likely written by administrators, not faculty or students

Social practice:
- Reflects neoliberal governance of higher education
- Constructs students as future workers rather than learners
- Power asymmetry: institution defines "professional" without
  student input
```

#### Gee's Discourse Analysis

James Paul Gee distinguishes between discourse (language-in-use) and Discourse (with a capital D) -- ways of being in the world that integrate language with action, interaction, values, beliefs, symbols, objects, tools, and places.

**Gee's seven building tasks of language:**

1. **Significance** -- How does this language make certain things significant or insignificant?
2. **Activities** -- What activity is this language enacting?
3. **Identities** -- What identity is the speaker/writer taking on?
4. **Relationships** -- What relationships is this language building or assuming?
5. **Politics** -- What is being treated as normal, appropriate, or valued?
6. **Connections** -- How does this language connect or disconnect things?
7. **Sign systems and knowledge** -- What sign systems (language, images, statistics) are privileged?

**Gee's analytical tools:**

- Situated meaning (context-dependent word meaning)
- Social languages (varieties associated with social groups/activities)
- Figured worlds (taken-for-granted stories or theories)
- Intertextuality (references to other texts)
- Conversations (societal-level debates indexed by the text)

### Conversation Analysis

Conversation analysis (CA), developed by Harvey Sacks, Emanuel Schegloff, and Gail Jefferson, studies the sequential organization of naturally occurring talk-in-interaction. CA is fundamentally empirical and data-driven -- it examines what participants actually do in conversation rather than imposing external categories.

**Core principles of CA:**

1. **Sequential organization** -- Utterances are understood in relation to what comes before and after
2. **Turn-taking system** -- Participants coordinate who speaks when through recognizable rules
3. **Preference organization** -- Some responses are structurally "preferred" (e.g., acceptance over rejection)
4. **Repair** -- Participants have systematic practices for dealing with troubles in speaking, hearing, or understanding
5. **Recipient design** -- Talk is designed for specific recipients and their knowledge

**Transcription conventions (Jefferson system):**

```
Symbol    Meaning
(0.5)     Pause in seconds
(.)       Micro-pause (less than 0.2 seconds)
=         Latching (no gap between speakers)
[         Start of overlapping talk
]         End of overlapping talk
word      Emphasis (underline)
WORD      Loud speech
.hh       In-breath
hh        Out-breath
wo::rd    Sound stretching
wo-       Cut-off
>word<    Faster speech
<word>    Slower speech
.         Falling intonation
?         Rising intonation
,         Continuing intonation
((nods))  Analyst description
```

**Example: CA analysis of a doctor-patient interaction**

```
01 DOC:  So how are you feeling today.
02       (0.8)
03 PAT:  Well (.) I'm okay I gu:ess.
04 DOC:  Mm hm,
05       (0.3)
06 PAT:  But my knee's been bothering me quite a bi:t.
07 DOC:  Your knee.
08 PAT:  Yeah the left one.=It's been (0.4) kind of
09       sti::ff in the mornings.

Analysis:
- Line 02: The 0.8 second pause before the patient's response
  suggests a dispreferred response is coming
- Line 03: "Well" is a discourse marker that prefigures disagreement
  or qualification. "I guess" hedges the assessment.
- Line 06: "But" introduces the actual reason for the visit,
  delivered as a contrast to "okay"
- Line 07: The doctor's partial repeat ("Your knee.") functions as
  a go-ahead / continuer, inviting elaboration
```

### Quantitative Content Analysis

Quantitative content analysis systematically codes textual, visual, or audio content into categories and analyzes the resulting data statistically. Unlike discourse analysis, it prioritizes reliability and generalizability over interpretive depth.

**Steps in quantitative content analysis:**

1. **Define the research question** -- What content features are you examining and why?
2. **Define the population and sampling frame** -- What is the universe of relevant content?
3. **Select a sample** -- Random, stratified, or purposive sampling of content units
4. **Define units of analysis** -- What gets coded? (article, paragraph, sentence, image, scene)
5. **Develop the coding scheme** -- Create exhaustive, mutually exclusive categories with clear decision rules
6. **Pilot test and train coders** -- Code a sample, discuss disagreements, refine the scheme
7. **Assess intercoder reliability** -- Calculate agreement statistics before proceeding
8. **Code the full sample** -- Apply the scheme systematically
9. **Analyze** -- Descriptive statistics, chi-square tests, logistic regression, etc.
10. **Report** -- Include reliability statistics, codebook, and examples

**Intercoder reliability metrics:**

| Metric | When to Use | Acceptable Threshold |
|--------|------------|---------------------|
| Percent agreement | Never alone (does not account for chance) | N/A |
| Cohen's kappa | Two coders, nominal categories | > 0.80 (good), > 0.67 (acceptable) |
| Krippendorff's alpha | Any number of coders, any measurement level | > 0.80 (good), > 0.667 (acceptable) |
| Scott's pi | Two coders, nominal categories | > 0.80 |
| ICC (intraclass correlation) | Continuous/ordinal ratings | > 0.75 (good) |

### Comparative Methods

#### Qualitative Comparative Analysis (QCA)

QCA, developed by Charles Ragin, bridges the qualitative-quantitative divide by using Boolean algebra and set theory to analyze causal complexity across cases. It is designed for medium-N research (10-50 cases) where statistical methods lack power but individual case studies cannot establish generality.

**QCA variants:**

| Variant | Data Type | Best For |
|---------|----------|----------|
| crisp-set QCA (csQCA) | Binary (0/1) | Clear-cut conditions |
| fuzzy-set QCA (fsQCA) | Continuous (0.0-1.0) | Degree of membership |
| multi-value QCA (mvQCA) | Categorical (0, 1, 2...) | Non-binary categories |

**Steps in fsQCA:**

1. **Identify conditions and outcome** -- Select theoretically grounded conditions (typically 4-7)
2. **Calibrate sets** -- Convert raw data into fuzzy-set membership scores (0.0 to 1.0) using three anchor points: fully in (0.95), crossover (0.50), fully out (0.05)
3. **Construct truth table** -- List all logically possible combinations of conditions
4. **Analyze necessary conditions** -- Test whether any single condition is necessary for the outcome (consistency > 0.90)
5. **Analyze sufficient conditions** -- Use Boolean minimization to identify combinations of conditions sufficient for the outcome
6. **Interpret solutions** -- Distinguish between parsimonious, intermediate, and complex solutions
7. **Return to cases** -- Validate the solutions against within-case knowledge

**Example: QCA truth table row**

```
Conditions: HIGH_FUNDING * STRONG_LEADERSHIP * COMMUNITY_SUPPORT * ~POLITICAL_OPPOSITION
Outcome: PROGRAM_SUCCESS
Cases: Portland, Austin, Minneapolis
Consistency: 0.92
Coverage: 0.45

Interpretation: The combination of high funding AND strong leadership
AND community support AND the absence of political opposition is
sufficient for program success, as observed in three cases.
```

**Software:** fsQCA (free), QCA package in R, TOSMANA

#### Mill's Methods

John Stuart Mill's methods of agreement and difference remain foundational for comparative case selection:

- **Method of Agreement** -- If two or more cases share the outcome and one common condition while differing on others, that condition may be causal
- **Method of Difference** -- If two cases differ on the outcome and one condition while being similar on others, that condition may be causal
- **Method of Concomitant Variation** -- If a condition and outcome vary together across cases, they may be causally related
- **Joint Method** -- Combining agreement and difference for stronger inference

### Process Tracing

Process tracing is a within-case method for identifying causal mechanisms. Developed in political science (George & Bennett, 2005; Beach & Pedersen, 2019), it examines the causal chain between an independent variable and outcome by identifying observable evidence of theorized mechanisms.

**Process tracing variants:**

1. **Theory-testing** -- Evaluates whether a hypothesized causal mechanism operated in a specific case
2. **Theory-building** -- Inductively identifies causal mechanisms from detailed case evidence
3. **Explaining-outcome** -- Iteratively constructs a case-specific explanation

**Bayesian process tracing (Beach & Pedersen):**

For each piece of evidence, assess:
- **Prior probability** -- How likely is the hypothesis before seeing this evidence?
- **Likelihood of evidence if hypothesis is true** -- Would we expect this evidence if the mechanism operated?
- **Likelihood of evidence if hypothesis is false** -- Could this evidence exist without the mechanism?

**Four types of process tracing tests:**

| Test | High uniqueness | Low uniqueness |
|------|----------------|----------------|
| **High certainty** | Doubly decisive | Hoop test |
| **Low certainty** | Smoking gun | Straw-in-the-wind |

- **Hoop test** -- Evidence the hypothesis must pass to remain viable (necessary but not sufficient)
- **Smoking gun** -- Evidence that strongly confirms if found (sufficient but not necessary)
- **Doubly decisive** -- Evidence that is both necessary and sufficient (rare)
- **Straw-in-the-wind** -- Slightly shifts the probability but is neither necessary nor sufficient

### Archival Research

Archival research involves systematic analysis of primary source documents stored in archives, libraries, government records offices, organizational files, and digital repositories. It is a core method in history, political science, sociology, and area studies.

**Types of archival sources:**

- Government records (legislation, policy memos, diplomatic cables, census data)
- Organizational records (meeting minutes, correspondence, financial records)
- Personal papers (diaries, letters, memoirs)
- Legal documents (court records, contracts, charters)
- Media archives (newspapers, broadcasts, advertisements)
- Visual materials (photographs, maps, architectural plans)
- Digital archives (email collections, web archives, social media datasets)

**Evaluating archival sources -- the four questions:**

1. **Authenticity** -- Is this document what it purports to be? (forgery detection, provenance chain)
2. **Reliability** -- How accurate is the information? (proximity to events, author bias, corroboration)
3. **Representativeness** -- What has survived and what has been lost? (selection bias in archives)
4. **Meaning** -- What did this document mean in its original context? (historical semantics, cultural context)

**Practical archival research workflow:**

1. Identify relevant archives through finding aids, archival catalogs, and secondary literature
2. Contact archivists in advance -- they are invaluable guides to collection organization
3. Review finding aids to identify relevant boxes, folders, and series
4. Develop a systematic note-taking protocol (metadata, transcription, analysis notes)
5. Photograph or scan documents when permitted (check institutional policies)
6. Cross-reference documents across collections to corroborate claims
7. Maintain a chain of custody for all evidence cited in publications

### Participatory Action Research and CBPR

Participatory action research (PAR) and community-based participatory research (CBPR) challenge the researcher-subject hierarchy by positioning community members as co-researchers. Research is conducted with communities, not on them.

**Core CBPR principles (Israel et al., 2005):**

1. Recognizes community as a unit of identity
2. Builds on strengths and resources within the community
3. Facilitates collaborative, equitable partnership in all research phases
4. Integrates knowledge and intervention for mutual benefit
5. Promotes co-learning and empowering processes
6. Involves cyclical and iterative process
7. Addresses health from both positive and ecological perspectives
8. Disseminates findings to all partners
9. Involves long-term commitment

**CBPR research phases:**

```
Phase 1: Partnership Formation
- Identify community partners and establish trust
- Develop memoranda of understanding (MOUs)
- Create community advisory board (CAB)
- Define roles, responsibilities, and decision-making processes

Phase 2: Collaborative Research Design
- Jointly identify research priorities
- Co-develop research questions
- Design culturally appropriate methods
- Obtain IRB approval with community input

Phase 3: Data Collection
- Train community members as co-researchers
- Collect data using agreed-upon methods
- Maintain ongoing communication with CAB

Phase 4: Analysis and Interpretation
- Collaborative data analysis (member checking, community forums)
- Validate findings with community knowledge
- Identify actionable implications

Phase 5: Action and Dissemination
- Develop and implement action plans
- Disseminate to community and academic audiences
- Evaluate impact and plan next cycle
```

### Delphi Method

The Delphi method uses structured, iterative rounds of expert consultation to build consensus on complex or uncertain topics.

**Standard Delphi process:**

1. **Panel selection** -- Identify 15-30 experts with relevant knowledge and diverse perspectives
2. **Round 1** -- Open-ended questionnaire to generate ideas and identify key issues
3. **Round 2** -- Structured questionnaire based on Round 1 themes; experts rate items on Likert scales
4. **Feedback** -- Share anonymized aggregate results (medians, IQR, distribution)
5. **Round 3** -- Experts revise their ratings in light of group feedback; provide rationale for outlier positions
6. **Consensus assessment** -- Determine which items meet pre-defined consensus thresholds
7. **Optional Round 4** -- Additional iteration if consensus is not reached

**Consensus thresholds (common definitions):**

| Criterion | Threshold | Meaning |
|-----------|-----------|---------|
| Percent agreement | 70-80% | Proportion rating item above threshold |
| Median | 4+ on 5-point scale | Central tendency indicates agreement |
| IQR | 1.0 or less | Low dispersion indicates consensus |
| Stability | Change < 15% between rounds | Ratings have stabilized |

### Q Methodology

Q methodology maps the range of subjective viewpoints on a topic by having participants rank-order statements into a quasi-normal distribution. Factor analysis of the sorted Q-sets reveals shared viewpoints.

**Q methodology steps:**

1. **Develop the concourse** -- Compile the full range of opinions on the topic (from interviews, literature, media)
2. **Select the Q-set** -- Choose 30-60 representative statements from the concourse
3. **Select the P-set** -- Recruit 20-40 participants with diverse perspectives
4. **Q-sorting** -- Each participant ranks statements from "most disagree" to "most agree" on a forced distribution grid
5. **Factor analysis** -- By-person factor analysis (Q-factor analysis) to identify shared viewpoint patterns
6. **Factor interpretation** -- Examine the idealized sort for each factor; identify distinguishing and consensus statements

### Social Network Analysis

Social network analysis (SNA) examines the structure and implications of relationships between actors (individuals, organizations, nations). It shifts the analytical focus from attributes of individual cases to patterns of connections.

**Key SNA concepts:**

| Concept | Definition | Measure |
|---------|-----------|---------|
| Degree centrality | Number of direct connections | Count of ties |
| Betweenness centrality | How often a node lies on shortest paths between others | Freeman betweenness |
| Closeness centrality | Average distance to all other nodes | Inverse of average path length |
| Eigenvector centrality | Connections to well-connected nodes | Eigenvector score |
| Density | Proportion of possible ties that are present | Actual ties / possible ties |
| Clustering coefficient | Extent to which a node's neighbors are connected to each other | Proportion of closed triads |
| Homophily | Tendency for similar nodes to be connected | E-I index, assortivity |
| Structural holes | Gaps between clusters that a node can bridge | Burt's constraint measure |

**SNA software:**

| Software | Strengths | Cost |
|----------|----------|------|
| Gephi | Visualization, large networks | Free |
| UCINET | Classic SNA measures, ERGM | Paid |
| igraph (R/Python) | Programmable, scalable | Free |
| NetworkX (Python) | Programmable, well-documented | Free |
| Pajek | Very large networks | Free |
| NodeXL | Excel integration, social media | Paid |
| statnet (R) | Statistical models (ERGM, STERGM) | Free |

**Example: Research question to SNA measure mapping**

```
Question: Who are the most influential researchers in the field?
  --> Eigenvector centrality (connected to other influential nodes)

Question: Who bridges different research communities?
  --> Betweenness centrality (lies on paths between clusters)

Question: How cohesive is this policy network?
  --> Density, average path length, clustering coefficient

Question: Do researchers collaborate within or across institutions?
  --> Homophily (E-I index by institutional affiliation)

Question: How has the collaboration network evolved?
  --> Longitudinal SNA (STERGM, RSIENA)
```

### Bibliometrics and Scientometrics

Bibliometrics uses quantitative analysis of scholarly publications to map research fields, identify trends, and evaluate impact. Scientometrics is the broader study of the scientific enterprise using quantitative methods.

**Core bibliometric techniques:**

1. **Citation analysis** -- Who cites whom? Identifies intellectual influence and knowledge flows
2. **Co-citation analysis** -- Which works are cited together? Reveals intellectual structure
3. **Bibliographic coupling** -- Which works share references? Identifies research fronts
4. **Co-authorship analysis** -- Who collaborates with whom? Maps collaboration networks
5. **Keyword co-occurrence** -- Which concepts appear together? Maps thematic structure
6. **Science mapping** -- Visual representation of field structure and evolution

**Bibliometric tools:**

| Tool | Type | Best For |
|------|------|----------|
| VOSviewer | Visualization | Network visualization, co-citation maps |
| Bibliometrix (R) | Analysis package | Comprehensive bibliometric analysis |
| CiteSpace | Visualization + analysis | Burst detection, timeline visualization |
| Publish or Perish | Citation metrics | Individual-level citation analysis |
| Dimensions | Database + analytics | AI-powered literature analytics |
| Lens.org | Database | Patent + scholarly literature integration |
| Scopus/WoS | Database | Authoritative citation data |

### Systematic Mapping Reviews

Systematic mapping reviews (also called scoping reviews or evidence maps) provide a broad overview of a research area, identifying the volume and nature of available evidence without synthesizing effect sizes. They differ from systematic reviews in scope and depth.

**Mapping review vs. systematic review:**

| Feature | Systematic Review | Mapping Review |
|---------|------------------|----------------|
| Question | Focused, specific | Broad, exploratory |
| Search | Comprehensive | Comprehensive |
| Quality appraisal | Formal, required | Optional |
| Data extraction | Detailed outcomes | Descriptive categorization |
| Synthesis | Meta-analysis or narrative | Visual maps, frequency tables |
| Purpose | Answer specific question | Map the territory |

**PRISMA-ScR (Scoping Reviews) checklist items:**

1. Title identifying the report as a scoping review
2. Structured abstract
3. Rationale and objectives
4. Eligibility criteria
5. Information sources and search strategy
6. Selection of evidence
7. Data charting process
8. Critical appraisal (if conducted)
9. Results with flow diagram
10. Discussion of findings in context

### Program Evaluation

Program evaluation systematically assesses the design, implementation, and outcomes of interventions, programs, or policies. It serves both accountability and learning functions.

**Major evaluation frameworks:**

| Framework | Focus | Key Feature |
|-----------|-------|-------------|
| Logic Model | Program theory | Inputs -> Activities -> Outputs -> Outcomes |
| Theory of Change | Causal pathways | Maps assumptions and mechanisms |
| RE-AIM | Implementation | Reach, Effectiveness, Adoption, Implementation, Maintenance |
| CIPP (Stufflebeam) | Decision-making | Context, Input, Process, Product evaluation |
| Utilization-Focused (Patton) | Use | Designed for intended users |
| Developmental Evaluation | Innovation | Real-time evaluation for adaptive programs |
| Empowerment Evaluation | Equity | Community ownership of evaluation process |

**Logic model template:**

```
INPUTS          ACTIVITIES         OUTPUTS           OUTCOMES
                                                Short-term | Long-term
-----------     -------------      ----------    --------   ----------
Funding         Training           # trained     Knowledge  Policy change
Staff           Workshops          # sessions    Attitudes  Health improvement
Materials       Counseling         # served      Skills     Reduced inequality
Partnerships    Outreach           # materials   Behaviors  Systems change
Technology      Data collection    # referrals   Access     Sustainability
```

### Policy Analysis Methods

Policy analysis provides structured approaches to evaluating public policies and generating alternatives.

**Bardach's Eightfold Path:**

1. Define the problem
2. Assemble some evidence
3. Construct the alternatives
4. Select the criteria (efficiency, equity, feasibility, political acceptability)
5. Project the outcomes
6. Confront the trade-offs
7. Decide
8. Tell your story

**Cost-benefit analysis (CBA) and cost-effectiveness analysis (CEA):**

| Feature | CBA | CEA |
|---------|-----|-----|
| Outcome measure | Monetized | Natural units (lives saved, cases prevented) |
| Comparison | Net benefits | Cost per unit of outcome |
| When to use | When outcomes can be monetized | When monetization is inappropriate |
| Result | Benefit-cost ratio or net present value | Incremental cost-effectiveness ratio (ICER) |

## Best Practices

### Method Selection

1. **Start with the question, not the method** -- The research question should drive method selection, not the reverse. Ask: what kind of evidence would answer my question?
2. **Consider mixed methods** -- Many research questions benefit from combining approaches (e.g., QCA for cross-case patterns + process tracing for within-case mechanisms).
3. **Match epistemology to method** -- Discourse analysis assumes constructionist epistemology; QCA assumes configurational causation. Ensure your philosophical assumptions align with your method.
4. **Be realistic about resources** -- Archival research requires travel and time. CBPR requires long-term community relationships. SNA requires relational data that may be hard to collect.
5. **Study exemplars** -- Before designing your study, read 5-10 published studies that use your chosen method well.

### Rigor and Quality

1. **Transparent reporting** -- Document every analytical decision, not just the results.
2. **Reliability** -- In content analysis, report intercoder reliability. In qualitative methods, use audit trails.
3. **Validity** -- Use member checking, triangulation, and negative case analysis.
4. **Reflexivity** -- In interpretive methods, acknowledge how your positionality shapes the analysis.
5. **Replicability** -- Share data and materials to the extent ethically possible.

### Ethics in Social Science Research

1. **Informed consent** -- Ensure participants understand what they are agreeing to, especially in participatory and archival research.
2. **Community benefit** -- In CBPR, ensure the research benefits the community, not just the researcher.
3. **Power dynamics** -- Be attentive to power differentials between researchers and participants, between institutions and communities.
4. **Data sensitivity** -- Social science data often involves personal information. Follow institutional and legal requirements for data protection.
5. **Representation** -- Report findings in ways that do not stigmatize or misrepresent communities.

## Common Pitfalls

### Discourse Analysis Pitfalls

- **Cherry-picking examples** -- Selecting only extracts that support your argument while ignoring contradictory evidence.
- **Over-interpretation** -- Reading ideological significance into mundane language choices without supporting evidence.
- **Ignoring context** -- Analyzing text in isolation from its conditions of production and reception.
- **Conflating description with analysis** -- Describing what the text says is not the same as analyzing how it works.

### Comparative Methods Pitfalls

- **Too many conditions for the number of cases** -- QCA becomes unreliable when the ratio of conditions to cases is too high. Aim for at least 3 cases per condition.
- **Atheoretical condition selection** -- Conditions in QCA must be theoretically justified, not data-mined.
- **Ignoring contradictory cases** -- Cases that do not fit the solution require explanation, not dismissal.
- **Treating QCA as purely mechanical** -- Boolean minimization is a tool, not a substitute for case knowledge.

### Process Tracing Pitfalls

- **Confirmation bias** -- Seeking evidence that confirms your preferred mechanism while ignoring disconfirming evidence.
- **Insufficient evidence** -- A single piece of evidence is rarely decisive. Build cumulative inference across multiple types of evidence.
- **Conflating correlation with mechanism** -- Observing that X and Y co-occur within a case does not establish the mechanism connecting them.
- **Ignoring alternative mechanisms** -- Always test competing explanations, not just your favorite hypothesis.

### CBPR Pitfalls

- **Tokenistic participation** -- Inviting community members to meetings without giving them genuine decision-making power.
- **Extractive research** -- Taking community knowledge and data without returning meaningful benefits.
- **Unresolved power dynamics** -- Academic researchers holding all the funding and institutional authority while claiming "equal partnership."
- **Publication pressure** -- Academic timelines and community timelines often conflict. Negotiate expectations early.

### SNA Pitfalls

- **Boundary specification** -- Defining the network boundary incorrectly (too broad or too narrow) distorts all subsequent measures.
- **Missing data** -- Non-response in network surveys is more damaging than in attribute surveys because each missing node affects the entire structure.
- **Treating descriptive measures as causal** -- High betweenness centrality describes a structural position; it does not prove the node caused information flow.
- **Ignoring tie strength and direction** -- Not all connections are equal. Distinguish strong from weak ties, directed from undirected.

## References

- Fairclough, N. (2003). *Analysing Discourse: Textual Analysis for Social Research*. Routledge.
- Gee, J. P. (2014). *An Introduction to Discourse Analysis: Theory and Method* (4th ed.). Routledge.
- Sacks, H., Schegloff, E. A., & Jefferson, G. (1974). A simplest systematics for the organization of turn-taking for conversation. *Language*, 50(4), 696-735.
- Ragin, C. C. (2008). *Redesigning Social Inquiry: Fuzzy Sets and Beyond*. University of Chicago Press.
- Beach, D., & Pedersen, R. B. (2019). *Process-Tracing Methods: Foundations and Guidelines* (2nd ed.). University of Michigan Press.
- Israel, B. A., Eng, E., Schulz, A. J., & Parker, E. A. (Eds.). (2005). *Methods in Community-Based Participatory Research for Health*. Jossey-Bass.
- Wasserman, S., & Faust, K. (1994). *Social Network Analysis: Methods and Applications*. Cambridge University Press.
- Aria, M., & Cuccurullo, C. (2017). bibliometrix: An R-tool for comprehensive science mapping analysis. *Journal of Informetrics*, 11(4), 959-975.
- Patton, M. Q. (2010). *Developmental Evaluation: Applying Complexity Concepts to Enhance Innovation and Use*. Guilford Press.
- Bardach, E., & Patashnik, E. M. (2019). *A Practical Guide for Policy Analysis* (6th ed.). CQ Press.
