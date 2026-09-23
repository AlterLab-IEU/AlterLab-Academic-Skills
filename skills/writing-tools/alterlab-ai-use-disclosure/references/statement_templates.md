# Disclosure Statement Templates (EN + TR)

These are fill-in templates. Replace every «…» field. Never state a check you did not
perform, and never leave a used tool out. The wording follows the verified rules in
`publisher_policies.md`, `funders_peer_review.md` and `turkey_eu.md`. The Elsevier
template in 1c and the reviewer template in 6b are quoted verbatim from Elsevier's policy;
all other wording is AlterLab's. `scripts/disclosure_builder.py` fills these patterns
automatically and checks them against the policy.

**Minimum content** (the union of the verified policies):
- tool name, version and provider (T&F, Wiley, TÜBİTAK and YÖK ask for the version;
  Elsevier asks for version and developer when AI is used in Methods);
- date or period of use (Wiley, YÖK);
- purpose, and the sections or stages affected (IEEE, TÜBİTAK, YÖK, PLOS);
- how outputs were checked (PLOS, Elsevier, Wiley);
- a responsibility sentence.

---

## 0. AI-use log (keep one per project)

Elsevier's FAQ asks authors to “keep a separate record of which tool and model was used,
and how AI tools were used”. Wiley asks authors to document all AI use. YÖK asks *when*
and *at which stage* AI was used. A log makes every statement below quick to fill in.

| Date | Tool + version | Provider | Task / purpose | Section / stage | Prompt & output saved at | How checked | By |
|---|---|---|---|---|---|---|---|
| «2026-03-04» | «ChatGPT, GPT-5» | «OpenAI» | «language polishing» | «Discussion» | «/ai-log/2026-03-04.md» | «read against original; meaning unchanged» | «AB» |

---

## 1. Manuscripts

### 1a. Acknowledgments variant (writing assistance: ICMJE, Wiley, IEEE, PLOS)

**EN**: The authors used «TOOL» («VERSION»; «PROVIDER»; accessed «MONTH YEAR») to «PURPOSE,
e.g. improve the language and readability of the Introduction and Discussion». The
authors reviewed and edited all output and take full responsibility for the content of
this article.

**TR**: Bu çalışmanın hazırlanmasında «ARAÇ» (sürüm: «SÜRÜM»; sağlayıcı: «SAĞLAYICI»;
kullanım: «AY YIL») aracı «AMAÇ; ör. Giriş ve Tartışma bölümlerinin dilinin ve
okunabilirliğinin iyileştirilmesi» amacıyla kullanılmıştır. Araç çıktılarının tamamı
yazarlarca gözden geçirilmiş ve düzenlenmiştir; makalenin içeriğine ilişkin tüm
sorumluluk yazarlara aittir.

*IEEE:* also name the **specific sections** and the **level** of AI use. *T&F:* give the
**full tool name with version number** and the **reason** for use.

### 1b. Methods variant (AI in research: code, analysis, screening, data visualisation)

**EN**: *Use of generative AI tools.* «TOOL» («VERSION»; «PROVIDER»; «DATES») was used to
«PURPOSE, e.g. draft R code for the mixed-effects models / screen titles and abstracts
against the eligibility criteria». «VALIDATION, e.g. all code was reviewed line by line
and re-run on the full dataset; results matched a manual re-analysis / two reviewers
checked every exclusion». Prompts and outputs are available «in Supplementary File S«n» /
on request».

**TR**: *Üretken yapay zekâ araçlarının kullanımı.* «ARAÇ» (sürüm: «SÜRÜM»; sağlayıcı:
«SAĞLAYICI»; «TARİHLER») aracı «AMAÇ; ör. karma etkiler modellerine ait R kodlarının
taslağının yazılması» amacıyla kullanılmıştır. «DOĞRULAMA; ör. kodların tamamı satır
satır incelenmiş ve tüm veri setiyle yeniden çalıştırılmıştır». İstemler (prompt) ve
çıktılar «Ek Dosya S«n»'de / talep üzerine» paylaşılabilir.

Where it goes:
- Elsevier: research-method AI goes in Methods, with tool, version and developer.
- ICMJE: data collection, analysis and figure generation go in Methods.
- Wiley: methodology, data and literature-review uses go in Methods.
- PLOS: a dedicated Methods subsection.

### 1c. Elsevier: required section title and recommended statement (verbatim)

> Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

> During the preparation of this work, the author(s) used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, the author(s) reviewed and edited the content as needed and take(s) full responsibility for the content of the published article.

Place it at the end of the manuscript, immediately before the references. Basic grammar,
spelling and punctuation checks need no declaration.

### 1d. Authors at Turkish universities: YÖK method-section paragraph (in addition to the journal's own statement)

**TR (Yöntem)**: Bu çalışmada üretken yapay zekâ (ÜYZ) aşağıdaki şekilde kullanılmıştır:
«ARAÇ» («SÜRÜM»), «TARİH» tarihinde, çalışmanın «AŞAMA/BÖLÜM» aşamasında «AMAÇ» amacıyla
kullanılmıştır. ÜYZ çıktıları yazarlarca «DOĞRULAMA» yoluyla doğrulanmış ve
düzenlenmiştir; içeriğin doğruluğu ve sorumluluğu yazarlara aittir.

**EN (Methods)**: Generative AI was used as follows: «TOOL» («VERSION») was used on «DATE»
at the «STAGE/SECTION» stage to «PURPOSE». The authors verified and edited the outputs by
«VERIFICATION» and are responsible for the accuracy of the content.

### 1e. No AI used (when a venue or form asks)

**EN**: No generative AI tools were used in the preparation of this work.
**TR**: Bu çalışmanın hazırlanmasında üretken yapay zekâ araçları kullanılmamıştır.

---

## 2. Figure captions and legends

**EN**: Figure «n». «TITLE». «TOOL» («VERSION», «PROVIDER»; accessed «DATE») was used to
«create an initial draft of this schematic»; the authors «redrew/revised it in «SOFTWARE»
and checked every element against «SOURCE»».

**TR**: Şekil «n». «BAŞLIK». Bu şeklin «ilk taslağı» «ARAÇ» («SÜRÜM», «SAĞLAYICI»;
kullanım: «TARİH») aracıyla oluşturulmuş; yazarlarca «YAZILIM» ile yeniden çizilmiş/
düzenlenmiş ve tüm öğeleri «KAYNAK» ile karşılaştırılarak doğrulanmıştır.

Venue rules:
- **Elsevier**: caption *and* the AI declaration for explanatory images; Methods for data
  visualisations; never for primary research images or graphical abstracts made with
  general-purpose image tools.
- **Wiley**: caption with name, version, date, role and the authors' role; no AI-edited
  photographs.
- **Springer Nature**: caption *and* AI Declaration, and only from verifiable inputs.
- **PLOS**: figure legend.

---

## 3. Grant proposals

### 3a. Generic / NSF (Project Description)

**EN**: *Use of generative AI in preparing this proposal.* «TOOL» («VERSION»; «PROVIDER»)
was used to «PURPOSE» in «SECTIONS». «VERIFICATION». The applicants reviewed and revised
all AI-assisted content and take full responsibility for the accuracy and originality of
the proposal. «No confidential, unpublished or personal data were entered into AI tools.»

**TR**: *Proje önerisinin hazırlanmasında üretken yapay zekâ kullanımı.* Bu proje önerisinin
hazırlanmasında «ARAÇ» (sürüm: «SÜRÜM»; sağlayıcı: «SAĞLAYICI») aracı «BÖLÜMLER»
kapsamında «AMAÇ» amacıyla kullanılmıştır. «DOĞRULAMA». Yapay zekâ destekli tüm içerik
başvuru sahiplerince gözden geçirilip düzeltilmiştir; önerinin doğruluğu ve özgünlüğüne
ilişkin tüm sorumluluk başvuru sahiplerine aittir.

- **NSF**: “encouraged to indicate in the project description the extent to which, if
  any, generative AI technology was used and how”.
- **NIH**: describe the use in the application, as NIH/ORI advised in May 2026. Keep AI
  away from substantially developing any section (NOT-OD-25-132).
- **UKRI**: declare substantive use; minimal use needs no statement; never use AI during
  interviews.
- **ERC**: no dedicated field. Acknowledge AI help as you would other external help, and
  follow the call documents.

### 3b. TÜBİTAK: ÜYZ Kullanım Beyanı (online application system, dedicated section)

**TR**:
- Kullanılan ÜYZ aracı/araçları ve sürümü: «ARAÇ, SÜRÜM»
- Kullanıldığı aşama/bölümler: «ör. literatür özetinin ilk taslağının oluşturulması;
  yöntem bölümündeki Python kodlarının üretilmesi»
- Kullanımın niteliği ve kapsamı: «ör. ilk taslak oluşturma, metin iyileştirme, kod
  parçacığı üretme»; üretilen içerik proje ekibince yeniden yazılmış ve tüm kaynaklar ile
  kodlar doğrulanmıştır.
- Gizli proje bilgileri, yayımlanmamış araştırma verileri ve kişisel veriler ÜYZ
  araçlarına girilmemiştir.

**EN**:
- Tool(s) and version: «…»
- Stage(s)/section(s): «…»
- Nature and scope of use: «…»; the team rewrote the generated content and verified all
  sources and code.
- No confidential proposal details, unpublished data or personal data were entered into
  AI tools.

Basic grammar or spelling checks alone need no declaration (§1.2.1). The same rules apply
to progress and final reports.

---

## 4. Thesis (YÖK: method section)

**TR (Yöntem bölümü)**: *Üretken yapay zekâ (ÜYZ) kullanımı.* Bu tezin hazırlanmasında
«ARAÇ» (sürüm: «SÜRÜM»; sağlayıcı: «SAĞLAYICI»; kullanım: «TARİH ARALIĞI») aracı
«AMAÇ; ör. literatürün taranması ve özetlenmesi ile İngilizce özetin çevirisi» amacıyla
kullanılmıştır (kullanıldığı bölüm/aşamalar: «BÖLÜMLER»). «DOĞRULAMA; ör. önerilen tüm
kaynaklar veri tabanlarından tek tek doğrulanmış, çeviri satır satır kontrol edilmiştir».
Yapay zekâ destekli tüm çıktılar tez yazarı tarafından gözden geçirilmiş ve
düzenlenmiştir; tezin içeriğine ilişkin tüm sorumluluk tez yazarına aittir.

**EN**: *Use of generative AI.* In preparing this thesis, the author used «TOOL»
(«VERSION»; «PROVIDER»; «DATES») to «PURPOSE» (used in: «SECTIONS»). «VERIFICATION».
The author reviewed and edited all AI-assisted output and takes full responsibility for
the content of this thesis.

**No AI used (TR)**: Bu tezin hazırlanmasında üretken yapay zekâ araçları kullanılmamıştır.
**No AI used (EN)**: No generative AI tools were used in the preparation of this thesis.

If your institute's thesis template has an ethics or declaration page, add one line that
points to the method-section paragraph. Such a page is an institution-specific rule, not a
YÖK rule.

---

## 5. Ethics-committee application (YÖK FAQ: inform the committee)

**TR (araştırma protokolü)**: *Araştırmada üretken yapay zekâ (ÜYZ) kullanımı.* Bu
araştırmada «ARAÇ» («SÜRÜM») aracı, araştırmanın «AŞAMA» aşamasında «AMAÇ; ör. görüşme
dökümlerinin ön kodlanması» amacıyla kullanılacaktır. Kullanımın kapsamı: «KAPSAM».
Kişisel veriler araca girilmeden önce «anonimleştirilecek/maskelenecektir». ÜYZ, gerçek
katılımcıların yerine kullanılmayacaktır. Araştırma ekibi tüm ÜYZ çıktılarını doğrulayacak
ve bunlardan sorumlu olacaktır.

**EN**: *Use of generative AI in the study.* In this study, «TOOL» («VERSION») will be used
at the «STAGE» stage to «PURPOSE». Scope: «SCOPE». Personal data will be «anonymised/masked»
before any input to the tool. Generative AI will not be used in place of real
participants. The research team will verify all AI outputs and remains responsible for
them.

The full dossier (committee type, consent, KVKK) belongs to `alterlab-tr-research-ethics`.

---

## 6. Peer review

### 6a. No AI used: required stance for NIH and TÜBİTAK, safe everywhere

**EN**: I did not use generative AI tools to analyse, summarise or evaluate this submission
or to draft or edit this review, and I did not upload or share any of its content with
such tools.

**TR**: Bu değerlendirmenin hazırlanmasında üretken yapay zekâ araçlarını başvuruyu/makaleyi
analiz etmek, özetlemek veya değerlendirmek ya da değerlendirme metnini yazmak veya
düzenlemek için kullanmadım; başvuru/makale içeriğinin hiçbir bölümünü bu araçlara
yüklemedim veya bu araçlarla paylaşmadım.

### 6b. Permitted language help on your own text (only where the venue allows it)

Elsevier's suggested reviewer statement, verbatim:

> During the preparation of this report, I used [NAME OF TOOL / SERVICE] in order to [REASON]. After using this tool/service, I reviewed and edited the content as needed and I take full responsibility for its content.

**EN (other venues)**: In preparing this review, I used «TOOL» («VERSION») only to polish the
language of comments I had written myself. No part of the submission was entered into or
shared with the tool. I take full responsibility for the content of this review.

**TR**: Bu değerlendirmenin hazırlanmasında «ARAÇ» («SÜRÜM») aracını yalnızca kendi yazdığım
yorumların dilini düzeltmek amacıyla kullandım. Başvuru/makale içeriğinin hiçbir bölümü
araca girilmemiş veya araçla paylaşılmamıştır. Bu değerlendirmenin içeriğine ilişkin tüm
sorumluluk bana aittir.

Where it goes:
- Elsevier: in the report.
- Springer Nature: describe it in the report.
- Wiley: tell the handling editor.
- PLOS: in the review form.
- Sage: assistive help needs no disclosure.

**Never** at NIH or TÜBİTAK. At NSF, only with NSF-approved tools. At ERC or UKRI, only
without proposal text or personal data.

### 6c. Asking the editor first (ICMJE V.B: “request permission from the journal”)

**EN**: Before I start the review, may I use «TOOL» for «PURPOSE»? No manuscript content
would be entered into the tool.
**TR**: Değerlendirmeye başlamadan önce «AMAÇ» için «ARAÇ» kullanmam uygun mudur? Araca makale
içeriğinden hiçbir bölüm girilmeyecektir.

---

## 7. Late or corrective disclosure (AI use found after submission)

ICMJE V.A: “Nondisclosure of AI use may require corrective action”. Disclose it yourself,
promptly:

**EN**: Dear Editor, regarding manuscript «ID», we wish to add a disclosure omitted at
submission: «TOOL» («VERSION») was used to «PURPOSE» in «SECTIONS». We have re-verified
the affected content «HOW» and attach a revised statement for the «SECTION». We apologise
for the omission.

**TR**: Sayın Editör, «ID» numaralı makalemizde gönderim sırasında eksik kalan bir beyanı
eklemek isteriz: «ARAÇ» («SÜRÜM») aracı «BÖLÜMLER» bölümlerinde «AMAÇ» amacıyla
kullanılmıştır. İlgili içeriği «NASIL» yeniden doğruladık; güncellenmiş beyanı «BÖLÜM»
için ekte sunuyoruz. Bu eksiklik için özür dileriz.

*Reviewers who breached a no-upload rule should tell the editor, or the funder's
designated official, directly. Never word a statement that hides the breach.*
