# Feature Dictionary

Feature file: `outputs/tables/feature_ready_households.csv`.

Observation window: all weeks through `max_week - 13`. Label window: final 13 weeks. The pipeline derives features only from the observation window and labels only from the future window.

## Target-like Labels

- `next_period_active_flag`: 1 when the household has at least one basket in the final 13-week future window.
- `next_period_spend_decline_flag`: 1 when future spend is below the observation-window spend rate scaled to 13 weeks.
- `future_spend`: future-window spend, retained for audit and excluded from model features.

## Feature Groups

- Recency: `recency_weeks`.
- Frequency: `frequency_baskets`.
- Monetary/value: `monetary_spend`, `avg_line_sales`, `total_units`.
- Basket/product composition: `product_diversity`, `category_diversity`.
- Discount sensitivity: `discount_amount`, `discount_rate`.
- Coupon engagement: `coupon_line_count`, `coupon_engagement`.
- Campaign engagement: `campaign_exposure_count` from campaigns starting before the observation cutoff.
- Category affinity: `top_department_share`.
- Trend/change: `first_half_spend`, `second_half_spend`, `spend_trend_change`.
- Demographics: raw demographic columns when available.
- Missingness: `missing_demographic_flag`.

## Preprocessing Contract

Numeric fields use median imputation for modeling checks. Categorical demographic fields should use unknown-category handling, rare-category grouping when cardinality is high, and one-hot encoding. Distance/model checks use scaling. Future label fields are excluded from feature matrices to avoid leakage.
