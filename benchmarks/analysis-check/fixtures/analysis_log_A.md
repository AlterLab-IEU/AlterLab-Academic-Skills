SYNTHETIC FIXTURE — created for benchmarking; not real analyses, data, or persons.
L2: Analysis log A - teaching and faculty-development projects
L3: Prepared by a colleague for the department's internal methods review. Each analysis names its data file
L4: (in this folder). Alpha = .05, two-sided, throughout.
L5:
L6: Analysis A1 - Writing-retreat programme and state anxiety
L7: Data: A1_writing_retreat_anxiety.csv. Twelve faculty members took part in a six-week academic-writing
L8: retreat programme. State anxiety (STAI-S, range 20-80) was measured on each participant twice: before
L9: the first session (stai_pre) and after the last session (stai_post). One row per participant.
L10: Analysis run: independent-samples t-test (Student, equal variances assumed) comparing the stai_pre values
L11: with the stai_post values.
L12: Result: t(22) = 1.72, p = .10.
L13: Conclusion drawn: the programme did not significantly change anxiety.
L14:
L15: Analysis A2 - Teaching method and course pass rate
L16: Data: A2_pass_fail_by_method.csv (counts). Twenty-two students in two independent sections, one taught
L17: with a flipped-classroom design (12 students) and one with traditional lectures (10 students); each
L18: student passed or failed the course once.
L19: Analysis run: Pearson chi-square test of independence on the 2 x 2 table (no continuity correction).
L20: Result: chi-square(1, N = 22) = 4.77, p = .029.
L21: Conclusion drawn: pass rates differ by teaching method; the flipped classroom improves pass rates.
L22:
L23: Analysis A3 - Final-exam scores in three course sections
L24: Data: A3_exam_by_section.csv. Three independent sections of the same course (different students in each
L25: section, six per section); outcome = final-exam score (%).
L26: Pre-specified plan (written before the exam): one-way ANOVA, followed by Tukey HSD post-hoc comparisons
L27: if the omnibus test is significant; normality checked per section with Shapiro-Wilk and homogeneity of
L28: variance with Levene's test before the ANOVA is interpreted.
L29: Assumption checks: Shapiro-Wilk p = .95 (section 1), > .99 (section 2), .96 (section 3); Levene's test
L30: (median-centred) F(2, 15) = 0.10, p = .91. Section SDs 2.58, 2.43, 2.16.
L31: Result: F(2, 15) = 17.79, p < .001, eta-squared = .70.
L32: Tukey HSD: section 2 > section 1 (difference 7.83, p < .001); section 2 > section 3 (difference 6.17,
L33: p = .001); section 1 vs section 3 (difference 1.67, p = .47).
L34: Conclusion drawn: mean exam scores differ across sections; section 2 scored higher than sections 1 and 3.
