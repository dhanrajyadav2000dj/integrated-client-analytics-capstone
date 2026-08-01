# Full Source Inventory

Generated: 2026-08-02 01:21:58 +0530

| Source filename | Actual path | Size bytes | Row count | Column count | Columns / data types | Null counts | Likely key | Row grain | Used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| transaction_data.csv | data/raw/transaction_data.csv | 141742346 | 2595732 | 16 | household_key:BIGINT, basket_id:BIGINT, day:INTEGER, week_no:INTEGER, product_id:BIGINT, quantity:DOUBLE, sales_value:DOUBLE, store_id:BIGINT, retail_disc_signed:DOUBLE, coupon_disc_signed:DOUBLE, coupon_match_disc_signed:DOUBLE, retail_discount_amt:DOUBLE, coupon_discount_amt:DOUBLE, coupon_match_discount_amt:DOUBLE, trans_time:INTEGER, trans_hour:DOUBLE | none | basket/product/household/store | item-receipt line | YES |
| product.csv | data/raw/product.csv | 6429896 | 92353 | 7 | product_id:BIGINT, manufacturer:BIGINT, department:VARCHAR, brand:VARCHAR, commodity_desc:VARCHAR, sub_commodity_desc:VARCHAR, curr_size_of_product:VARCHAR | none | product_id | product | YES |
| hh_demographic.csv | data/raw/hh_demographic.csv | 44349 | 801 | 8 | age_desc:VARCHAR, marital_status_code:VARCHAR, income_desc:VARCHAR, homeowner_desc:VARCHAR, hh_comp_desc:VARCHAR, household_size_desc:VARCHAR, kid_category_desc:VARCHAR, household_key:BIGINT | none | household_key | covered household | YES |
| campaign_desc.csv | data/raw/campaign_desc.csv | 540 | 30 | 4 | description:VARCHAR, campaign:BIGINT, start_day:BIGINT, end_day:BIGINT | none | campaign | campaign | YES |
| campaign_table.csv | data/raw/campaign_table.csv | 95874 | 7208 | 3 | description:VARCHAR, household_key:BIGINT, campaign:BIGINT | none | household_key,campaign | household-campaign exposure | YES |
| coupon.csv | data/raw/coupon.csv | 2822804 | 124548 | 3 | coupon_upc:BIGINT, product_id:BIGINT, campaign:BIGINT | none | campaign,coupon_upc,product_id after dedup | campaign-coupon-product mapping | YES |
| coupon_redempt.csv | data/raw/coupon_redempt.csv | 54108 | 2318 | 4 | household_key:BIGINT, day:BIGINT, coupon_upc:BIGINT, campaign:BIGINT | none | household,campaign,coupon,day | redemption event | YES |
| causal_data.csv | data/raw/causal_data.csv | 695858427 | 36786524 | 5 | product_id:BIGINT, store_id:BIGINT, week_no:BIGINT, display:VARCHAR, mailer:VARCHAR | none | product_id,store_id,week_no after dedup | product-store-week exposure | YES |

Null counts use full staged tables, not samples. Duplicate and grain checks are in validation_checks.csv.
