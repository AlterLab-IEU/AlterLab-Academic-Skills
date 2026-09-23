# Aperta — Repository Facts & Deposit Checklist

> **Last verified: 2026-09-23** by live requests to the repository. Confirm the live submission
> form before depositing.

## What Aperta is

| Property | Value | Source |
|----------|-------|--------|
| Name | Aperta — TÜBİTAK Açık Arşivi / Türkiye Açık Arşivi (Turkey Open Archive) | policy PDF + ULAKBİM page |
| Operator | TÜBİTAK ULAKBİM | ULAKBİM page |
| URL | `https://aperta.ulakbim.gov.tr/` | live |
| Purpose | Stores, preserves and gives free access to TÜBİTAK-supported publications and data, articles of TÜBİTAK's academic journals and their research data, and UBYT-incentivised outputs | ULAKBİM page |
| Platform | **InvenioRDM** (the page markup carries the InvenioRDM theme) | live |
| Persistent ID | A **DOI** per record under prefix **10.48623** (e.g. `10.48623/aperta.2261`, `10.48623/303489`); versioned records also carry a concept DOI for the version family | live API |
| Access modes | `access_right` values `open`, `embargoed`, `restricted` observed; restricted records expose an access-request link | live API |
| Machine interfaces | REST API `https://aperta.ulakbim.gov.tr/api/records` (JSON, query with `?q=`); OAI-PMH `https://aperta.ulakbim.gov.tr/oai2d` (repositoryName "Aperta", adminEmail `aperta@tubitak.gov.tr`, earliest datestamp 2021-03-12) | live |

## Why InvenioRDM matters for compliance

InvenioRDM separates **metadata** (public) from **files** (open, embargoed, or restricted). That is
exactly the shape İlke 1 and İlke 6 need: an accepted manuscript can be deposited on acceptance
with open metadata and an embargo date, and a closed clinical/KVKK dataset can have a public,
citable record (title, authors, abstract, DOI) while its files sit behind restricted access with
an access-request route. Versioning lets a later, opened or anonymised version supersede an
embargoed one without losing the DOI lineage.

## Deposit checklist (per record)

Walk these for each manuscript or dataset. Field names follow the generic InvenioRDM deposit form;
confirm exact labels on the live Aperta form.

1. **Resource type** — publication (accepted manuscript) vs dataset vs both.
2. **Object/version** — for a publication, upload the **kabul edilmiş makale**
   (author-accepted version), unless the publisher permits the version of record.
3. **Core metadata** — title, creators (with affiliations/ORCID if available),
   publication/issue date, language, abstract, keywords. Metadata is open from the deposit date
   (İlke 1).
4. **Funding** — record the TÜBİTAK project (program + grant number) so the deposit is linked to
   the funded project for final-report reporting.
5. **Licence** — choose an open licence for openly released outputs (İlke 3 recommends the widest
   access; the specific licence is the author's/publisher's call).
6. **Access mode** —
   - *Open* → immediately, or with an embargo that ends no later than 6 months (STEM) / 12 months
     (SSH) **after publication** (İlke 2; see `policy_mandates.md`).
   - *Restricted* → keep metadata public; gate the files; attach the İlke-6 justification. Set
     the embargo lift date if the closure is temporary.
7. **DOI** — let Aperta mint the DOI (prefix 10.48623); capture it for the final report.
8. **Version** — if replacing an earlier embargoed/preprint version, add a new version rather
   than a new record to preserve citation lineage.

## Verifying a deposit (for the sonuç raporu)

The public records API confirms a deposit and its access state without logging in:

```bash
curl -s "https://aperta.ulakbim.gov.tr/api/records?q=%22<title words>%22&size=5" \
  | python3 -c "import sys,json; [print(h['doi'], h['metadata']['access_right'], h['metadata']['title']) for h in json.load(sys.stdin)['hits']['hits']]"
```

Report the DOI, `access_right` and the embargo/open date per output. The API shape was observed
on the verification date; if it changes, check the record page instead.

## After deposit

- Record the **DOI**, the **access mode**, and the **open-access date** for the project's
  *sonuç raporu* (final report) compliance statement (İlke 9).
- If anything is restricted, ensure the İlke-6 justification is on file and referenced from the
  VYP.

## Not Aperta's job (route elsewhere)

- International deposit (Zenodo/Dryad/Figshare/OSF), open-access routes, or preprint posting to
  arXiv/bioRxiv/SSRN → `alterlab-open-science`.
- The KVKK lawful-basis/anonymisation determination → `alterlab-kvkk-dmp`.
