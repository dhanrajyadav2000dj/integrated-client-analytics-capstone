CREATE OR REPLACE TABLE kpi_summary AS
SELECT COUNT(DISTINCT household_key) active_households, COUNT(*) baskets, SUM(basket_spend) spend, AVG(basket_spend) avg_basket_value,
       SUM(basket_units) units, AVG(basket_units) avg_basket_size, SUM(total_retail_discount+total_coupon_discount+total_coupon_match_discount) discount_amount,
       SUM(coupon_used_flag) coupon_baskets, SUM(coupon_used_flag)*1.0/COUNT(*) coupon_basket_rate
FROM mart_baskets;
