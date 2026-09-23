#!/usr/bin/env python3
"""disclosure_builder.py - Draft a generative-AI use disclosure and check it against the
publisher, funder or institutional policy that applies.

Reads a small JSON description of how AI was used and prints:
  * a disclosure statement in English or Turkish, worded for the context
    (manuscript, figure, grant, peer_review, thesis, ethics_application);
  * where the statement goes under each applicable policy;
  * WARNINGS where a policy forbids or discourages a declared use, or where a field the
    policy asks for (version, date, provider, sections, verification) is missing;
  * NOTES for uses a policy exempts from disclosure or does not address.

Design constraints (AlterLab house style):
- STDLIB ONLY, deterministic, no network access.
- NO FABRICATION. Every rule in POLICIES was transcribed from a primary source fetched on
  POLICY_DATA_DATE; the verbatim wording and URLs live in ../references/*.md. A use that a
  fetched source does not address is encoded as CHECK ("not addressed"), never guessed.
  Venues whose policy page could not be fetched (see UNVERIFIED) fall back to the
  conservative generic rules and are reported as UNVERIFIED.
- NO CONCEALMENT. A FORBIDDEN use is left out of the drafted statement and raised as a
  warning that tells the user to remove the use or raise it with the editor or funder;
  the script never words a disclosure so as to hide or understate a use.

Input JSON (keys other than "context" and "venue" are optional):
  {
    "context": "manuscript",            # manuscript|figure|grant|peer_review|thesis|ethics_application
    "venue": "elsevier",                # policy key, see --list-venues (aliases accepted)
    "also_apply": ["yok"],              # extra policies, e.g. YOK for an author in Turkey
    "language": "en",                   # en|tr
    "authors": "plural",                # plural|single (peer_review is always first person)
    "tools": [{"name": "ChatGPT", "version": "GPT-5", "provider": "OpenAI",
               "date": "March 2026", "purposes": ["language_polishing"]}],
    "purposes": ["code"],               # applied to every tool that lists none of its own
    "sections": ["Introduction", "Methods"],
    "human_verification": "All suggestions were checked against the cited sources.",
    "confidential_input": false,        # false = confirm no confidential data went in
    "figure_label": "Figure 2",
    "include_exempt": false             # also describe uses the policy exempts
  }

Usage:
  uv run python disclosure_builder.py input.json          # or "-" to read stdin
  uv run python disclosure_builder.py input.json --json   # machine-readable result
  uv run python disclosure_builder.py --list-venues
  uv run python disclosure_builder.py --list-purposes
  uv run python disclosure_builder.py --matrix peer_review
  uv run python disclosure_builder.py --self-test

Exit codes: 0 = statement drafted (read the WARNINGS); 1 = at least one FORBIDDEN use;
            2 = bad input or usage.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field

POLICY_DATA_DATE = "2026-09-23"

FORBIDDEN = "FORBIDDEN"      # the policy says the use is not permitted
AVOID = "AVOID"              # the policy says it should not be done / refrain (softer wording)
REQUIRED = "REQUIRED"        # the policy requires the use to be disclosed
CHECK = "CHECK"              # the fetched policy does not address the use: disclose, ask the venue
RECOMMENDED = "RECOMMENDED"  # disclosure encouraged / expected / recommended, not mandated
EXEMPT = "EXEMPT"            # the policy says no disclosure is needed
RANK = {FORBIDDEN: 5, AVOID: 4, REQUIRED: 3, CHECK: 2, RECOMMENDED: 1, EXEMPT: 0}
SYMBOL = {FORBIDDEN: "✗", AVOID: "⚠", REQUIRED: "D", CHECK: "?", RECOMMENDED: "R", EXEMPT: "E"}

CONTEXTS = ("manuscript", "figure", "grant", "peer_review", "thesis", "ethics_application")
LANGS = ("en", "tr")

# --------------------------------------------------------------------------- #
# Uses of AI. EN phrase follows "to ..."; TR phrase precedes "amacıyla".       #
# --------------------------------------------------------------------------- #
PURPOSES: dict[str, tuple[str, str]] = {
    "grammar_spelling": ("check grammar, spelling and punctuation",
                         "dil bilgisi, yazım ve noktalama denetimi"),
    "language_polishing": ("improve the wording and readability of text written by the authors",
                           "yazarlarca yazılan metnin ifadesinin ve okunabilirliğinin iyileştirilmesi"),
    "translation": ("translate text written by the authors",
                    "yazarlarca yazılan metnin çevirisi"),
    "restructuring": ("suggest a reorganisation of sections and of the flow of the argument",
                      "bölümlerin ve argüman akışının yeniden düzenlenmesine yönelik öneri alınması"),
    "drafting": ("generate draft text", "taslak metin üretilmesi"),
    "interpretation": ("interpret results or draft the discussion",
                       "bulguların yorumlanması veya tartışma bölümünün taslağının yazılması"),
    "ideation": ("brainstorm ideas, research questions or hypotheses",
                 "fikir, araştırma sorusu veya hipotez üretimi (beyin fırtınası)"),
    "literature_search": ("search for and summarise literature",
                          "literatürün taranması ve özetlenmesi"),
    "systematic_search_screening": ("design or run literature searches or screen studies for inclusion",
                                    "literatür arama stratejisinin tasarlanması/yürütülmesi veya çalışmaların taranıp seçilmesi"),
    "reference_management": ("organise and format references",
                             "kaynakların düzenlenmesi ve biçimlendirilmesi"),
    "code": ("write analysis code", "analiz kodunun yazılması"),
    "code_debugging": ("debug, format or document code",
                       "kodun hata ayıklaması, biçimlendirilmesi veya belgelenmesi"),
    "data_analysis": ("analyse data or interpret statistical output",
                      "verilerin analiz edilmesi veya istatistiksel çıktıların yorumlanması"),
    "qualitative_coding": ("code qualitative data or identify themes",
                           "nitel verilerin kodlanması veya temaların belirlenmesi"),
    "synthetic_data": ("generate synthetic or simulated data",
                       "sentetik veya simüle veri üretilmesi"),
    "synthetic_participants": ("simulate participants or their responses",
                               "katılımcıların veya katılımcı yanıtlarının simüle edilmesi"),
    "figure_explanatory": ("create explanatory (conceptual or schematic) figures",
                           "açıklayıcı (kavramsal veya şematik) şekillerin oluşturulması"),
    "figure_data_visualization": ("create data visualisations from the study data",
                                  "çalışma verilerinden veri görselleştirmelerinin oluşturulması"),
    "figure_primary_image_edit": ("generate or alter primary research images (micrographs, blots, scans, photographs)",
                                  "birincil araştırma görüntülerinin (mikrograf, blot, tarama, fotoğraf) üretilmesi veya değiştirilmesi"),
    "figure_graphical_abstract": ("create the graphical abstract",
                                  "grafik özetin oluşturulması"),
    "ai_as_author": ("be listed as an author", "yazar olarak gösterilmesi"),
    "cite_ai_as_source": ("serve as a cited source of information",
                          "bilgi kaynağı olarak atıf yapılması"),
    "accessibility_assistive": ("provide disability-related assistive support",
                                "engellilik kaynaklı erişilebilirlik desteği sağlanması"),
    "upload_confidential": ("process confidential, unpublished or personal content",
                            "gizli, yayımlanmamış veya kişisel içeriğin işlenmesi"),
    "grant_interview": ("assist during the funding interview",
                        "fon mülakatı sırasında yardım alınması"),
    "review_language_polish": ("polish the language of my own review comments",
                               "kendi değerlendirme yorumlarımın dilinin düzeltilmesi"),
    "review_literature_search": ("search publicly available literature on the topic",
                                 "konuyla ilgili kamuya açık literatürün taranması"),
    "review_summarize_submission": ("summarise the submission",
                                    "başvurunun/makalenin özetlenmesi"),
    "review_draft_report": ("draft the review or critique",
                            "değerlendirme raporunun veya eleştirinin taslağının yazılması"),
    "review_assess_merit": ("assess the submission's merit or recommend a decision",
                            "başvurunun/makalenin niteliğinin değerlendirilmesi veya karar önerilmesi"),
}

MANUSCRIPT_PURPOSES = (
    "grammar_spelling", "language_polishing", "translation", "restructuring", "drafting",
    "interpretation", "ideation", "literature_search", "systematic_search_screening",
    "reference_management", "code", "code_debugging", "data_analysis", "qualitative_coding",
    "synthetic_data", "synthetic_participants", "figure_explanatory",
    "figure_data_visualization", "figure_primary_image_edit", "figure_graphical_abstract",
    "ai_as_author", "cite_ai_as_source", "accessibility_assistive",
)
MATRIX_ROWS = {
    "manuscript": MANUSCRIPT_PURPOSES,
    "thesis": MANUSCRIPT_PURPOSES,
    "figure": ("figure_explanatory", "figure_data_visualization", "figure_primary_image_edit",
               "figure_graphical_abstract"),
    "grant": ("grammar_spelling", "language_polishing", "translation", "drafting", "ideation",
              "literature_search", "code", "data_analysis", "synthetic_data",
              "figure_explanatory", "figure_primary_image_edit", "upload_confidential",
              "grant_interview"),
    "peer_review": ("review_language_polish", "review_literature_search",
                    "review_summarize_submission", "review_draft_report", "review_assess_merit",
                    "upload_confidential", "accessibility_assistive"),
    "ethics_application": ("literature_search", "translation", "data_analysis",
                           "qualitative_coding", "synthetic_data", "synthetic_participants"),
}
REVIEW_ONLY = {"review_language_polish", "review_literature_search", "review_summarize_submission",
               "review_draft_report", "review_assess_merit"}


@dataclass(frozen=True)
class Rule:
    status: str
    note: str
    note_tr: str = ""


@dataclass(frozen=True)
class Ctx:
    placement: str
    placement_tr: str
    default: Rule
    rules: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    key: str
    label: str
    as_of: str
    ref: str
    contexts: dict
    requires: tuple = ()       # fields the policy asks every disclosure to state
    info: dict = field(default_factory=dict)  # context -> extra fact worth surfacing


def R(status: str, note: str, note_tr: str = "") -> Rule:
    return Rule(status, note, note_tr)


PUB = "references/publisher_policies.md"
FUN = "references/funders_peer_review.md"
TRE = "references/turkey_eu.md"

# Rules shared by several publishers' manuscript and figure contexts.
_NO_AUTHOR = "no verified policy allows an AI tool to be listed as an author"

# --------------------------------------------------------------------------- #
# POLICY TABLE - transcribed from sources fetched on POLICY_DATA_DATE.          #
# Do not edit a rule without re-reading the source quoted in references/.       #
# --------------------------------------------------------------------------- #
_ICMJE_MS = Ctx(
    "Describe the use in the cover letter AND in the manuscript: writing assistance -> Acknowledgments; data collection, analysis or figure generation -> Methods (ICMJE II.A.4, V.A).",
    "Kullanımı hem ön yazıda (cover letter) hem makalede açıklayın: yazım desteği -> Teşekkür; veri toplama, analiz veya şekil üretimi -> Yöntem (ICMJE II.A.4, V.A).",
    R(REQUIRED, "ICMJE II.A.4: journals should require authors to disclose AI-assisted technologies; no exemption is stated."),
    {
        "ai_as_author": R(FORBIDDEN, "ICMJE II.A.4: authors should not list AI as an author or co-author, nor cite AI as an author."),
        "cite_ai_as_source": R(FORBIDDEN, "ICMJE V.A: referencing AI-generated material as the primary source is not acceptable."),
    },
)

_SN_MS = Ctx(
    "Describe the use and confirm author accountability in the manuscript's AI declaration (Springer Nature names an 'AI Declaration' for visual content); methodological (Amber) uses also need a clear methods description with validation steps.",
    "Kullanımı makalenin YZ beyanında (AI Declaration) açıklayın ve yazar sorumluluğunu teyit edin; yöntemsel (Amber) kullanımlar yöntem bölümünde doğrulama adımlarıyla birlikte anlatılmalıdır.",
    R(REQUIRED, "Springer Nature risk framework: Green and Amber uses -> 'Clearly describe use and confirm author accountability'."),
    {
        "drafting": R(REQUIRED, "Springer Nature Amber: drafting sections based on author input - all AI-generated or assisted content must be clearly labelled; AI writing results or discussion independently is Red (not permitted)."),
        "interpretation": R(FORBIDDEN, "Springer Nature Red: 'Writing results or discussion independently; generating scientific claims or interpretations'."),
        "ideation": R(REQUIRED, "Nature Portfolio framework: stress-testing research questions is Green; generating hypotheses, analyses or conclusions and presenting them as human-derived is Red."),
        "synthetic_participants": R(AVOID, "Nature Portfolio Red: 'Fabricating data, citations or results' - simulated responses must never be presented as real data."),
        "figure_explanatory": R(REQUIRED, "Springer Nature: permitted only when derived from verifiable data, source material or author-developed content; disclose model and purpose in the caption/legend and the AI Declaration."),
        "figure_data_visualization": R(REQUIRED, "Springer Nature: permitted when derived from verifiable inputs; disclose model and purpose in the caption/legend and the AI Declaration."),
        "figure_primary_image_edit": R(FORBIDDEN, "Springer Nature Red: 'producing data or figures as if empirical'; AI visual content without verifiable inputs 'is not permitted by Springer Nature policy'."),
        "figure_graphical_abstract": R(CHECK, "Springer Nature: visual content is permitted only with verifiable inputs; content created from text prompts alone is Red. Graphical abstracts are not singled out."),
        "ai_as_author": R(FORBIDDEN, "Springer Nature Red: 'listing AI as an author'."),
    },
)

_ELS_MS = Ctx(
    "Separate section 'Declaration of generative AI and AI-assisted technologies in the manuscript preparation process' at the end of the manuscript, immediately before the references; AI used in research methods, code or data visualisations goes in the Methods section (tool, version, developer).",
    "Kaynakçadan hemen önce, makalenin sonunda ayrı bir beyan bölümü: 'Declaration of generative AI and AI-assisted technologies in the manuscript preparation process'; araştırma yönteminde, kodda veya veri görselleştirmede kullanılan YZ Yöntem bölümünde (araç, sürüm, geliştirici) açıklanır.",
    R(REQUIRED, "Elsevier (policy updated June 2026): disclose AI tools used for manuscript preparation in a separate AI declaration statement."),
    {
        "grammar_spelling": R(EXEMPT, "Elsevier: 'Basic checks of grammar, spelling and punctuation do not need a declaration statement.'"),
        "reference_management": R(EXEMPT, "Elsevier FAQ: basic reference-manager functions need no disclosure; using an AI tool to select, collate, generate or edit references must be declared."),
        "accessibility_assistive": R(EXEMPT, "Elsevier: no disclosure for AI features within specialist disability-related assistive technology used solely for accessibility."),
        "language_polishing": R(REQUIRED, "Elsevier: only basic grammar/spelling/punctuation checks are exempt; substantive changes to sentence structure or organisation must be disclosed."),
        "translation": R(REQUIRED, "Elsevier FAQ: disclose the use of AI tools for translations included in the manuscript."),
        "code": R(REQUIRED, "Elsevier FAQ: code written or edited with AI as part of the research is declared in detail in the Methods section."),
        "code_debugging": R(REQUIRED, "Elsevier FAQ: code written or edited with AI as part of the research is declared in detail in the Methods section."),
        "data_analysis": R(REQUIRED, "Elsevier: AI used in research design or methods is described reproducibly in the Methods section (tool, version, developer)."),
        "drafting": R(REQUIRED, "Elsevier FAQ: generating sections of a manuscript without genuine intellectual contribution from the author is an inappropriate use."),
        "interpretation": R(AVOID, "Elsevier: AI tools 'must never be used as a substitute for human critical thinking, expertise and evaluation'."),
        "figure_explanatory": R(REQUIRED, "Elsevier: explanatory images are permitted; disclose in the figure caption and the manuscript's AI disclosure statement."),
        "figure_data_visualization": R(REQUIRED, "Elsevier: permitted only if directly derived from the data by reproducible methods; disclose tool, version and developer in the Methods section."),
        "figure_primary_image_edit": R(FORBIDDEN, "Elsevier: AI tools must not be used to create or alter primary research images, including brightness, contrast or colour adjustments."),
        "figure_graphical_abstract": R(FORBIDDEN, "Elsevier: 'General-purpose generative AI image tools must not be used to create graphical abstracts.'"),
        "ai_as_author": R(FORBIDDEN, "Elsevier: authors should not list AI tools as an author or co-author, nor cite AI tools as an author."),
    },
)

_WILEY_MS = Ctx(
    "Acknowledgments for drafting, editing, translation or formatting help; Methods for AI in methodology, data collection/analysis or literature review; figure captions for any AI-generated or AI-edited visual.",
    "Taslak, düzenleme, çeviri veya biçim desteği -> Teşekkür; yöntem, veri toplama/analiz veya literatür taramasında YZ -> Yöntem; YZ ile üretilen/düzenlenen her görsel -> şekil altyazısı.",
    R(REQUIRED, "Wiley: authors must disclose their use of AI Technologies when submitting (AI guidelines)."),
    {
        "grammar_spelling": R(EXEMPT, "Wiley: AI tools used solely for spelling, grammar and general editing are not included in the disclosure requirements."),
        "language_polishing": R(EXEMPT, "Wiley table: 'Language polishing' (grammar, word choice, rephrasing awkward sentences) does not require disclosure."),
        "reference_management": R(EXEMPT, "Wiley tables: formatting citations and organising references do not require disclosure."),
        "literature_search": R(EXEMPT, "Wiley table: keyword search support and summaries for the author's own understanding do not require disclosure; agentic search, screening, or synthesis used in the manuscript does."),
        "code_debugging": R(EXEMPT, "Wiley table: debugging, code style and documentation do not require disclosure."),
        "restructuring": R(REQUIRED, "Wiley table: 'Cohesion and organization' (restructuring arguments or document flow) requires disclosure."),
        "translation": R(REQUIRED, "Wiley table: AI translation of manuscript sections requires disclosure."),
        "systematic_search_screening": R(REQUIRED, "Wiley table: agentic search and screening/selection for reviews require disclosure (Methods)."),
        "qualitative_coding": R(REQUIRED, "Wiley table: AI coding of interview or textual data requires disclosure (Methods)."),
        "figure_explanatory": R(REQUIRED, "Wiley table: research illustrations generated or edited by AI require disclosure in the caption."),
        "figure_data_visualization": R(REQUIRED, "Wiley table: data visualisations generated by AI require disclosure in the caption."),
        "figure_primary_image_edit": R(FORBIDDEN, "Wiley: 'AI-edited photographs are not permitted'; factual and evidential images must not be generated, modified or enhanced with AI."),
        "ai_as_author": R(FORBIDDEN, "Wiley: AI tools 'cannot fulfil the role of an author and must not be listed as one'."),
        "ideation": R(CHECK, "Wiley's tables do not list brainstorming; study-design uses such as AI-generated survey questions require disclosure."),
        "interpretation": R(REQUIRED, "Wiley table: AI generating interpretations of results or synthesising findings requires disclosure (Methods)."),
        "data_analysis": R(REQUIRED, "Wiley table: AI statistical analysis or interpretation of test results requires disclosure (Methods); routine transformations and data cleaning do not."),
    },
)

_TF_MS = Ctx(
    "A specific AI-usage disclosure statement inside the article giving the full tool name with version number, how it was used and why (book authors: preface or introduction, after editorial approval).",
    "Makale içinde, aracın tam adını ve sürüm numarasını, nasıl ve neden kullanıldığını belirten ayrı bir YZ kullanım beyanı (kitaplarda editör onayından sonra önsöz veya giriş).",
    R(REQUIRED, "Taylor & Francis: authors must acknowledge any use of Generative AI tools; some journals allow nothing beyond language improvement."),
    {
        "figure_explanatory": R(REQUIRED, "T&F: GenAI is permitted to assist conceptual illustrations of processes, flow diagrams or teaching illustrations."),
        "figure_data_visualization": R(REQUIRED, "T&F: GenAI is permitted to assist research data visualisations."),
        "figure_primary_image_edit": R(FORBIDDEN, "T&F: GenAI is not permitted in the creation or manipulation of research results, clinical samples or diagnostic images."),
        "synthetic_data": R(AVOID, "T&F: do not submit work using synthetic data generated to substitute missing data without robust methodology."),
        "drafting": R(REQUIRED, "T&F: do not submit text or code generated without rigorous revision."),
        "ai_as_author": R(FORBIDDEN, "T&F: Generative AI tools must not be listed as an author."),
    },
)

_SAGE_MS = Ctx(
    "Disclose on submission, within the Methods or the Acknowledgements.",
    "Gönderim sırasında, Yöntem veya Teşekkür bölümünde beyan edin.",
    R(REQUIRED, "Sage: AI-generated content (references, text, images, or content affecting methods, analysis, results or conclusions) must be disclosed on submission."),
    {
        "grammar_spelling": R(EXEMPT, "Sage: assistive tools that improve language, grammar or structure need no disclosure."),
        "language_polishing": R(EXEMPT, "Sage: assistive tools that improve language, grammar or structure need no disclosure."),
        "restructuring": R(EXEMPT, "Sage: assistive tools that improve language, grammar or structure need no disclosure."),
        "translation": R(REQUIRED, "Sage: translation of materials as part of the research process requires disclosure; translating the manuscript itself is not addressed."),
        "literature_search": R(REQUIRED, "Sage: assistance with literature review or compilation of sources requires disclosure."),
        "reference_management": R(REQUIRED, "Sage: assistance with compilation of references requires disclosure."),
        "code_debugging": R(REQUIRED, "Sage: code enhanced or checked for errors by AI requires disclosure."),
        "qualitative_coding": R(FORBIDDEN, "Sage lists 'Analysis of experiences and themes' as an inappropriate use of GenAI."),
        "synthetic_participants": R(FORBIDDEN, "Sage: 'Conducting interviews with GenAI tools in lieu of participants' is an inappropriate use."),
        "figure_primary_image_edit": R(FORBIDDEN, "Sage: 'Generated images that are presented as unique or novel research images' is an inappropriate use."),
        "cite_ai_as_source": R(AVOID, "Sage: cite original sources, rather than GenAI tools as primary sources."),
        "ai_as_author": R(CHECK, "Not addressed on Sage's AI-policy page, which points to COPE's position statement on authorship and AI tools."),
    },
)

_IEEE_MS = Ctx(
    "Acknowledgments section: identify the AI system, the specific sections that contain AI-generated content, and the level at which AI was used.",
    "Teşekkür bölümü: YZ sistemini, YZ ile üretilmiş içerik barındıran bölümleri ve kullanım düzeyini belirtin.",
    R(REQUIRED, "IEEE: AI-generated content (text, figures, images, code) shall be disclosed in the acknowledgments."),
    {
        "grammar_spelling": R(RECOMMENDED, "IEEE: editing and grammar enhancement is outside the policy; disclosure not required but recommended (leave the reference list out of the tool)."),
        "language_polishing": R(RECOMMENDED, "IEEE PSPB: language improvement of human text needs no acknowledgment if it does not change the meaning or add intellectual content; disclosure recommended."),
        "synthetic_data": R(REQUIRED, "IEEE PSPB: data generated by an AI tool to simulate or emulate a process must be clearly labeled as generated by AI."),
        "cite_ai_as_source": R(CHECK, "IEEE PSPB: an AI tool may be cited, but used as a source only if the author independently verified the content."),
        "ai_as_author": R(CHECK, "Not stated explicitly in the IEEE text fetched; IEEE requires acknowledging AI-generated content instead."),
        "translation": R(CHECK, "Translation is not addressed by the IEEE text fetched."),
        "restructuring": R(RECOMMENDED, "IEEE: editing is outside the disclosure policy (recommended) provided the tool does not change the meaning or add intellectual content."),
    },
)

_PLOS_MS = Ctx(
    "In the body of the article: a dedicated section of the Methods, the Acknowledgements, or the relevant figure legend(s). State the tool(s), how they were used and what was affected, and how you evaluated the validity of the outputs. Cover letters need no disclosure.",
    "Makale gövdesinde: Yöntem içinde ayrı bir alt bölüm, Teşekkür bölümü veya ilgili şekil açıklaması. Aracı, nasıl kullanıldığını, neyi etkilediğini ve çıktıların geçerliliğinin nasıl değerlendirildiğini yazın. Ön yazı için beyan gerekmez.",
    R(REQUIRED, "PLOS: any AI use to generate or revise content, or to support the research, must be clearly disclosed."),
    {
        "grammar_spelling": R(EXEMPT, "PLOS FAQ: no disclosure for language improvements such as spelling or grammar correction."),
        "language_polishing": R(EXEMPT, "PLOS FAQ: no disclosure for rephrasing content for clarity or conciseness."),
        "translation": R(RECOMMENDED, "PLOS FAQ: disclosing AI translation is recommended but not strictly required."),
        "code": R(REQUIRED, "PLOS FAQ: AI generation or development of analysis scripts or software code must be disclosed."),
        "figure_explanatory": R(REQUIRED, "PLOS FAQ: AI use in figure preparation is disclosed in the figure legend."),
        "figure_data_visualization": R(REQUIRED, "PLOS FAQ: AI use in figure preparation is disclosed in the figure legend."),
        "figure_primary_image_edit": R(AVOID, "PLOS: using AI to fabricate or otherwise misrepresent primary research data is a breach of publication ethics."),
        "interpretation": R(AVOID, "PLOS: statements reporting hypotheses, interpretations, results, conclusions and implications must represent the authors' own ideas."),
        "ideation": R(CHECK, "PLOS: statements reporting hypotheses must represent the authors' own ideas; disclose any AI brainstorming."),
        "ai_as_author": R(FORBIDDEN, "PLOS: AI tools cannot be listed as authors."),
    },
)

_ARXIV_MS = Ctx(
    "In the work itself: report any significant use of text-to-text generative AI, consistent with your field's standards for reporting methodology.",
    "Çalışmanın içinde: metin üreten YZ'nin her önemli kullanımını, alanınızın yöntem raporlama standartlarına uygun biçimde bildirin.",
    R(REQUIRED, "arXiv: authors must report significant use of sophisticated tools, including text-to-text generative AI."),
    {
        "grammar_spelling": R(CHECK, "arXiv requires reporting 'significant use' only; whether minor language help counts is not addressed."),
        "language_polishing": R(CHECK, "arXiv requires reporting 'significant use' only; whether minor language help counts is not addressed."),
        "ai_as_author": R(FORBIDDEN, "arXiv: generative AI language tools should not be listed as an author."),
    },
)

_YOK_MS = Ctx(
    "Method section: explain the parts produced with generative AI - which tool and version, when, and at which stage or place of the study (YÖK guide, 2024). For theses, also follow your graduate institute's thesis-writing guide (institution-specific, not part of the YÖK guide).",
    "Yöntem bölümü: ÜYZ kullanılan bölümleri açıklayın - hangi araç ve sürüm, ne zaman, çalışmanın hangi aşamasında veya yerinde (YÖK Etik Rehberi, 2024). Tezlerde ayrıca enstitünüzün tez yazım kılavuzuna uyun (kuruma özgüdür; YÖK rehberinin parçası değildir).",
    R(REQUIRED, "YÖK guide: the parts where generative AI was used must be explained in the method section; ignoring this leads to disciplinary responsibility.",
      "YÖK Rehberi: ÜYZ kullanılan bölümlerin yöntem kısmında açıklanması gereklidir; göz ardı edilmesi disiplin sorumluluğuna yol açar."),
    {
        "ai_as_author": R(FORBIDDEN, "YÖK guide: generative AI cannot be an author of scientific work.",
                          "YÖK Rehberi: ÜYZ bilimsel çalışmalarda yazar olarak yer alamaz."),
        "synthetic_participants": R(AVOID, "YÖK guide: using generative AI instead of real participants is not correct.",
                                    "YÖK Rehberi: gerçek katılımcılar yerine ÜYZ kullanılması doğru değildir."),
        "ideation": R(AVOID, "YÖK guide: AI use should not extend to stages needing high-level expertise such as hypothesis development, discussion and interpretation.",
                      "YÖK Rehberi: ÜYZ kullanımı hipotez geliştirme, tartışma ve yorumlama gibi üst düzey uzmanlık gerektiren aşamaları içermemelidir."),
        "interpretation": R(AVOID, "YÖK guide: AI use should not extend to discussion and interpretation stages.",
                            "YÖK Rehberi: ÜYZ kullanımı tartışma ve yorumlama aşamalarını içermemelidir."),
        "figure_primary_image_edit": R(AVOID, "YÖK guide: data fabrication, forgery and falsification are among the ethical problems AI use can cause.",
                                       "YÖK Rehberi: veri uydurma, veri sahteciliği ve veri tahrifatı ÜYZ kullanımının yol açabileceği etik sorunlar arasındadır."),
        "drafting": R(REQUIRED, "YÖK guide: having AI write an entire article is 'not conceivable'; declare every part it drafted.",
                      "YÖK Rehberi: bir makalenin tamamının ÜYZ'ye yazdırılması düşünülemez; taslağını ÜYZ'nin yazdığı her bölümü beyan edin."),
    },
)

_GENERIC_MS = Ctx(
    "Follow the venue's own instructions. Where it gives none, use the ICMJE pattern: writing assistance -> Acknowledgments; data, analysis or figures -> Methods; and mention the use in the cover letter.",
    "Yayın organının kendi yönergesine uyun. Yönerge yoksa ICMJE düzenini kullanın: yazım desteği -> Teşekkür; veri, analiz veya şekil -> Yöntem; ayrıca ön yazıda belirtin.",
    R(REQUIRED, "Unverified or unknown venue: disclose every use conservatively and check the live author guidelines."),
    {
        "ai_as_author": R(FORBIDDEN, "Not permitted by any policy verified for this skill (" + _NO_AUTHOR + ")."),
        "figure_primary_image_edit": R(AVOID, "Forbidden by Elsevier, Wiley, T&F and Springer Nature (without verifiable inputs); check the venue's image policy."),
        "figure_graphical_abstract": R(CHECK, "Elsevier forbids general-purpose generative image tools for graphical abstracts; check this venue."),
        "synthetic_participants": R(AVOID, "Sage forbids and YÖK rejects replacing participants with generative AI."),
    },
)


def _fig(ms: Ctx, placement: str, placement_tr: str) -> Ctx:
    return Ctx(placement, placement_tr, ms.default, ms.rules)


POLICIES: dict[str, Policy] = {
    "icmje": Policy(
        "icmje", "ICMJE Recommendations", "updated January 2026", PUB,
        {
            "manuscript": _ICMJE_MS,
            "figure": _fig(_ICMJE_MS, "Figure generation with AI is described in the Methods (ICMJE II.A.4) and in the cover letter.",
                           "YZ ile şekil üretimi Yöntem bölümünde (ICMJE II.A.4) ve ön yazıda açıklanır."),
            "peer_review": Ctx(
                "Disclose any AI use to the journal (ICMJE V.B).",
                "YZ kullanımını dergiye bildirin (ICMJE V.B).",
                R(CHECK, "ICMJE V.B: follow the journal's stated AI policy or request permission before using AI to facilitate a review."),
                {
                    "upload_confidential": R(FORBIDDEN, "ICMJE V.B: confidentiality may prohibit uploading the manuscript where confidentiality cannot be assured, unless the journal explicitly permits it."),
                    "review_summarize_submission": R(FORBIDDEN, "Requires entering the manuscript into the tool - see ICMJE V.B on confidentiality."),
                }),
        }),
    "springer_nature": Policy(
        "springer_nature", "Springer Nature / Nature Portfolio", "2026 risk-assessment framework", PUB,
        {
            "manuscript": _SN_MS,
            "figure": _fig(_SN_MS, "Give specific disclosure in the caption or legend AND describe the AI system, purpose and extent of contribution in the manuscript's AI Declaration.",
                           "Şekil altyazısında özel beyan verin VE makalenin YZ beyanında (AI Declaration) YZ sistemini, amacını ve katkının kapsamını açıklayın."),
            "peer_review": Ctx(
                "Describe the AI use in the review report and take accountability for all its content.",
                "YZ kullanımını değerlendirme raporunda açıklayın ve raporun tüm içeriğinin sorumluluğunu üstlenin.",
                R(CHECK, "Springer Nature: judge the use against the Green/Amber/Red peer-review framework."),
                {
                    "review_language_polish": R(REQUIRED, "Springer Nature Green: improving clarity, tone and structure of reviewer comments - describe the use in the report."),
                    "review_literature_search": R(REQUIRED, "Springer Nature Amber: comparing to general literature patterns - describe the use and confirm independent judgement."),
                    "review_summarize_submission": R(FORBIDDEN, "Springer Nature Red: uploading manuscripts to public/unsecured tools; its guidance says to work from your own notes, not the manuscript."),
                    "review_draft_report": R(FORBIDDEN, "Springer Nature Red: 'generating full review reports'."),
                    "review_assess_merit": R(FORBIDDEN, "Springer Nature Red: 'producing accept/reject recommendations; delegating critique to AI'."),
                    "upload_confidential": R(FORBIDDEN, "Springer Nature Red: 'Uploading manuscripts to public/unsecured tools'."),
                }),
        }),
    "elsevier": Policy(
        "elsevier", "Elsevier journals", "policy updated June 2026", PUB,
        {
            "manuscript": _ELS_MS,
            "figure": _fig(_ELS_MS, "Explanatory images: figure caption AND the AI declaration section. Data visualisations and images produced as part of the research methods: Methods section (tool, version, developer). AI cover art needs prior permission from the editor and publisher.",
                           "Açıklayıcı görseller: şekil altyazısı VE YZ beyan bölümü. Veri görselleştirmeleri ve araştırma yönteminin parçası olan görüntüler: Yöntem bölümü (araç, sürüm, geliştirici). YZ ile üretilmiş kapak görseli için editör ve yayıncıdan önceden izin gerekir."),
            "peer_review": Ctx(
                "Disclose in the review report (tool and purpose); use only private AI tools.",
                "Değerlendirme raporunda (araç ve amaç) beyan edin; yalnızca özel (private) YZ araçları kullanın.",
                R(CHECK, "Elsevier: AI may only be used in a supportive capacity with confidentiality maintained."),
                {
                    "review_language_polish": R(REQUIRED, "Elsevier: supportive use to improve the language and structure of a review report is allowed with a private tool; disclose tool and purpose (basic spelling/grammar checks exempt)."),
                    "review_literature_search": R(REQUIRED, "Elsevier: assisting a background literature search is a supportive use; disclose tool and purpose."),
                    "review_summarize_submission": R(FORBIDDEN, "Elsevier: reviewers should not upload a submitted manuscript or any part of it into an AI tool."),
                    "review_draft_report": R(FORBIDDEN, "Elsevier: AI tools cannot replace a reviewer's critical thinking or independent evaluation; supportive use only."),
                    "review_assess_merit": R(FORBIDDEN, "Elsevier: reviewers are responsible for the scientific assessment; AI cannot replace independent evaluation."),
                    "upload_confidential": R(FORBIDDEN, "Elsevier: reviewers should not upload a submitted manuscript or any part of it into an AI tool."),
                }),
        }),
    "wiley": Policy(
        "wiley", "Wiley journals", "AI guidelines page (undated)", PUB,
        {
            "manuscript": _WILEY_MS,
            "figure": _fig(_WILEY_MS, "Figure caption/legend: tool name and version, date or year of use, its role, and the authors' role; AI analysis of research photographs goes in the Methods.",
                           "Şekil altyazısı: araç adı ve sürümü, kullanım tarihi/yılı, aracın rolü ve yazarların rolü; araştırma fotoğraflarının YZ ile analizi Yöntem bölümünde."),
            "peer_review": Ctx(
                "Disclose the use to the handling editor when the review is submitted.",
                "Kullanımı değerlendirmeyi gönderirken sorumlu editöre bildirin.",
                R(CHECK, "Wiley: beyond improving the written feedback, reviewer AI use is not addressed."),
                {
                    "review_language_polish": R(REQUIRED, "Wiley: reviewers may use AI to improve the clarity or quality of written feedback and must disclose it to the handling editor."),
                    "review_summarize_submission": R(FORBIDDEN, "Wiley: reviewers are not permitted to upload manuscripts or any part of them into AI Technology."),
                    "review_draft_report": R(FORBIDDEN, "Wiley: responsibility for the review 'must not be delegated to AI Technology'."),
                    "review_assess_merit": R(FORBIDDEN, "Wiley: responsibility for the review 'must not be delegated to AI Technology'."),
                    "upload_confidential": R(FORBIDDEN, "Wiley: no uploading of manuscripts, including figures and tables, into AI Technology."),
                }),
        },
        requires=("version", "date", "verification")),
    "taylor_francis": Policy(
        "taylor_francis", "Taylor & Francis", "AI policy page (undated)", PUB,
        {
            "manuscript": _TF_MS,
            "figure": _fig(_TF_MS, "State the use in the article's AI-usage disclosure statement (full tool name with version, how and why); T&F's image policy also applies.",
                           "Kullanımı makalenin YZ kullanım beyanında (tam araç adı ve sürümü, nasıl ve neden) belirtin; T&F görsel politikası da geçerlidir."),
            "peer_review": Ctx(
                "The T&F AI policy sets no reviewer disclosure location; tell the editor if you used AI to improve your review's language.",
                "T&F YZ politikası hakemler için bir beyan yeri belirlemez; değerlendirmenizin dilini YZ ile iyileştirdiyseniz editöre bildirin.",
                R(CHECK, "T&F: reviewer uses other than language help are not addressed."),
                {
                    "review_language_polish": R(CHECK, "T&F: 'Generative AI may be utilised to assist with improving review language'; disclosure is not specified."),
                    "review_summarize_submission": R(FORBIDDEN, "T&F: reviewers should not use GenAI for analysis or to summarise submitted articles."),
                    "review_draft_report": R(FORBIDDEN, "T&F: reviewers must not use AI tools to generate review reports."),
                    "review_assess_merit": R(FORBIDDEN, "T&F: reviewers should not use GenAI for analysis of submitted articles."),
                    "upload_confidential": R(FORBIDDEN, "T&F: reviewers must not upload unpublished manuscripts or project proposals into GenAI tools."),
                }),
        },
        requires=("version",)),
    "sage": Policy(
        "sage", "Sage journals", "AI policy page (undated)", PUB,
        {
            "manuscript": _SAGE_MS,
            "figure": _fig(_SAGE_MS, "Disclose representative illustrations and visualisation help within the Methods or Acknowledgements.",
                           "Temsili illüstrasyon ve görselleştirme desteğini Yöntem veya Teşekkür bölümünde beyan edin."),
            "peer_review": Ctx(
                "No reviewer disclosure is required for assistive language help.",
                "Yardımcı (assistive) dil desteği için hakem beyanı gerekmez.",
                R(CHECK, "Sage: reviewer uses other than writing/formatting help are not addressed individually."),
                {
                    "review_language_polish": R(EXEMPT, "Sage: reviewers may use GenAI to help write and format reports; assistive tools need no disclosure."),
                    "review_summarize_submission": R(FORBIDDEN, "Sage: uploading or copy-pasting the manuscript or parts of it into a GenAI tool is inappropriate."),
                    "review_draft_report": R(FORBIDDEN, "Sage: using GenAI to conduct peer review or generate review reports is inappropriate."),
                    "review_assess_merit": R(FORBIDDEN, "Sage: using GenAI to conduct peer review is inappropriate."),
                    "upload_confidential": R(FORBIDDEN, "Sage: uploading or copy-pasting the manuscript into a GenAI tool is inappropriate."),
                }),
        }),
    "ieee": Policy(
        "ieee", "IEEE publications", "PSPB Operations Manual amended 25 June 2026", PUB,
        {
            "manuscript": _IEEE_MS,
            "figure": _fig(_IEEE_MS, "Acknowledgments section (AI-generated figures and images are covered); identify the figure and the level of AI use.",
                           "Teşekkür bölümü (YZ ile üretilen şekil ve görüntüler dahildir); ilgili şekli ve YZ kullanım düzeyini belirtin."),
            "peer_review": Ctx(
                "IEEE sets no reviewer disclosure mechanism; its rule is a confidentiality prohibition.",
                "IEEE hakem beyanı için bir yöntem belirlemez; kuralı bir gizlilik yasağıdır.",
                R(CHECK, "IEEE: only processing manuscript content through public platforms is addressed."),
                {
                    "review_language_polish": R(AVOID, "IEEE: content 'in or about a manuscript under review' shall not be processed through a public platform for AI generation of review content - use no public tool; ask the editor."),
                    "review_summarize_submission": R(FORBIDDEN, "IEEE: manuscript content shall not be processed through a public platform for AI generation of content for a review."),
                    "review_draft_report": R(FORBIDDEN, "IEEE: manuscript content shall not be processed through a public platform for AI generation of content for a review."),
                    "review_assess_merit": R(FORBIDDEN, "IEEE: manuscript content shall not be processed through a public platform for AI generation of content for a review."),
                    "upload_confidential": R(FORBIDDEN, "IEEE: processing manuscript content through a public AI platform is a breach of confidentiality."),
                }),
        },
        requires=("sections",)),
    "plos": Policy(
        "plos", "PLOS journals", "AI policy (undated)", PUB,
        {
            "manuscript": _PLOS_MS,
            "figure": _fig(_PLOS_MS, "Disclose AI use for figure preparation in the figure legend.",
                           "Şekil hazırlığında YZ kullanımını şekil açıklamasında (legend) beyan edin."),
            "peer_review": Ctx(
                "Disclose in the review form (or decision letter) so the authors see it.",
                "Yazarların görebilmesi için değerlendirme formunda (veya karar mektubunda) beyan edin.",
                R(CHECK, "PLOS: AI use in review is allowed only if it keeps confidentiality and does not misrepresent the reviewer's own contribution; ask the journal office."),
                {
                    "review_language_polish": R(REQUIRED, "PLOS: translating or copyediting the reviewer's own comments (without confidential content) is allowable; any AI use must be disclosed."),
                    "review_literature_search": R(REQUIRED, "PLOS: surfacing general/published information relevant to the article is allowable; disclose it."),
                    "review_summarize_submission": R(FORBIDDEN, "PLOS: AI should not be used to summarize or evaluate submission content."),
                    "review_draft_report": R(FORBIDDEN, "PLOS: AI tools cannot serve as peer reviewers."),
                    "review_assess_merit": R(FORBIDDEN, "PLOS: AI should not be used to evaluate submission content."),
                    "upload_confidential": R(FORBIDDEN, "PLOS: reviewers must not upload submissions, summaries or revealing comments to generative AI tools."),
                }),
        },
        requires=("verification",)),
    "arxiv": Policy(
        "arxiv", "arXiv", "moderation policy (undated)", PUB,
        {
            "manuscript": _ARXIV_MS,
            "figure": _fig(_ARXIV_MS, "Report significant AI use in the work itself.", "Önemli YZ kullanımını çalışmanın içinde bildirin."),
        }),
    "nih": Policy(
        "nih", "NIH (US National Institutes of Health)", "NOT-OD-25-132 (2025), NOT-OD-23-149 (2023), NIH/ORI post 14 May 2026", FUN,
        {
            "grant": Ctx(
                "Describe the AI use in the application itself (NIH/ORI, 14 May 2026: 'Clearly describe in applications ... the use of the AI tools'); the notices fetched define no dedicated form field.",
                "YZ kullanımını başvurunun içinde açıklayın (NIH/ORI, 14 Mayıs 2026); incelenen duyurular ayrı bir form alanı tanımlamaz.",
                R(RECOMMENDED, "NIH/ORI (May 2026) advise describing AI use in applications; AI 'may be appropriate ... for limited aspects' (NOT-OD-25-132)."),
                {
                    "drafting": R(AVOID, "NOT-OD-25-132: applications substantially developed by AI, or with sections substantially developed by AI, are not considered the applicants' original ideas; post-award detection may be referred to ORI."),
                    "ideation": R(AVOID, "NOT-OD-25-132: NIH expects applicants to propose original ideas; substantially AI-developed content is not considered theirs."),
                    "figure_primary_image_edit": R(AVOID, "NIH/ORI (May 2026): altering images with AI without full disclosure may constitute data falsification - disclose any image-editing process."),
                    "synthetic_data": R(AVOID, "NIH/ORI (May 2026): generating data with AI and claiming it was obtained another way could constitute fabrication or falsification."),
                }),
            "peer_review": Ctx(
                "Not applicable: NIH prohibits generative AI in peer review; any accessibility technology must be cleared with the Designated Federal Officer beforehand.",
                "Uygulanmaz: NIH hakem değerlendirmesinde üretken YZ'yi yasaklar; erişilebilirlik teknolojileri önceden Designated Federal Officer ile paylaşılmalıdır.",
                R(FORBIDDEN, "NOT-OD-23-149: NIH peer reviewers may not use generative AI to analyze or formulate critiques, nor upload or share application or critique content with online generative AI tools."),
                {
                    "accessibility_assistive": R(CHECK, "NOT-OD-23-149: technologies used for accessibility needs may be granted an exception; tell the DFO before use."),
                }),
        },
        info={"grant": "NOT-OD-25-132: NIH accepts at most six new, renewal, resubmission or revision applications per PI per calendar year (all activity codes except T and R13), from the 25 Sept 2025 receipt date."}),
    "nsf": Policy(
        "nsf", "NSF (US National Science Foundation)", "notice of 14 Dec 2023", FUN,
        {
            "grant": Ctx(
                "Project Description: indicate the extent to which, if any, generative AI was used and how.",
                "Project Description (proje tanımı): üretken YZ'nin kullanılıp kullanılmadığını, ne ölçüde ve nasıl kullanıldığını belirtin.",
                R(RECOMMENDED, "NSF: proposers are encouraged to indicate the extent and manner of generative AI use; they remain responsible for accuracy and authenticity."),
            ),
            "peer_review": Ctx(
                "No reviewer disclosure mechanism; the rule is a confidentiality prohibition (Form 1230P).",
                "Hakem beyanı yöntemi yoktur; kural bir gizlilik yasağıdır (Form 1230P).",
                R(CHECK, "NSF: only uploading proposal content, review information and related records is addressed."),
                {
                    "review_language_polish": R(FORBIDDEN, "NSF: reviewers may not upload review information (which includes review analysis) to non-approved generative AI tools."),
                    "review_literature_search": R(CHECK, "NSF: reviewers may share publicly available information with generative AI tools."),
                    "review_summarize_submission": R(FORBIDDEN, "NSF: reviewers may not upload any proposal content to non-approved generative AI tools."),
                    "review_draft_report": R(FORBIDDEN, "NSF: uploading proposal content or review information to non-approved tools is prohibited."),
                    "review_assess_merit": R(FORBIDDEN, "NSF: uploading proposal content or review information to non-approved tools is prohibited."),
                    "upload_confidential": R(FORBIDDEN, "NSF: reviewers are prohibited from uploading proposal content, review information and related records to non-approved generative AI tools."),
                }),
        }),
    "ukri": Policy(
        "ukri", "UKRI", "policy published 23 Sept 2024", FUN,
        {
            "grant": Ctx(
                "In the application: UKRI expects applicants to be transparent where generative AI was used; the policy names no specific location.",
                "Başvurunun içinde: UKRI üretken YZ kullanımında şeffaflık bekler; politika belirli bir yer tanımlamaz.",
                R(RECOMMENDED, "UKRI: applications are expected to be transparent about generative AI use; this will not affect assessment."),
                {
                    "grammar_spelling": R(EXEMPT, "UKRI: minimal use (improving the standard of English, formatting) need not be disclosed."),
                    "language_polishing": R(EXEMPT, "UKRI: minimal use such as improving the standard of English need not be disclosed."),
                    "translation": R(EXEMPT, "UKRI: translating an application from another language into English is minimal use."),
                    "drafting": R(RECOMMENDED, "UKRI: generating an abstract is substantive use; generating an entire application or sections without human involvement is not allowed."),
                    "grant_interview": R(FORBIDDEN, "UKRI: applicants must not use generative AI during interviews."),
                    "upload_confidential": R(AVOID, "UKRI: sensitive or personal data of others must never be input into a generative AI tool without formal consent."),
                    "figure_primary_image_edit": R(AVOID, "UKRI: AI outputs used in an application must not contain falsified, fabricated or misrepresented information."),
                }),
            "peer_review": Ctx(
                "Assessors: language refinement only; the policy sets no disclosure mechanism.",
                "Değerlendiriciler: yalnızca dil iyileştirme; politika bir beyan yöntemi belirlemez.",
                R(FORBIDDEN, "UKRI: assessors must not use generative AI as part of assessment activities except for language refinement."),
                {
                    "review_language_polish": R(CHECK, "UKRI: allowed only if no part of the application or personal information is entered and AI is not tasked with understanding, summarising or evaluating it."),
                    "accessibility_assistive": R(CHECK, "Not addressed by UKRI; the general prohibition applies unless UKRI agrees an accommodation - ask first."),
                }),
        }),
    "erc": Policy(
        "erc", "ERC (European Research Council)", "Scientific Council position 1 Dec 2023 (updated 25 Mar 2026); reviewer guidelines 23 Mar 2026", FUN,
        {
            "grant": Ctx(
                "The Scientific Council position sets no AI-disclosure field; applicants keep full and sole authorship responsibility, including for acknowledgements - acknowledge AI help as you would other external help and follow the call documents.",
                "Bilim Konseyi tutumu ayrı bir YZ beyan alanı tanımlamaz; başvuru sahibi teşekkürler dahil yazarlık sorumluluğunun tamamını taşır - YZ desteğini diğer dış yardımlar gibi belirtin ve çağrı belgelerine uyun.",
                R(CHECK, "ERC Scientific Council: external help, including AI, does not relieve applicants of authorship responsibilities (acknowledgements, plagiarism)."),
            ),
            "peer_review": Ctx(
                "ERC panel members and remote reviewers: guidelines of 23 March 2026 (no disclosure mechanism specified).",
                "ERC panel üyeleri ve uzaktan hakemler: 23 Mart 2026 yönergeleri (beyan yöntemi belirtilmemiş).",
                R(FORBIDDEN, "ERC Scientific Council: using generative AI for the evaluation of proposals is not permitted (non-delegation; confidentiality)."),
                {
                    "review_language_polish": R(CHECK, "ERC Q4: allowed conditionally - no personal data or proposal content disclosed, and the AI must not generate arguments."),
                    "review_literature_search": R(CHECK, "ERC Q6: AI may be used to search for information on the proposal's topic, never with proposal text as input."),
                    "upload_confidential": R(FORBIDDEN, "ERC Q1: uploading a proposal or part of it to online AI tools violates confidentiality."),
                    "accessibility_assistive": R(CHECK, "Not addressed by the ERC guidelines; the non-delegation and confidentiality principles apply - ask the ERC first."),
                }),
        }),
    "tubitak": Policy(
        "tubitak", "TÜBİTAK", "ÜYZ guide v04, Ocak 2026 (first issued Eylül 2025)", TRE,
        {
            "grant": Ctx(
                "Mandatory declaration in the dedicated section of TÜBİTAK's online application system: tool name and version, stages/sections used, nature and scope of use. The same applies to progress and final reports.",
                "TÜBİTAK çevrimiçi başvuru sisteminde bu amaçla ayrılmış bölümde zorunlu beyan: araç adı ve sürümü, kullanıldığı aşama/bölümler, kullanımın niteliği ve kapsamı. Ara/gelişme/sonuç raporları için de geçerlidir.",
                R(REQUIRED, "TÜBİTAK guide 1.2.1: declaring AI use in preparing the proposal is mandatory (use beyond basic grammar/spelling checks).",
                  "TÜBİTAK Rehberi 1.2.1: proje önerisinin hazırlanmasında ÜYZ kullanımının beyanı zorunludur (temel dil bilgisi/yazım denetiminin ötesindeki kullanımlar)."),
                {
                    "grammar_spelling": R(EXEMPT, "TÜBİTAK guide 1.2.1: basic grammar or spelling checks fall outside 'significant use'.",
                                          "TÜBİTAK Rehberi 1.2.1: basit dil bilgisi veya yazım denetimi 'önemli ölçüde kullanım' kapsamında değildir."),
                    "drafting": R(REQUIRED, "TÜBİTAK guide 1.1.2: AI-drafted proposal sections must never be taken as final text; rewrite and verify every claim and reference.",
                                  "TÜBİTAK Rehberi 1.1.2: ÜYZ ile oluşturulan taslaklar asla nihai metin olarak kabul edilmemeli; tüm iddia ve kaynaklar doğrulanmalıdır."),
                    "data_analysis": R(REQUIRED, "TÜBİTAK guide 1.1.2: AI data analysis must be checked by a domain expert, validated by conventional methods, and its limits stated.",
                                       "TÜBİTAK Rehberi 1.1.2: ÜYZ ile yapılan veri analizi alan uzmanınca denetlenmeli, geleneksel yöntemlerle doğrulanmalı ve sınırlılıkları belirtilmelidir."),
                    "synthetic_data": R(REQUIRED, "TÜBİTAK guide 1.1.2: synthetic data to fill missing data is a high-risk use - validate it and state the tool's limits.",
                                        "TÜBİTAK Rehberi 1.1.2: eksik verileri tamamlamak için sentetik veri üretimi yüksek risklidir; doğrulanmalı ve sınırlılıklar belirtilmelidir."),
                    "figure_explanatory": R(REQUIRED, "TÜBİTAK guide 1.1.1: AI-generated visuals and the tool used must be stated.",
                                            "TÜBİTAK Rehberi 1.1.1: görsellerin YZ ile oluşturulduğu ve kullanılan araç mutlaka belirtilmelidir."),
                    "figure_primary_image_edit": R(AVOID, "TÜBİTAK guide 1.5.2: fabricating or falsifying data or results with AI is prohibited.",
                                                   "TÜBİTAK Rehberi 1.5.2: ÜYZ ile veri uydurmak veya sonuçları çarpıtmak kesinlikle yasaktır."),
                    "upload_confidential": R(FORBIDDEN, "TÜBİTAK guide 1.5.3: entering confidential proposal details, unpublished data, personal data (KVKK) or third-party commercial information into AI tools is strictly prohibited.",
                                             "TÜBİTAK Rehberi 1.5.3: gizli proje ayrıntılarını, yayımlanmamış verileri, KVKK kapsamındaki kişisel verileri veya üçüncü kişilere ait ticari bilgileri ÜYZ araçlarına girmek kesinlikle yasaktır."),
                }),
            "peer_review": Ctx(
                "Not applicable: TÜBİTAK evaluators (referees, panellists, monitors) may not use generative AI for any evaluation-related purpose.",
                "Uygulanmaz: TÜBİTAK değerlendiricileri (hakem, panelist, izleyici) değerlendirme göreviyle ilgili hiçbir amaçla ÜYZ kullanamaz.",
                R(FORBIDDEN, "TÜBİTAK guide 2.1.1: evaluators are strictly prohibited from using generative AI for any purpose related to the evaluation, including drafting e-mails; violations fall under AYEK rules.",
                  "TÜBİTAK Rehberi 2.1.1: değerlendiricilerin değerlendirme göreviyle ilgili herhangi bir amaçla (e-posta taslağı dahil) ÜYZ kullanması kesinlikle yasaktır; ihlaller AYEK Yönetmeliği kapsamında ele alınır."),
            ),
        },
        requires=("version", "sections")),
    "ec_living_guidelines": Policy(
        "ec_living_guidelines", "European Commission ERA living guidelines (non-binding)", "third version, May 2026", FUN,
        {
            "manuscript": Ctx(
                "Methods section (or equivalent), following the journal's guidelines or the discipline's standards.",
                "Yöntem bölümü (veya eşdeğeri); derginin yönergesine veya alanın standartlarına göre.",
                R(REQUIRED, "EC living guidelines: detail generative AI tools used substantially in the research process."),
                {
                    "grammar_spelling": R(EXEMPT, "EC living guidelines: using generative AI as a basic editorial support tool is not a substantial use."),
                    "language_polishing": R(EXEMPT, "EC living guidelines: using generative AI as a basic editorial support tool is not a substantial use."),
                    "ai_as_author": R(FORBIDDEN, "EC living guidelines: AI systems are neither authors nor co-authors."),
                    "figure_primary_image_edit": R(AVOID, "EC living guidelines (fn. 18): researchers do not use generative AI to falsify, alter or manipulate original research data."),
                    "upload_confidential": R(AVOID, "EC living guidelines: do not upload unpublished or sensitive work into external AI systems without assurances the data will not be re-used."),
                }),
            "grant": Ctx(
                "Declare substantial use in the application where the funder provides a way (EC recommendation to funders).",
                "Önemli ölçüdeki kullanımı, fon kuruluşunun sağladığı yöntemle başvuruda beyan edin (AK'nin fon kuruluşlarına tavsiyesi).",
                R(REQUIRED, "EC living guidelines: applicants declare if they substantially used generative AI to prepare their application."),
                {
                    "grammar_spelling": R(EXEMPT, "EC living guidelines: basic support tools are not a substantial use."),
                    "language_polishing": R(EXEMPT, "EC living guidelines: basic support tools are not a substantial use."),
                    "figure_primary_image_edit": R(AVOID, "EC living guidelines (fn. 18): researchers do not use generative AI to falsify, alter or manipulate original research data."),
                    "upload_confidential": R(AVOID, "EC living guidelines: do not upload unpublished or sensitive work, or third parties' personal data, into external AI systems without safeguards."),
                }),
            "peer_review": Ctx(
                "Refrain from substantial generative-AI use in peer review and proposal evaluation (non-binding).",
                "Hakemlik ve proje değerlendirmede üretken YZ'nin önemli ölçüde kullanımından kaçının (bağlayıcı değildir).",
                R(AVOID, "EC living guidelines: refrain from using generative AI substantially in peer review or the evaluation of research proposals."),
                {
                    "review_language_polish": R(CHECK, "EC living guidelines (fn. 28): polishing one's own review text is listed neither as substantial nor as non-substantial use."),
                    "review_literature_search": R(CHECK, "EC living guidelines: searching background information for a review is not a substantial use."),
                    "upload_confidential": R(AVOID, "EC living guidelines: do not upload others' unpublished work into external AI systems without assurances against re-use."),
                }),
        }),
    "yok": Policy(
        "yok", "YÖK (Council of Higher Education, Türkiye)", "ethics guide, Mayıs 2024", TRE,
        {
            "manuscript": _YOK_MS,
            "thesis": _YOK_MS,
            "figure": _fig(_YOK_MS, "Explain the AI-produced figure in the method section (tool, version, when, stage).",
                           "YZ ile üretilen şekli yöntem bölümünde açıklayın (araç, sürüm, ne zaman, hangi aşamada)."),
            "ethics_application": Ctx(
                "Ethics-committee application / research protocol: give the committee the purpose, scope and nature of the AI use, plus tool, version and stage.",
                "Etik kurul başvurusu / araştırma protokolü: ÜYZ kullanımının amacı, kapsamı ve niteliği ile araç, sürüm ve aşama bilgisi Kurula verilmelidir.",
                R(REQUIRED, "YÖK guide FAQ 8: the ethics committee must be given the necessary information on generative AI use.",
                  "YÖK Rehberi SSS: Etik Kurulu başvurusunda ÜYZ kullanımı konusunda Kurula gerekli bilgi verilmelidir."),
                {
                    "synthetic_participants": R(AVOID, "YÖK guide: using generative AI instead of real participants is not correct.",
                                                "YÖK Rehberi: gerçek katılımcılar yerine ÜYZ kullanılması doğru değildir."),
                }),
        },
        requires=("version", "date", "sections")),
    "generic": Policy(
        "generic", "Generic / unverified venue", "conservative fallback", PUB,
        {
            "manuscript": _GENERIC_MS,
            "figure": _fig(_GENERIC_MS, "Caption/legend plus the manuscript's AI statement, unless the venue says otherwise.",
                           "Yayın organı aksini belirtmedikçe şekil altyazısı ve makalenin YZ beyanı."),
            "grant": Ctx(
                "Follow the call text; if it is silent, add a short AI-use statement to the proposal narrative.",
                "Çağrı metnine uyun; metin sessizse proje anlatımına kısa bir YZ kullanım beyanı ekleyin.",
                R(CHECK, "Funder rules not verified - disclose substantive use (the EC living guidelines recommend declaring substantial use)."),
            ),
            "peer_review": Ctx(
                "Follow the journal's or funder's reviewer instructions; if they are silent, ask the editor before using any AI.",
                "Derginin veya fon kuruluşunun hakem yönergesine uyun; yönerge sessizse YZ kullanmadan önce editöre sorun.",
                R(AVOID, "Unless the venue explicitly permits it, keep generative AI away from confidential review material (ICMJE V.B)."),
                {
                    "review_language_polish": R(CHECK, "Several publishers allow polishing your own review text with no manuscript content entered; check the venue and disclose."),
                    "upload_confidential": R(FORBIDDEN, "Uploading confidential submission content breaches confidentiality under every policy verified for this skill."),
                    "review_summarize_submission": R(FORBIDDEN, "Requires entering the confidential submission into the tool."),
                }),
            "thesis": _GENERIC_MS,
            "ethics_application": Ctx(
                "Describe planned AI use in the protocol or application form the committee provides.",
                "Planlanan YZ kullanımını kurulun sağladığı protokol veya başvuru formunda açıklayın.",
                R(REQUIRED, "Unverified committee: describe purpose, scope, tool, version and stage conservatively."),
            ),
        }),
}

ALIASES = {
    "springer": "springer_nature", "nature": "springer_nature", "nature_portfolio": "springer_nature",
    "tandf": "taylor_francis", "t&f": "taylor_francis", "taylor_and_francis": "taylor_francis",
    "ec": "ec_living_guidelines", "era_guidelines": "ec_living_guidelines",
    "yök": "yok", "tübitak": "tubitak",
}
# Policy pages that could NOT be fetched on POLICY_DATA_DATE (HTTP 403 / bot challenge).
UNVERIFIED = {
    "cope": "COPE position statement (publicationethics.org returned HTTP 403)",
    "science": "Science/AAAS editorial policies (science.org returned HTTP 403)",
    "aaas": "Science/AAAS editorial policies (science.org returned HTTP 403)",
    "cell_press": "Cell Press journal policies (cell.com returned HTTP 403)",
    "cell": "Cell Press journal policies (cell.com returned HTTP 403)",
    "acm": "ACM Policy on Authorship (acm.org returned HTTP 403)",
    "apa": "APA Journals generative-AI policy (apa.org served a bot challenge)",
}
REQUIRES_FOR_METHOD_USES = {  # Elsevier: tool, version and developer in Methods
    "elsevier": ({"code", "code_debugging", "data_analysis", "figure_data_visualization"},
                 ("version", "provider")),
}
REQUIRES_FOR_CONTEXT = {  # Springer Nature visual content: "including model and purpose of use"
    ("springer_nature", "figure"): ("version",),
}
FORBIDDEN_ACTION = {
    "ai_as_author": "Remove the AI tool from the author list and describe its use in the disclosure instead.",
    "cite_ai_as_source": "Cite the original sources instead of the AI output.",
    "upload_confidential": ("Left out of the statement. If it already happened, tell the editor, programme officer or "
                            "funder now; do not submit a statement that hides it."),
}
REVIEW_FORBIDDEN_ACTION = ("Left out of the statement. Do not use AI this way for this review; if it already happened, "
                           "tell the editor or the funder's designated review official (NIH: the Designated Federal "
                           "Officer) before submitting - do not submit a review that hides it.")
DEFAULT_FORBIDDEN_ACTION = ("Left out of the statement: remove this use (redo that part without AI) or raise it with the "
                            "editor/funder before submitting; do not submit a statement that hides it.")


# --------------------------------------------------------------------------- #
# Engine                                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Result:
    context: str
    language: str
    policies: list
    statement: str
    placements: list
    warnings: list
    notes: list
    exit_code: int


class InputError(ValueError):
    pass


def resolve_key(key: str) -> tuple[str, str | None]:
    """Return (policy_key, unverified_label)."""
    k = key.strip().lower().replace(" ", "_").replace("-", "_")
    k = ALIASES.get(k, k)
    if k in POLICIES:
        return k, None
    if k in UNVERIFIED:
        return "generic", UNVERIFIED[k]
    raise InputError(f"unknown venue/policy key {key!r}; see --list-venues")


# Uses where a policy's general default would mislead ("disclose it and it is fine"). When a policy's
# fetched text does not address one of these explicitly, the result is CHECK with a pointer to the
# policies that do - unless the context is a blanket ban (default FORBIDDEN), which stands.
SENSITIVE = {
    "figure_primary_image_edit": R(CHECK, "Not specifically addressed here; Elsevier, Wiley, T&F, Springer Nature and Sage forbid generating or altering primary research images - treat it as potential falsification and ask the venue."),
    "figure_graphical_abstract": R(CHECK, "Not specifically addressed here; Elsevier forbids general-purpose generative image tools for graphical abstracts - check this venue."),
    "synthetic_participants": R(CHECK, "Not specifically addressed here; Sage forbids and YÖK rejects replacing real participants with AI - never present simulated responses as real data."),
    "synthetic_data": R(CHECK, "Not specifically addressed here; IEEE requires AI-generated data to be labelled as such - never present it as observed data."),
    "interpretation": R(CHECK, "Not specifically addressed here; Springer Nature forbids AI-generated scientific interpretations and YÖK advises against AI in discussion/interpretation."),
    "cite_ai_as_source": R(CHECK, "Not specifically addressed here; ICMJE rejects AI output as a primary source and Sage asks for the original sources."),
    "accessibility_assistive": R(CHECK, "Not specifically addressed here; Elsevier exempts accessibility-only assistive technology and NIH reviewers may request an exception - describe it if unsure."),
    "upload_confidential": R(CHECK, "Not specifically addressed here for this role; TÜBİTAK forbids entering confidential or personal data into AI tools and UKRI requires consent for others' personal data."),
    "grant_interview": R(CHECK, "Not specifically addressed here; UKRI forbids generative AI during funding interviews."),
}


def rule_for(policy: Policy, context: str, purpose: str) -> Rule:
    ctx = policy.contexts[context]
    if purpose in ctx.rules:
        return ctx.rules[purpose]
    if purpose in SENSITIVE and ctx.default.status != FORBIDDEN:
        return SENSITIVE[purpose]
    return ctx.default


def _note(rule: Rule, lang: str) -> str:
    return rule.note_tr if (lang == "tr" and rule.note_tr) else rule.note


def _join(items: list[str], lang: str) -> str:
    if len(items) <= 1:
        return "".join(items)
    if lang == "en":  # serial comma when a phrase already contains "and"
        last = ", and " if (len(items) > 2 or any(" and " in i for i in items)) else " and "
    else:  # "ile" avoids a double "ve" when a phrase already contains one
        last = " ile " if any((" ve " in i) or (" veya " in i) for i in items) else " ve "
    return ", ".join(items[:-1]) + last + items[-1]


def _tool_label(tool: dict, lang: str) -> str:
    bits = []
    if tool.get("version"):
        bits.append(tool["version"] if lang == "en" else f"sürüm: {tool['version']}")
    if tool.get("provider"):
        bits.append(tool["provider"] if lang == "en" else f"sağlayıcı: {tool['provider']}")
    if tool.get("date"):
        bits.append(f"accessed {tool['date']}" if lang == "en" else f"kullanım: {tool['date']}")
    return f"{tool['name']} ({'; '.join(bits)})" if bits else tool["name"]


def _sections_clause(sections: list[str], lang: str) -> str:
    if not sections:
        return ""
    return (f" (used in: {', '.join(sections)})" if lang == "en"
            else f" (kullanıldığı bölüm/aşamalar: {', '.join(sections)})")


def _sections_sentence(sections: list[str], lang: str) -> str:
    if lang == "en":
        return f"The AI assistance concerned these parts of the work: {', '.join(sections)}."
    return f"YZ desteğinin kullanıldığı bölüm/aşamalar: {', '.join(sections)}."


VERIFY_PLACEHOLDER = {
    "en": "<Describe how the output was checked, e.g. compared with primary sources, code re-run and tested.>",
    "tr": "<Çıktıların nasıl doğrulandığını yazın; ör. birincil kaynaklarla karşılaştırıldı, kod yeniden çalıştırılıp test edildi.>",
}
NO_AI = {
    ("manuscript", "en"): "No generative AI tools were used in the preparation of this work.",
    ("manuscript", "tr"): "Bu çalışmanın hazırlanmasında üretken yapay zekâ araçları kullanılmamıştır.",
    ("figure", "en"): "No generative AI tools were used to create or edit this figure.",
    ("figure", "tr"): "Bu şeklin oluşturulmasında veya düzenlenmesinde üretken yapay zekâ araçları kullanılmamıştır.",
    ("grant", "en"): "No generative AI tools were used in preparing this proposal.",
    ("grant", "tr"): "Bu proje önerisinin hazırlanmasında üretken yapay zekâ araçları kullanılmamıştır.",
    ("thesis", "en"): "No generative AI tools were used in the preparation of this thesis.",
    ("thesis", "tr"): "Bu tezin hazırlanmasında üretken yapay zekâ araçları kullanılmamıştır.",
    ("ethics_application", "en"): "No generative AI tools will be used in this study.",
    ("ethics_application", "tr"): "Bu araştırmada üretken yapay zekâ araçları kullanılmayacaktır.",
    ("peer_review", "en"): ("I did not use generative AI tools to analyse, summarise or evaluate this submission "
                            "or to draft or edit this review, and I did not upload or share any of its content with such tools."),
    ("peer_review", "tr"): ("Bu değerlendirmenin hazırlanmasında üretken yapay zekâ araçlarını başvuruyu/makaleyi analiz etmek, "
                            "özetlemek veya değerlendirmek ya da değerlendirme metnini yazmak veya düzenlemek için kullanmadım; "
                            "başvuru/makale içeriğinin hiçbir bölümünü bu araçlara yüklemedim veya bu araçlarla paylaşmadım."),
}
HEADING = {
    ("manuscript", "en"): "Statement on the use of generative AI",
    ("manuscript", "tr"): "Üretken yapay zekâ kullanımına ilişkin beyan",
    ("grant", "en"): "Use of generative AI in preparing this proposal",
    ("grant", "tr"): "Proje önerisinin hazırlanmasında üretken yapay zekâ kullanımı",
    ("thesis", "en"): "Use of generative AI",
    ("thesis", "tr"): "Üretken yapay zekâ (ÜYZ) kullanımı",
    ("ethics_application", "en"): "Use of generative AI in the study",
    ("ethics_application", "tr"): "Araştırmada üretken yapay zekâ (ÜYZ) kullanımı",
    ("peer_review", "en"): "Reviewer statement on the use of AI",
    ("peer_review", "tr"): "Hakemin yapay zekâ kullanımına ilişkin beyanı",
    ("figure", "en"): "Figure caption - AI-use sentence",
    ("figure", "tr"): "Şekil altyazısı - YZ kullanım cümlesi",
    ("methods", "en"): "Methods - use of generative AI tools",
    ("methods", "tr"): "Yöntem - üretken yapay zekâ araçlarının kullanımı",
}
ELSEVIER_TITLE = "Declaration of generative AI and AI-assisted technologies in the manuscript preparation process"
# Research-method uses that ICMJE, Elsevier, Wiley, PLOS and Springer Nature send to the Methods.
METHOD_USES = {"code", "code_debugging", "data_analysis", "qualitative_coding", "systematic_search_screening",
               "synthetic_data", "synthetic_participants", "figure_data_visualization"}
SPLIT_POLICIES = {"icmje", "elsevier", "wiley", "plos", "springer_nature", "generic"}


def _tool_sentences(context: str, lang: str, venue: str, tools: list[dict], plural: bool,
                    figure_label: str, block: str) -> list[str]:
    out = []
    for t in tools:
        phrases = [PURPOSES[p][0 if lang == "en" else 1] for p in t["_kept"]]
        if not phrases:
            continue
        label = _tool_label(t, lang)
        purp = _join(phrases, lang)
        sec = _sections_clause(t.get("sections") or [], lang)
        if lang == "en":
            who = "the authors" if plural else "the author"
            if block == "methods":
                out.append(f"{label} was used to {purp}{sec}.")
            elif context == "peer_review":
                if venue == "elsevier":
                    out.append(f"During the preparation of this report, I used {label} in order to {purp}.")
                else:
                    out.append(f"In preparing this review, I used {label} to {purp}.")
            elif context in ("manuscript", "thesis") and venue == "elsevier":
                out.append(f"During the preparation of this work {who} used {label} in order to {purp}{sec}.")
            elif context == "grant":
                out.append(f"In preparing this proposal, {label} was used to {purp}{sec}.")
            elif context == "ethics_application":
                out.append(f"In this study, {label} will be used to {purp}{sec}.")
            elif context == "figure":
                out.append(f"{figure_label or 'Figure X'}: {label} was used to {purp}{sec}.")
            elif context == "thesis":
                out.append(f"In preparing this thesis, the author used {label} to {purp}{sec}.")
            else:
                out.append(f"{who.capitalize()} used {label} to {purp}{sec}.")
        else:
            if block == "methods":
                out.append(f"{label} aracı {purp} amacıyla kullanılmıştır{sec}.")
            elif context == "peer_review":
                out.append(f"Bu değerlendirmenin hazırlanmasında {label} aracını {purp} amacıyla kullandım.")
            elif context == "grant":
                out.append(f"Bu proje önerisinin hazırlanmasında {label} aracı {purp} amacıyla kullanılmıştır{sec}.")
            elif context == "ethics_application":
                out.append(f"Bu araştırmada {label} aracı {purp} amacıyla kullanılacaktır{sec}.")
            elif context == "figure":
                out.append(f"{figure_label or 'Şekil X'}: {label} aracı {purp} amacıyla kullanılmıştır{sec}.")
            elif context == "thesis":
                out.append(f"Bu tezin hazırlanmasında {label} aracı {purp} amacıyla kullanılmıştır{sec}.")
            else:
                out.append(f"Bu çalışmanın hazırlanmasında {label} aracı {purp} amacıyla kullanılmıştır{sec}.")
    return out


def _closing(context: str, lang: str, venue: str, plural: bool) -> str:
    if lang == "en":
        if context == "peer_review":
            if venue == "elsevier":
                return ("After using this tool/service, I reviewed and edited the content as needed "
                        "and I take full responsibility for its content.")
            return "I reviewed and edited all AI-assisted text and take full responsibility for the content of this review."
        if context in ("manuscript", "thesis") and venue == "elsevier":
            who, verb = ("the authors", "take") if plural else ("the author", "takes")
            return (f"After using this tool/service, {who} reviewed and edited the content as needed "
                    f"and {verb} full responsibility for the content of the published article.")
        if context == "grant":
            return ("The applicants reviewed and revised all AI-assisted content and take full responsibility "
                    "for the accuracy and originality of the proposal.")
        if context == "ethics_application":
            return "The research team will verify all AI outputs and remains responsible for them."
        if context == "thesis":
            return "The author reviewed and edited all AI-assisted output and takes full responsibility for the content of this thesis."
        who, verb = ("The authors", "take") if plural else ("The author", "takes")
        return f"{who} reviewed and edited all AI-assisted output and {verb} full responsibility for the content of this work."
    if context == "peer_review":
        return "Yapay zekâ destekli tüm metinleri gözden geçirip düzenledim; bu değerlendirmenin içeriğine ilişkin tüm sorumluluk bana aittir."
    if context == "grant":
        return ("Yapay zekâ destekli tüm içerik başvuru sahiplerince gözden geçirilip düzeltilmiştir; önerinin doğruluğu "
                "ve özgünlüğüne ilişkin tüm sorumluluk başvuru sahiplerine aittir.")
    if context == "ethics_application":
        return "Araştırma ekibi tüm ÜYZ çıktılarını doğrulayacak ve bunlardan sorumlu olacaktır."
    if context == "thesis":
        return ("Yapay zekâ destekli tüm çıktılar tez yazarı tarafından gözden geçirilmiş ve düzenlenmiştir; "
                "tezin içeriğine ilişkin tüm sorumluluk tez yazarına aittir.")
    who = "yazarlar" if plural else "yazar"
    owner = "yazarlara" if plural else "yazara"
    return (f"Yapay zekâ destekli tüm çıktılar {who} tarafından gözden geçirilmiş ve düzenlenmiştir; "
            f"çalışmanın içeriğine ilişkin tüm sorumluluk {owner} aittir.")


CONFIDENTIAL_SENTENCE = {
    ("peer_review", "en"): "No part of the submission was entered into or shared with the tool.",
    ("peer_review", "tr"): "Başvuru/makale içeriğinin hiçbir bölümü araca girilmemiş veya araçla paylaşılmamıştır.",
    ("ethics_application", "en"): "No confidential or identifiable personal data will be entered into the AI tools.",
    ("ethics_application", "tr"): "Gizli veya kimliği belirlenebilir kişisel veriler yapay zekâ araçlarına girilmeyecektir.",
    ("*", "en"): "No confidential, unpublished or personal data were entered into the AI tools.",
    ("*", "tr"): "Gizli, yayımlanmamış veya kişisel veriler yapay zekâ araçlarına girilmemiştir.",
}


def _verification(tools: list[dict], verification: str, lang: str) -> str:
    texts = [t["verification"] for t in tools if t.get("verification")] or [verification or VERIFY_PLACEHOLDER[lang]]
    return " ".join(x if x.endswith((".", ">")) else x + "." for x in texts)


def _tubitak_block(lang: str, tools: list[dict], sections: list[str], verification: str,
                   conf_sentence: str) -> str:
    kept_tools = [t for t in tools if t["_kept"]]
    names = "; ".join(_tool_label(t, lang) for t in kept_tools)
    uses = "; ".join(_join([PURPOSES[p][0 if lang == "en" else 1] for p in t["_kept"]], lang)
                     for t in kept_tools)
    all_secs = sections + [s for t in kept_tools for s in (t.get("sections") or []) if s not in sections]
    secs = ", ".join(all_secs) if all_secs else ("<stage/section>" if lang == "en" else "<aşama/bölüm>")
    if lang == "en":
        lines = ["Generative AI use declaration (TÜBİTAK)",
                 f"- Tool(s) and version: {names}",
                 f"- Stage(s)/section(s) of the proposal: {secs}",
                 f"- Nature and scope of use: {uses}",
                 f"- Verification: {verification}"]
    else:
        lines = ["Üretken Yapay Zekâ (ÜYZ) Kullanım Beyanı",
                 f"- Kullanılan ÜYZ aracı/araçları ve sürümü: {names}",
                 f"- Kullanıldığı aşama/bölümler: {secs}",
                 f"- Kullanımın niteliği ve kapsamı: {uses}",
                 f"- Doğrulama: {verification}"]
    if conf_sentence:
        lines.append(f"- {conf_sentence}")
    return "\n".join(lines)


def _norm_list(value, what: str) -> list[str]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise InputError(f"{what} must be a list")
    return [str(x).strip() for x in value if str(x).strip()]


def build(data: dict) -> Result:
    if not isinstance(data, dict):
        raise InputError("input must be a JSON object")
    context = str(data.get("context", "")).strip().lower()
    if context not in CONTEXTS:
        raise InputError(f"context must be one of {', '.join(CONTEXTS)}")
    lang = str(data.get("language", "en")).strip().lower()
    if lang not in LANGS:
        raise InputError("language must be 'en' or 'tr'")
    if not data.get("venue"):
        raise InputError("venue is required (use 'generic' if unknown); see --list-venues")

    warnings: list[str] = []
    notes: list[str] = []
    keys: list[str] = []
    for raw in [data["venue"], *_norm_list(data.get("also_apply"), "also_apply")]:
        key, unverified = resolve_key(str(raw))
        if unverified:
            warnings.append(f"[UNVERIFIED] {raw}: {unverified} on {POLICY_DATA_DATE}; generic conservative rules "
                            "applied - read the venue's live policy before submitting.")
        if key not in keys:
            keys.append(key)
    for key in keys:
        if context not in POLICIES[key].contexts:
            valid = sorted(k for k, p in POLICIES.items() if context in p.contexts)
            raise InputError(f"policy {key!r} has no rules for context {context!r}; valid: {', '.join(valid)}")
    primary = keys[0]

    tools = data.get("tools") or []
    if not isinstance(tools, list):
        raise InputError("tools must be a list")
    top_purposes = _norm_list(data.get("purposes"), "purposes")
    for p in top_purposes:
        if p not in PURPOSES:
            raise InputError(f"unknown purpose {p!r}; see --list-purposes")
    if top_purposes and not tools:
        raise InputError("purposes were given but no tools; name each AI tool in 'tools'")
    norm_tools = []
    for t in tools:
        if not isinstance(t, dict) or not str(t.get("name", "")).strip():
            raise InputError("each tool needs at least a 'name'")
        ps = _norm_list(t.get("purposes"), "tool purposes") or list(top_purposes)
        if not ps:
            raise InputError(f"tool {t['name']!r} has no purposes (give 'purposes' on the tool or top level)")
        for p in ps:
            if p not in PURPOSES:
                raise InputError(f"unknown purpose {p!r}; see --list-purposes")
        if data.get("confidential_input") is True and "upload_confidential" not in ps:
            ps.append("upload_confidential")
        tool = {k: str(t.get(k) or "").strip() for k in ("name", "version", "provider", "date", "verification")}
        tool.update({"sections": _norm_list(t.get("sections"), "tool sections"), "purposes": ps, "_kept": []})
        norm_tools.append(tool)
    if context != "peer_review":
        stray = sorted({p for t in norm_tools for p in t["purposes"] if p in REVIEW_ONLY})
        if stray:
            raise InputError(f"purposes {stray} only apply to context 'peer_review'")

    include_exempt = bool(data.get("include_exempt"))
    any_forbidden = False
    for p in sorted({p for t in norm_tools for p in t["purposes"]}):
        per_policy = [(POLICIES[k], rule_for(POLICIES[k], context, p)) for k in keys]
        worst = max(per_policy, key=lambda pr: RANK[pr[1].status])[1].status
        for pol, rule in per_policy:
            tag = f"{pol.label}: '{p}'"
            if rule.status == FORBIDDEN:
                any_forbidden = True
                action = FORBIDDEN_ACTION.get(p) or (REVIEW_FORBIDDEN_ACTION if context == "peer_review"
                                                     else DEFAULT_FORBIDDEN_ACTION)
                warnings.append(f"[FORBIDDEN] {tag} - {_note(rule, lang)} {action}")
            elif rule.status == AVOID:
                warnings.append(f"[AVOID] {tag} - {_note(rule, lang)} Disclosed in the statement; reconsider the use.")
            elif rule.status == EXEMPT:
                notes.append(f"[EXEMPT] {tag} - {_note(rule, lang)}")
            elif rule.status == CHECK:
                notes.append(f"[CHECK] {tag} - {_note(rule, lang)} Disclosed conservatively; confirm with the venue.")
            elif rule.status == RECOMMENDED:
                notes.append(f"[RECOMMENDED] {tag} - {_note(rule, lang)}")
            elif p in pol.contexts[context].rules:  # purpose-specific REQUIRED rule: surface its caveat
                notes.append(f"[DISCLOSE] {tag} - {_note(rule, lang)}")
        is_choice = p in ("ai_as_author", "cite_ai_as_source")
        if is_choice and worst != FORBIDDEN:
            notes.append(f"[NOTE] '{p}' is an authorship/citation choice, not a use to describe in the statement.")
        keep = worst != FORBIDDEN and (worst != EXEMPT or include_exempt) and not is_choice
        for t in norm_tools:
            if p in t["purposes"] and keep:
                t["_kept"].append(p)
    for t in norm_tools:  # keep the user's purpose order
        t["_kept"] = [p for p in t["purposes"] if p in t["_kept"]]

    # Missing fields demanded by the applicable policies.
    sections = _norm_list(data.get("sections"), "sections")
    verification = str(data.get("human_verification") or "").strip()
    used_tools = [t for t in norm_tools if t["_kept"]]
    has_sections = bool(sections) or (bool(used_tools) and all(t["sections"] for t in used_tools))
    has_verification = bool(verification) or (bool(used_tools) and all(t["verification"] for t in used_tools))
    for key in keys:
        pol = POLICIES[key]
        needs = set(pol.requires) | set(REQUIRES_FOR_CONTEXT.get((key, context), ()))
        extra = REQUIRES_FOR_METHOD_USES.get(key)
        if extra and any(p in extra[0] for t in used_tools for p in t["_kept"]):
            needs |= set(extra[1])
        for fld in sorted(needs):
            if fld in ("version", "date", "provider"):
                missing = [t["name"] for t in used_tools if not t.get(fld)]
                if missing:
                    warnings.append(f"[MISSING] {pol.label} asks for the tool {fld}; not given for: {', '.join(missing)}.")
            elif fld == "sections" and used_tools and not has_sections:
                warnings.append(f"[MISSING] {pol.label} asks where in the work AI was used; add 'sections'.")
            elif fld == "verification" and used_tools and not has_verification:
                warnings.append(f"[MISSING] {pol.label} asks how the outputs were checked; add 'human_verification'.")
    if used_tools and not has_verification and not any(w.endswith("add 'human_verification'.") for w in warnings):
        notes.append("[NOTE] No 'human_verification' given - a placeholder was inserted; say how outputs were checked.")

    # Statement.
    plural = str(data.get("authors", "plural")).lower() != "single"
    figure_label = str(data.get("figure_label") or "")
    conf = data.get("confidential_input")
    conf_sentence = ""
    if conf is False:
        conf_sentence = CONFIDENTIAL_SENTENCE.get((context, lang)) or CONFIDENTIAL_SENTENCE[("*", lang)]
    elif conf is None and used_tools:
        notes.append("[NOTE] Set \"confidential_input\": false once you have confirmed no confidential, unpublished "
                     "or personal data were entered; the statement then says so.")
    heading = HEADING[(context, lang)]
    if primary == "elsevier" and context in ("manuscript", "thesis"):
        heading = ELSEVIER_TITLE
    blocks: list[str] = []
    if not used_tools:
        if any_forbidden:
            body = ("<No statement drafted: every declared use is FORBIDDEN under the applicable policy - see WARNINGS.>"
                    if lang == "en" else
                    "<Beyan taslağı oluşturulmadı: beyan edilen tüm kullanımlar ilgili politikaya göre YASAK - UYARILAR'a bakın.>")
        elif norm_tools:
            body = ("<No disclosure required: every declared use is exempt under the applicable policy. Set include_exempt to describe it anyway.>"
                    if lang == "en" else
                    "<Beyan gerekmez: beyan edilen tüm kullanımlar ilgili politikaya göre muaf. Yine de yazmak için include_exempt kullanın.>")
        else:
            body = NO_AI[(context, lang)]
        blocks.append(f"{heading}\n{body}")
    elif primary == "tubitak" and context == "grant":
        blocks.append(_tubitak_block(lang, norm_tools, sections, _verification(used_tools, verification, lang),
                                     conf_sentence))
    else:
        split = context in ("manuscript", "thesis") and primary in SPLIT_POLICIES
        groups = [("main", lambda p: True)]
        if split:
            groups = [("main", lambda p: p not in METHOD_USES), ("methods", lambda p: p in METHOD_USES)]
        for block, keep_fn in groups:
            btools = [{**t, "_kept": [p for p in t["_kept"] if keep_fn(p)]} for t in norm_tools]
            btools = [t for t in btools if t["_kept"]]
            if not btools:
                continue
            parts = _tool_sentences(context, lang, primary, btools, plural, figure_label, block)
            if sections and not all(t["sections"] for t in btools):
                parts.append(_sections_sentence(sections, lang))
            parts.append(_verification(btools, verification, lang))
            if block == "main" and context != "figure":
                parts.append(_closing(context, lang, primary, plural))
            if conf_sentence:
                parts.append(conf_sentence)
            head = HEADING[("methods", lang)] if block == "methods" else heading
            blocks.append(f"{head}\n{' '.join(parts)}")
        if split and len(blocks) == 2:
            notes.append("[NOTE] Two blocks drafted: the first goes where the policy puts writing assistance, the "
                         "second (research-method uses) goes in the Methods section.")
        if split and "yok" in keys:
            notes.append("[NOTE] YÖK asks for every AI-used part to be explained in the method section - carry the "
                         "writing-assistance uses into the Methods paragraph as well.")
    statement = "\n\n".join(blocks)

    placements = []
    for key in keys:
        pol = POLICIES[key]
        ctx = pol.contexts[context]
        placements.append(f"{pol.label} ({pol.as_of}): {ctx.placement_tr if lang == 'tr' else ctx.placement}")
        if context in pol.info:
            notes.append(f"[INFO] {pol.label}: {pol.info[context]}")
    if primary in ("elsevier", "taylor_francis") and context in ("manuscript", "figure"):
        notes.append("[INFO] Journal-level instructions can be stricter than the publisher policy "
                     "(Elsevier: 'the range of AI use varies depending on the journal'; T&F: some journals allow "
                     "nothing beyond language improvement).")
    return Result(context, lang, [POLICIES[k].label for k in keys], statement, placements,
                  warnings, notes, 1 if any_forbidden else 0)


def render(res: Result) -> str:
    out = [f"=== AI-use disclosure | context: {res.context} | policies: {', '.join(res.policies)} ===",
           f"Policy data verified {POLICY_DATA_DATE} (see references/). Re-check the live policy before submission.",
           "", "STATEMENT", res.statement, "", "PLACEMENT"]
    out += [f"- {p}" for p in res.placements]
    out += ["", "WARNINGS"] + ([f"- {w}" for w in res.warnings] or ["- none"])
    out += ["", "NOTES"] + ([f"- {n}" for n in res.notes] or ["- none"])
    out += ["", "Draft generated with AI assistance by alterlab-ai-use-disclosure; the author verifies and owns it."]
    return "\n".join(out)


def matrix(context: str) -> str:
    cols = [k for k, p in POLICIES.items() if context in p.contexts and k != "generic"]
    head = "| Use | " + " | ".join(cols) + " |"
    sep = "|---|" + "|".join(":-:" for _ in cols) + "|"
    rows = [head, sep]
    for p in MATRIX_ROWS[context]:
        cells = [SYMBOL[rule_for(POLICIES[c], context, p).status] for c in cols]
        rows.append(f"| `{p}` | " + " | ".join(cells) + " |")
    legend = ("Legend: ✗ forbidden · ⚠ avoid (discouraged) · D disclose (required) · R disclosure recommended "
              "or encouraged · E exempt from disclosure · ? not addressed by the fetched policy (disclose "
              "conservatively and ask). Generated by scripts/disclosure_builder.py --matrix " + context +
              f" from policy data verified {POLICY_DATA_DATE}.")
    return "\n".join(rows) + "\n\n" + legend


def list_venues() -> str:
    lines = []
    for k, p in POLICIES.items():
        lines.append(f"{k:22} {p.label} [{p.as_of}] contexts: {', '.join(p.contexts)}")
    lines.append("aliases: " + ", ".join(f"{a}->{b}" for a, b in sorted(ALIASES.items())))
    lines.append("UNVERIFIED (generic rules + warning): " + ", ".join(sorted(UNVERIFIED)))
    return "\n".join(lines)


def list_purposes() -> str:
    return "\n".join(f"{k:30} {en}" for k, (en, _tr) in PURPOSES.items())


# --------------------------------------------------------------------------- #
# Self-test (offline)                                                           #
# --------------------------------------------------------------------------- #
def self_test() -> int:
    fails: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    # 1. Table integrity.
    for k, pol in POLICIES.items():
        check(bool(pol.label and pol.as_of and pol.ref.startswith("references/")), f"{k}: metadata")
        for c, ctx in pol.contexts.items():
            check(c in CONTEXTS, f"{k}: bad context {c}")
            check(bool(ctx.placement and ctx.placement_tr), f"{k}/{c}: placement text")
            check(ctx.default.status in RANK and bool(ctx.default.note), f"{k}/{c}: default rule")
            for p, r in ctx.rules.items():
                check(p in PURPOSES, f"{k}/{c}: unknown purpose {p}")
                check(r.status in RANK and bool(r.note), f"{k}/{c}/{p}: rule")
    for p, (en, tr) in PURPOSES.items():
        check(bool(en and tr), f"purpose {p} phrases")

    # 2. Key verified rules (must match references/).
    exp = [
        ("nih", "peer_review", "review_language_polish", FORBIDDEN),
        ("nih", "peer_review", "accessibility_assistive", CHECK),
        ("tubitak", "peer_review", "review_language_polish", FORBIDDEN),
        ("tubitak", "grant", "upload_confidential", FORBIDDEN),
        ("tubitak", "grant", "grammar_spelling", EXEMPT),
        ("tubitak", "grant", "language_polishing", REQUIRED),
        ("elsevier", "manuscript", "grammar_spelling", EXEMPT),
        ("elsevier", "manuscript", "language_polishing", REQUIRED),
        ("elsevier", "figure", "figure_graphical_abstract", FORBIDDEN),
        ("elsevier", "figure", "figure_primary_image_edit", FORBIDDEN),
        ("wiley", "manuscript", "language_polishing", EXEMPT),
        ("wiley", "manuscript", "translation", REQUIRED),
        ("taylor_francis", "manuscript", "grammar_spelling", REQUIRED),
        ("sage", "manuscript", "qualitative_coding", FORBIDDEN),
        ("plos", "manuscript", "translation", RECOMMENDED),
        ("ieee", "manuscript", "grammar_spelling", RECOMMENDED),
        ("icmje", "manuscript", "ai_as_author", FORBIDDEN),
        ("springer_nature", "peer_review", "review_draft_report", FORBIDDEN),
        ("erc", "peer_review", "review_language_polish", CHECK),
        ("erc", "peer_review", "review_summarize_submission", FORBIDDEN),
        ("nsf", "peer_review", "review_literature_search", CHECK),
        ("nsf", "grant", "drafting", RECOMMENDED),
        ("ukri", "grant", "translation", EXEMPT),
        ("ukri", "grant", "grant_interview", FORBIDDEN),
        ("ukri", "peer_review", "review_draft_report", FORBIDDEN),
        ("yok", "thesis", "ai_as_author", FORBIDDEN),
        ("yok", "ethics_application", "synthetic_participants", AVOID),
        ("icmje", "manuscript", "figure_primary_image_edit", CHECK),
        ("nih", "peer_review", "review_literature_search", FORBIDDEN),
        ("wiley", "manuscript", "interpretation", REQUIRED),
        ("plos", "manuscript", "interpretation", AVOID),
        ("ec_living_guidelines", "grant", "upload_confidential", AVOID),
        ("arxiv", "manuscript", "grammar_spelling", CHECK),
    ]
    for k, c, p, s in exp:
        got = rule_for(POLICIES[k], c, p).status
        check(got == s, f"rule {k}/{c}/{p}: expected {s}, got {got}")

    # 3. End-to-end builds.
    r = build({"context": "peer_review", "venue": "nih", "tools": [{"name": "ChatGPT", "purposes": ["review_language_polish"]}]})
    check(r.exit_code == 1 and any(w.startswith("[FORBIDDEN]") for w in r.warnings), "NIH review polish must be forbidden")
    check("ChatGPT" not in r.statement, "forbidden use must not appear in the statement")
    r = build({"context": "peer_review", "venue": "nih", "language": "tr"})
    check(r.exit_code == 0 and "kullanmadım" in r.statement, "NIH no-AI reviewer declaration (tr)")
    r = build({"context": "manuscript", "venue": "elsevier", "human_verification": "All edits were checked.",
               "tools": [{"name": "ChatGPT", "version": "GPT-5", "provider": "OpenAI", "date": "March 2026",
                          "purposes": ["grammar_spelling", "language_polishing"]}]})
    check(r.statement.startswith(ELSEVIER_TITLE), "Elsevier section title")
    check("in order to improve the wording" in r.statement and "check grammar" not in r.statement,
          "Elsevier: exempt grammar use omitted, polishing kept")
    check(r.exit_code == 0 and not any(w.startswith("[FORBIDDEN]") for w in r.warnings), "Elsevier clean run")
    r = build({"context": "manuscript", "venue": "wiley", "language": "tr",
               "tools": [{"name": "Claude", "purposes": ["translation"]}]})
    check(any("[MISSING]" in w and "version" in w for w in r.warnings), "Wiley requires version")
    check("aracı" in r.statement and "çevirisi amacıyla kullanılmıştır" in r.statement, "Turkish manuscript sentence")
    r = build({"context": "grant", "venue": "tubitak", "language": "tr", "sections": ["Yöntem"],
               "confidential_input": False, "human_verification": "Kodlar ekipçe test edildi.",
               "tools": [{"name": "Gemini", "version": "2.5 Pro", "purposes": ["code", "drafting"]}]})
    check("Üretken Yapay Zekâ (ÜYZ) Kullanım Beyanı" in r.statement and "Yöntem" in r.statement, "TÜBİTAK block")
    check("Gizli, yayımlanmamış" in r.statement and r.exit_code == 0, "TÜBİTAK confidentiality confirmation")
    r = build({"context": "grant", "venue": "tubitak", "confidential_input": True,
               "tools": [{"name": "ChatGPT", "version": "x", "purposes": ["drafting"]}], "sections": ["Özgün değer"]})
    check(r.exit_code == 1, "TÜBİTAK confidential input must be forbidden")
    r = build({"context": "thesis", "venue": "yok", "language": "tr",
               "tools": [{"name": "ChatGPT", "purposes": ["literature_search"]}]})
    missing = " ".join(w for w in r.warnings if w.startswith("[MISSING]"))
    check(all(f in missing for f in ("version", "date", "where in the work")), "YÖK missing version/date/sections flagged")
    check(any("Yöntem bölümü" in p for p in r.placements), "YÖK placement is the method section")
    check("Bu tezin hazırlanmasında ChatGPT aracı" in r.statement, "Turkish thesis sentence")
    r = build({"context": "manuscript", "venue": "plos", "tools": [{"name": "X", "purposes": ["ai_as_author"]}]})
    check(r.exit_code == 1 and any("author list" in w for w in r.warnings), "AI authorship forbidden with specific action")
    r = build({"context": "grant", "venue": "nih", "tools": [{"name": "X", "purposes": ["drafting"]}]})
    check(any(w.startswith("[AVOID]") for w in r.warnings) and any("six" in n for n in r.notes), "NIH drafting + cap info")
    r = build({"context": "manuscript", "venue": "science", "tools": [{"name": "X", "purposes": ["drafting"]}]})
    check(any(w.startswith("[UNVERIFIED]") for w in r.warnings), "unverified venue flagged")
    r = build({"context": "manuscript", "venue": "elsevier", "also_apply": ["yok"],
               "tools": [{"name": "ChatGPT", "purposes": ["grammar_spelling"]}]})
    check("check grammar" in r.statement, "strictest policy wins (YÖK requires what Elsevier exempts)")
    check(len(r.placements) == 2, "both placements listed")
    for bad in ({"context": "x", "venue": "elsevier"}, {"context": "grant", "venue": "elsevier"},
                {"context": "manuscript", "venue": "nope"},
                {"context": "manuscript", "venue": "plos", "tools": [{"name": "A", "purposes": ["zzz"]}]},
                {"context": "manuscript", "venue": "plos", "tools": [{"name": "A", "purposes": ["review_draft_report"]}]}):
        try:
            build(bad)
            fails.append(f"bad input accepted: {bad}")
        except InputError:
            pass
    check("| `review_draft_report` |" in matrix("peer_review"), "matrix renders")
    check(_join(["a and b", "c"], "en") == "a and b, and c", "serial comma join")
    check(_join(["x ve y", "z"], "tr") == "x ve y ile z", "Turkish join avoids double 've'")
    r = build({"context": "ethics_application", "venue": "yok", "language": "tr", "confidential_input": False,
               "tools": [{"name": "X", "version": "1", "date": "2026", "purposes": ["qualitative_coding"]}],
               "sections": ["Veri analizi"]})
    check("girilmeyecektir" in r.statement and "kullanılacaktır" in r.statement, "ethics application uses future tense")

    if fails:
        print("SELF-TEST FAILED:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"self-test OK ({len(exp)} rule checks, {len(POLICIES)} policies, {len(PURPOSES)} purposes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draft an AI-use disclosure and check it against venue/funder policy.")
    ap.add_argument("input", nargs="?", help="JSON file describing the AI use, or '-' for stdin")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    ap.add_argument("--list-venues", action="store_true")
    ap.add_argument("--list-purposes", action="store_true")
    ap.add_argument("--matrix", choices=sorted(MATRIX_ROWS), help="print the policy matrix for a context")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.list_venues:
        print(list_venues())
        return 0
    if args.list_purposes:
        print(list_purposes())
        return 0
    if args.matrix:
        print(matrix(args.matrix))
        return 0
    if not args.input:
        ap.print_usage(sys.stderr)
        return 2
    try:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        res = build(json.loads(raw))
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(res), ensure_ascii=False, indent=2) if args.json else render(res))
    return res.exit_code


if __name__ == "__main__":
    sys.exit(main())
