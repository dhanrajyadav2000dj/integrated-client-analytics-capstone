# Final Recommendation Memo

## Executive Summary
The retailer should prioritize high-value customer retention, category actions that combine scale with penetration and stability, and randomized testing for campaign improvements. The evidence is strong for descriptive patterns and weaker for causal campaign claims.

## KPI Snapshot
- Active households: 2500
- Baskets: 276484
- Spend: 8057463.08
- Average basket value: 29.14
- Coupon basket rate: 0.061

## Finding 1: Customer value is concentrated
Use high-value and declining household segments for retention operations instead of broad untargeted offers. Evidence is in the value concentration chart and feature mart.

## Finding 2: Category decisions need denominator checks
| commodity_desc | category_sales | household_penetration | discount_rate | sales_growth |
| --- | --- | --- | --- | --- |
| COUPON/MISC ITEMS | 514685.71999999986 | 0.5436 | 0.03237927017263656 | 86865.69999999972 |
| SOFT DRINKS | 327647.300000015 | 0.962 | 0.2561366728815221 | 16912.900000000373 |
| BEEF | 312103.2200000013 | 0.8952 | 0.1718699681039223 | 25200.29999999993 |
| FLUID MILK PRODUCTS | 205356.0500000006 | 0.9684 | 0.18800441268322907 | 21370.810000001788 |
| CHEESE | 189528.18000000017 | 0.94 | 0.21289499589057853 | 15662.4599999997 |
| FRZN MEAT/MEAT DINNERS | 160517.16999999917 | 0.8276 | 0.23045630491310282 | 18390.030000000115 |
| BAG SNACKS | 148375.1599999964 | 0.9392 | 0.13106244620131022 | 16063.239999999016 |
| BEERS/ALES | 147309.67999999796 | 0.6424 | 0.0007622384998614618 | 9588.79999999996 |
| FROZEN PIZZA | 146037.249999999 | 0.8208 | 0.18339654380335696 | 8784.029999999999 |
| BAKED BREAD/BUNS/ROLLS | 145930.84999999643 | 0.96 | 0.20444206929967382 | 14712.590000001132 |

Prioritize categories with sufficient household penetration and growth; investigate high-sales declining categories before reducing support.

## Finding 3: Campaign results are associations, not proof
| campaign | campaign_type | exposed_households | redeeming_households | household_redemption_rate |
| --- | --- | --- | --- | --- |
| 18 | TypeA | 1133 | 214 | 0.18887908208296558 |
| 13 | TypeA | 1077 | 196 | 0.18198700092850512 |
| 8 | TypeA | 1076 | 158 | 0.14684014869888476 |
| 30 | TypeA | 361 | 36 | 0.0997229916897507 |
| 26 | TypeA | 332 | 31 | 0.09337349397590361 |
| 22 | TypeB | 276 | 17 | 0.06159420289855073 |
| 20 | TypeC | 244 | 20 | 0.08196721311475409 |
| 14 | TypeC | 224 | 18 | 0.08035714285714286 |
| 11 | TypeB | 214 | 6 | 0.028037383177570093 |
| 17 | TypeB | 202 | 18 | 0.0891089108910891 |

TypeA targeting creates strong selection-bias risk. TypeB/TypeC still need denominator and exposure caveats.

## Recommended Experiment
Run a household-randomized retention offer test for high-value declining households. Treatment receives a category-affinity coupon bundle; control receives business-as-usual. Primary metric: next 4-week spend per household. Guardrails: basket frequency, discount cost, redemption, category cannibalization, and customer complaints if available. Success requires practical lift, not just statistical significance.

## Visual Evidence
Charts: 01_data_coverage.png, 02_basket_spend_distribution.png, 03_frequency_distribution.png, 04_value_concentration.png, 05_retention_heatmap.png, 06_top_categories.png, 07_category_penetration_sales.png, 08_discount_sales.png, 09_campaign_funnel.png, 10_campaign_prepost.png
