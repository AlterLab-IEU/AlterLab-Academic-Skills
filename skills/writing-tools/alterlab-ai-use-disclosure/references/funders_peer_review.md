# Funders and Peer Review: AI Rules (verified 2026-09-23)

Each rule below comes from the funder's own notice or guideline, fetched on
**2026-09-23**. Text in curly double quotes or in `>` blocks is **verbatim**. TÜBİTAK's guide
is summarised here and quoted in full in `turkey_eu.md`. Publishers' reviewer rules are
quoted in `publisher_policies.md`.

---

## 1. Applicants: what each funder asks

| Funder (as of) | Disclosure rule | Where | Exempt | Hard limits |
|---|---|---|---|---|
| **NIH**: NOT-OD-25-132 (released 17 July 2025; effective from the 25 Sept 2025 receipt date); NIH/ORI post of 14 May 2026 | NIH/ORI advise describing AI use in applications. No dedicated form field appears in the notices fetched | In the application | Not addressed | Applications “substantially developed by AI”, or with such sections, are not treated as the applicants' original ideas. Post-award detection can go to ORI. **Six applications per PI per calendar year** (all activity codes except T and R13) |
| **NSF**: notice of 14 Dec 2023 | Proposers are *encouraged* to state whether, to what extent, and how generative AI was used | Project Description | Not addressed | Proposers stay responsible for accuracy and authenticity. The PAPPG misconduct rules apply |
| **UKRI**: policy published 23 Sept 2024 | Transparency is *expected* for substantive use (ideas, hypotheses, data or text analysis, comparing literature, code, abstracts) | In the application (no location named) | Minimal use: translating into English, improving English, formatting, cutting word count | No whole applications or sections generated without human involvement. **No AI during interviews.** Others' personal data never go into AI tools without consent |
| **ERC**: Scientific Council position (1 Dec 2023, updated 25 Mar 2026) | No dedicated AI field. Applicants keep “full and sole authorship responsibilities with regard to acknowledgements, plagiarism and the practice of good scientific and professional conduct” | Follow the call documents; acknowledge AI help like other external help | Not addressed | Not addressed |
| **TÜBİTAK**: ÜYZ guide v04, Ocak 2026 (first issued Eylül 2025) | Declaration **mandatory** for significant use | Dedicated section of the online application system; also progress and final reports | Basic grammar and spelling checks | **No** confidential proposal details, unpublished data, KVKK personal data or third-party commercial data in AI tools |
| **European Commission**: ERA living guidelines, 3rd version (May 2026), **non-binding** | Recommends that funders ask applicants to “declare if they substantially used generative AI tool(s) to prepare their application” | Wherever the funder provides | Basic editorial support is “not a substantial use” | Protect unpublished and personal data. Do not use AI to falsify or manipulate research data |

## 2. Reviewers and panel members: what is allowed

| Body | Language polish of *your own* text | Summarise / analyse the submission | AI-drafted critique or score | Upload submission content | Disclosure |
|---|---|---|---|---|---|
| **NIH** (NOT-OD-23-149) | ✗ | ✗ | ✗ | ✗ | n/a. Accessibility technology: tell the Designated Federal Officer before use |
| **NSF** (Dec 2023) | ✗ with non-approved tools (review text is review information) | ✗ | ✗ | ✗ with non-approved tools; public information may be shared | n/a |
| **UKRI** (Sept 2024) | Only if no application text or personal data is entered | ✗ | ✗ | ✗ | Not specified. Do not speculate in the assessment about applicants' AI use |
| **ERC** (23 Mar 2026 guidelines) | Conditionally yes, if no proposal text and no generated arguments (Q4) | ✗ (Q2) | ✗ (Q3, Q7, Q8) | ✗ (Q1). Only university-hosted systems under contract (Q9), and non-delegation still applies | Not specified |
| **TÜBİTAK** (guide §2) | ✗: no use for **any** evaluation-related purpose | ✗ | ✗ | ✗ | n/a. Breaches go to AYEK |
| **EC living guidelines** (non-binding) | Not classified | Avoid (substantial) | Avoid (substantial) | Avoid without re-use assurances | Background search is not a substantial use |
| Journals | See `publisher_policies.md` §1: never upload the manuscript; language help allowed by Springer Nature, Elsevier, Wiley, T&F, Sage and PLOS within their limits | | | | |

## 3. Generated matrices (from `scripts/disclosure_builder.py`)

Grant applications (`--matrix grant`):

| Use | nih | nsf | ukri | erc | tubitak | ec_living_guidelines |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `grammar_spelling` | R | R | E | ? | E | E |
| `language_polishing` | R | R | E | ? | D | E |
| `translation` | R | R | E | ? | D | D |
| `drafting` | ⚠ | R | R | ? | D | D |
| `ideation` | ⚠ | R | R | ? | D | D |
| `literature_search` | R | R | R | ? | D | D |
| `code` | R | R | R | ? | D | D |
| `data_analysis` | R | R | R | ? | D | D |
| `synthetic_data` | ⚠ | ? | ? | ? | D | ? |
| `figure_explanatory` | R | R | R | ? | D | D |
| `figure_primary_image_edit` | ⚠ | ? | ⚠ | ? | ⚠ | ⚠ |
| `upload_confidential` | ? | ? | ⚠ | ? | ✗ | ⚠ |
| `grant_interview` | ? | ? | ✗ | ? | ? | ? |

Peer review (`--matrix peer_review`):

| Use | icmje | springer_nature | elsevier | wiley | taylor_francis | sage | ieee | plos | nih | nsf | ukri | erc | tubitak | ec_living_guidelines |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `review_language_polish` | ? | D | D | D | ? | E | ⚠ | D | ✗ | ✗ | ? | ? | ✗ | ? |
| `review_literature_search` | ? | D | D | ? | ? | ? | ? | D | ✗ | ? | ✗ | ? | ✗ | ? |
| `review_summarize_submission` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ⚠ |
| `review_draft_report` | ? | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ⚠ |
| `review_assess_merit` | ? | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ⚠ |
| `upload_confidential` | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ⚠ |
| `accessibility_assistive` | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ? | ✗ | ? |

Legend: ✗ forbidden · ⚠ avoid · D disclose · R disclosure recommended/encouraged ·
E exempt · ? not addressed by the fetched text (ask first). A “?” in the NIH
accessibility cell means an exception is possible **with prior DFO notice**. It does not
mean free use.

---

## 4. Key sentences, verbatim

### NIH: NOT-OD-25-132, *Supporting Fairness and Originality in NIH Research Applications* (17 July 2025)

> NIH will not consider applications that are either substantially developed by AI, or contain sections substantially developed by AI, to be original ideas of applicants. If the detection of AI is identified post award, NIH may refer the matter to the Office of Research Integrity to determine whether there is research misconduct while simultaneously taking enforcement actions including but not limited to disallowing costs, withholding future awards, wholly or in part suspending the grant, and possible termination.

> NIH will only accept six new, renewal, resubmission, or revision applications from an individual Principal Investigator/Program Director or Multiple Principal Investigator for all council rounds in a calendar year. This policy applies to all activity codes except T activity codes and R13 Conference Grant Applications.

The notice also says “AI tools may be appropriate to assist in application preparation
for limited aspects or in specific circumstances” and “This policy is effective for
applications submitted to the September 25, 2025, receipt date and beyond.”

### NIH: NOT-OD-23-149, *The Use of Generative AI Technologies is Prohibited for the NIH Peer Review Process* (23 June 2023)

> the NIH prohibits NIH scientific peer reviewers from using natural language processors, large language models, or other generative Artificial Intelligence (AI) technologies for analyzing and formulating peer review critiques for grant applications and R&D contract proposals.

> Reviewers should be aware that uploading or sharing content or original concepts from an NIH grant application, contract proposal, or critique to online generative AI tools violates the NIH peer review confidentiality and integrity requirements.

> Computer technologies that are used for accessibility needs may be granted an exception to this policy. NIH Peer Reviewers must communicate the technology being used with their Designated Federal Officer in charge of the review meeting or other designated NIH official prior to use.

The prohibition also extends to members of NIH National Advisory Councils and Boards.

### NIH and HHS ORI: *Helpful Reminders to Ensure Integrity of NIH-Supported Research When Using Artificial Intelligence* (Extramural Nexus, 14 May 2026)

Under “What researchers can do”:

> Clearly describe in applications, manuscripts, and presentations the use of the AI tools and how they may have been used during the development of an application, research itself, and/or data analysis and subsequent results, including a section on described methods for reproducibility

Also listed: “Disclose any specific image-editing processes used”. Among possible
misconduct, the post lists “Altering images with AI without full disclosure, which may
constitute data falsification” and “Presenting AI-generated, non-existent references
overtly as real, which could constitute data fabrication”.

### NSF: *Notice to Research Community: Use of Generative AI Technology in the NSF Merit Review Process* (14 Dec 2023)

> NSF reviewers are prohibited from uploading any content from proposals, review information and related records to non-approved generative AI tools.

> Proposers are encouraged to indicate in the project description the extent to which, if any, generative AI technology was used and how it was used to develop their proposal.

The notice adds: “NSF reviewers may share publicly available information with current
generation generative AI tools.” Footnote 3 reads: “Review information includes panel
summaries, review analysis, recommendations for funding, PO comments and other similar
records.” On the proposer side: “Proposers are responsible for the accuracy and
authenticity of their proposal submission in consideration for merit review, including
content developed with the assistance of generative AI tools.”

### UKRI: *Use of generative AI in application preparation and assessment* (published 23 Sept 2024)

> In line with current sector good practice, applicants and applications are expected to be transparent where they have used generative AI tools in the development of an application. This information will not affect the assessment process.

Also: “Applicants do not need to disclose any minimal use of generative AI tools in their
application.” The minimal-use examples are translation into English, improving English,
and formatting or reducing word count. Two further rules:

> Applicants must not use generative AI tools to generate an entire application, or sections of an application, without human involvement.

> Applicants must not use generative AI during interviews, where this forms part of the application process.

Assessors must “not use generative AI tools as part of their assessment activities except
for language refinement purposes”. When they refine language, “no part of the application
being assessed is entered into generative AI”. They must also “not take into account or
speculate within their assessment whether generative AI has been used to develop the
application”.

### ERC: Scientific Council position (1 Dec 2023; page last updated 25 Mar 2026)

> The Scientific Council emphasises that use of external help in preparing a proposal does not relieve the author from taking full and sole authorship responsibilities with regard to acknowledgements, plagiarism and the practice of good scientific and professional conduct.

> The Scientific Council emphasises that the use of external help, including generative AI systems, for the evaluation of research proposals is not permitted due to both the reviewer's obligation to assess proposals independently without delegating their tasks, and concerns about confidentiality and privacy.

### ERC: *The use of AI in grant proposal evaluation*, guidelines for panel members and remote reviewers (23 March 2026)

The guidelines rest on two principles: “(1) non-delegation of the evaluation task, and
(2) privacy and confidentiality”. Reviewers may not “upload a proposal, or part of it, to
an online AI tool such as ChatGPT” (Q1). A local model may not be used to summarise the
proposal (Q2). On language help (Q4):

> You may use AI tools to polish your language or translate your review, provided that: a) you do not disclose personal information to a third party (data protection) b) you do not disclose parts of the proposal to the AI tool (confidentiality) and c) you do not ask the AI to generate arguments for you (non-delegation).

Drafting (Q7): “No. Generating a draft review involves evaluative judgement and
constitutes a delegation of the evaluation task, even if the reviewer later revises the
text.”

### European Commission: *Living guidelines on the responsible use of generative AI in research* (third version, May 2026)

The guidelines are non-binding: “While non-binding, they should be considered as a
supporting tool for researchers, research organisations and research funding bodies”.

For researchers, they state “AI systems are neither authors nor co-authors.” They also
say “When generative AI meaningfully shapes results, researchers transparently note its
use according to the guidelines of their journal or standards in their discipline in the
methods section (or equivalent) responsibly evaluating the extent of the contribution”.
Footnote 21 adds: “using generative AI as a basic editorial support tool is not a
substantial use.” Footnote 22 says references to the tool “could include the name,
version, date, etc. and how it was used and affected the research process.”

Recommendation 6 is to refrain from substantial use in peer review and proposal
evaluation. Footnote 28 draws the line:

> using generative AI to search background info for a review using it to better understand punctually some ideas or concepts is not a substantial use, while delegating the evaluation or the assessment of a paper, drafting peer review report, helping to understand the main elements of a paper, or evaluating a funding proposal is a substantial use.

For funders: “Applicants declare if they substantially used generative AI tool(s) to
prepare their application.”

## Sources (all retrieved 2026-09-23)

- NIH NOT-OD-25-132: https://grants.nih.gov/grants/guide/notice-files/NOT-OD-25-132.html
- NIH NOT-OD-23-149: https://grants.nih.gov/grants/guide/notice-files/NOT-OD-23-149.html
- NIH/ORI Extramural Nexus, 14 May 2026: https://grants.nih.gov/news-events/nih-extramural-nexus-news/2026/05/helpful-reminders-to-ensure-integrity-of-nih-supported-research-when-using-artificial-intelligence
- NSF notice (14 Dec 2023; the old /news/ URL now redirects here): https://www.nsf.gov/policies/ai/merit-review
- UKRI policy: https://www.ukri.org/publications/generative-artificial-intelligence-in-application-and-assessment-policy/use-of-generative-artificial-intelligence-in-application-preparation-and-assessment/
- ERC Scientific Council position: https://erc.europa.eu/news-events/news/current-position-erc-scientific-council-ai
- ERC reviewer guidelines (PDF, 23 Mar 2026): https://erc.europa.eu/system/files/2026-03/Use-AI-grant-proposal-evaluation.pdf ; press release (24 Mar 2026): https://erc.europa.eu/news-events/news/erc-clarifies-limits-ai-use-grant-evaluation
- EC living guidelines, 3rd version (PDF): https://research-and-innovation.ec.europa.eu/document/download/2b6cf7e5-36ac-41cb-aab5-0d32050143dc_en?filename=ec_rtd_ai-guidelines.pdf ; update notice (8 May 2026): https://research-and-innovation.ec.europa.eu/news/all-research-and-innovation-news/updated-era-living-guidelines-responsible-use-generative-ai-research-2026-05-08_en
- TÜBİTAK guide: see `turkey_eu.md`
