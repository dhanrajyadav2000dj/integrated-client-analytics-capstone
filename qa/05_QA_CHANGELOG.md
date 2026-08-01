# QA Changelog

| Date | Issue ID | File | Original problem | Change made | Reason | Retest | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-02 | QA-001 | sql/05; src/audit_enhancements.py | Non-adjacent retention and in-sample model | Complete period spine and training-only holdout pipeline | Correct KPI and leakage control | pipeline + pytest | PASS |
| 2026-08-02 | QA-004 | sql/05; src/audit_enhancements.py | Discount denominator and demographic flag defects | Corrected gross formula and demographic detection | Financial/feature correctness | reconciliation tests | PASS |
| 2026-08-02 | QA-002 | sql/05; campaign_bias_analysis.md | No actual causal-data analysis and unequal campaign windows | Added exact promotion mart and equal 28-day stratified comparison | Assignment coverage | row/sales/unit checks | PASS with limitation |
| 2026-08-02 | QA-003 | category_analysis.md; mart_category_diagnostics.csv | Weak stability evidence | Added growth rate, engagement change, CV, and decision flags | Category depth | pipeline + tests | PASS with caveat |
| 2026-08-02 | QA-005 | tests; qa; docs; README | Strict QA artifacts and coverage incomplete | Expanded tests, numbered reports, relationship map, mart catalog, and commands | Submission readiness | pytest + manual audit | PASS |
