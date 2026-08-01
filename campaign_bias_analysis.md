# Campaign Bias-Aware Analysis

## Campaign Funnel

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

## Pre/Post Association by Campaign Type

| campaign_type | households | avg_pre_spend | avg_post_spend | avg_change |
| --- | --- | --- | --- | --- |
| TypeA | 1513 | 587.95 | 1638.15 | 1050.2 |
| TypeB | 1023 | 825.46 | 1813.46 | 988.0 |
| TypeC | 397 | 474.25 | 1589.49 | 1115.24 |

Campaign exposure is not proof that a household saw or understood a campaign. Redemption is sparse and mechanically different from exposure. TypeA campaigns are targeted, so exposed households are likely selected based on prior behavior; TypeB and TypeC are still observational and may reflect participation or eligibility differences.

The pre/post comparison uses a 28-day baseline before campaign start and campaign plus 28-day follow-up. It is a bias-aware descriptive design, not a causal estimate. The result should be phrased as association or lift hypothesis. The recommended next step is a randomized household-level test among high-value declining households.
