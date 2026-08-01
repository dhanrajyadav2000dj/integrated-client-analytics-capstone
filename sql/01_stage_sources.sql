CREATE OR REPLACE TABLE stg_transactions AS
SELECT household_key::BIGINT AS household_key, basket_id::BIGINT AS basket_id, day::INTEGER AS day, week_no::INTEGER AS week_no,
       product_id::BIGINT AS product_id, quantity::DOUBLE AS quantity, sales_value::DOUBLE AS sales_value, store_id::BIGINT AS store_id,
       retail_disc::DOUBLE AS retail_disc_signed, coupon_disc::DOUBLE AS coupon_disc_signed, coupon_match_disc::DOUBLE AS coupon_match_disc_signed,
       ABS(COALESCE(retail_disc,0))::DOUBLE AS retail_discount_amt,
       ABS(COALESCE(coupon_disc,0))::DOUBLE AS coupon_discount_amt,
       ABS(COALESCE(coupon_match_disc,0))::DOUBLE AS coupon_match_discount_amt,
       TRY_CAST(trans_time AS INTEGER) AS trans_time,
       CASE WHEN TRY_CAST(trans_time AS INTEGER) BETWEEN 0 AND 2359 AND TRY_CAST(trans_time AS INTEGER) % 100 < 60 THEN FLOOR(TRY_CAST(trans_time AS INTEGER)/100) ELSE NULL END AS trans_hour
FROM raw_transaction_data;
CREATE OR REPLACE TABLE stg_products AS SELECT * FROM raw_product;
CREATE OR REPLACE TABLE stg_households AS SELECT * FROM raw_hh_demographic;
CREATE OR REPLACE TABLE stg_campaign_desc AS SELECT * FROM raw_campaign_desc;
CREATE OR REPLACE TABLE stg_campaign_table AS SELECT * FROM raw_campaign_table;
CREATE OR REPLACE TABLE stg_coupon AS SELECT * FROM raw_coupon;
CREATE OR REPLACE TABLE stg_coupon_redempt AS SELECT * FROM raw_coupon_redempt;
CREATE OR REPLACE TABLE stg_causal_data AS SELECT * FROM raw_causal_data;
