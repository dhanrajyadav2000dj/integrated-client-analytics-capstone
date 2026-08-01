# Customer Value And Retention Analysis

Four-week periods come from WEEK_NO and are not calendar months. The household-period mart includes inactive periods; retention requires activity in two adjacent periods. The incomplete final period is flagged.

| segment | households | avg_spend | avg_baskets |
| --- | --- | --- | --- |
| high_value | 625 | 7793.0 | 227.99 |
| mid_value | 1211 | 2312.12 | 93.55 |
| at_risk_lapsed | 155 | 754.51 | 29.65 |
| low_value | 509 | 530.28 | 31.64 |

customer_period_summary.csv contains active, new, returning, prior-active, retained counts, and denominators. customer_retention_matrix.csv contains cohort retention. Bootstrap intervals are in the quantitative appendix.
