<div align="center">
<img src=".github/header-banner.svg" width="100%" alt="AlterLab Academic Skills">
<br>

<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Beceri-242-7C3AED?style=for-the-badge&logo=bookstack&logoColor=white" alt="Beceri: 242"></a>
<a href="docs/CATALOG.md"><img src="https://img.shields.io/badge/Alan-18-2563EB?style=for-the-badge&logo=databricks&logoColor=white" alt="Alan: 18"></a>
<a href="#lisans"><img src="https://img.shields.io/badge/Lisans-MIT%20depo%20%2B%20beceri%20bazl%C4%B1-10B981?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="Lisans: depo MIT, beceri bazında lisanslar"></a>
<a href="https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases"><img src="https://img.shields.io/github/v/release/AlterLab-IEU/AlterLab-Academic-Skills?style=for-the-badge&logo=github&color=8B5CF6&logoColor=white&label=S%C3%BCr%C3%BCm" alt="Sürüm"></a>

**Dil:** [English](README.md) · [Türkçe](README.tr-TR.md)

### Toplam: 242 beceri · 18 alan — öğretim üyeleri ve araştırmacılar için Claude Agent Skills

</div>

AlterLab Academic Skills, akademik çalışma için bir [Agent Skills](https://agentskills.io)
kütüphanesidir: literatür taraması, makale yazımı ve hakemliği, kaynak denetimi, araştırma
tasarımı ve istatistik, bilimsel veri tabanları ve araç takımları, ve Türk akademik sistemi
(YÖK, ÜAK, DergiPark, TÜBİTAK). Her beceri, çoğunlukla başvuru belgeleri ve küçük yardımcı
betiklerle birlikte gelen bir `SKILL.md` talimat dosyasıdır; Claude'a tek bir iş türü için bir
yöntem verir.

Bir becerinin ürettiğine, yetkin bir araştırma asistanının taslağına bakar gibi bakın: işe
yarar, ama kontrol edilmesi gerekir. Beceriler Claude'dan kaynak göstermesini ve yapay zekâ
desteğini beyan etmesini ister; çıktıyı doğru, eksiksiz ya da teslime hazır hâle getirmez.

[AlterLab Yaratıcı Teknolojiler Laboratuvarı](https://github.com/AlterLab-IEU) tarafından
öğretim üyeleri ve araştırmacılar için hazırlanmıştır (öğrenci becerileri:
[AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills)).

## Neler denetlendi, neler denetlenmedi

| Düzey | Durum |
|---|---|
| Yapısal olarak geçerli değerlendirme (eval) dosyası olan beceriler | **242 / 242** — 1.535 vaka; her PR'da CI'da denetlenir (yalnızca şema ve tetiklenme kapsamı; model çağrılmaz) |
| Girdi dosyası sağlayan eval vakaları | 5 beceride 6 vaka, artı aşağıdaki kıyaslama (benchmark) fikstürleri |
| Canlı modelle davranışsal olarak değerlendirilen beceriler | **5** — aşağıdaki beş kıyaslama görevi. Diğer 237 becerinin kayıtlı bir davranışsal sonucu yok. (Bunları notlandırması gereken gecelik CI işi haftalarca hiçbir şey notlandırmadı: API anahtarı eksikti ve başarısızlıklar başarı olarak raporlanıyordu. İş kaldırıldı; hiçbir şey notlandırmayan bir çalıştırma artık sıfırdan farklı kodla çıkar.) |
| Çıplak modeli geçtiği gösterilen beceriler | Beş kıyaslama görevinden **1'i** (doçentlik ön taraması). Diğer dördünde çıplak model zaten tavana yakındı. |
| Yardımcı betikler | birim testli: girdi doğrulama, referans değerler ve hata yolları (`tests/`) |
| Dinamik iş akışları (`/alterlab-workflows:*`) | hata enjeksiyonu dâhil sahte bir çalışma ortamında kuru çalıştırma; canlı çalıştırılmadı |
| Becerinin otomatik seçilmesi (aktivasyon) | ölçüm aracı var (`run_evals.py --activation`); güncel kayıtlı çalıştırma yok |

### Kıyaslama

Beş görev; her birinde standart, zor-negatif ve eksik-girdi vakası var. Model her maddeyi
etiketler, bir betik etiketleri kanıt dayanaklı beklenen yanıtlarla karşılaştırarak puanlar
(LLM hakem yok). İki kol da aynı araçlarla yalıtılmış çalışma dizinlerinde çalışır; beceri
kolu ayrıca beceriyi alır. Model `claude-opus-5-5`, Claude Code CLI üzerinden, kol başına 2
çalıştırma, 2026-10-14.

| Görev (beceri) | Doğru — beceri | Doğru — çıplak | Yanlış onay / yanlış suçlama — beceri | — çıplak |
|---|---:|---:|---:|---:|
| citation-integrity (`alterlab-citation-verifier`) | 56/56 | 55/56 | 0 / 0 | 0 / 0 |
| manuscript-review (`alterlab-paper-reviewer`) | 40/40 | 40/40 | 0 / 0 | 0 / 0 |
| screening (`alterlab-research-workflows`) | 38/38 | 38/38 | 0 / 0 | 0 / 0 |
| analysis-check (`alterlab-test-selection-guard`) | 30/32 | 30/32 | 2 / 0 | 2 / 0 |
| docentlik (`alterlab-docentlik-eligibility`) | **41/42** | 30/42 | 0 / 0 | 2 / 0 |
| **Toplam** | **205/208** | 193/208 | 2 / 0 | 4 / 0 |

Beceri kolunun maliyeti (CLI'nin bildirdiği) yaklaşık %39 daha yüksek, süresi yaklaşık %24 daha uzundu. Beceri kolundaki iki yanlış onay, iki kolun da aynı şekilde kaçırdığı tek bir sınırda analiz maddesidir.

Bunları sentetik fikstürler üzerinde küçük örneklemli sonuçlar olarak okuyun; kataloğun
doğrulaması değildir. Tüm sonuçlar, madde bazında hatalar, yöntem ve sınırlılıklar:
[`docs/benchmark-results.md`](docs/benchmark-results.md).

## Kurulum

**Claude Code (eklentiler)** — `claude plugin validate` ile doğrulandı:

```bash
/plugin marketplace add AlterLab-IEU/AlterLab-Academic-Skills
/plugin install alterlab-essentials@alterlab-academic-skills   # başlangıç seti ya da tek bir alan:
/plugin install alterlab-turkish-academia@alterlab-academic-skills
/reload-plugins
```

**Doğrudan kurulum** (Claude Code beceri dizini ya da araçlar arası `~/.agents/skills/`;
`python3` gerekir). Seçilen becerinin bağımlı olduğu beceriler de kurulur (`--no-deps` ile
atlanır):

```bash
git clone https://github.com/AlterLab-IEU/AlterLab-Academic-Skills.git && cd AlterLab-Academic-Skills
scripts/install.sh --list
scripts/install.sh core/alterlab-citation-verifier      # tek beceri (+ bağımlılıkları)
scripts/install.sh turkish-academia                     # bir alan
```

**claude.ai / Claude uygulaması** — becerileri tek tek yükleyin:
[Sürümler](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/releases) sayfasından
`skill-<ad>-<sürüm>.zip` dosyasını indirip Customize ▸ Skills ▸ Upload a skill ile yükleyin
(kod yürütme açık olmalı). Bu arşivler becerinin paylaşılan dosyalarını ve lisans bildirimlerini
içerir; yükleyicinin reddettiği bildirilen ön bilgi (frontmatter) alanlarını çıkarır. Eşlik eden
bir beceriye ihtiyaç duyan beceriler sürüm notlarında belirtilir. Paketleme burada test edildi;
canlı yükleyicinin kabulü test edilmedi. `alterlab-<alan>-<sürüm>.zip` arşivleri yükleme
dosyası değildir — bir beceri dizinine açılır.

**Diğer ajanlar** — beceriler açık Agent Skills biçimini izler;
[`docs/portability.md`](docs/portability.md) neyin taşınabildiğini ve neyin Claude Code'a özgü
olduğunu listeler. Diğer ortamlar burada test edilmedi.

## Kullanım

Beceri adlarını bilmeniz gerekmez. İşi anlatın ya da *"AlterLab becerilerini kullan"* deyin;
`alterlab-skill-finder` bir beceri seçer ve hangisini, neden seçtiğini söyler. Claude Code'da
`alterlab-workflows` eklentisi yedi çok-ajanlı iş akışı ekler: kaynak denetimi
(`citation-audit`), hakem paneli (`review-panel`), iddia sınaması (`claim-stress-test`), PRISMA
taraması (`systematic-review-screening`), hakemlere yanıt (`rebuttal`), proje değerlendirme
paneli (`grant-mock-panel`, TÜBİTAK dâhil) ve literatür haritası (`literature-map`).

Her iş akışı `status: complete | partial | blocked` ile birlikte bir kapsam hesabı (istenen,
tamamlanan, başarısız, çözülmemiş) döndürür ve rapor dosyasını ancak geri okunduktan sonra
bildirir. Aynı modelin ayrı ajanları birbirine demirlenmekten kaçınır ama bağımsız doğrulama
değildir; raporlar bunu açıkça yazar.

## Bütünlük araçları neyi gösterir

- **`alterlab-citation-verifier`** kaynakların var olduğunu ve künyelerinin Crossref, OpenAlex,
  Semantic Scholar, arXiv ve doi.org kayıtlarıyla uyuştuğunu denetler, geri çekilmeleri işaretler.
  Denetleyemediği bir kayıt `unverified` olur, asla geçer sayılmaz; ayrıştıramadığı girdi
  çalıştırmayı `PARTIAL` yapar (çıkış kodu 3).
- **`claim_faithfulness.py`** bir iddiayı yalnızca atıf yapılan çalışmanın **özetiyle**
  karşılaştırır ve bir iddiayı asla doğrulanmış saymaz: sezgisel eşleşme
  `LEXICAL_MATCH_REQUIRES_REVIEW`, model yargısı `MODEL_JUDGED_SUPPORT_REQUIRES_REVIEW` olarak
  etiketlenir; yanlış sayı, ters çevrilmiş karşılaştırma, popülasyon uyuşmazlığı ve temkinli
  kanıt durumlarında karar vermekten kaçınır. Bir iddiayı desteklenmiş saymadan önce atıf
  yapılan pasajı okuyun. Ayrıntı: [`docs/integrity.md`](docs/integrity.md).

## Alanlar

Çekirdek hat 10 · Veri tabanları 39 · Biyoinformatik 38 · Keminformatik 12 · Klinik araştırma 7 ·
Veri bilimi 22 · Görselleştirme 9 · Yazım araçları 14 · Laboratuvar entegrasyonları 9 ·
Alana özgü 18 · Belge araçları 3 · Araştırma araçları 14 · Finans ve ekonomi 7 ·
Türk akademisi 13 · Akademik yaşam 6 · Metodoloji 3 · Sosyal bilim iş akışı 17 ·
Araştırma iş akışları 1 + 7 iş akışı.

Tüm beceriler: [`docs/CATALOG.md`](docs/CATALOG.md) · aranabilir katalog:
[alterlab-ieu.github.io/AlterLab-Academic-Skills](https://alterlab-ieu.github.io/AlterLab-Academic-Skills/).

## Kendiniz denetleyin

```bash
uv run --frozen pytest tests/ -q
uv run python scripts/run_evals.py --strict
uv run python scripts/run_evals.py --behavioral --skill alterlab-docentlik-eligibility
uv run python scripts/run_benchmark.py
```

Canlı komutlar `claude` CLI'nin kendi oturumunu kullanır; kimliği doğrulanmış bir Claude Code
ortamında çalışırlar ve sonuçları `eval-results/` altına JSON olarak yazarlar. Davranışsal
çalıştırma yalnızca seçilen her vaka bir karar üretip geçtiyse `0` ile çıkar. Ayrıntı:
[`docs/evals.md`](docs/evals.md).

## Lisans

Depo MIT lisanslıdır; ancak her becerinin içeriği kendi `license:` alanındaki lisansa tabidir
ve bunlar farklıdır: 202 MIT, 19 Apache-2.0, 4 CC-BY-NC-4.0, 4 GPL-3.0, 2 GPL-2.0, 1 LGPL-3.0,
1 CeCILL-2.1, 2 BSD-3-Clause, 2 CC-BY-4.0, 1 CC-BY-3.0, 4 CC0-1.0. Dört çekirdek hat becerisi
(`alterlab-deep-research`, `alterlab-paper-writer`, `alterlab-paper-reviewer`,
`alterlab-research-pipeline`) kaynak projeleri nedeniyle **ticari olmayan** kullanım lisanslıdır
(CC-BY-NC-4.0). Bir beceriyi yeniden dağıtmadan ya da ticari amaçla kullanmadan önce lisansına
bakın. Kurulan ya da paketlenen her beceri `LICENSE`, `NOTICE` ve `THIRD_PARTY_NOTICES.md`
dosyalarını taşır. Köken bilgisi: [`PROVENANCE.md`](PROVENANCE.md),
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Atıf

```bibtex
@software{alterlab_academic_skills_2026,
  title   = {AlterLab Academic Skills},
  author  = {{AlterLab Creative Technologies Laboratory, Izmir University of Economics (IEU)}},
  year    = {2026},
  version = {3.0.1},
  url     = {https://github.com/AlterLab-IEU/AlterLab-Academic-Skills}
}
```

Ayrıntılı üst veri [`CITATION.cff`](CITATION.cff) dosyasındadır; sürüm geçmişi
[`CHANGELOG.md`](CHANGELOG.md) dosyasındadır.

## Katkı ve teşekkür

Katkılarınızı bekliyoruz — bkz. [`CONTRIBUTING.md`](CONTRIBUTING.md). Şu anda en yararlı katkı
davranışsal kanıttır: dayanaklı yanıtlarla yeni kıyaslama vakaları ya da bir becerinin
eval'lerinin kayıtlı bir çalıştırması.

Proje, K-Dense'in [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)
(MIT) kütüphanesinin içerik çatalı olarak başladı; çekirdek araştırma hattını Cheng-I Wu'nun
[academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
(CC-BY-NC 4.0) projesinden uyarlar. Kardeş projeler:
[AlterLab-FC-Skills](https://github.com/AlterLab-IEU/AlterLab-FC-Skills) (iletişim öğrencileri)
ve [AlterLab_GameForge](https://github.com/AlterLab-IEU/AlterLab_GameForge) (oyun geliştirme).
