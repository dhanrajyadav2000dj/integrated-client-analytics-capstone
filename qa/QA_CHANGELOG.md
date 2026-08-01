# QA Changelog

Generated at: 2026-08-01 23:48:18 +05:30

| Date | File | Original issue | Exact change | Reason | Validation result |
| --- | --- | --- | --- | --- | --- |
| 2026-08-01 23:48:18 +05:30 | qa/QA_BASELINE_STATE.md | Required original-state preservation before repairs | Recorded Git HEAD and initial status | Satisfy QA audit rule 14 | File created successfully |
| 2026-08-01 23:48:18 +05:30 | qa/generate_qa_reports.py | Required QA output files missing | Added evidence-based QA report generator | Produce traceability, inventory, issue register, checklist, readiness report | Script compiles and runs |
| 2026-08-01 23:48:18 +05:30 | 	ests/test_capstone_outputs.py | No automated tests existed | Added pytest coverage for source files, outputs, mart grain, reconciliation, rates, validation checks, feature leakage, and secret scan | Satisfy assignment QA/test controls | Final pytest: 8 passed |
| 2026-08-01 23:48:18 +05:30 | 	ests/test_capstone_outputs.py | Coupon bridge test assumed raw bridge uniqueness | Changed test to verify distinct bridge count is detected and reported | Raw coupon mapping may contain repeated rows; assignment requires detection/control, not blind uniqueness assumption | Final pytest: 8 passed |
| 2026-08-01 23:48:18 +05:30 | 	ests/test_capstone_outputs.py | Secret scan matched its own literal pattern | Split marker string while preserving scan behavior | Avoid false positive in the test source | Final pytest: 8 passed |
| 2026-08-01 23:48:18 +05:30 | equirements.txt | Test runner dependency missing | Added pytest>=8.0 | Make automated QA tests reproducible | Pytest executed successfully in current environment |
| 2026-08-01 23:51:42 +05:30 | `src/run_pipeline.py` | Feature table lacked explicit campaign engagement and trend/change features | Added observation-window campaign exposure count, first/second-half spend, spend trend change, and top department share | Satisfy feature-ready dataset requirements without future leakage | Pipeline rerun passed; pytest: 8 passed |
| 2026-08-01 23:51:42 +05:30 | `README.md` | README needed stronger raw-data instructions and alternate filename mapping | Added alternate file names, raw data instructions, pytest run command, QA/tests deliverable notes | Improve clean-machine reproducibility | Manual inspection and pytest passed |
| 2026-08-01 23:51:42 +05:30 | `feature_dictionary.md` | Feature groups were not explicit enough after QA repair | Documented target labels, observation/future windows, campaign engagement, trend/change, affinity, and preprocessing contract | Improve reviewer traceability and leakage review | Manual inspection and pytest passed |
