# Claim Stress-Test Report

Status: COMPLETE

## Coverage

| Unit | Requested | Dispatched | Completed | Failed | Unresolved | Retried |
|------|-----------|------------|-----------|--------|------------|---------|
| Claims | 1 (found 1, cap 8) | 1 | 1 rated | 0 | 0 unrated | 0 |
| Lens attacks | 3 | 3 | 3 | 0 | 0 | 0 |

Claims not tested: 0. Status reasons: none.

The three lenses all completed for C1: counter-evidence, citation-support and inference. No lens failed or went unreported. The rating below rests on all three.

## Summary of ratings

| Claim | Rating | Lenses completed (of 3) | Decisive argument | Calibrated rewrite |
|-------|--------|-------------------------|-------------------|--------------------|
| C1: Retrieval practice (taking practice tests) improves long-term retention more than restudying the same material, as shown by Roediger & Karpicke (2006), *Psychological Science* 17(3), 249-255, doi:10.1111/j.1467-9280.2006.01693.x. | **survives** | 3 | The citation matches Crossref in every field. The randomized design supports causal wording. On the delayed tests (2 days and 1 week) testing beat restudying with large effects (d = 0.83 to 1.26). The word "long-term" excludes the 5-minute reversal. Four meta-analyses agree on direction. | Kept as written (survives). |

Ratings tally: survives 1, contested 0, weakened 0, refuted 0, unrated 0.

Input note: the claim came with no supporting evidence from the manuscript (evidence field: "not supplied"). The lenses relied only on sources they retrieved themselves.

## C1: Retrieval practice vs restudying (Roediger & Karpicke, 2006)

**Claim:** Retrieval practice (taking practice tests) improves long-term retention more than restudying the same material, as shown by Roediger & Karpicke (2006), *Psychological Science* 17(3), 249-255, doi:10.1111/j.1467-9280.2006.01693.x.

**Rating:** survives. All 3 lenses completed, and none found a fatal objection (severity "none" from each). Lenses that did not report: none.

### Lens 1: Counter-evidence (completed; refuted: no; severity: none)

**Argument.** The citation is correct, and the abstract matches the claim: on tests given 2 days or 1 week later, students who had taken practice tests retained substantially more than students who restudied. Restudying beat testing at 5 minutes. Because the claim says "long-term", it already excludes that condition and does not overstate the finding. Four meta-analyses agree on direction. The counter-evidence the lens found sets limits on the effect but does not refute it:

1. Gereau & Mulligan (2026) report that 66% of free-recall testing effects come from designs that mix direct and forward testing effects, and that those designs give larger effects. Typical effect sizes may therefore overstate the direct benefit, though the direction still holds.
2. Van Gog & Sweller (2015) propose that the effect shrinks or disappears as material gets more complex. Karpicke & Aue (2015) dispute this, so the question is unresolved. The lens had metadata only for both papers.
3. Sigayret et al. (2026) found no testing effect in two small preliminary experiments run on Prolific. The authors attribute this to how engaged online participants were.
4. Mayrhofer et al. (2023) found that retrieval practice lost its advantage over concept mapping once study time was equated. That is a different comparison condition from restudying.

Weighed by the evidence hierarchy, the converging meta-analyses outweigh these boundary and null studies. The effect is moderate (about d or g = 0.5) and depends on test format, feedback and how complex the material is. The claim needs no rewording to be accurate.

Source access: the PubMed MCP returned an API error, so the lens used Europe PMC and Crossref.

**Retrieved evidence**

| Source | Finding |
|--------|---------|
| [doi:10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | Crossref confirms *Psychological Science* 17(3), 2006. Abstract: restudy beat testing at 5 min; "on the delayed tests, prior testing produced substantially greater retention than studying." |
| [doi:10.1037/a0037559](https://doi.org/10.1037/a0037559) | Rowland (2014), *Psychological Bulletin*, meta-analysis: recall tests give larger testing benefits than recognition tests. (The inference lens later found no abstract on this Crossref record, so the source of this quote is unclear. See Lens 3.) |
| [doi:10.3102/0034654316689306](https://doi.org/10.3102/0034654316689306) | Adesope et al. (2017) meta-analysis: practice tests beat restudying and all other comparison conditions. Effects vary with test features and study characteristics. |
| [doi:10.1037/bul0000309](https://doi.org/10.1037/bul0000309) | Yang et al. (2021): 222 studies, 48,478 students, g = 0.499. Boundary conditions include feedback, consistency of test format and the control strategy. |
| [doi:10.1177/1475725717695149](https://doi.org/10.1177/1475725717695149) | Schwieren et al. (2017): psychology classrooms, 72 effect sizes, d = 0.56. |
| [doi:10.1037/xlm0001634](https://doi.org/10.1037/xlm0001634) | Gereau & Mulligan (2026): 66% of testing effects come from mixed direct/forward designs, which give larger effects. The direction (testing beats restudy) still holds. |
| [doi:10.1007/s10648-015-9310-x](https://doi.org/10.1007/s10648-015-9310-x) | Van Gog & Sweller (2015), metadata only: proposes that the effect weakens with complex material. |
| [doi:10.1007/s10648-015-9308-4](https://doi.org/10.1007/s10648-015-9308-4) | Karpicke & Aue (2015), metadata only: "Still a Winner", a rebuttal disputing that complexity limits the effect. |
| [doi:10.3389/fpsyg.2026.1727423](https://doi.org/10.3389/fpsyg.2026.1727423) | Sigayret et al. (2026): no delayed-test difference in two preliminary Prolific experiments. The authors attribute this to online-sample engagement. |
| [doi:10.3389/fpsyg.2023.1258359](https://doi.org/10.3389/fpsyg.2023.1258359) | Mayrhofer et al. (2023), preregistered: the advantage over concept mapping vanished once study time was equated. This compares against concept mapping, not restudying. |

### Lens 2: Citation support (completed; refuted: no; severity: none)

**Argument.** The DOI resolves through the Crossref MCP tool and the public REST API to Roediger & Karpicke (2006), "Test-Enhanced Learning", *Psychological Science* 17(3), 249-255. Authors, year, journal, volume, issue and pages all match. A PubMed citation lookup found no match, which is expected for a psychology journal outside the biomedical literature. The abstract supports the claim on direction, outcome measure and population:

- **Design:** prose passages; one or three immediate free-recall tests without feedback, compared with restudying the same number of times.
- **Final test:** 5 minutes, 2 days or 1 week later.
- **Result:** on the delayed tests, testing produced substantially greater retention than restudying.

The claim gives no effect size, so it cannot overstate one. None of the following weakens the claim as worded, but each is worth stating: (1) restudying won at 5 minutes; (2) the evidence covers prose passages and free recall without feedback only; (3) students who restudied felt more confident even though they retained less.

**Retrieved evidence**

| Source | Finding |
|--------|---------|
| [doi:10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | Crossref metadata matches every element of the citation (Roediger & Karpicke, *Psychological Science*, 17(3), 2006-03, 249-255). |
| [doi:10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | Abstract (design): prose passages; one or three immediate free-recall tests without feedback, or restudying; final test at 5 min, 2 days or 1 week. |
| [doi:10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | Abstract (result): restudy better at 5 min; testing "substantially greater" on delayed tests; restudying raised confidence. |
| [api.crossref.org/works/10.1111/j.1467-9280.2006.01693.x](https://api.crossref.org/works/10.1111/j.1467-9280.2006.01693.x) | REST API: pages 249-255, volume 17, issue 3, cited by 2,334 works. |

### Lens 3: Inference (completed; refuted: no; severity: none)

**Argument.** The causal wording is justified because the learning condition was manipulated experimentally. Experiment 1 was a 2x3 mixed design (N = 120): restudy versus test within subjects and counterbalanced, delay between subjects. Experiment 2 was a 3x2 between-subjects design (N = 180, 30 per cell). The paper reports effect sizes as well as significance tests, and the effects are large:

- **Experiment 1:** the condition x interval interaction was F(2,117) = 32.10, partial eta squared = .35. Testing beat restudy at 2 days (68% vs 54%, d = 0.95) and at 1 week (56% vs 42%, d = 0.83).
- **Experiment 2:** at 1 week, STTT beat SSSS (61% vs 40%, d = 1.26).

The word "long-term" is essential. At 5 minutes the result reverses (Experiment 1, d = 0.52; Experiment 2, d = 1.22). Without that word the claim would be false.

- **Multiplicity:** the post hoc t-tests were run without a stated correction. This does not threaten the main contrasts (t = 6.4 to 7.0). Repeated versus single testing at 1 week was only marginal (d = 0.31), but the claim does not assert anything about that comparison.
- **Uncertainty:** no confidence intervals are reported. This is a reporting gap, not a reason to reject the result. The lens found no sign of optional stopping, since cell sizes were fixed.
- **Sample frame:** undergraduates aged 18-24 at one university; two TOEFL prose passages of 256 and 275 words; free-recall tests without feedback; longest delay 1 week.

Claims about classrooms, other test formats, feedback, other populations or delays of months need the broader literature. The lens confirmed only that Rowland (2014) exists; its Crossref record has no abstract, so the lens did not check its findings.

**Retrieved evidence**

| Source | Finding |
|--------|---------|
| [doi:10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x) | Crossref confirms title, authors, volume, issue and date. Abstract: restudy better at 5 min; testing better on the delayed tests. |
| [Roediger-Karpicke-2006.pdf (psychology.ecu.edu)](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf) | Experiment 1: N = 120 Washington University undergraduates aged 18-24; 2x3 mixed design; F(2,117) = 32.10, partial eta squared = .35; 5 min 81% vs 75% (d = 0.52, favouring restudy); 2 days 68% vs 54% (d = 0.95); 1 week 56% vs 42% (d = 0.83); no feedback; TOEFL passages of 256 and 275 words. |
| [Roediger-Karpicke-2006.pdf (psychology.ecu.edu)](https://psychology.ecu.edu/wp-content/pv-uploads/sites/216/2019/03/Roediger-Karpicke-2006.pdf) | Experiment 2: N = 180, 3x2 between subjects, 30 per cell; F(2,174) = 18.48, partial eta squared = .18; at 5 min SSSS > STTT (d = 1.22); at 1 week STTT > SSSS (d = 1.26; 61% vs 40%); STTT vs SSST marginal (d = 0.31); SSSS students more confident, F(2,177) = 6.09. |
| [doi:10.1037/a0037559](https://doi.org/10.1037/a0037559) | Rowland (2014), *Psychological Bulletin* 140(6): existence confirmed only (no abstract in Crossref). Cited as a pointer to the evidence a broader generalization would need. |

## Three changes that would most strengthen the paper

1. **State the scope of the 2006 result next to the citation.** Write "on delayed tests (2 days to 1 week), with prose passages and free-recall practice tests without feedback", and mention that restudying won at a 5-minute delay. The claim already survives as written. This wording stops readers from extending it to formats, delays or populations the study did not test (inference and citation-support lenses).
2. **Cite meta-analytic evidence for any broader generalization.** If the paper uses this finding for classrooms, other test formats, longer delays or other learners, cite Adesope et al. (2017), Yang et al. (2021; g = 0.499 across 222 classroom studies) and Rowland (2014) alongside the single 2006 study. Verify Rowland's findings from the full text first; this run confirmed only that the paper exists, not what it reports.
3. **Report the expected effect size and its known moderators.** Give a moderate pooled effect (about g or d = 0.5, smaller than the single-study d of 0.83 to 1.26) and note the moderators: test format, feedback, the disputed role of material complexity (Van Gog & Sweller vs Karpicke & Aue, 2015), and the possible overestimate from designs that mix direct and forward testing effects (Gereau & Mulligan, 2026).

## Note on independence

The three skeptics (counter-evidence, citation-support, inference) are separate agents running the same underlying model. Their agreement that C1 survives is not independent verification. They share the same training data, the same blind spots and largely the same retrieval routes (Crossref, Europe PMC). Two items were retrieved as metadata only (Van Gog & Sweller; Karpicke & Aue). The Rowland (2014) quotation in Lens 1 could not be matched to an abstract by Lens 3. Before publication, a human should check these against the full texts.

## AI-assistance disclosure

An AI model (Claude, Anthropic) produced this report through an automated multi-agent claim stress-test workflow. Three agent instances attacked the claim through separate lenses, retrieved sources from public scholarly APIs (Crossref, Europe PMC; the PubMed MCP returned an error), and a further step compiled their outputs. Quotations and statistics are reproduced as the agents reported them. The AI may have mis-transcribed or misread sources, so a human author should verify every source before relying on this assessment. Responsibility for the claim and its citation stays with the authors.
