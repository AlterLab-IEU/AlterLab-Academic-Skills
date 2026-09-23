# Turkey (YÖK, TÜBİTAK) and the EU AI Act (verified 2026-09-23)

All quotations are **verbatim** from the official documents, fetched on **2026-09-23**.
The Turkish originals are authoritative. English lines marked “official EN” come from
YÖK's own English edition; other English renderings are summaries and are not quoted.

---

## 1. YÖK: *Yükseköğretim Kurumları Bilimsel Araştırma ve Yayın Faaliyetlerinde Üretken Yapay Zekâ Kullanımına Dair Etik Rehber* (Mayıs 2024)

**Status and scope.** YÖK prepared the guide “yükseköğretim kurumlarını bilgilendirmek
amacıyla”, that is, to inform higher-education institutions. It covers scientific research
and publication in general. There is no separate chapter for theses, articles or
ethics-committee files: the same rules apply to each. It warns that ignoring its
disclosure rule leads to disciplinary liability.

### 1.1 Articles, theses and every other scholarly work: the method-section rule

> Bilimsel araştırma ve yayın yazım aşamalarında ÜYZ kullanılan bölümlerin yöntem kısmında açıklanması gereklidir. Bu hususların göz ardı edilmesi, şartları çerçevesinde disiplin sorumluluğuna yol açacaktır.

(official EN: “In scientific research and publication writing stages, the sections where
GAI is used should be explained in the method section. Ignoring these issues will lead to
disciplinary responsibility within the framework of its conditions.”)

The guide lists as its first risk: “İçerik üretiminde ÜYZ kullanıldığını eserde
bildirmeme”, that is, failing to state in the work that generative AI was used to produce
content.

**What to report (FAQ: *ÜYZ sistemlerinden elde edilen içeriklerin raporlanmasında nelere dikkat edilmelidir?*):**

> Hangi ÜYZ aracının, ne zaman, çalışmanın hangi aşamasında veya yerinde kullanıldığı ve ilgili aracın versiyonu belirtilmelidir.

The same FAQ adds three points: AI content must be reviewed with academic rigour; the
user is responsible for its accuracy (“İçeriklerin doğruluğu kullanıcının
sorumluluğundadır.”); and researchers carry responsibility for the report's content,
results and arguments.

### 1.2 Authorship

> ÜYZ, bir çalışmanın nihai halinin sorumluluğunu bir araştırmacı gibi alamayacağı için, bilimsel çalışmalarda yazar olarak yer alamaz.

(official EN: “Since GAI cannot take responsibility for the final version of a study as a
researcher, it cannot take part as an author in scientific studies.”) The guide also says
“bir makalenin tamamının ÜYZ’ye yazdırılması düşünülemeyeceğinden”: having AI write a
whole article is not conceivable.

### 1.3 What AI should not do

> Bu nedenle ÜYZ’nin kullanım amacı ve kapsamı hipotez geliştirme, tartışma, yorumlama ve uygulama gibi üst düzey beceri, deneyim ve uzmanlık gerektiren aşamaları içermemelidir.

Participants: “Gerçek katılımcılar yerine ÜYZ kullanılması doğru değildir.” (official EN:
“It is not correct to use GAI instead of real participants.”)

Translation and language checking are allowed:

> Kullanılabilir. Bununla beraber ÜYZ ile çevirisi veya dil kontrolü yapılan içeriğin son halinin de kullanıcı tarafından kontrol edilmesi esastır. Ortaya çıkan metnin nihai sorumluluğu yazara/yazarlara aittir.

### 1.4 Ethics-committee applications (etik kurul)

> Etik Kurulu başvurusunda ÜYZ kullanımı konusunda Kurula gerekli bilgi verilmelidir. Bu kapsamda araştırma protokolünde ÜYZ’nin kullanım amacı, kapsamı, niteliği konusunda bilgi verilebilir.

In practice, state in the protocol: purpose, scope, nature, tool and version, and stage.
Build the full dossier with `alterlab-tr-research-ethics`.

### 1.5 Theses (tez)

The guide has **no thesis-specific clause**. For a thesis, apply §1.1–1.4:
- explain the AI-used parts in the method section (*Yöntem*), with tool, version, when,
  and stage or place;
- no AI authorship;
- ethics-committee information where the study needs approval.

Among the laws to consider, the guide lists the “Lisansüstü Eğitim-Öğretim ve Sınav
Yönetmeliği” together with KVKK (6698), the 2547 Higher Education Law, the 5846 Law on
Intellectual and Artistic Works, and the “Yükseköğretim Kurumları Bilimsel Araştırma ve
Yayın Etiği Yönergesi”. **Institute-level thesis rules** (a declaration page, an AI-use
form, similarity-report thresholds) come from each university's *enstitü tez yazım
kılavuzu*. The skill did not verify any of them. Check your own institute's current
guide.

---

## 2. TÜBİTAK: *Destek Süreçlerinde Üretken Yapay Zekânın (ÜYZ) Sorumlu ve Güvenilir Kullanımı Rehberi*

**Versions.** First issued as *Eylül 2025* (v03). The Turkish landing page now links
**v04, dated *Ocak 2026***. The two versions differ in two ways. v04 deletes “kasıtlı
olarak” (intentionally) from the fabrication and falsification bans in §1.3.3 and §1.5.2,
so AI-assisted fabrication is prohibited whatever the intent. v04 also updates the YÖK
link. **Scope:** all TÜBİTAK support programmes, applicants and evaluators, and also
interim, progress and final reports.

### 2.1 Applicants: declaration (§1.2)

> Proje önerisinin hazırlanmasında ÜYZ araçlarının kullanıldığı durumlarda bu durumun beyan edilmesi zorunludur.

The guide defines significant use (“önemli ölçüde kullanım”) as follows:

> Bu ifade, basit dilbilgisi veya yazım denetimi gibi temel kullanımların ötesine geçen durumları kapsar.

Drafting a section, generating analysis code, data analysis, creating visuals, and
producing content that supports the proposal's main arguments all count as significant
use.

Method (§1.2.2): “ÜYZ kullanım beyanı, TÜBİTAK'ın çevrimiçi başvuru sistemlerinde bu
amaçla özel olarak ayrılmış bölümde yapılmalıdır.” The declaration states:
- “Kullanılan ÜYZ aracının/araçlarının adı ve versiyonu.”
- the stages or sections where AI was used, for example “literatür özetinin ilk
  taslağının oluşturulmasında” or “yöntem bölümündeki Python kodlarının üretilmesinde”;
- “Kullanımın niteliği ve kapsamı hakkında kısa bir açıklama”.

### 2.2 Applicants: allowed with care, and prohibited

- **Supportive uses (§1.1.1):** literature search and summarising; language and style;
  coding help; brainstorming; visualisation suggestions. For visuals, the guide says
  “Görsellerin ve içeriklerin yapay zekâ ile oluşturulduğu ve kullanılan yapay zekâ aracı
  mutlaka belirtilmelidir.”
- **High-risk uses (§1.1.2):** AI-drafted proposal sections, data analysis or synthetic
  data, and AI figures. These are allowed only with thorough verification. Drafts “asla
  nihai metin olarak kabul edilmemelidir”: they must never be accepted as final text.
- **Prohibited (§1.5):** plagiarism through AI; fabricated or falsified data or
  references; and:

> TÜBİTAK'a sunulacak proje önerisiyle ilgili gizli detayları, yayınlanmamış araştırma verilerini, KVKK kapsamında korunan kişisel verileri veya üçüncü şahıslara ait özel/ticari bilgileri ÜYZ araçlarına girmek veya yüklemek kesinlikle yasaktır.

### 2.3 Evaluators (referees, panellists, monitors): total ban (§2.1)

> TÜBİTAK Değerlendiricilerinin, değerlendirme göreviyle ilgili herhangi bir amaçla ÜYZ araçlarını (örneğin, GPT, Gemini, Claude, Imagen, Veo benzeri web tabanlı veya API erişimli modeller) kullanmaları kesinlikle yasaktır.

The ban covers every stage, including summarising the project, identifying strengths and
weaknesses, drafting reports, preparing panel notes, monitoring reports, and
“Değerlendirme ile ilgili herhangi bir metni (örneğin, e-posta taslakları) oluşturmak.”
Under §2.3, breaches are handled as a breach of confidentiality and under TÜBİTAK AYEK
Yönetmeliği Madde 9/1-ı (“görevi ihmal veya kötüye kullanma”).

---

## 3. EU AI Act: what matters for researchers' disclosure

**Regulation (EU) 2024/1689** (the AI Act) is amended by **Regulation (EU) 2026/1744**,
the “Digital Omnibus on AI” (8 July 2026). The Omnibus was published in the OJ on
24.7.2026 and entered into force “on the third day following that of its publication”.

### 3.1 Article 50: the transparency duties (verbatim, unchanged by the Omnibus except para. 7)

Art. 50(2), **providers**:

> Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, shall ensure that the outputs of the AI system are marked in a machine-readable format and detectable as artificially generated or manipulated.

Art. 50(4), first subparagraph, **deployers**, deep fakes:

> Deployers of an AI system that generates or manipulates image, audio or video content constituting a deep fake, shall disclose that the content has been artificially generated or manipulated.

Art. 50(4), second subparagraph, **deployers**, public-interest text:

> Deployers of an AI system that generates or manipulates text which is published with the purpose of informing the public on matters of public interest shall disclose that the text has been artificially generated or manipulated. This obligation shall not apply where the use is authorised by law to detect, prevent, investigate or prosecute criminal offences or where the AI-generated content has undergone a process of human review or editorial control and where a natural or legal person holds editorial responsibility for the publication of the content.

Timing (Art. 50(5)): the information must be given “in a clear and distinguishable manner
at the latest at the time of the first interaction or exposure”.

Definitions (Art. 3):
- “‘deployer’ means a natural or legal person, public authority, agency or other body
  using an AI system under its authority except where the AI system is used in the course
  of a personal non-professional activity”;
- “‘deep fake’ means AI-generated or manipulated image, audio or video content that
  resembles existing persons, objects, places, entities or events and would falsely
  appear to a person to be authentic or truthful”.

### 3.2 Research exclusions (Art. 2)

> This Regulation does not apply to AI systems or AI models, including their output, specifically developed and put into service for the sole purpose of scientific research and development.

> This Regulation does not apply to any research, testing or development activity regarding AI systems or AI models prior to their being placed on the market or put into service.

Territorial scope includes “providers and deployers of AI systems that have their place
of establishment or are located in a third country, where the output produced by the AI
system is used in the Union” (Art. 2(1)(c)).

### 3.3 Dates

- Art. 113 as adopted: the Regulation “shall apply from 2 August 2026”. Article 50 sits
  in Chapter IV, which has no earlier or later date, so it applies from **2 August 2026**.
- The Omnibus adds Art. 111(4), a four-month transition for **providers** only:

> Providers of AI systems, including general-purpose AI systems, generating synthetic audio, image, video or text content, that have been placed on the market before 2 August 2026 shall take the necessary steps in order to comply with Article 50(2) by 2 December 2026.

- The Omnibus replaces Art. 50(7) (codes of practice for detecting, marking and
  labelling AI-generated content). It does not amend Art. 50(1)–(6).

### 3.4 What this means in practice (interpretation, not legal advice)

1. **Article 50 does not replace journal or funder rules.** A peer-reviewed article still
   needs the publisher's AI declaration (see `publisher_policies.md`), whatever the Act
   says.
2. **Marking (Art. 50(2)) is the providers' duty**, meaning the companies that supply
   generative tools. It is not the duty of authors who use those tools, unless a research
   group itself provides such a system to others.
3. **Deep fakes (Art. 50(4) first subparagraph)** concern researchers who publish
   AI-generated or AI-manipulated images, audio or video that resemble real persons,
   places or objects and would falsely appear authentic. Examples: a photorealistic
   “photo” of a real lab or person in outreach material, or a synthetic interview clip.
   Label such content.
4. **Public-interest text (Art. 50(4) second subparagraph)** does not apply where the text
   underwent human review or editorial control *and* someone holds editorial
   responsibility. The Act does not say which scholarly outputs are published with the purpose of
   “informing the public on matters of public interest”. Treat press releases, policy briefs,
   public reports and blog posts made with AI as the likeliest cases. Get legal advice
   for edge cases.
5. **Art. 2(6)** covers AI systems built “for the sole purpose of scientific research and
   development”. It does **not** exempt the use of commercial general-purpose tools such
   as chatbots in research.
6. **Researchers in Turkey:** whether Art. 2(1)(c) reaches a given output “used in the
   Union” is a legal question for the institution's legal office. The skill does not
   decide it.

---

## Sources (all retrieved 2026-09-23)

- YÖK guide, Turkish PDF (Mayıs 2024): https://proje.yok.gov.tr/documentFiles/17539645334.Y%C3%BCksek%C3%B6%C4%9Fretimde%20%C3%BCretken%20yapay%20zeka%20kullan%C4%B1m%C4%B1-tr.pdf ; English PDF: https://proje.yok.gov.tr/documentFiles/17539645794.Y%C3%BCksek%C3%B6%C4%9Fretimde%20%C3%BCretken%20yapay%20zeka%20kullan%C4%B1m%C4%B1-en.pdf ; landing page: https://proje.yok.gov.tr/tr/page/635 (the older eski.yok.gov.tr PDF link cited in TÜBİTAK v03 did not respond)
- TÜBİTAK guide v04 (Ocak 2026), Turkish: https://tubitak.gov.tr/sites/default/files/2026-01/UYZ_Rehberi_v04_TR.pdf ; v03 (Eylül 2025): https://tubitak.gov.tr/sites/default/files/2025-10/UYZ_Rehberi_v03_TR.pdf ; landing pages: https://tubitak.gov.tr/tr/kurumsal/hakkimizda/uretken-yapay-zeka-rehberi and https://tubitak.gov.tr/en/institutional/about-us/generative-artificial-intelligence-guideline (English PDF v04 linked there, not used for quotes)
- Regulation (EU) 2024/1689, OJ text via the EU Publications Office (CELEX 32024R1689): http://publications.europa.eu/resource/celex/32024R1689 (EUR-Lex HTML returned a bot challenge; the Publications Office served the same OJ act)
- Regulation (EU) 2026/1744 (Digital Omnibus on AI), OJ L 24.7.2026 (CELEX 32026R1744): http://publications.europa.eu/resource/celex/32026R1744
