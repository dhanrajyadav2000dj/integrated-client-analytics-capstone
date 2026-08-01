# Feature Dictionary And Leakage Contract

Scoring grain is one household. Observation weeks end 13 weeks before max week; labels use only the final 13 weeks.

| Group | Columns | Use |
| --- | --- | --- |
| Recency, frequency, value | recency_weeks, frequency_baskets, monetary_spend, avg_line_sales | Observation |
| Composition | total_units, product_diversity, category_diversity, top_department_share | Observation |
| Discount and engagement | discount_amount, discount_rate, coupon_line_count, coupon_engagement, campaign_exposure_count | Observation |
| Trend | first_half_spend, second_half_spend, spend_trend_change | Observation |
| Demographics | age, income, home, household fields, missing_demographic_flag | Static subset |
| Labels | future_spend, next_period_active_flag, next_period_spend_decline_flag | Outcome only |

A stratified household holdout is used. Numeric median imputation, categorical imputation, rare grouping with minimum frequency 20, unknown-safe one-hot encoding, and scaling fit training households only. The fitted transformer aligns holdout columns. Duplicate households and infinite values are tested.
