CREATE OR REPLACE TABLE mart_baskets AS
SELECT basket_id, household_key, MIN(day) AS day, MIN(week_no) AS week_no, MIN(store_id) AS store_id,
       SUM(sales_value) AS basket_spend, SUM(quantity) AS basket_units, COUNT(*) AS basket_item_line_count,
       COUNT(DISTINCT product_id) AS distinct_product_count, SUM(retail_discount_amt) AS total_retail_discount,
       SUM(coupon_discount_amt) AS total_coupon_discount, SUM(coupon_match_discount_amt) AS total_coupon_match_discount,
       SUM(sales_value+retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt) AS gross_sales,
       CASE WHEN SUM(sales_value+retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt)>0
            THEN SUM(retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt)
                 /SUM(sales_value+retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt) END AS discount_rate,
       MAX(CASE WHEN coupon_discount_amt+coupon_match_discount_amt>0 THEN 1 ELSE 0 END) AS coupon_used_flag
FROM stg_transactions GROUP BY 1,2;

CREATE OR REPLACE TABLE mart_household_period AS
WITH RECURSIVE periods(period_id) AS (
  SELECT 1 UNION ALL SELECT period_id+1 FROM periods
  WHERE period_id < (SELECT CEIL(MAX(week_no)/4.0)::INTEGER FROM mart_baskets)
),
households AS (SELECT DISTINCT household_key FROM mart_baskets),
spine AS (SELECT h.household_key, p.period_id FROM households h CROSS JOIN periods p),
basket_agg AS (
  SELECT household_key, FLOOR((week_no-1)/4)+1 AS period_id, 1 AS active_flag,
         COUNT(*) AS basket_count, SUM(basket_spend) AS total_spend, SUM(basket_units) AS total_units,
         AVG(basket_spend) AS average_basket_value, AVG(basket_units) AS average_basket_size,
         SUM(total_retail_discount+total_coupon_discount+total_coupon_match_discount) AS total_discount,
         SUM(coupon_used_flag) AS coupon_basket_count
  FROM mart_baskets GROUP BY 1,2
),
product_agg AS (
  SELECT household_key, FLOOR((week_no-1)/4)+1 AS period_id,
         COUNT(DISTINCT t.product_id) AS distinct_product_count,
         COUNT(DISTINCT COALESCE(p.commodity_desc,p.department,'UNKNOWN')) AS distinct_category_count
  FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2
),
campaign_agg AS (
  SELECT household_key, FLOOR((start_day-1)/28)+1 AS period_id, COUNT(*) AS campaign_exposure_count
  FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign) GROUP BY 1,2
),
redemption_agg AS (
  SELECT household_key, FLOOR((day-1)/28)+1 AS period_id, COUNT(*) AS coupon_redemption_count
  FROM stg_coupon_redempt GROUP BY 1,2
),
base AS (
  SELECT s.household_key, s.period_id,
         (s.period_id-1)*28+1 AS period_start,
         LEAST(s.period_id*28,(SELECT MAX(day) FROM stg_transactions)) AS period_end,
         CASE WHEN s.period_id=(SELECT MAX(period_id) FROM periods)
                   AND s.period_id*28>(SELECT MAX(day) FROM stg_transactions) THEN 1 ELSE 0 END AS incomplete_period_flag,
         COALESCE(b.active_flag,0) AS active_flag, COALESCE(b.basket_count,0) AS basket_count,
         COALESCE(b.total_spend,0) AS total_spend, COALESCE(b.total_units,0) AS total_units,
         b.average_basket_value, b.average_basket_size, COALESCE(b.total_discount,0) AS total_discount,
         COALESCE(b.coupon_basket_count,0) AS coupon_basket_count,
         COALESCE(p.distinct_product_count,0) AS distinct_product_count,
         COALESCE(p.distinct_category_count,0) AS distinct_category_count,
         COALESCE(r.coupon_redemption_count,0) AS coupon_redemption_count,
         COALESCE(c.campaign_exposure_count,0) AS campaign_exposure_count,
         CASE WHEN COALESCE(b.total_spend,0)+COALESCE(b.total_discount,0)>0
              THEN b.total_discount/(b.total_spend+b.total_discount) END AS discount_rate
  FROM spine s
  LEFT JOIN basket_agg b USING(household_key,period_id)
  LEFT JOIN product_agg p USING(household_key,period_id)
  LEFT JOIN campaign_agg c USING(household_key,period_id)
  LEFT JOIN redemption_agg r USING(household_key,period_id)
)
SELECT *,
       LAG(total_spend) OVER(PARTITION BY household_key ORDER BY period_id) AS prior_period_spend,
       CASE WHEN period_id=1 THEN NULL
            ELSE total_spend-LAG(total_spend) OVER(PARTITION BY household_key ORDER BY period_id) END AS spend_change,
       CASE WHEN active_flag=1 AND LAG(active_flag) OVER(PARTITION BY household_key ORDER BY period_id)=1 THEN 1 ELSE 0 END AS retention_repeat_flag
FROM base;

CREATE OR REPLACE TABLE mart_products AS
WITH pp AS (
  SELECT product_id, FLOOR((week_no-1)/13)+1 AS quarter_like_period, SUM(sales_value) AS sales
  FROM stg_transactions GROUP BY 1,2
),
bounds AS (SELECT MIN(quarter_like_period) first_period, MAX(quarter_like_period) last_period FROM pp),
g AS (
  SELECT product_id,
         MAX(CASE WHEN quarter_like_period=(SELECT first_period FROM bounds) THEN sales END) AS first_sales,
         MAX(CASE WHEN quarter_like_period=(SELECT last_period FROM bounds) THEN sales END) AS last_sales
  FROM pp GROUP BY 1
),
r AS (
  SELECT household_key, product_id, COUNT(DISTINCT basket_id) AS household_baskets
  FROM stg_transactions GROUP BY 1,2
)
SELECT t.product_id, ANY_VALUE(p.manufacturer) AS manufacturer,
       ANY_VALUE(p.brand) AS brand, ANY_VALUE(p.curr_size_of_product) AS curr_size_of_product,
       ANY_VALUE(p.department) AS department, ANY_VALUE(p.commodity_desc) AS commodity_desc,
       ANY_VALUE(p.sub_commodity_desc) AS sub_commodity_desc,
       SUM(t.sales_value) AS product_sales, SUM(t.quantity) AS units,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) AS basket_penetration,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) AS household_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)>0
            THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)
                 /SUM(t.sales_value+t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt) END AS discount_rate,
       COALESCE(g.last_sales,0)-COALESCE(g.first_sales,0) AS sales_growth,
       CASE WHEN COALESCE(g.first_sales,0)>0 THEN (g.last_sales-g.first_sales)/g.first_sales END AS sales_growth_rate,
       COUNT(DISTINCT CASE WHEN r.household_baskets>=2 THEN t.household_key END) AS repeat_household_count
FROM stg_transactions t
LEFT JOIN stg_products p USING(product_id)
LEFT JOIN g USING(product_id)
LEFT JOIN r USING(household_key,product_id)
GROUP BY t.product_id,g.last_sales,g.first_sales;

CREATE OR REPLACE TABLE mart_categories AS
SELECT COALESCE(p.department,'UNKNOWN') AS department, COALESCE(p.commodity_desc,'UNKNOWN') AS commodity_desc,
       SUM(t.sales_value) AS category_sales, SUM(t.quantity) AS units,
       COUNT(DISTINCT t.household_key) AS household_count,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) AS household_penetration,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) AS basket_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)>0
            THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)
                 /SUM(t.sales_value+t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt) END AS discount_rate,
       SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) AS first_year_sales,
       SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END) AS second_year_sales,
       SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END)-SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) AS sales_growth,
       CASE WHEN SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END)>0
            THEN (SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END)-SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END))
                 /SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) END AS sales_growth_rate
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2;

CREATE OR REPLACE TABLE mart_category_period AS
SELECT COALESCE(p.department,'UNKNOWN') AS department, COALESCE(p.commodity_desc,'UNKNOWN') AS commodity_desc,
       FLOOR((t.week_no-1)/13)+1 AS quarter_like_period, SUM(t.sales_value) AS sales,
       COUNT(DISTINCT t.household_key) AS households, COUNT(DISTINCT t.basket_id) AS baskets
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2,3;

CREATE OR REPLACE TABLE mart_category_diagnostics AS
WITH x AS (
  SELECT department, commodity_desc, AVG(sales) AS mean_period_sales, STDDEV_SAMP(sales) AS sd_period_sales,
         MAX(CASE WHEN quarter_like_period=1 THEN households END) AS first_period_households,
         MAX(CASE WHEN quarter_like_period=(SELECT MAX(quarter_like_period) FROM mart_category_period) THEN households END) AS last_period_households
  FROM mart_category_period GROUP BY 1,2
)
SELECT c.*, x.mean_period_sales, x.sd_period_sales,
       x.sd_period_sales/NULLIF(x.mean_period_sales,0) AS sales_coefficient_of_variation,
       x.last_period_households-x.first_period_households AS household_engagement_change,
       CASE WHEN c.household_count<50 THEN 1 ELSE 0 END AS small_group_flag,
       CASE WHEN c.category_sales>=(SELECT QUANTILE_CONT(category_sales,.75) FROM mart_categories)
                  AND c.sales_growth<0 THEN 1 ELSE 0 END AS high_sales_declining_flag,
       CASE WHEN c.household_penetration>=(SELECT QUANTILE_CONT(household_penetration,.75) FROM mart_categories)
                  AND c.category_sales/NULLIF(c.household_count,0)<=(SELECT MEDIAN(category_sales/NULLIF(household_count,0)) FROM mart_categories)
            THEN 1 ELSE 0 END AS high_penetration_low_spend_flag
FROM mart_categories c JOIN x USING(department,commodity_desc);

CREATE OR REPLACE TABLE mart_promotion_performance AS
WITH tx AS (
  SELECT product_id, store_id, week_no, SUM(sales_value) AS sales, SUM(quantity) AS units,
         COUNT(DISTINCT basket_id) AS baskets, COUNT(*) AS transaction_lines
  FROM stg_transactions GROUP BY 1,2,3
),
causal_exact AS (
  SELECT product_id, store_id, week_no,
         MAX(CASE WHEN COALESCE(display,'0')<>'0' THEN 1 ELSE 0 END) AS display_flag,
         MAX(CASE WHEN COALESCE(mailer,'0')<>'0' THEN 1 ELSE 0 END) AS mailer_flag
  FROM stg_causal_data GROUP BY 1,2,3
),
joined AS (
  SELECT tx.*, COALESCE(c.display_flag,0) AS display_flag, COALESCE(c.mailer_flag,0) AS mailer_flag
  FROM tx LEFT JOIN causal_exact c USING(product_id,store_id,week_no)
)
SELECT CASE WHEN display_flag=1 OR mailer_flag=1 THEN 'promoted' ELSE 'not_promoted' END AS promotion_status,
       COUNT(*) AS product_store_weeks, SUM(transaction_lines) AS transaction_lines,
       SUM(sales) AS sales, SUM(units) AS units, SUM(baskets) AS basket_occurrences,
       AVG(sales) AS avg_sales_per_product_store_week
FROM joined GROUP BY 1;

CREATE OR REPLACE TABLE validation_checks AS
SELECT 'transaction_rows' AS check_name, COUNT(*)::VARCHAR AS check_value FROM stg_transactions
UNION ALL SELECT 'distinct_baskets', COUNT(DISTINCT basket_id)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'distinct_households', COUNT(DISTINCT household_key)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'distinct_products', COUNT(DISTINCT product_id)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'distinct_stores', COUNT(DISTINCT store_id)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'campaign_count', COUNT(DISTINCT campaign)::VARCHAR FROM stg_campaign_desc
UNION ALL SELECT 'exposed_households', COUNT(DISTINCT household_key)::VARCHAR FROM stg_campaign_table
UNION ALL SELECT 'coupon_count', COUNT(DISTINCT coupon_upc)::VARCHAR FROM stg_coupon
UNION ALL SELECT 'coupon_redemption_rows', COUNT(*)::VARCHAR FROM stg_coupon_redempt
UNION ALL SELECT 'causal_source_rows', COUNT(*)::VARCHAR FROM stg_causal_data
UNION ALL SELECT 'min_day', MIN(day)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'max_day', MAX(day)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'min_week', MIN(week_no)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'max_week', MAX(week_no)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'mart_basket_rows', COUNT(*)::VARCHAR FROM mart_baskets
UNION ALL SELECT 'basket_fanout_ok', (COUNT(*)=COUNT(DISTINCT basket_id))::VARCHAR FROM mart_baskets
UNION ALL SELECT 'basket_sales_reconciled', (ABS((SELECT SUM(sales_value) FROM stg_transactions)-(SELECT SUM(basket_spend) FROM mart_baskets))<0.01)::VARCHAR
UNION ALL SELECT 'basket_units_reconciled', (ABS((SELECT SUM(quantity) FROM stg_transactions)-(SELECT SUM(basket_units) FROM mart_baskets))<0.01)::VARCHAR
UNION ALL SELECT 'household_period_unique', (COUNT(*)=COUNT(DISTINCT (household_key,period_id)))::VARCHAR FROM mart_household_period
UNION ALL SELECT 'product_join_fanout_ok', ((SELECT COUNT(*) FROM stg_transactions)=(SELECT COUNT(*) FROM stg_transactions t LEFT JOIN stg_products p USING(product_id)))::VARCHAR
UNION ALL SELECT 'product_join_sales_reconciled', (ABS((SELECT SUM(sales_value) FROM stg_transactions)-(SELECT SUM(t.sales_value) FROM stg_transactions t LEFT JOIN stg_products p USING(product_id)))<0.01)::VARCHAR
UNION ALL SELECT 'products_duplicate_keys', (COUNT(*)-COUNT(DISTINCT product_id))::VARCHAR FROM stg_products
UNION ALL SELECT 'campaign_exposure_duplicate_keys', (COUNT(*)-COUNT(DISTINCT (household_key,campaign)))::VARCHAR FROM stg_campaign_table
UNION ALL SELECT 'coupon_bridge_duplicate_rows', (COUNT(*)-COUNT(DISTINCT (campaign,coupon_upc,product_id)))::VARCHAR FROM stg_coupon
UNION ALL SELECT 'causal_duplicate_exact_keys', (COUNT(*)-COUNT(DISTINCT (product_id,store_id,week_no)))::VARCHAR FROM stg_causal_data
UNION ALL SELECT 'transactions_missing_product_metadata', COUNT(*)::VARCHAR FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) WHERE p.product_id IS NULL
UNION ALL SELECT 'campaign_exposures_missing_description', COUNT(*)::VARCHAR FROM stg_campaign_table t LEFT JOIN stg_campaign_desc d USING(campaign) WHERE d.campaign IS NULL
UNION ALL SELECT 'redemptions_missing_campaign', COUNT(*)::VARCHAR FROM stg_coupon_redempt r LEFT JOIN stg_campaign_desc d USING(campaign) WHERE d.campaign IS NULL
UNION ALL SELECT 'negative_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value<0
UNION ALL SELECT 'zero_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value=0
UNION ALL SELECT 'negative_quantity_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE quantity<0
UNION ALL SELECT 'zero_quantity_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE quantity=0
UNION ALL SELECT 'invalid_trans_time_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE trans_hour IS NULL
UNION ALL SELECT 'discount_larger_than_net_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt>sales_value AND sales_value>0
UNION ALL SELECT 'coupon_product_bridge_distinct_rows', COUNT(*)::VARCHAR FROM (SELECT DISTINCT campaign,coupon_upc,product_id FROM stg_coupon)
UNION ALL SELECT 'causal_exact_key_rows', COUNT(*)::VARCHAR FROM (SELECT DISTINCT product_id,store_id,week_no FROM stg_causal_data)
UNION ALL SELECT 'transaction_product_store_week_rows', COUNT(*)::VARCHAR FROM (SELECT product_id,store_id,week_no FROM stg_transactions GROUP BY 1,2,3)
UNION ALL SELECT 'promotion_join_rows', SUM(product_store_weeks)::VARCHAR FROM mart_promotion_performance
UNION ALL SELECT 'promotion_join_fanout_ok', ((SELECT COUNT(*) FROM (SELECT product_id,store_id,week_no FROM stg_transactions GROUP BY 1,2,3))=(SELECT SUM(product_store_weeks) FROM mart_promotion_performance))::VARCHAR
UNION ALL SELECT 'promotion_join_sales_reconciled', (ABS((SELECT SUM(sales_value) FROM stg_transactions)-(SELECT SUM(sales) FROM mart_promotion_performance))<0.01)::VARCHAR
UNION ALL SELECT 'promotion_join_units_reconciled', (ABS((SELECT SUM(quantity) FROM stg_transactions)-(SELECT SUM(units) FROM mart_promotion_performance))<0.01)::VARCHAR
UNION ALL SELECT 'basket_discount_rate_in_range', (COUNT(*) FILTER(WHERE discount_rate<0 OR discount_rate>1)=0)::VARCHAR FROM mart_baskets;

CREATE OR REPLACE TABLE customer_period_summary AS
WITH firsts AS (
  SELECT household_key, MIN(period_id) FILTER(WHERE active_flag=1) AS first_active_period
  FROM mart_household_period GROUP BY 1
), lagged AS (
  SELECT *, LAG(active_flag) OVER(PARTITION BY household_key ORDER BY period_id) AS prior_active
  FROM mart_household_period
)
SELECT h.period_id, MIN(h.period_start) AS period_start, MAX(h.period_end) AS period_end,
       SUM(h.active_flag) AS active_households,
       SUM(CASE WHEN h.active_flag=1 AND h.period_id=f.first_active_period THEN 1 ELSE 0 END) AS new_households,
       SUM(CASE WHEN h.active_flag=1 AND h.period_id>f.first_active_period THEN 1 ELSE 0 END) AS returning_households,
       SUM(CASE WHEN h.prior_active=1 THEN 1 ELSE 0 END) AS prior_active_households,
       SUM(h.retention_repeat_flag) AS retained_households,
       SUM(h.retention_repeat_flag)*1.0/NULLIF(SUM(CASE WHEN h.prior_active=1 THEN 1 ELSE 0 END),0) AS retention_rate
FROM lagged h JOIN firsts f USING(household_key)
GROUP BY h.period_id ORDER BY h.period_id;

CREATE OR REPLACE TABLE customer_retention_matrix AS
WITH cohorts AS (
  SELECT household_key, MIN(period_id) FILTER(WHERE active_flag=1) AS cohort_period
  FROM mart_household_period GROUP BY 1
), sizes AS (
  SELECT cohort_period, COUNT(*) AS cohort_households FROM cohorts GROUP BY 1
)
SELECT c.cohort_period, h.period_id, SUM(h.active_flag) AS active_households,
       s.cohort_households, SUM(h.active_flag)*1.0/s.cohort_households AS retention_rate
FROM cohorts c JOIN mart_household_period h USING(household_key)
JOIN sizes s USING(cohort_period)
WHERE h.period_id>=c.cohort_period
GROUP BY 1,2,4 ORDER BY 1,2;

CREATE OR REPLACE TABLE campaign_bias_comparison AS
WITH exposures AS (
  SELECT ct.household_key, ct.campaign, cd.description AS campaign_type, cd.start_day,
         CASE WHEN cr.household_key IS NULL THEN 0 ELSE 1 END AS redeemed_flag
  FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign)
  LEFT JOIN (SELECT DISTINCT household_key,campaign FROM stg_coupon_redempt) cr
  USING(household_key,campaign)
), behavior AS (
  SELECT e.*, SUM(CASE WHEN t.day BETWEEN e.start_day-28 AND e.start_day-1 THEN t.sales_value ELSE 0 END) AS pre_spend,
         SUM(CASE WHEN t.day BETWEEN e.start_day AND e.start_day+27 THEN t.sales_value ELSE 0 END) AS post_spend,
         COUNT(DISTINCT CASE WHEN t.day BETWEEN e.start_day-28 AND e.start_day-1 THEN t.basket_id END) AS pre_baskets,
         COUNT(DISTINCT CASE WHEN t.day BETWEEN e.start_day AND e.start_day+27 THEN t.basket_id END) AS post_baskets
  FROM exposures e LEFT JOIN stg_transactions t
    ON e.household_key=t.household_key AND t.day BETWEEN e.start_day-28 AND e.start_day+27
  GROUP BY 1,2,3,4,5
), stratified AS (
  SELECT *, NTILE(4) OVER(PARTITION BY campaign ORDER BY pre_spend) AS prior_value_quartile
  FROM behavior
)
SELECT campaign_type, prior_value_quartile, redeemed_flag,
       COUNT(*) AS household_campaign_exposures,
       AVG(pre_spend) AS avg_pre_spend, AVG(post_spend) AS avg_post_spend,
       AVG(post_spend-pre_spend) AS avg_spend_change,
       AVG(pre_baskets) AS avg_pre_baskets, AVG(post_baskets) AS avg_post_baskets,
       AVG(post_baskets-pre_baskets) AS avg_basket_change
FROM stratified GROUP BY 1,2,3 ORDER BY 1,2,3;

CREATE OR REPLACE TABLE campaign_segment_analysis AS
WITH hh AS (
  SELECT household_key, SUM(basket_spend) AS spend, MAX(week_no) AS last_week
  FROM mart_baskets GROUP BY 1
), scored AS (
  SELECT *, NTILE(4) OVER(ORDER BY spend) AS value_quartile FROM hh
), segments AS (
  SELECT household_key,
         CASE WHEN value_quartile=4 THEN 'high_value'
              WHEN last_week<(SELECT MAX(week_no)-13 FROM mart_baskets) THEN 'at_risk_lapsed'
              WHEN value_quartile=1 THEN 'low_value' ELSE 'mid_value' END AS segment
  FROM scored
), exposed AS (
  SELECT ct.household_key, cd.description AS campaign_type, ct.campaign
  FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign)
), redeemed AS (
  SELECT DISTINCT household_key,campaign FROM stg_coupon_redempt
)
SELECT e.campaign_type, s.segment, COUNT(*) AS household_campaign_exposures,
       COUNT(r.household_key) AS redeemed_exposures,
       COUNT(r.household_key)*1.0/COUNT(*) AS redemption_rate
FROM exposed e JOIN segments s USING(household_key)
LEFT JOIN redeemed r USING(household_key,campaign)
GROUP BY 1,2 ORDER BY 1,2;

INSERT INTO validation_checks
SELECT 'duplicate_transaction_rows', (COUNT(*)-COUNT(DISTINCT (household_key,basket_id,day,week_no,product_id,quantity,sales_value,store_id,retail_disc_signed,coupon_disc_signed,coupon_match_disc_signed,trans_time)))::VARCHAR FROM stg_transactions
UNION ALL SELECT 'demographic_covered_households', COUNT(DISTINCT h.household_key)::VARCHAR FROM (SELECT DISTINCT household_key FROM stg_transactions) t JOIN stg_households h USING(household_key)
UNION ALL SELECT 'demographic_uncovered_households', COUNT(DISTINCT t.household_key)::VARCHAR FROM (SELECT DISTINCT household_key FROM stg_transactions) t LEFT JOIN stg_households h USING(household_key) WHERE h.household_key IS NULL
UNION ALL SELECT 'redemptions_missing_coupon_context', COUNT(*)::VARCHAR FROM stg_coupon_redempt r LEFT JOIN (SELECT DISTINCT campaign,coupon_upc FROM stg_coupon) c USING(campaign,coupon_upc) WHERE c.coupon_upc IS NULL
UNION ALL SELECT 'suspicious_quantity_rows_over_100', COUNT(*)::VARCHAR FROM stg_transactions WHERE quantity>100
UNION ALL SELECT 'outlier_baskets_above_p99', COUNT(*)::VARCHAR FROM mart_baskets WHERE basket_spend>(SELECT QUANTILE_CONT(basket_spend,.99) FROM mart_baskets)
UNION ALL SELECT 'outlier_households_above_p99_spend', COUNT(*)::VARCHAR FROM (SELECT household_key,SUM(basket_spend) spend FROM mart_baskets GROUP BY 1) WHERE spend>(SELECT QUANTILE_CONT(spend,.99) FROM (SELECT household_key,SUM(basket_spend) spend FROM mart_baskets GROUP BY 1))
UNION ALL SELECT 'outlier_products_above_p99_sales', COUNT(*)::VARCHAR FROM mart_products WHERE product_sales>(SELECT QUANTILE_CONT(product_sales,.99) FROM mart_products)
UNION ALL SELECT 'day_index_gap_count', (MAX(day)-MIN(day)+1-COUNT(DISTINCT day))::VARCHAR FROM stg_transactions
UNION ALL SELECT 'week_index_gap_count', (MAX(week_no)-MIN(week_no)+1-COUNT(DISTINCT week_no))::VARCHAR FROM stg_transactions
UNION ALL SELECT 'sparse_categories_under_50_households', COUNT(*)::VARCHAR FROM mart_categories WHERE household_count<50
UNION ALL SELECT 'null_or_blank_category_labels', COUNT(*)::VARCHAR FROM stg_products WHERE commodity_desc IS NULL OR TRIM(commodity_desc)=''
UNION ALL SELECT 'normalized_category_label_collisions', (COUNT(DISTINCT commodity_desc)-COUNT(DISTINCT UPPER(TRIM(commodity_desc))))::VARCHAR FROM stg_products;
