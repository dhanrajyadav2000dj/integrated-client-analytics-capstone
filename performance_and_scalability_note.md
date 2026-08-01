# Performance And Scalability Note

The largest source is causal_data with 36,786,524 rows; transactions have 2,595,732 item lines. DuckDB handles heavy staging and aggregation. Transactions reduce to product-store-week before promotion joins, and duplicate causal keys collapse at the same grain. Row, sales, and unit controls prevent fan-out.

Production should partition by week, cluster by product-store-week and household-week, materialize staging, refresh incrementally, enforce bridge uniqueness, and monitor workloads. Do not load full causal data into pandas or join coupons directly to item rows.
