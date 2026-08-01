# KPI Definitions

Discount reporting uses positive discount amounts derived from raw signed discount fields. Rates are not reported without denominators.

| kpi | business_definition | numerator | denominator | grain | time_window | exclusions_or_nulls | minimum_denominator | source_tables | output_column |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_household | household with >=1 basket | active households | eligible households | household-period or total | 4-week/total | none | >=1 basket | stg_transactions, mart_baskets | active_households |
| basket | distinct shopping trip basket | distinct basket_id | not applicable | basket | total | none | basket_id not null | stg_transactions | baskets |
| trip_frequency | shopping trips per active household | basket count | active households | household-period | 4-week | inactive periods retained with zero baskets | >=30 households for comparison | mart_household_period | basket_count |
| basket_size | units per basket | units | baskets | basket/period | 4-week/total | zero-basket rows excluded | >=1 basket | mart_baskets | basket_units |
| spend_net_sales | actual sales value | sum sales_value | not applicable | line/basket/period | any defined window | none | not applicable | stg_transactions | basket_spend,total_spend |
| gross_sales | sales before all recorded discounts | sales_value + retail_discount_amt + coupon_discount_amt + coupon_match_discount_amt | not applicable | line/basket/period | any defined window | none | not applicable | stg_transactions,mart_baskets | gross_sales |
| discount_rate | positive recorded discounts divided by gross sales | retail + coupon + match discounts | sales_value + retail + coupon + match discounts | basket/category | any defined window | denominator <=0 returns null | denominator >0 | mart_baskets,mart_categories | discount_rate |
| coupon_redemption_rate | share of exposed households redeeming | redeeming households | exposed households | campaign | campaign window | no denominator no rate | >=30 exposed households | mart_campaigns | household_redemption_rate |
| campaign_exposure_rate | share of active households exposed | exposed households | active households | campaign/period | campaign window | campaign denominator required | >=30 households | campaign_table,mart_campaigns | exposed_households |
| category_penetration | share of households buying category | category buyers | active households | category | total/year | missing category mapped unknown | >=50 category households | mart_categories | household_penetration |
| repeat_purchase | repeat buying household count | households with >=2 baskets/product | buyers | product/category | total | low buyers flagged | >=50 buyers | mart_products | repeat_household_count |
| retention_repeat | activity after prior activity | active current and prior period | active prior period | household-period | adjacent 4-week periods | first period has no prior | >=30 prior households | mart_household_period | retention_repeat_flag |
| customer_value | household spend | household spend | not applicable | household | observation/total | none | not applicable | mart_baskets | monetary_spend |
| customer_value_change | period spend delta | current spend - prior spend | prior spend | household-period | 4-week | first period null | prior spend >0 | mart_household_period | spend_change |
| high_value_customer | top quartile household value | top spend quartile | active households | household | observation window | none | quartile defined on active households | mart_customer_features | monetary_spend |
| at_risk_customer | declining or lapsed household | decline/lapse flag | prior active households | household | future label window | future fields excluded from features | prior active | mart_customer_features | next_period_spend_decline_flag |
| category_growth | later sales less early sales | second-year sales - first-year sales | first-year sales | category | year-like split | low-count categories caveated | >=50 households | mart_categories | sales_growth |
