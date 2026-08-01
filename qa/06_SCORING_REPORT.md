# Assignment Scoring Report

| Scoring Area | Maximum | Awarded | Evidence | Deductions |
| --- | --- | --- | --- | --- |
| Repository organization and reproducibility | 5 | 5 | README; pinned requirements; docs; clean workflow | None |
| Raw source inspection and grain documentation | 8 | 8 | Full source inventory and relationship map | None |
| SQL staging and analytics layer | 10 | 10 | Five modular executable SQL files | None |
| Join controls and data validation | 10 | 10 | Basket/product/promotion reconciliation | None |
| KPI definitions and financial consistency | 8 | 8 | KPI contracts and corrected gross/discount formula | None |
| Basket and household marts | 8 | 8 | Unique basket and complete period spine | None |
| Product and category analysis | 6 | 5 | Diagnostics and thresholds | Unequal year-like windows |
| Customer value and retention analysis | 7 | 6 | Cohorts, segments, adjacent retention, bootstrap | Limited subgroup uncertainty |
| Campaign, coupon, and promotion analysis | 8 | 6 | Funnel, strata, segments, exact promotion grain | Observational evidence |
| Quantitative and statistical evidence | 10 | 8.5 | CIs, tests, effects, correlation, model, MDE | Simple baseline and assumptions |
| Feature-ready dataset and leakage controls | 7 | 6 | Temporal labels and train-only preprocessing | No serialized production transformer |
| Similarity, matrix, and dimensionality reasoning | 3 | 2 | Dimensions, sparsity, cosine, PCA | Illustrative neighbor/PCA depth |
| Visual evidence | 5 | 4.5 | 12 generated visuals plus interpretations | No dedicated promotion chart |
| Experiment recommendation | 4 | 3 | Hypothesis, metrics, guardrails, MDE, rule | Normal approximation and missing margin |
| Performance and scalability | 3 | 3 | 36.8M-row strategy and production plan | None |
| Final memo and documentation | 6 | 6 | Reconciled memo and mandatory documents | None |

- Listed rubric maximum: 108 (the supplied line items total 108 although the brief says 100)
- Raw awarded points: 99.0
- Normalization: 100 x 99.0 / 108
- Raw normalized score: 91.67
- Severity cap: none; no open CRITICAL or HIGH issue
- Final score: 92/100
- Grade: Excellent - submission ready

Every deduction is shown in the table. The score is normalized to the stated 100-point total rather than silently treating 108 as 100.
