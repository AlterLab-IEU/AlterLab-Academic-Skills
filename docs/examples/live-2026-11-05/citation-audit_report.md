# Citation-Integrity Report: Weekly Low-Stakes Quizzing and Final-Exam Performance (synthetic manuscript)

Status: COMPLETE

Manuscript: `skills/workflows/alterlab-research-workflows/evals/fixtures/workflows/_shared/synthetic-manuscript.md`
Report date: 2026-11-05

## Coverage

| Stage | Requested | Dispatched | Completed | Failed | Unresolved | Retried |
|---|---|---|---|---|---|---|
| References (existence and metadata) | 3 | 3 | 3 | 0 | 0 | 0 |
| Claims (source support) | 4 | 4 | 4 | 0 | 0 | 0 |
| Re-checks (2 per flag, 4 flags) | 8 | 8 | 8 | 0 | n/a | 0 |

Extraction: 3 references listed (no missing or duplicated reference IDs), 5 citing sentences (claims) in the manuscript, 5 extracted (cap 150, 0 left unextracted), 0 placeholders. Of the 5 claims, 1 was not checkable on its own (it cites reference [3], judged NOT_FOUND), so 4 were sent for checking and all 4 completed. All 4 flags received two completed re-checks; 4 stood, 0 were overturned, and 0 have an incomplete re-check.

## Summary

| Count | Value |
|---|---|
| References listed | 3 |
| References with a verdict | 3 |
| Claims in manuscript | 5 |
| Claims extracted | 5 |
| Claims checkable | 4 |
| Claims checked (received a verdict) | 4 |
| of which uncheckable (no accessible source text) | 0 |
| NOT_FOUND | 1 |
| ID_INVALID | 0 |
| PAC (corrupted metadata) | 1 |
| IH (identifier points elsewhere) | 0 |
| PH (placeholders) | 0 |
| SH (claim not supported by cited source) | 2 |
| UNVERIFIED (lookup failed) | 0 |
| Retracted | 0 |
| Retraction status unknown (found works) | 0 |
| Flags overturned on re-check | 0 |
| Flags with re-check incomplete | 0 |

Reference [1] (Roediger & Karpicke, 2006) received a verdict and was not flagged; its DOI and metadata matched Crossref and Europe PMC. Two of the four checked claims received a verdict without a flag.

## NOT_FOUND

Both re-checks completed and neither found the work in any source that answered. Absence from these indexes is not proof that the work was fabricated: it may be unindexed, in press, cited under a different title, or in a venue these sources do not cover. The author must supply the source (DOI, URL, or a copy) or locate the correct reference.

| Ref | Cited as | Evidence | Fix |
|---|---|---|---|
| [3] | Marchetti-Oyelaran, T., & Lindqvist, H. (2021). Spaced retrieval lattices and examination performance in introductory courses: A fourteen-university replication. *Journal of Applied Retrieval Science, 9*(2), 113–131. | No match in Crossref, Europe PMC, arXiv or Open Library (closest Crossref title match scored 0.36 and was an unrelated work, 10.1016/j.compedu.2020.104084). Crossref and Europe PMC author searches for "Marchetti-Oyelaran" returned no works by this author; ORCID family-name search returned 0 profiles; Semantic Scholar author search returned 0. No journal named "Journal of Applied Retrieval Science" was found in Crossref, DOAJ, the ISSN portal or by web search, so no 2021 vol. 9(2) table of contents could be checked. The reference cites no DOI. Not reachable during checks: Semantic Scholar paper search (HTTP 429), OpenAlex (HTTP 429 / daily budget exhausted), and some Crossref works searches in the second re-check (HTTP 429). | Supply a DOI, URL or copy of the paper, or replace it with a locatable source. Until then, the claim it supports (claim C3: "spaced retrieval schedules raised introductory-course exam scores by 12 points across 14 universities") has no verifiable support and should be removed or re-sourced. |

## ID_INVALID

None.

## PAC (corrupted metadata)

| Ref | Cited as | Evidence | Corrected reference |
|---|---|---|---|
| [2] | Cohen, J. (1994). A power primer. *Psychological Bulletin, 112*(1), 155–159. https://doi.org/10.1037/0033-2909.112.1.155 | The DOI resolves to the cited work in Crossref (issued 1992, Psychological Bulletin vol. 112, issue 1, pp. 155–159); Europe PMC PMID 19565683 gives 1992. A Crossref query for Jacob Cohen in Psychological Bulletin (ISSN 0033-2909) during 1994 returned no items; volume 112 is the 1992 volume. Only the year is wrong. | Cohen, J. (1992). A power primer. *Psychological Bulletin, 112*(1), 155–159. https://doi.org/10.1037/0033-2909.112.1.155 |

Also update the in-text year if the manuscript cites Cohen by year anywhere.

## IH (identifier points elsewhere)

None.

## PH (placeholders)

None.

## SH (claim not supported by the cited source)

| Claim | Manuscript text | Cited source | Verbatim evidence | Calibrated rewrite |
|---|---|---|---|---|
| C1 (Introduction) | "Roediger and Karpicke (2006) showed that retrieval practice doubled final-exam grades in university statistics courses [1]." | [1] Roediger & Karpicke (2006), *Psychological Science* (PMID 16507066). Full text closed; judged on the abstract. | "In two experiments, students studied prose passages and took one or three immediate free-recall tests, without feedback, or restudied the material the same number of times as the students who received tests. Students then took a final retention test 5 min, 2 days, or 1 week later. When the final test was given after 5 min, repeated studying improved recall relative to repeated testing. However, on the delayed tests, prior testing produced substantially greater retention than studying" (Europe PMC abstract, retrieved 2026-11-05). The source reports laboratory experiments with prose passages and free recall; it does not mention statistics courses, final-exam grades, or a doubling. | "Roediger and Karpicke (2006) showed in two laboratory experiments that students who took free-recall tests on prose passages retained substantially more after 2 days and 1 week than students who restudied the passages, although restudying was better on a test given after 5 minutes [1]." |
| C4 (Discussion) | "Weekly quizzing caused the higher exam scores: the quiz section outperformed the re-read section by almost eight points, a medium effect by conventional benchmarks [2]." | [2] Cohen (1992), "A power primer" (PMID 19565683). | "A convenient, although not comprehensive, presentation of required sample sizes is provided here. Effect-size indexes and conventional values for these are given for operationally defined small, medium, and large effects." (Europe PMC abstract). Cohen can support only the meaning of the small/medium/large benchmarks. It cannot support the causal claim that quizzing caused the difference, nor the manuscript's own result; and a raw gap of "almost eight points" is not a standardized effect size, so it cannot be labelled "medium" on its own. | "The quiz section scored almost eight points higher than the re-read section on the exam (d = [computed value], which is [small/medium/large] by Cohen's [2] conventional benchmarks). Because sections were not randomly assigned, this difference cannot be attributed to quizzing alone." Note for the author: the Results section reports d = 0.45 (95% CI 0.09 to 0.81); 0.45 is below Cohen's 0.5 "medium" benchmark, and the interval spans small to large, so describe the label accordingly. |

## UNVERIFIED (lookup failed)

None. All reference and claim lookups completed.

## Retractions

No retractions were flagged by the verification stage. Reference [2] was not flagged as retracted in the sources checked. Reference [3] was not identified, so no retraction check applies to it. Found works with an unknown retraction status (retraction_unknown): 0. Note that "not flagged in the checked sources" is a statement about those sources, not a guarantee.

## Provisional flags — re-check incomplete

None. All 4 flags received two completed re-checks.

## Not checked

- References without a verdict: none.
- Claims without a verdict: none.
- Claims that could not be checked: 1.
  - C3: cites reference [3], which was judged NOT_FOUND, so there was no source text to check the claim against. It is reported with that reference above.
- Citing sentences never extracted because of the 150-claim cap: 0.

## Overturned on re-check

None. No flag was cleared on re-check.

## Method

- Extraction: reference list and citing sentences parsed from the manuscript (3 references, 5 claims, cap 150).
- Reference verification: `verify_citations.py` against Crossref, Europe PMC, arXiv and Open Library (all answered); Semantic Scholar returned HTTP 429 and was not checked in the first pass.
- Claim verification: cited sources retrieved through Europe PMC (abstracts) and Unpaywall/OpenAlex (open-access status; both checked sources were closed access, so claim judgments rest on abstracts).
- Re-checks: two separate passes per flag using Crossref (DOI lookup, bibliographic, author, journal and container-title searches), Europe PMC, Open Library, ORCID, Semantic Scholar author search, DOAJ, the ISSN portal and web search. OpenAlex and parts of Semantic Scholar and Crossref were rate-limited (HTTP 429) during re-checks; those sources are listed as not checked, not as "not found".
- Date of searches and of this report: 2026-11-05.

The re-checks were separate passes by agents running the same model. Their agreement is not independent verification, and a human should confirm each finding against the sources before acting on it. These are findings to check, not judgments about the authors' intent.

## AI-assistance disclosure

This report was generated by an AI-assisted citation-audit workflow (Claude, Anthropic) using public bibliographic APIs. The extraction, lookups, verdicts, re-checks and suggested rewrites were produced by AI agents and have not been reviewed by a human. Suggested rewrites are drafts; the author is responsible for the final wording and for confirming every finding.
