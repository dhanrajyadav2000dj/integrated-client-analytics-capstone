# QA Test Report

Generated at: 2026-08-02 00:07:59 +05:30

## Environment

- OS shell: PowerShell on Windows
- Python command: python
- SQL engine: DuckDB
- Dataset location: data/raw/
- Canonical pipeline: python src/run_pipeline.py

## Commands Executed

| Command | Exit code | Runtime | Result | Notes |
| --- | ---: | ---: | --- | --- |
| python -m py_compile src/enrich_outputs.py | 0 | <1s | PASS | Enrichment module syntax validated |
| python -m py_compile src/run_pipeline.py | 0 | <1s | PASS | Pipeline syntax validated |
| python src/run_pipeline.py | 0 | 64.3s | PASS | SQL, marts, charts, reports, enriched docs regenerated |
| python -m pytest -q | 0 | 22.40s | PASS | Final automated test suite passed |
| python qa/generate_qa_reports.py | 0 | 10.7s | PASS | Final QA reports regenerated |

## Test Totals

- Passed: 9
- Failed: 0
- Blocked: 0
- Warnings: 1 open low-severity warning
- Total: 9

## Automated Test Coverage

- Required source files present and nonempty
- Required output tables and charts present, including 12 visuals
- Basket mart grain and source sales/unit reconciliation
- Required basket/campaign columns and rate ranges
- Core validation checks pass
- Coupon bridge and causal-data grain guardrails
- Feature table temporal label/leakage column checks
- Secret-pattern scan over project files
- Enriched campaign/visual interpretation documents exist

## Generated Outputs Verified

- Output tables: 10 CSV files in outputs/tables/
- Charts: 12 PNG files in outputs/charts/
- QA reports: required QA files plus repository/source inventory and baseline record

## Evidence

Final pytest result: 9 passed in 22.40s.
