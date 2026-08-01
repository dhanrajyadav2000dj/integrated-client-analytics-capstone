CREATE OR REPLACE TABLE mart_baskets AS
SELECT basket_id, household_key, MIN(day) AS day, MIN(week_no) AS week_no, MIN(store_id) AS store_id,
       SUM(sales_value) AS basket_spend, SUM(quantity) AS basket_units, COUNT(*) AS basket_item_line_count,
       COUNT(DISTINCT product_id) AS distinct_product_count, SUM(retail_discount_amt) AS total_retail_discount,
       SUM(coupon_discount_amt) AS total_coupon_discount, SUM(coupon_match_discount_amt) AS total_coupon_match_discount,
       CASE WHEN SUM(sales_value)+SUM(retail_discount_amt)>0 THEN SUM(retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt)/(SUM(sales_value)+SUM(retail_discount_amt)) END AS discount_rate,
       MAX(CASE WHEN coupon_discount_amt+coupon_match_discount_amt>0 THEN 1 ELSE 0 END) AS coupon_used_flag
FROM stg_transactions GROUP BY 1,2;
CREATE OR REPLACE TABLE mart_household_period AS
WITH b AS (SELECT *, FLOOR((week_no-1)/4)+1 AS period_id FROM mart_baskets),
agg AS (SELECT household_key, period_id, MIN(day) AS period_start_day, MAX(day) AS period_end_day, 1 AS active_flag, COUNT(*) AS basket_count,
        SUM(basket_spend) AS total_spend, SUM(basket_units) AS total_units, AVG(basket_spend) AS average_basket_value, AVG(basket_units) AS average_basket_size,
        SUM(total_retail_discount+total_coupon_discount+total_coupon_match_discount) AS total_discount, SUM(coupon_used_flag) AS coupon_basket_count
        FROM b GROUP BY 1,2),
prod AS (SELECT household_key, FLOOR((week_no-1)/4)+1 AS period_id, COUNT(DISTINCT t.product_id) distinct_product_count,
         COUNT(DISTINCT COALESCE(p.commodity_desc,p.department,'UNKNOWN')) distinct_category_count
         FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2),
camp AS (SELECT household_key, FLOOR((start_day-1)/28)+1 AS period_id, COUNT(*) AS campaign_exposure_count FROM stg_campaign_table ct LEFT JOIN stg_campaign_desc cd USING(campaign) GROUP BY 1,2),
red AS (SELECT household_key, FLOOR((day-1)/28)+1 AS period_id, COUNT(*) AS coupon_redemption_count FROM stg_coupon_redempt GROUP BY 1,2)
SELECT a.*, p.distinct_product_count, p.distinct_category_count, COALESCE(r.coupon_redemption_count,0) coupon_redemption_count,
       COALESCE(c.campaign_exposure_count,0) campaign_exposure_count,
       CASE WHEN a.total_spend+a.total_discount>0 THEN a.total_discount/(a.total_spend+a.total_discount) END AS discount_rate,
       LAG(a.total_spend) OVER(PARTITION BY a.household_key ORDER BY a.period_id) AS prior_period_spend,
       a.total_spend - LAG(a.total_spend) OVER(PARTITION BY a.household_key ORDER BY a.period_id) AS spend_change,
       CASE WHEN LAG(a.active_flag) OVER(PARTITION BY a.household_key ORDER BY a.period_id)=1 THEN 1 ELSE 0 END AS retention_repeat_flag
FROM agg a LEFT JOIN prod p USING(household_key,period_id) LEFT JOIN camp c USING(household_key,period_id) LEFT JOIN red r USING(household_key,period_id);
CREATE OR REPLACE TABLE mart_products AS
WITH pp AS (SELECT product_id, FLOOR((week_no-1)/13)+1 qtr, SUM(sales_value) sales FROM stg_transactions GROUP BY 1,2),
g AS (SELECT product_id, MAX(CASE WHEN qtr=1 THEN sales END) q1, MAX(CASE WHEN qtr=(SELECT MAX(qtr) FROM pp) THEN sales END) qlast FROM pp GROUP BY 1),
r AS (SELECT household_key, product_id, COUNT(DISTINCT basket_id) hb FROM stg_transactions GROUP BY 1,2)
SELECT t.product_id, ANY_VALUE(p.department) department, ANY_VALUE(p.commodity_desc) commodity_desc, ANY_VALUE(p.sub_commodity_desc) sub_commodity_desc,
       SUM(t.sales_value) product_sales, SUM(t.quantity) units,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) basket_penetration,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) household_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt)>0 THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)/SUM(t.sales_value+t.retail_discount_amt) END AS discount_rate,
       COALESCE(g.qlast,0)-COALESCE(g.q1,0) sales_growth, COUNT(DISTINCT CASE WHEN r.hb>=2 THEN t.household_key END) repeat_household_count
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) LEFT JOIN g USING(product_id) LEFT JOIN r USING(household_key,product_id) GROUP BY t.product_id,g.qlast,g.q1;
CREATE OR REPLACE TABLE mart_categories AS
SELECT COALESCE(p.department,'UNKNOWN') department, COALESCE(p.commodity_desc,'UNKNOWN') commodity_desc,
       SUM(t.sales_value) category_sales, SUM(t.quantity) units, COUNT(DISTINCT t.household_key) household_count,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) household_penetration,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) basket_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt)>0 THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)/SUM(t.sales_value+t.retail_discount_amt) END AS discount_rate,
       SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) first_year_sales, SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END) second_year_sales,
       SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END)-SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) sales_growth
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2;
CREATE OR REPLACE TABLE mart_campaigns AS
SELECT cd.campaign, cd.description, cd.description AS campaign_type, cd.start_day, cd.end_day,
       COUNT(DISTINCT ct.household_key) exposed_households, COUNT(DISTINCT cr.household_key) redeeming_households, COUNT(cr.household_key) redemption_count,
       CASE WHEN COUNT(DISTINCT ct.household_key)>0 THEN COUNT(DISTINCT cr.household_key)*1.0/COUNT(DISTINCT ct.household_key) END household_redemption_rate
FROM stg_campaign_desc cd LEFT JOIN stg_campaign_table ct USING(campaign) LEFT JOIN stg_coupon_redempt cr USING(campaign,household_key) GROUP BY 1,2,3,4,5;
CREATE OR REPLACE TABLE mart_coupon_redemptions AS SELECT cr.*, cd.description AS campaign_type, cd.start_day, cd.end_day FROM stg_coupon_redempt cr LEFT JOIN stg_campaign_desc cd USING(campaign);
