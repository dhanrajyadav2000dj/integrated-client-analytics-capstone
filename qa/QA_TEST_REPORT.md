# Test Execution Report

Execution date: 2026-08-02 01:21:58 +0530

## Environment

- OS: Windows-11-10.0.26200-SP0
- Python: 3.12.6
- SQL engine: DuckDB 1.1.3
- Dataset: eight local CSV files under data/raw
- Raw files preserved: YES
- Canonical pipeline: python src/run_pipeline.py

## Commands Executed

| Command | Exit code | Runtime | Result | Notes |
| --- | --- | --- | --- | --- |
| python -m py_compile src/run_pipeline.py src/audit_enhancements.py | 0 | <1s | PASS | Syntax |
| python src/run_pipeline.py (schema-discovery run 1) | 1 | 25.3s | FAIL/FIXED | Optional product columns absent |
| python src/run_pipeline.py (schema-discovery run 2) | 1 | 24.6s | FAIL/FIXED | Replacement corrected after exact inspection |
| python src/run_pipeline.py | 0 | 65.5s | PASS | SQL, marts, charts, model, reports |
| python -m venv .venv | 0 | 22.8s | PASS | Fresh isolated environment |
| .venv python -m pip install -r requirements.txt | 124 | controller timeout | COMPLETE/VERIFIED | Install completed; pip check and imports passed |
| .venv python -m pip check | 0 | 1.4s | PASS | No broken requirements |
| .venv python -m pytest -q | 0 | 14.96s | PASS | 20 deterministic tests |
| python src/execute_notebook.py | 0 | 79.9s | PASS | Notebook code cells top to bottom |
| python qa/strict_audit.py | 0 | current run | PASS | Numbered reports |

## Results

- Automated tests passed: 20
- Automated tests failed: 0
- Audit cases passed: 367
- Audit cases partial: 16
- Audit cases blocked: 0
- Tables generated: 18
- Charts generated: 12
- Warnings: observational marketing evidence; unequal 52/50-week growth windows; no production model deployment artifact.

The two failed discovery runs are retained because strict QA records errors. Both were corrected and the full pipeline subsequently exited 0.
