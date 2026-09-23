# Publisher and Venue AI Policies (verified 2026-09-23)

Every row below was checked against the publisher's own policy page, fetched on
**2026-09-23**. Text in curly double quotes or in `>` blocks is **verbatim**; everything else
is a summary. Policies change without notice: re-open the live page before you submit.
A journal's own *Guide for Authors* can be stricter than its publisher's policy.
Elsevier says “the range of AI use varies depending on the journal”, and Taylor &
Francis says “some journals may not allow use of Generative AI tools beyond language
improvement”. **The journal's own instructions win.**

Venues whose pages could **not** be fetched are listed in §4 as UNVERIFIED. The skill
does not state their rules.

---

## 1. Comparison table

| Venue (as of) | AI as author? | Where the disclosure goes | What to state | Exempt from disclosure | Images / figures | Reviewers |
|---|---|---|---|---|---|---|
| **ICMJE** Recommendations (updated Jan 2026) | No | Cover letter **and** manuscript: writing help → Acknowledgments; data collection, analysis or figure generation → Methods | How the technology was used | None stated | Figure generation → Methods | Follow the journal's AI policy or ask permission; confidentiality may bar uploading; disclose use to the journal |
| **Springer Nature / Nature Portfolio** (2026 risk framework) | No (Red) | “AI Declaration” in the manuscript; visuals also get a caption/legend disclosure; Amber research uses need a methods description | Use, author accountability; for visuals: AI system, purpose, extent | None: Green uses (including grammar editing) still carry “Clearly describe use and confirm author accountability” | Allowed only from verifiable inputs; opaque, prompt-only images and photorealistic deepfakes are Red | Green/Amber uses described in the report; no uploads to public/unsecured tools; no AI-written reports or accept/reject recommendations |
| **Elsevier** (policy updated June 2026) | No | Separate section before the references, titled “Declaration of generative AI and AI-assisted technologies in the manuscript preparation process”; AI in methods/code/data visualisation → Methods | Tool name, purpose, extent of oversight; in Methods also version and developer | Basic grammar, spelling and punctuation checks; basic reference-manager functions; accessibility-only assistive technology | Explanatory images OK (caption + declaration); data visualisations only if reproducibly derived from data (Methods); **no** AI creation or alteration of primary research images; **no** general-purpose generative tools for graphical abstracts; cover art needs prior permission | Never upload the manuscript or any part of it; supportive use only (language/structure of the report, background literature search), private tools only; disclose tool + purpose in the report |
| **Wiley** (AI guidelines, undated) | No | Acknowledgments (drafting, editing, translation, formatting); Methods (methodology, data, literature review); figure captions (visuals) | Tool name and version, date/year, role, sections, authors' oversight | Spelling, grammar, general editing, word choice, conciseness, citation formatting, debugging | Data visualisations and illustrations need caption disclosure; **no** AI-edited photographs; **no** AI generation, modification or enhancement of factual/evidential images | May improve the clarity of written feedback, disclosed to the handling editor; no uploads of any part of a manuscript |
| **Taylor & Francis** (AI policy, undated) | No | A specific AI-usage disclosure statement in the article (books: preface or introduction, after approval) | Full tool name **with version number**, how it was used, why | None stated (“any use”) | Data visualisations and conceptual illustrations permitted; **no** creation or manipulation of research results, clinical samples or diagnostic images | No uploads; no AI analysis or summaries of submissions; no AI-generated reports; language improvement allowed |
| **Sage** (AI policy, undated) | Not stated on the AI page (it links COPE's statement) | On submission, within Methods or Acknowledgements | The generated content and its use | Assistive tools for language, grammar or structure (authors **and** reviewers) | Representative illustrations and visualisation help need disclosure; images presented as novel research images are inappropriate | May use GenAI to help write and format reports; uploading or copy-pasting the manuscript and AI-generated reviews are inappropriate |
| **IEEE** (PSPB Operations Manual amended 25 June 2026) | Not stated explicitly | Acknowledgments section | AI system, the specific sections affected, level of use | Editing and grammar enhancement: not required, **recommended** | AI-generated figures and images are disclosed like text; AI-simulated data must be labelled as AI-generated | No processing of manuscript content through a public AI platform for review content |
| **PLOS** (AI policy, undated) | No | In the article body: a Methods section, the Acknowledgements, or the figure legend(s) | Tools, how used and what was affected, how validity was evaluated | Spelling/grammar and rephrasing for clarity or conciseness; cover letters. Translation: recommended, not required | Allowed if primary research outputs are not misrepresented; disclose in the legend | AI cannot act as reviewer; no uploads; no summarising or evaluating submissions; allowable uses disclosed in the review form |
| **arXiv** (moderation policy, undated) | No | In the work, following the field's methodology-reporting norms | Any significant use of text-to-text generative AI | Only significant use must be reported | Not addressed | Not applicable |

## 2. Use-by-policy matrix (manuscripts and figures)

Generated from the rule table in `scripts/disclosure_builder.py` (`--matrix manuscript`),
so the script and this file cannot drift apart. `ec_living_guidelines` and `yok` are
explained in `funders_peer_review.md` and `turkey_eu.md`.

| Use | icmje | springer_nature | elsevier | wiley | taylor_francis | sage | ieee | plos | arxiv | ec_living_guidelines | yok |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `grammar_spelling` | D | D | E | E | D | E | R | E | ? | E | D |
| `language_polishing` | D | D | D | E | D | E | R | E | ? | E | D |
| `translation` | D | D | D | D | D | D | ? | R | D | D | D |
| `restructuring` | D | D | D | D | D | E | R | D | D | D | D |
| `drafting` | D | D | D | D | D | D | D | D | D | D | D |
| `interpretation` | ? | ✗ | ⚠ | D | ? | ? | ? | ⚠ | ? | ? | ⚠ |
| `ideation` | D | D | D | ? | D | D | D | ? | D | D | ⚠ |
| `literature_search` | D | D | D | E | D | D | D | D | D | D | D |
| `systematic_search_screening` | D | D | D | D | D | D | D | D | D | D | D |
| `reference_management` | D | D | E | E | D | D | D | D | D | D | D |
| `code` | D | D | D | D | D | D | D | D | D | D | D |
| `code_debugging` | D | D | D | E | D | D | D | D | D | D | D |
| `data_analysis` | D | D | D | D | D | D | D | D | D | D | D |
| `qualitative_coding` | D | D | D | D | D | ✗ | D | D | D | D | D |
| `synthetic_data` | ? | ? | ? | ? | ⚠ | ? | D | ? | ? | ? | ? |
| `synthetic_participants` | ? | ⚠ | ? | ? | ? | ✗ | ? | ? | ? | ? | ⚠ |
| `figure_explanatory` | D | D | D | D | D | D | D | D | D | D | D |
| `figure_data_visualization` | D | D | D | D | D | D | D | D | D | D | D |
| `figure_primary_image_edit` | ? | ✗ | ✗ | ✗ | ✗ | ✗ | ? | ⚠ | ? | ⚠ | ⚠ |
| `figure_graphical_abstract` | ? | ? | ✗ | ? | ? | ? | ? | ? | ? | ? | ? |
| `ai_as_author` | ✗ | ✗ | ✗ | ✗ | ✗ | ? | ? | ✗ | ✗ | ✗ | ✗ |
| `cite_ai_as_source` | ✗ | ? | ? | ? | ? | ⚠ | ? | ? | ? | ? | ? |
| `accessibility_assistive` | ? | ? | E | ? | ? | ? | ? | ? | ? | ? | ? |

Legend: ✗ forbidden · ⚠ avoid (discouraged) · D disclose (required) · R disclosure
recommended · E exempt from disclosure · ? not addressed by the fetched text (disclose
conservatively and ask the venue). “?” for primary-image editing or simulated
participants does **not** mean “allowed”: several other policies forbid them.

---

## 3. Key sentences, verbatim

### ICMJE (Recommendations, updated January 2026)

> At submission, the journal should require authors to disclose whether they used artificial intelligence (AI)-assisted technologies (such as Large Language Models [LLMs], chatbots, or image creators) in the production of submitted work (see also Section V).

> Authors who use such technology should describe, in both the cover letter and the submitted work in the appropriate section if applicable, how they used it. For example, if AI was used for writing assistance, describe this in the acknowledgment section (see Section II.A.3). If AI was used for data collection, analysis, or figure generation, authors should describe this use in the methods (see Section IV.A.3.d).

> Authors should not list AI and AI-assisted technologies as an author or co-author, nor cite AI as an author.

Section V.A adds: “Referencing AI-generated material as the primary source is not
acceptable.” and “Nondisclosure of AI use may require corrective action and may be
construed as misconduct in some circumstances (see Sections III.A and III.B).”

Section V.B (reviewers):

> Reviewers must adhere to the journal’s stated policy on the use of AI or request permission from the journal prior to using AI technology to facilitate their review.

> Reviewers who use AI in their review should disclose its use to the journal and ensure the content is appropriate and valid as AI can generate output that can be incorrect, incomplete, or biased.

Confidentiality “may prohibit the uploading of the manuscript to software or other AI
technologies where confidentiality cannot be assured unless such use of AI is
explicitly permitted by journals.”

### Springer Nature and Nature Portfolio (2026 risk-assessment framework)

> Springer Nature applies a risk-assessment approach, focusing on how AI is used, rather than whether it is used.

Manuscript-preparation table:
- **Green:** grammar and language editing, readability, formatting, translation,
  summarising author-written text.
- **Amber:** outlines, drafting sections from author input, alternative phrasing,
  reference-management support, visuals from verifiable source data.

Both carry the declaration “Clearly describe use and confirm author accountability”.
Red, “Not permitted”:

> Writing results or discussion independently; generating scientific claims or interpretations; producing data or figures as if empirical; listing AI as an author; creating content from text prompts or without verifiable source data or material

Visual content:

> AI generated visual content that is not derived from independently verifiable data, source material, methods, computational outputs or author-developed content is considered opaque and is not permitted by Springer Nature policy.

> Where AI-generated or AI-assisted visual content is published, information about the AI system used, the purpose of its use, and the extent of its contribution should be provided in an AI Declaration in your manuscript.

> Specific disclosure should be provided within the caption or legend of the visual content.

The Nature Portfolio page applies the same framework to authors, reviewers and editors.
Its core expectations include “Manuscripts, peer review reports, and sensitive data must
not be shared with unsecured or public AI systems.” Its Red examples include “Creating
photorealistic images (deepfakes)” and “Assigning authorship or accountability to AI
systems or tools”. Peer reviewers “May use AI to support peer review but must not upload
manuscript content to unsecured or public AI tools” and “Must not delegate critique or
judgement to AI systems”.

The current Nature Portfolio AI page (retrieved 2026-09-23) has **no separate
generative-image section**. Images now fall under the risk framework above. Quote only
this current text, not older secondary summaries of a Nature image ban.

Peer review (Springer Nature), Red, “Not permitted”:

> Uploading manuscripts to public/unsecured tools; generating full review reports; producing accept/reject recommendations; delegating critique to AI

### Elsevier (policy updated June 2026)

> Authors should disclose the use of AI tools for manuscript preparation in a separate AI declaration statement included in their manuscript upon submission.

> Please note: Basic checks of grammar, spelling and punctuation do not need a declaration statement. However, when an AI tool makes substantive changes to sentence structure or organization of a part of the text, this should be disclosed.

Recommended wording, section title then statement:

> Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

> During the preparation of this work, the author(s) used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.

The FAQ places it “at the end of your manuscript, immediately before the references”.
It also asks authors to “keep a separate record of which tool and model was used, and
how AI tools were used”.

Images:

> AI tools must not be used to create or alter images that represent primary observed or experimental data that were not directly obtained in the research. This includes adjustments to brightness, contrast, or color balance, which should only be done using established image processing software.

> Where AI tools are used in the generation of data visualizations, authors should disclose the name of the model or tool, the version used, and the developer or manufacturer, in the Methods section.

> General-purpose generative AI image tools must not be used to create graphical abstracts.

Reviewers:

> Reviewers should not upload a submitted manuscript or any part of it into an AI tool as this may violate the authors’ confidentiality and proprietary rights and, where the paper contains personally identifiable information, may breach data privacy rights.

> During the preparation of this report, I used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, I reviewed and edited the content as needed and I take full responsibility for its content.

### Wiley (AI guidelines, undated page)

> Authors must also disclose their use of AI Technologies when submitting a manuscript to a Wiley journal.

> AI Tools used solely for spelling, grammar, and general editing are not included in these disclosure requirements.

Where it goes:

> In your Acknowledgments when AI assists with manuscript drafting, editing, translation, or formatting.

> In your Methods when AI is used to assist with your research methodology, data collection or analysis, or literature review processes.

> In your figure captions when AI generates or edits any visual content that appears in your manuscript.

Authorship: AI tools “cannot fulfil the role of an author and must not be listed as one on
an article”. Images: “AI-edited photographs are not permitted in Wiley journals.” For
factual and evidential images, “AI Technologies must not be used to generate, modify, or
enhance these images, as they require verifiable accuracy.”

Reviewers:

> If this occurs, the reviewer must disclose that use to the handling editor when the review is submitted. Beyond this limited use, editors and peer reviewers are not permitted to upload manuscripts (or any parts of manuscripts including figures and tables) into AI Technology.

### Taylor & Francis (AI policy, undated page)

> Generative AI tools must not be listed as an author because such tools are unable to assume responsibility for the submitted content or manage copyright and licensing agreements.

> Authors must clearly acknowledge within the article or book any use of Generative AI tools through a statement that includes: the full name of the tool used (with version number), how it was used and the reason for use. For article submissions, a specific statement of AI usage disclosure must be included.

> Taylor & Francis does not permit the use of Generative AI in the creation or manipulation of outputs of research or clinical testing, for example, research results, clinical samples and diagnostic images.

Reviewers “must not upload unpublished manuscripts or project proposals, including any
associated files, images, or information, into Generative AI tools.”

> Reviewers must not use artificial intelligence tools to generate manuscript and proposal review reports, including LLM based tools like ChatGPT. However, Generative AI may be utilised to assist with improving review language.

### Sage (AI policy, undated page)

> We distinguish various uses for AI and related technologies as: assistive (and no longer requiring disclosure), generative (requiring disclosure), and prohibitive.

> AI tools that make suggestions to improve or enhance your own work, such as tools to improve language, grammar, or structure, are considered assistive AI tools and do not require disclosure by authors or reviewers.

> The primary or partial use of AI tools and/or LLMs that produce content such as references, text, images, or any other content that directly impacts the research methodology, analysis, results and/or conclusions must be disclosed upon submission so the editorial team can evaluate the content generated.

Uses to disclose “within the methods or acknowledgements” include literature-review help,
translation of research materials, AI-generated or AI-checked code, data-visualisation
help, representative illustrations and reference compilation. Uses listed as inappropriate
include “Conducting interviews with GenAI tools in lieu of participants for qualitative
research”, “Analysis of experiences and themes”, and “Generated images that are presented
as unique or novel research images”. Reviewers: “Peer reviewers may use generative AI
(GenAI) to help write and format the peer review reports, but they remain responsible for
the content of the reports.”

### IEEE (Author Center; PSPB Operations Manual amended 25 June 2026)

> The use of content generated by artificial intelligence (AI) in an article (including but not limited to text, figures, images, and code) shall be disclosed in the acknowledgments section of any article submitted to an IEEE publication. The AI system used shall be identified, and specific sections of the article that use AI-generated content shall be identified and accompanied by a brief explanation regarding the level at which the AI system was used to generate the content.

> The use of AI systems for editing and grammar enhancement is common practice and, as such, is generally outside the intent of the above policy. In this case, disclosure as noted above is not required, but recommended.

The PSPB manual adds: “Data generated by an AI tool to simulate or emulate a process must
be clearly labeled as generated by AI.” It also says an AI tool “may be cited in references
and bibliographies but only used as a source if the author has independently verified the
accuracy of the content.” Reviewers:

> Information or content contained in or about a manuscript under review shall not be processed through a public platform (directly or indirectly) for AI generation of content for a review.

### PLOS (AI policy, undated page)

> AI tools may be used to support development or revision of a PLOS submission. However, articles should report the listed authors’ own work and ideas, and AI tools cannot be listed as authors.

> For AI use by authors, disclosures should be in the body of the article, either in a dedicated section of the Methods, in the Acknowledgement section, or in the relevant figure legend(s).

A disclosure names the tools, describes how they were used and what they affected, and
gives “a description of how the user evaluated the validity of the tool’s outputs.”

> We do not require disclosure of AI use for language improvements, such as to correct spelling or grammar, or to rephrase content for clarity or conciseness. If an AI tool has been used for language translation, we recommend this be disclosed in order to preempt concerns, but this is not strictly required.

Reviewers: “AI tools cannot serve as peer reviewers or as decision-issuing editors, and
should not be used by reviewers or editors to summarize or evaluate submission content.”
Any allowed use goes “in the review form or decision letter”.

### arXiv (moderation policy, undated)

arXiv continues “to require authors to report in their work any significant use of
sophisticated tools, such as instruments and software; we now include in particular
text-to-text generative AI among those that should be reported consistent with subject
standards for methodology.” It also says “generative AI language tools should not be
listed as an author”.

---

## 4. UNVERIFIED on 2026-09-23 (not fetched, so the skill states nothing about them)

| Venue | What happened | What the skill does |
|---|---|---|
| COPE position statement “Authorship and AI tools” | publicationethics.org returned HTTP 403 (Cloudflare) to both the tool and the fetcher | Cites ICMJE for the no-AI-author rule instead; Wiley and Sage point to the COPE statement |
| Science / AAAS journals | science.org returned HTTP 403 | Generic rules plus an `[UNVERIFIED]` warning |
| Cell Press | cell.com journal-policy pages returned HTTP 403. A 2024 Cell Press author-guide PDF was reachable, but it predates Elsevier's June 2026 update, so it was not used | Generic rules plus a warning; read the specific journal's own policy page |
| ACM | acm.org returned HTTP 403 | Generic rules plus a warning |
| APA Journals | apa.org served a bot challenge (Incapsula) | Generic rules plus a warning. For APA *citation* formats for ChatGPT, see `alterlab-syllabus-ai-policy` |

## Sources (all retrieved 2026-09-23)

- ICMJE, *Defining the Role of Authors and Contributors* (II.A.3–4): https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html ; *AI Use by Authors*: https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html ; *AI Use by Reviewers*: https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-reviewers.html ; “Updated January 2026”: https://www.icmje.org/recommendations/
- Springer Nature, *AI use in manuscript preparation*: https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation ; *AI use in research practice*: https://www.springernature.com/gp/policies/editorial-policies/using-ai-in-research ; *AI use in peer review*: https://www.springernature.com/gp/policies/editorial-policies/using-ai-in-peer-review ; Nature Portfolio *Artificial Intelligence (AI)*: https://www.nature.com/nature-portfolio/editorial-policies/ai
- Elsevier, *Generative AI policies for journals* (“Policy updated June 2026”): https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals
- Wiley, *Ethics guidelines, Artificial Intelligence*: https://authorservices.wiley.com/ethics-guidelines/index.html ; *Using AI tools in your research*: https://www.wiley.com/en-us/publish/article/ai-guidelines
- Taylor & Francis, *AI Policy*: https://taylorandfrancis.com/our-policies/ai-policy/
- Sage, *Artificial intelligence policy*: https://www.sagepub.com/journals/publication-ethics-policies/artificial-intelligence-policy
- IEEE Author Center, *Submission and peer review policies*: https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/ ; IEEE PSPB Operations Manual (amended 25 June 2026), pp. 5–6 and 8.2: https://pspb.ieee.org/images/files/PSPB/opsmanual.pdf
- PLOS ONE, *Ethical Publishing Practice → Artificial Intelligence Tools and Technologies*: https://journals.plos.org/plosone/s/ethical-publishing-practice
- arXiv, *Moderation → Policy for authors' use of generative AI language tools*: https://info.arxiv.org/help/moderation/index.html
