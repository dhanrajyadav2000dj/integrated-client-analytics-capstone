# Mart Catalog

| Table | Grain / unique key | Measures | Intended use |
| --- | --- | --- | --- |
| mart_baskets | basket_id | spend, gross sales, units, line/product counts, discounts | Basket KPIs |
| mart_household_period | household_key, four-week period_id | activity, spend, baskets, prior spend, adjacent retention | Customer trends |
| mart_products | product_id | sales, units, penetration, growth, repeats | Product diagnostics |
| mart_categories | department, commodity | sales, units, penetration, discount, growth | Category performance |
| mart_category_diagnostics | department, commodity | variation, engagement change, decision flags | Stable category decisions |
| mart_campaigns | campaign | exposures, redemptions, rates | Campaign funnel |
| mart_coupon_redemptions | redemption source event | redemption context | Coupon behavior |
| mart_promotion_performance | promotion status | exact-grain observation counts, sales, units | Descriptive promotion evidence |
| mart_customer_features | household_key | observation features plus separately identified labels | Scoring readiness |
| customer_period_summary | four-week period_id | active/new/returning/retained counts | Retention denominators |
| customer_retention_matrix | cohort_period, period_id | active cohort and retention rate | Cohort evidence |
