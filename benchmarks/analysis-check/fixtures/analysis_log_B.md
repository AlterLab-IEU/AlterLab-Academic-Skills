SYNTHETIC FIXTURE — created for benchmarking; not real analyses, data, or persons.
L2: Analysis log B - faculty-development and research-office projects
L3: Prepared by a colleague. Each analysis names its data file (in this folder) or gives the summary
L4: statistics used. Alpha = .05, two-sided, throughout.
L5:
L6: Analysis B1 - Mentoring scheme and grant submission
L7: Data: B1_mentoring_grant_submission.csv (counts). Fifty early-career faculty members, 20 in the
L8: mentoring scheme and 30 not in it; outcome = submitted at least one external grant proposal within
L9: 12 months (yes/no). Each faculty member is counted once.
L10: Analysis run: Pearson chi-square test of independence on the 2 x 2 table (no continuity correction).
L11: Result: chi-square(1, N = 50) = 6.38, p = .012; 85% of mentored vs 50% of non-mentored faculty submitted.
L12: Conclusion drawn: submission rates were higher among mentored faculty.
L13:
L14: Analysis B2 - Revision-app use and exam score
L15: Data: B2_app_use_exam.csv. Thirteen students; self-reported hours per week using a revision app, and
L16: final-exam score.
L17: Analysis run: Pearson correlation across all 13 students.
L18: Result: r = .86, p < .001.
L19: Conclusion drawn: there is a strong positive linear relationship - more app use goes with higher scores.
L20:
L21: Analysis B3 - Ethics-review time by submission route
L22: Data: B3_ethics_review_days.csv. Twenty applications (10 paper, 10 online); outcome = working days from
L23: submission to approval.
L24: Pre-specified plan (department analysis plan): Welch's t-test; if Shapiro-Wilk p < .05 in either group -
L25: checked before any between-group comparison is run - use the Mann-Whitney U test instead.
L26: Assumption check (run first): Shapiro-Wilk p < .001 (paper) and p = .006 (online); both distributions
L27: are strongly right-skewed (medians 4.5 and 8 days; maxima 31 and 45 days).
L28: Analysis run: Mann-Whitney U test, as pre-specified.
L29: Result: U = 31, p = .16.
L30: Conclusion drawn: no evidence of a difference in review time between the two routes.
L31:
L32: Analysis B4 - Mentoring and postdoctoral wellbeing (summary statistics only)
L33: Two independent groups of postdoctoral researchers: with a mentoring scheme (n = 18) and without (n = 21);
L34: outcome = Warwick-Edinburgh Mental Wellbeing Scale score. Pre-registered test: independent-samples t-test.
L35: Result of the pre-registered test: t(37) = 1.80, p = .08. Because this was close to significance, we
L36: also ran a Mann-Whitney U test (U = 112, p = .03) and report the Mann-Whitney result as the main finding.
L37: Conclusion drawn: mentored postdocs report higher wellbeing.
L38:
L39: Analysis B5 - Course evaluations, online vs face-to-face (summary statistics only)
L40: Two independent sets of courses: online (n = 14) and face-to-face (n = 22); outcome = mean
L41: course-evaluation score (0-40), one score per course.
L42: Pre-specified plan: Welch's t-test for every two-group comparison, regardless of the result of any
L43: variance test.
L44: Checks reported: Shapiro-Wilk p = .48 (online) and .62 (face-to-face); Levene's test p = .41.
L45: Analysis run: Welch's t-test. Online M = 31.4, SD = 5.1; face-to-face M = 27.6, SD = 4.6;
L46: t(25.7) = 2.26, p = .032.
L47: Conclusion drawn: online courses received higher evaluation scores than face-to-face courses.
