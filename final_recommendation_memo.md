# Final Recommendation Memo

## Executive Summary

The retailer should prioritize high-value customer retention, category actions that combine scale with penetration and stability, and a randomized campaign test. The data foundation is strong enough for descriptive and diagnostic recommendations. Campaign evidence remains observational, so the memo separates facts, estimates, hypotheses, and recommended tests.

## KPI Snapshot

- Active households: 2500
- Baskets: 276484
- Spend: 8057463.08
- Average basket value: 29.14
- Coupon basket rate: 0.061

## Finding 1: Customer Value Is Concentrated

Customer spend is skewed and engagement varies materially by household. Retention actions should focus on high-value and declining households rather than broad untargeted discounting.

| segment | households | avg_spend | avg_baskets |
| --- | --- | --- | --- |
| high_value | 625 | 7793.0 | 227.99 |
| mid_value | 1211 | 2312.12 | 93.55 |
| at_risk_lapsed | 155 | 754.51 | 29.65 |
| low_value | 509 | 530.28 | 31.64 |

Recommended action: build a weekly retention watchlist from `feature_ready_households.csv` using monetary spend, recency, frequency, spend trend, discount sensitivity, and category affinity.

## Finding 2: Category Decisions Need Scale, Penetration, And Growth

Top categories by validated denominator:

| commodity_desc | category_sales | household_penetration | discount_rate | sales_growth |
| --- | --- | --- | --- | --- |
| COUPON/MISC ITEMS | 514685.72 | 0.5436 | 0.03237927017263654 | 86865.69999999978 |
| SOFT DRINKS | 327647.30000001536 | 0.962 | 0.25613667288152414 | 16912.900000000343 |
| BEEF | 312103.22000000137 | 0.8952 | 0.17186996810392227 | 25200.29999999993 |
| FLUID MILK PRODUCTS | 205356.0500000015 | 0.9684 | 0.18800441268322962 | 21370.810000001773 |
| CHEESE | 189528.18000000025 | 0.94 | 0.21289499589057864 | 15662.45999999973 |
| FRZN MEAT/MEAT DINNERS | 160517.16999999905 | 0.8276 | 0.2304563049131033 | 18390.0300000001 |
| BAG SNACKS | 148375.15999999628 | 0.9392 | 0.13106244620131052 | 16063.239999999088 |
| BEERS/ALES | 147309.6799999979 | 0.6424 | 0.0007622384998614622 | 9588.799999999901 |
| FROZEN PIZZA | 146037.24999999904 | 0.8208 | 0.18339654380335707 | 8784.030000000042 |
| BAKED BREAD/BUNS/ROLLS | 145930.8499999966 | 0.96 | 0.2044420692996737 | 14712.590000001117 |

High-sales categories are not automatically the best action targets. Prioritize categories with both high household penetration and positive growth. Investigate high-sales declining categories before reducing support, because mix, promotion cadence, or availability can explain decline.

Category growth leaders with denominator threshold:

| commodity_desc | first_year_sales | second_year_sales | sales_growth | household_penetration |
| --- | --- | --- | --- | --- |
| COUPON/MISC ITEMS | 213910.0099999999 | 300775.7099999997 | 86865.69999999978 | 0.5436 |
| BEEF | 143451.46000000002 | 168651.75999999995 | 25200.29999999993 | 0.8952 |
| COUPON/MISC ITEMS | 47553.609999999964 | 72406.42999999993 | 24852.81999999997 | 0.5572 |
| FLUID MILK PRODUCTS | 91992.61999999822 | 113363.43 | 21370.810000001773 | 0.9684 |
| FRZN MEAT/MEAT DINNERS | 71063.56999999967 | 89453.59999999977 | 18390.0300000001 | 0.8276 |
| SOFT DRINKS | 155367.20000000234 | 172280.10000000268 | 16912.900000000343 | 0.962 |
| BAG SNACKS | 66155.95999999983 | 82219.19999999892 | 16063.239999999088 | 0.9392 |
| CHEESE | 86932.8599999996 | 102595.31999999932 | 15662.45999999973 | 0.94 |
| BAKED BREAD/BUNS/ROLLS | 65609.12999999871 | 80321.71999999983 | 14712.590000001117 | 0.96 |
| FUEL | 8991.76 | 20544.8 | 11553.039999999999 | 0.1384 |

## Finding 3: Campaign Results Are Useful But Not Causal

Campaign funnel:

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

Pre/post association:

| campaign_type | households | avg_pre_spend | avg_post_spend | avg_change |
| --- | --- | --- | --- | --- |
| TypeA | 1513 | 587.95 | 1638.15 | 1050.2 |
| TypeB | 1023 | 825.46 | 1813.46 | 988.0 |
| TypeC | 397 | 474.25 | 1589.49 | 1115.24 |

TypeA campaigns are targeted and selection-biased. TypeB/TypeC campaigns are not equivalent to TypeA and still require exposure denominator and participation caveats. Do not claim campaign causality from these comparisons.

## Recommended Experiment

Business hypothesis: targeted category-affinity offers for high-value declining households will increase next 4-week spend without excessive discount cost.

Target population: high-value households with worsening spend trend or recency risk. Treatment: personalized coupon bundle in categories where the household has demonstrated affinity. Control: business-as-usual campaign treatment. Randomization unit: household. Primary metric: next 4-week spend per household. Secondary metrics: basket frequency, units, category penetration, redemption rate. Guardrails: discount cost, estimated margin proxy, category cannibalization, sparse subgroup sizes, customer complaint/unsubscribe measures if available.

Minimum denominator: at least 30 households per reporting segment and enough households per randomized arm to detect the selected MDE. Success rule: statistically reliable lift that also clears a pre-defined business value threshold after discount cost.

## What Not To Conclude

Do not infer real weekdays/months/holidays, do not treat item rows as baskets, do not report redemption without exposure denominators, do not join coupon or causal data at uncontrolled grain, and do not claim that observational campaigns caused spend changes.

## Next Data To Collect

Campaign eligibility rules, true send/open/click exposure, offer cost and margin, inventory/stockout flags, store geography, real calendar dates, and customer communication opt-outs.

## Evidence Files

- Tables: `outputs/tables/`
- Charts: `outputs/charts/`
- Chart interpretations: `visual_evidence_interpretations.md`
- QA readiness: `qa/FINAL_SUBMISSION_READINESS.md`
