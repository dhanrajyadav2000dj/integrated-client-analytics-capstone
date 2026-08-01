# Validation Report

## Source files
```json
{
  "transaction_data": "transaction_data.csv",
  "product": "product.csv",
  "hh_demographic": "hh_demographic.csv",
  "campaign_desc": "campaign_desc.csv",
  "campaign_table": "campaign_table.csv",
  "coupon": "coupon.csv",
  "coupon_redempt": "coupon_redempt.csv",
  "causal_data": "causal_data.csv"
}
```

## Table counts
```json
{
  "mart_baskets": 276484,
  "mart_household_period": 48303,
  "mart_products": 92339,
  "mart_categories": 360,
  "mart_campaigns": 30,
  "mart_coupon_redemptions": 2318,
  "mart_customer_features": 2499,
  "kpi_summary": 1,
  "validation_checks": 11
}
```

## Actual checks
| check_name | check_value |
| --- | --- |
| transaction_rows | 2595732 |
| distinct_baskets | 276484 |
| mart_basket_rows | 276484 |
| basket_fanout_ok | true |
| products_duplicate_keys | 0 |
| transactions_missing_product_metadata | 0 |
| negative_sales_rows | 0 |
| zero_sales_rows | 18850 |
| invalid_trans_time_rows | 0 |
| discount_larger_than_sales_rows | 1983 |
| coupon_product_bridge_distinct_rows | 119384 |

Fan-out control: item rows are aggregated to basket before basket metrics; coupon/product bridges are kept separate; campaign marts aggregate at campaign and household levels.
