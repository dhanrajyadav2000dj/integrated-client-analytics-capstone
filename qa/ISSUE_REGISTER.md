# Issue Register

Generated at: 2026-08-01 23:51:37 +0530

| Issue ID | Severity | Requirement | File | Line/section | Problem | Evidence | Risk | Required fix | Retest method | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QA-003 | MEDIUM | Campaign causal evidence | final_recommendation_memo.md | campaign section | Campaign analysis is pre/post observational, not matched/DiD randomized evidence | Memo uses association wording and selection-bias caveats | Reviewer may expect deeper quasi-experimental diagnostics | Keep caveat; future work may add matching or regression adjustment | Run pytest and python src/run_pipeline.py; inspect QA reports | OPEN |
| QA-004 | LOW | Notebook execution | notebooks/integrated_client_analytics_capstone.ipynb | notebook | Notebook is a wrapper around script rather than fully narrated analysis notebook | Notebook delegates reproducible work to src/run_pipeline.py | Some reviewers prefer rich notebook prose | README documents script-first reproducibility | Run pytest and python src/run_pipeline.py; inspect QA reports | OPEN |
