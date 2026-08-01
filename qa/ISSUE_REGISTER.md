# Issue Register

Generated at: 2026-08-02 00:07:30 +0530

| Issue ID | Severity | Requirement | File | Line/section | Problem | Evidence | Risk | Required fix | Retest method | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QA-003 | LOW | Campaign causal evidence | campaign_bias_analysis.md | campaign section | Campaign analysis is pre/post observational rather than randomized or matched causal evidence | Dedicated campaign bias file uses association wording and selection-bias caveats | Reviewer may prefer deeper matching/DiD but assignment caution is satisfied | Keep caveat; future work may add matching or regression adjustment | Run pytest and python src/run_pipeline.py; inspect QA reports | OPEN |
