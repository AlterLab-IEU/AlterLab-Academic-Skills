<div align="center">

# AlterLab Akademik Beceriler

**Her yerdeki akademisyenler ve araştırmacılar için 180 Claude AI becerisi**
*13 araştırma alanına göre düzenlenmiş — Claude'u kendi alanınızın uzmanına dönüştürün.*

[![Skills](https://img.shields.io/badge/Beceri-180-7C3AED?style=for-the-badge)](skills/)
[![Domains](https://img.shields.io/badge/Alan-13-2563EB?style=for-the-badge)](skills/)
[![License](https://img.shields.io/badge/Lisans-MIT-10B981?style=for-the-badge)](LICENSE)

[English README](README.md) · [Becerileri Keşfet](skills/) · [Hızlı Başlangıç](#-hızlı-başlangıç) · [Katkıda Bulun](CONTRIBUTING.md)

</div>

---

## Bu Proje Nedir?

**AlterLab Akademik Beceriler**, fakülte üyeleri, akademisyenler ve araştırmacılar için tasarlanmış 180 adet uzmanlaşmış Claude AI becerisinden oluşan bir kütüphanedir. Her beceri, Claude'u belirli bir akademik alanda uzman bir asistana dönüştürür — bilimsel veritabanları, biyoinformatik araçlar, klinik araştırma protokolleri, akademik yazım, hibe başvuruları ve daha fazlası.

Her beceri tek bir `.md` dosyasıdır. Claude Code veya Claude Projects içine bırakırsınız, Claude o alanın bilgisiyle donanmış olarak çalışmaya başlar.

> [!NOTE]
> Bu Türkçe dosya bir özet çeviridir. Becerilerin tam ve güncel listesi için [İngilizce README](README.md) dosyasına bakın.

> [!TIP]
> **Hedef kitle:** Fakülte üyeleri, doktora sonrası araştırmacılar, doktora öğrencileri. Lisans seviyesi iletişim öğrencileri için [AlterLab FC Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills) projesine bakabilirsiniz.

---

## 13 Araştırma Alanı

| Alan | Beceri Sayısı | Kapsam |
|---|:---:|---|
| **Çekirdek Pipeline** | 7 | Araştırma → yazım → hakemlik → revizyon — tam akademik üretim hattı |
| **Bilimsel Veritabanları** | 39 | PubMed, ChEMBL, UniProt, ClinicalTrials.gov, COSMIC, AlphaFold ve daha fazlası |
| **Biyoinformatik** | 25 | Genomik, proteomik, tek hücre RNA analizi — Scanpy, BioPython, ESM, scvi-tools |
| **Kemoinformatik** | 12 | İlaç keşfi, moleküler dinamik, RDKit, docking, ADMET |
| **Klinik Araştırma** | 7 | Klinik karar desteği, tedavi planlaması, tıbbi görüntüleme, regülasyon |
| **Veri Bilimi** | 22 | scikit-learn, PyTorch Lightning, SHAP, transformerlar |
| **Görselleştirme** | 8 | Matplotlib, Seaborn, Plotly, bilimsel şematikler |
| **Akademik Yazım** | 13 | Bilimsel yazım, atıf yönetimi, hibe önerileri, posterler, akademik kariyer |
| **Laboratuvar Entegrasyonları** | 9 | Benchling, DNAnexus, Opentrons, Protocols.io |
| **Alan-Spesifik** | 17 | Kuantum hesaplama, jeo-uzamsal, malzeme bilimi, sosyal bilim metodolojisi, dijital beşeri bilimler |
| **Doküman Araçları** | 2 | MarkItDown belge dönüştürme, Open Notebook |
| **Araştırma Araçları** | 12 | Arama, keşif, Zotero, nitel yöntemler, etik, anketler, açık bilim |
| **Finans & Ekonomi** | 7 | FRED, Alpha Vantage, SEC EDGAR, piyasa araştırması |

**Toplam: 180 beceri, 13 alan.**

---

## 🚀 Hızlı Başlangıç

### Seçenek 1 — Claude Projects *(Önerilen)*

```
1. claude.ai → Projeler → Yeni Proje Oluştur
2. İlgili alandan SKILL.md dosyalarını projenin "Knowledge" bölümüne yükleyin
3. Sohbete başlayın — Claude artık o alanın uzmanı
```

### Seçenek 2 — Claude Code Eklenti Pazarı *(Önerilen)*

Depo, `alterlab-academic-skills` adlı bir Claude Code eklenti pazarı olarak yayınlanır ve 13 alan eklentisi içerir (`alterlab-core`, `alterlab-databases`, `alterlab-bioinformatics`, … `alterlab-finance-economics`).

```bash
# Claude Code içinde:
/plugin marketplace add AlterLab-IEU/AlterLab-Academic-Skills
/plugin install alterlab-core@alterlab-academic-skills
# ihtiyacınız olan diğer alanlar için tekrarlayın, ör.:
/plugin install alterlab-bioinformatics@alterlab-academic-skills
```

> [!NOTE]
> Becerilerin Claude tarafından otomatik tetiklenmesi için ilgili `SKILL.md` dosyaları `~/.claude/skills/` dizinine kopyalanmalıdır.

### Seçenek 3 — Tekil Beceri Kullanımı

Her beceri bağımsız bir `.md` dosyasıdır. `skills/` klasörüne göz atın ve ihtiyacınız olanları indirin.

---

## ⚡ Çekirdek Pipeline — 7 Beceri

> *Sistemin kalbi: araştırmadan yayına çok-ajanlı bir üretim hattı.*

| # | Beceri | Ajan Sayısı | Ne Yapar |
|:---:|---|:---:|---|
| 1 | **Derin Araştırma** | 13 | Sistematik inceleme, Sokratik diyalog, kaynak doğrulama |
| 2 | **Makale Yazarı** | 12 | LaTeX akademik makale, çift-dilli özet, 9 yazım modu |
| 3 | **Makale Hakemi** | 7 | Çoklu-perspektif hakemlik, Şeytanın Avukatı modu, 0–100 kalite rubriği |
| 4 | **Araştırma Pipeline** | 7 | 10 aşamalı orkestratör, bütünlük doğrulama |
| 5 | **Öğretim Tasarımı** | — | Ders programı, müfredat, rubrik, Bloom taksonomisi |
| 6 | **Tez Danışmanı** | — | Doktora rehberliği, savunma hazırlığı, jüri yönetimi |

### Tam Pipeline Akışı

```
derin-araştırma (sokratik/tam)
  → makale-yazarı (plan/tam)
    → makale-hakemi (tam/rehberli)
      → makale-yazarı (revizyon)
        → makale-hakemi (yeniden hakemlik, en fazla 2 döngü)
          → makale-yazarı (format dönüşümü → nihai çıktı)
```

---

## 🇹🇷 Türkçe Desteği

Pipeline becerileri Türkçe girdiyi tanır ve çıktıyı kullanıcının diline uygun üretir. Örnek:

```
Sen: "Yapay zekanın eğitimdeki etkileri konusunda hızlı bir literatür taraması yap."
Claude (alterlab-deep-research): [Türkçe RQ Brief + İngilizce kaynak listesi + Türkçe sentez]
```

Çift-dilli özet (Türkçe + İngilizce) `alterlab-paper-writer` becerisinde varsayılan olarak desteklenir.

---

## 🏗️ Proje Yapısı

```
AlterLab-Academic-Skills/
├── skills/
│   ├── core/                  # 7 çekirdek pipeline becerisi
│   │   └── shared/            # Paylaşılan referans dokümanları
│   ├── databases/             # 39 bilimsel veritabanı bağlayıcısı
│   ├── bioinformatics/        # 25 biyoinformatik beceri
│   └── ...                    # ve 10 diğer alan
├── scripts/
│   ├── audit_skills.py        # SKILL.md şema denetleyicisi
│   └── normalize_skills.py    # Otomatik şema düzeltici
├── tests/                     # pytest harness (1863 doğrulama)
├── CLAUDE.md                  # Proje düzeyi yönlendirme kuralları
└── README.md                  # İngilizce ana README
```

Her beceri klasörü şu yapıdadır:

```
alterlab-{ad}/
├── SKILL.md           # Frontmatter + ana yönergeler (≤500 satır)
└── references/        # Detaylı doküman parçaları (gerektiğinde yüklenir)
```

---

## ⚙️ Beceriler Nasıl Çalışır?

1. **Tetikleyici** — Beceri açıklamasındaki anahtar kelimeler Claude'un beceriyi etkinleştirip etkinleştirmeyeceğini belirler.
2. **Yükleme** — Etkinleşince, Claude SKILL.md gövdesini bağlama yükler.
3. **Referanslar** — Görev gerektirdikçe, `references/*.md` dosyaları talep üzerine yüklenir.
4. **MCP Tercihi** — MCP araçları (PubMed, Scholar Gateway, Clinical Trials, Hugging Face) mevcutsa, beceriler eğitim verisi yerine canlı veriyi tercih eder ve kaynağı + erişim tarihini gösterir.

Bu kademeli yükleme yaklaşımı sayesinde 180 beceri aynı projede yüklenebilir; Claude yalnızca ihtiyaç duyduğunu hafızaya çeker.

---

## 🤝 Katkıda Bulunma

Yeni beceri eklemek veya mevcut bir beceriyi geliştirmek için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına göz atın. Hızlı kontrol listesi:

- Beceri ismi `alterlab-` öneki ile başlamalı, klasör adı ile eşleşmeli
- `license: MIT` (depo üst-seviye lisansı)
- `allowed-tools` alanı kategori varsayılanına göre doldurulmalı
- `description` alanı 1024 karakteri geçmemeli
- SKILL.md gövdesi 500 satırı geçmemeli — detay `references/` içine taşınmalı
- Açıklamada AlterLab suite ibaresi geçmeli

Pull request açmadan önce:

```bash
python3 scripts/audit_skills.py      # şema denetimi
python3 scripts/normalize_skills.py  # otomatik düzeltme
pytest tests/                        # pytest harness
```

---

## 📜 Lisans

[MIT Lisansı](LICENSE). Becerinin kapsadığı her aracın ayrı bir lisansı olabilir — ilgili SKILL.md frontmatter'ında veya araç dokümantasyonunda kontrol edin.

---

## 🙏 Üreten

**AlterLab Creative Technologies Laboratory** — İzmir Ekonomi Üniversitesi bünyesinde kurulmuş, ancak herhangi bir kuruma bağlı olmayan, açık kaynak akademik araç geliştirme laboratuvarı.

Bu beceriler dünyanın herhangi bir noktasındaki herhangi bir araştırmacı için tasarlanmıştır. Kurumsal kilit yoktur.

[![GitHub](https://img.shields.io/badge/GitHub-AlterLab--IEU-181717?logo=github)](https://github.com/AlterLab-IEU)
