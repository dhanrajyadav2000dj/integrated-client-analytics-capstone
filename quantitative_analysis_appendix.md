# Quantitative Analysis Appendix

Average basket spend bootstrap 95% CI: (np.float64(29.01), np.float64(29.276)). Household total spend bootstrap 95% CI: (np.float64(3102.6), np.float64(3350.263)).

Hypothesis test 1: early and late household-period spend are equal versus different. Welch t-statistic -6.157, p-value 0.0.

Hypothesis test 2: high-discount and low-discount category sales distributions are equal versus different. Mann-Whitney statistic 24631.0, p-value 0.0. Effect sizes and p-values are interpreted as observational evidence only.

Customer-category matrix sparsity: 0.628. Nearest-neighbor cosine similarity example: 0.423. PCA explained variance: [0.165, 0.04, 0.033, 0.029, 0.025].

Temporal baseline model AUC for next-period active flag: 0.857. Top coefficients: [('recency_weeks', -0.94), ('frequency_baskets', 0.527), ('category_diversity', 0.353), ('total_units', -0.257), ('coupon_engagement', 0.209), ('product_diversity', 0.171), ('monetary_spend', 0.162), ('avg_line_sales', 0.159), ('discount_amount', 0.156), ('coupon_line_count', -0.103)]. Logistic regression is interpretable screening, not a black-box decision system.

Future experiment power should be computed at household level using baseline variance; recommend planning for a 3-5% minimum detectable lift in repeat activity or spend. Statistical significance is not the same as business significance.
