CREATE OR REPLACE TABLE validation_checks AS
SELECT 'transaction_rows' check_name, COUNT(*)::VARCHAR check_value FROM stg_transactions
UNION ALL SELECT 'distinct_baskets', COUNT(DISTINCT basket_id)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'mart_basket_rows', COUNT(*)::VARCHAR FROM mart_baskets
UNION ALL SELECT 'basket_fanout_ok', (COUNT(*)=COUNT(DISTINCT basket_id))::VARCHAR FROM mart_baskets
UNION ALL SELECT 'products_duplicate_keys', (COUNT(*)-COUNT(DISTINCT product_id))::VARCHAR FROM stg_products
UNION ALL SELECT 'transactions_missing_product_metadata', COUNT(*)::VARCHAR FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) WHERE p.product_id IS NULL
UNION ALL SELECT 'negative_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value<0
UNION ALL SELECT 'zero_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value=0
UNION ALL SELECT 'invalid_trans_time_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE trans_hour IS NULL
UNION ALL SELECT 'discount_larger_than_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt>sales_value+retail_discount_amt AND sales_value>0
UNION ALL SELECT 'coupon_product_bridge_distinct_rows', COUNT(*)::VARCHAR FROM (SELECT DISTINCT campaign,coupon_upc,product_id FROM stg_coupon);
