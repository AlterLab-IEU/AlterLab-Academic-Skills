---
name: alterlab-aperta
description: "Drives TÜBİTAK Açık Bilim Politikası (Open Science Policy) compliance and deposition into Aperta — TÜBİTAK ULAKBİM's national open archive at aperta.ulakbim.gov.tr — encoding its principles (İlke 1: deposit the accepted manuscript in Aperta on acceptance; İlke 2: open access at most 6 months after publication for STEM, 12 for SSH; İlke 6: document data that must stay closed, e.g. for KVKK; İlke 9: report compliance in the final report) and scaffolding the five-question TÜBİTAK Veri Yönetim Planı / VYP (data management plan) uploaded with ARDEB applications. Use when depositing to Aperta, complying with the TÜBİTAK açık bilim policy, preparing a TÜBİTAK data management plan (VYP), reporting open-access compliance in a final report, or documenting a justified data embargo. For Zenodo/Dryad/OSF and international DMPs prefer alterlab-open-science; for the KVKK lawful-basis/anonymisation plan prefer alterlab-kvkk-dmp. Part of the AlterLab Academic Skills suite."
license: MIT
allowed-tools: Read Write Edit Bash(python:*) WebFetch
compatibility: "No API key required. Guidance + scaffolding skill; uses WebFetch for live policy/repository checks and optional Python helpers via `uv run python` (stdlib-only, requests optional)."
metadata:
  skill-author: AlterLab
  version: "1.1.0"
  last_updated: "2026-09-23"
  depends_on: "alterlab-kvkk-dmp (İlke-6 closed-data justification), alterlab-open-science (international repositories/DMPs)"
---

# Aperta & TÜBİTAK Open Science Compliance

Turkey's national open-science track. Given a TÜBİTAK-funded output (an
accepted manuscript, a dataset, or a grant proposal that needs a data plan),
this skill turns the **TÜBİTAK Açık Bilim Politikası** (Open Science Policy) into
a concrete checklist: deposit the right object to **Aperta**, set the correct
open-access embargo, justify any closed data under **İlke-6** (Principle 6, the
closed-data clause), and produce a **Veri Yönetim Planı / VYP** (data management
plan) for the application. It is the Turkish/TÜBİTAK counterpart to the
international-facing `alterlab-open-science`.

Canonical Turkish terms used below (English gloss on first use): *açık bilim*
(open science), *Veri Yönetim Planı / VYP* (data management plan), *kabul edilmiş
makale* (accepted manuscript), *ambargo* (embargo), *İlke* (Principle), *etik
kurul* (ethics committee), *KVKK* (Turkish Personal Data Protection Law 6698).

## When to Use This Skill

```
Aperta'ya makalemi nasıl yüklerim? (How do I deposit my article to Aperta?)
Prepare a TÜBİTAK data management plan (VYP) for my 1001 application
My article was just accepted — what does the TÜBİTAK open-science policy require?
Justify keeping my clinical dataset closed under TÜBİTAK İlke-6 (privacy/KVKK)
Document open-access compliance for my project's final report (sonuç raporu)
What embargo applies to my social-sciences paper under TÜBİTAK policy?
```

→ Identify the object (manuscript / dataset / proposal), apply the policy rule
from `references/policy_mandates.md`, and either generate the deposit checklist,
the VYP, or the İlke-6 justification. Always end with the
**verify-against-current-policy** disclaimer (see below).

### Does NOT Trigger

This skill owns **TÜBİTAK/Aperta** open science only. Route adjacent asks to the
correct sibling:

| The ask is really about… | Route to |
|--------------------------|----------|
| Zenodo / Dryad / Figshare / OSF deposit, FAIR, CC licences, an **NSF/NIH/ERC/UKRI** DMP, Green/Gold/Diamond OA in general | `alterlab-open-science` |
| The **KVKK** lawful-basis selector, anonymisation vs pseudonymisation, VERBİS, cross-border transfer plan | `alterlab-kvkk-dmp` |
| Which **etik kurul** (ethics committee) is needed, informed-consent / onam form, TİTCK permit | `alterlab-tr-research-ethics` |
| Scaffolding the **ARDEB 1001 / 1002-A proposal** narrative (özgün değer, yaygın etki, work packages) | `alterlab-tubitak-proposal` |
| Posting a **preprint** to a server (arXiv, bioRxiv, SSRN) before/independent of acceptance, or open-access routes in general | `alterlab-open-science` |
| Writing the TÜBİTAK **sonuç raporu / ara rapor** narrative itself (progress, deliverables) — this skill writes only the open-science/data-deposition compliance statement, not the report body | (out of scope — narrative report writing) |
| Checking a journal's **TR Dizin** indexing status before submitting | `alterlab-trdizin` |
| Depositing a graduate **thesis** to YÖK Ulusal Tez Merkezi | `alterlab-yok-tez` |

The line: this skill answers **"what must I deposit/embargo/justify to satisfy
TÜBİTAK's open-science policy, and how do I do it in Aperta?"** It does not write
the proposal, choose the ethics committee, or run the KVKK analysis — it consumes
the KVKK decision (closed/anonymised?) and emits the İlke-6 justification.

## What Aperta Is

| Property | Value |
|----------|-------|
| Operator | TÜBİTAK ULAKBİM (the national academic-IT centre) |
| URL | `https://aperta.ulakbim.gov.tr/` |
| Role | The "TÜBİTAK Açık Arşivi" named by the policy: TÜBİTAK-supported outputs, UBYT-incentivised works, TÜBİTAK researchers' publications, and the research data behind TÜBİTAK academic-journal articles |
| Platform | InvenioRDM |
| Identifiers | A **DOI** per record under prefix `10.48623` |
| Access modes | Open, **embargoed**, **restricted** and **versioned** records — metadata stays open while files are gated |
| Machine access | Public records API `https://aperta.ulakbim.gov.tr/api/records?q=…` and OAI-PMH at `/oai2d` |

Scope and operator come from ULAKBİM's page
(`ulakbim.tubitak.gov.tr/en/turkey-open-archive-aperta/`); platform, DOI prefix and
interfaces were checked live on 2026-09-23. Deposit mechanics live in
`references/aperta_repository.md`.

## The Binding Mandates (summary)

The **TÜBİTAK Açık Bilim Politikası** (in force 14 March 2019) covers publications
and research data produced wholly or partly with TÜBİTAK support (grants,
scholarships, awards, incentives). Its principles, quoted in
`references/policy_mandates.md` (verified 2026-09-23), are the authority — cite
that file, not memory.

1. **İlke 1 — deposit in Aperta, on acceptance.** Deposit the *kabul edilmiş
   makale* (accepted manuscript) in the TÜBİTAK Açık Arşivi (Aperta) as soon as the
   article is accepted; its metadata must be open and machine-readable from the
   deposit date.
2. **İlke 2 — open-access ceilings, counted from publication.** The full text must
   be open on acceptance where possible, otherwise **no later than 6 months after
   publication** for *Fen Bilimleri, Teknoloji, Mühendislik ve Matematik* (STEM)
   and **12 months after publication** for *Sosyal ve Beşeri Bilimler* (SSH).
3. **İlke 4 + ARDEB rule — VYP with the application.** The policy recommends a
   *Veri Yönetim Planı*; ARDEB's VYP note requires uploading it to PBS with the
   other application documents, on TÜBİTAK's five-question template.
4. **İlke 6 — document closed data.** Where data cannot be opened, fully or for a
   period (personal or sensitive data under **KVKK**, confidentiality, national
   security, patent/registration periods), the reason must be documented and
   stated explicitly; the dataset can sit in Aperta as a **restricted** record
   with open metadata.
5. **İlke 9 — report compliance.** The grantee reports policy compliance in the
   project *sonuç raporu* (final report), and TÜBİTAK takes compliance into
   account when assessing the grantee's future applications.

> If a detail is not in `references/policy_mandates.md` (for example a
> publisher's own embargo terms), say so and send the user to the policy PDF or
> the publisher's self-archiving policy rather than filling the gap from memory.

## Workflows

### A. Deposit an accepted manuscript or dataset to Aperta

1. Classify the object: *kabul edilmiş makale* vs dataset vs both.
2. Determine the field bucket — STEM (≤ 6 months after publication) or SSH
   (≤ 12 months after publication) — to set the latest open date. Default to
   **immediate open** unless the user needs a delay; check the publisher's
   self-archiving terms against the ceiling before the author signs.
3. Decide access mode: open, or **restricted** if İlke-6 applies (see workflow C).
4. Walk the deposit checklist in `references/aperta_repository.md` (record
   metadata, file upload, licence, DOI minting, version).
5. Confirm the DOI and the open-access date satisfy the embargo ceiling.

### B. Scaffold a TÜBİTAK Veri Yönetim Planı (VYP)

Run the generator, then refine its prose with the user's specifics:

```bash
uv run python skills/turkish-academia/alterlab-aperta/scripts/vyp_scaffold.py \
    --project "Proje adı" --field stem --lang both \
    --data-closed --closed-reason kvkk \
    --out vyp.md
```

- `--field stem|ssh` sets the publication open-access ceiling cited in the plan.
- `--lang tr|en|both` emits a Turkish VYP, an English DMP, or both.
- `--data-closed` + `--closed-reason kvkk|commercial|security|ethics` injects an
  İlke-6 justification stub. **If the reason is KVKK, hand the lawful-basis /
  anonymisation decision to `alterlab-kvkk-dmp` and paste its conclusion in** —
  this skill records *that* data is closed and *why* at the funder level; it does
  not perform the KVKK analysis.

The scaffold's eight sections map onto the official five-question ARDEB template
(`veri_yonetim_plani.docx`, uploaded to PBS with the application); the mapping and
the section tree are in `references/vyp_template.md`.

### C. Justify a closed dataset under İlke-6

1. Confirm the closure reason is legitimate (KVKK personal/special-category data,
   commercial confidentiality, security, or an active ethics restriction).
2. For KVKK reasons, get the lawful-basis + anonymisation outcome from
   `alterlab-kvkk-dmp` first — note that **re-identifiable "anonymised" data does
   not qualify** as truly anonymous.
3. Choose the Aperta access mode: **restricted record with open metadata** (so the
   dataset is discoverable and citable even while access is gated).
4. Write the İlke-6 justification (one paragraph: what data, which legal/ethical
   basis for closure, who may request access, and any future-opening trigger).
5. Carry that justification into both the VYP and the *sonuç raporu*.

### D. Final-report open-access compliance check

Produce a short compliance statement for the *sonuç raporu* (İlke 9): for each
output, list the Aperta DOI, the access mode, and the open-access date, and
confirm it meets the İlke-2 ceiling — or, if closed, cite the İlke-6
justification. The public records API confirms each deposit's DOI and
`access_right` (recipe in `references/aperta_repository.md`). If generative AI
helped draft the report, TÜBİTAK's 2025 ÜYZ guide asks for that use to be
declared in the report as well.

## Live verification (optional)

When the user needs the current policy or to confirm a repository feature, fetch:

- Policy PDF: `https://tubitak.gov.tr/sites/default/files/tubitak_acik_bilim_politikasi_190316.pdf`
- ARDEB VYP template: `https://tubitak.gov.tr/sites/default/files/2024-04/veri_yonetim_plani.docx`
- ULAKBİM Aperta page: `https://ulakbim.tubitak.gov.tr/en/turkey-open-archive-aperta/`
- The repository itself: `https://aperta.ulakbim.gov.tr/`

`scripts/policy_check.py` does a light reachability + keyword probe of these so
you can tell the user whether the live policy matches what this skill encodes
(it does **not** scrape or assert new mandates).

## Verify-Against-Current-Policy Disclaimer

TÜBİTAK can revise the Açık Bilim Politikası, the VYP template and Aperta's
deposit flow. Close by telling the user to confirm the open-access ceilings, the
deposit object, and the VYP template against the current policy PDF, the live
programme page and the Aperta submission form before relying on this output —
a stale rule here would put their grant compliance at risk.

## References

- `references/policy_mandates.md` — the TÜBİTAK Açık Bilim Politikası principles
  (İlke 1–9, quoted), with sources and last-verified date.
- `references/aperta_repository.md` — what Aperta is, its InvenioRDM features and
  interfaces, the record-by-record deposit checklist, and how to verify a deposit.
- `references/vyp_template.md` — the official five-question VYP form, its mapping
  to the scaffold, and the bilingual section tree the script emits.

Part of the AlterLab Academic Skills suite.
