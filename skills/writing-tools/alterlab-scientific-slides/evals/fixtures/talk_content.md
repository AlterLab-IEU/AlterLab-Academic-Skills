# Talk material — "Predicting Student Dropout with Gradient Boosting"

Venue: EDM 2027 (Educational Data Mining), 15-minute slot incl. 3 min Q&A. Speaker: A. Researcher (fictional).

**Question.** Can first-semester LMS and grade data flag students at risk of dropping out early enough
to intervene, and is the model fair across groups?

**Data.** 48,312 students, 2015–2024, one public university; 112 features (attendance, grades, LMS logins,
credits). Dropout rate 8.4%.

**Method.** XGBoost with focal loss; nested 5-fold CV; isotonic calibration on the 2024 cohort; SHAP for
explanations; fairness audit by gender, nationality, first-generation status.

**Key results.**
- AUC 0.87 (logistic regression baseline 0.79); Brier 0.061; ECE 0.012 after calibration.
- At a 20% flag rate the model catches 71% of eventual dropouts by week 6.
- Attendance and first-term GPA carry 55% of total SHAP importance.
- Equal-opportunity gap ≤ 2.1 points across all audited groups; first-generation students were
  under-flagged before reweighting (gap 6.4 → 1.9).
- External validation at a second university: AUC 0.83.

**Take-home.** Early, calibrated, audited risk scores are feasible; the bottleneck is advisor capacity, not
prediction.
