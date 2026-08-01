# Campaign, Coupon, And Promotion Analysis

## Validated Funnel

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

Rates divide distinct redeeming households by distinct exposed households. TypeA is separate because targeting creates stronger selection. TypeB and TypeC remain non-random. Exposure is not proof of viewing, and sparse redemption requires denominators.

## Bias-Aware Comparison

campaign_bias_comparison.csv uses equal 28-day pre and post windows and stratifies by campaign type, prior-spend quartile, and redemption status. campaign_segment_analysis.csv reports redemption by customer segment. These controls do not remove self-selection, regression to the mean, unobserved eligibility, inventory, or concurrent activity. Results are associations, not causal lift.

## Promotion Evidence

| promotion_status | product_store_weeks | transaction_lines | sales | units | basket_occurrences | avg_sales_per_product_store_week |
| --- | --- | --- | --- | --- | --- | --- |
| not_promoted | 1887464 | 2031958.0 | 6499712.25 | 259891029.0 | 2031958.0 | 3.4436 |
| promoted | 483320 | 563774.0 | 1557750.83 | 794593.0 | 563774.0 | 3.223 |

Causal data is deduplicated to product-store-week before joining transactions aggregated at exactly that grain. Product, store, timing, and merchandising selection confound the promoted comparison. Row, sales, and unit reconciliation is recorded in validation_checks.csv.
