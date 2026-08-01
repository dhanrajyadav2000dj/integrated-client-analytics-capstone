# Final Recommendation Memo

## Executive Summary

Prioritize a retention test for high-value declining households, manage categories using scale plus stability, and treat marketing results as hypotheses. The corrected layer contains 2500 active households, 276484 baskets, net spend 8057463.08, and average basket value 29.14.

## Customer Finding

| segment | households | avg_spend | avg_baskets |
| --- | --- | --- | --- |
| high_value | 625 | 7793.0 | 227.99 |
| mid_value | 1211 | 2312.12 | 93.55 |
| at_risk_lapsed | 155 | 754.51 | 29.65 |
| low_value | 509 | 530.28 | 31.64 |

The complete period spine measures adjacent retention and flags the incomplete final period. Operate a watchlist from recency, frequency, value, trend, discount sensitivity, and affinity.

## Category Finding

Use mart_category_diagnostics.csv to require adequate counts, penetration, direction, and stability. High sales alone is insufficient. The second comparison window is shorter, so investigate availability, mix, and promotions before acting.

## Marketing Finding

| campaign | campaign_type | exposed_households | redeeming_households | redemption_count | household_redemption_rate |
| --- | --- | --- | --- | --- | --- |
| 18 | TypeA | 1133 | 214 | 653 | 0.1889 |
| 13 | TypeA | 1077 | 196 | 629 | 0.182 |
| 8 | TypeA | 1076 | 158 | 372 | 0.1468 |
| 30 | TypeA | 361 | 36 | 64 | 0.0997 |
| 26 | TypeA | 332 | 31 | 73 | 0.0934 |
| 22 | TypeB | 276 | 17 | 47 | 0.0616 |
| 20 | TypeC | 244 | 20 | 33 | 0.082 |
| 14 | TypeC | 224 | 18 | 34 | 0.0804 |
| 11 | TypeB | 214 | 6 | 8 | 0.028 |
| 17 | TypeB | 202 | 18 | 45 | 0.0891 |

Campaign windows are equal length and stratified by prior value. Promotion joins use exact product-store-week keys and reconcile totals. Selection and product/store mix prevent causal claims.

## Recommended Experiment

Hypothesis: affinity offers increase next four-week spend among eligible high-value declining households after discount cost. Randomize households to offer or business-as-usual. Primary metric is spend per eligible household. Secondary metrics are baskets, units, penetration, and redemption. Guardrails are discount cost, margin proxy, cannibalization, complaints, opt-outs, sample-ratio mismatch, missing outcomes, and contamination.

Use alpha 0.05, power 0.80, and experiment_mde.csv for sizing. Require 30 households in reported segments. Success requires statistical reliability and a pre-registered net-value threshold.

## Do Not Conclude And Next Data

Do not infer calendar seasonality, equate lines with baskets, report rates without denominators, or claim campaign causality. Collect delivery/open data, eligibility, cost and margin, inventory, geography, dates, opt-outs, and randomized assignment.
