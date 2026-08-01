# Quantitative Analysis Appendix

Average basket spend bootstrap 95% CI: (np.float64(29.012), np.float64(29.271)). Household total spend bootstrap 95% CI: (np.float64(3102.6), np.float64(3350.263)).

Hypothesis test 1: early and late household-period spend are equal versus different. Welch t-statistic -6.157, p-value 0.0.

Hypothesis test 2: high-discount and low-discount category sales distributions are equal versus different. Mann-Whitney statistic 24631.0, p-value 0.0. Effect sizes and p-values are interpreted as observational evidence only.

Customer-category matrix sparsity: 0.628. Nearest-neighbor cosine similarity example: 0.423. PCA explained variance: [0.165, 0.04, 0.033, 0.029, 0.025].

Temporal baseline model AUC for next-period active flag: 0.874. Top coefficients: [('spend_trend_change', 1.012), ('frequency_baskets', 0.827), ('recency_weeks', -0.666), ('category_diversity', 0.518), ('second_half_spend', 0.462), ('total_units', -0.451), ('top_department_share', 0.213), ('avg_line_sales', 0.205), ('monetary_spend', 0.205), ('first_half_spend', -0.169)]. Logistic regression is interpretable screening, not a black-box decision system.

Future experiment power should be computed at household level using baseline variance; recommend planning for a 3-5% minimum detectable lift in repeat activity or spend. Statistical significance is not the same as business significance.
