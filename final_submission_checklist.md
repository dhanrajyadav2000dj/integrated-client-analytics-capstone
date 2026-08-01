# Final Submission Checklist

- Required source files downloaded and inspected through DuckDB staging.
- Source grains documented in README, SQL, validation report, and assumptions file.
- SQL transformations included in `sql/01_stage_sources.sql` through `sql/04_validation_checks.sql`.
- Mart outputs generated in `outputs/tables/`.
- KPI definitions include denominators and grain notes in `kpi_definitions.md`.
- Basket-level analysis uses distinct `basket_id`, not item transaction rows.
- Fan-out risks are controlled by aggregating before joins and by keeping coupon/product bridge logic separate.
- Discount sign convention is positive reporting amounts from raw signed discount fields.
- Time fields are treated as relative indexes; no real calendar seasonality is inferred.
- Customer, product/category, and campaign/coupon analyses are covered.
- Depth tracks: customer value/retention, category performance, campaign/coupon effectiveness.
- Quantitative appendix includes confidence intervals, hypothesis tests, matrix reasoning, PCA, baseline model, and experiment power framing.
- Feature-ready household dataset uses an observation window and future label window.
- Validation report includes actual numeric checks.
- Charts are generated in `outputs/charts/`.
- Final client recommendation memo is included.
- Assumptions, limitations, performance plan, feature dictionary, and AI declaration are included.

Run verification command:

```powershell
python src/run_pipeline.py
```
