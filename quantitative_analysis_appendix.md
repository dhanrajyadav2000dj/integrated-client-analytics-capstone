# Quantitative Analysis Appendix

## Descriptive Statistics

| avg_basket_spend | median_basket_spend | sd_basket_spend | avg_basket_units | median_basket_units | avg_discount_rate | median_discount_rate |
| --- | --- | --- | --- | --- | --- | --- |
| 29.14 | 17.07 | 36.1 | 942.86 | 8.0 | 0.1357 | 0.1138 |

Basket spend, basket units, discount rates, and coupon behavior are right-skewed. This motivates medians, denominator checks, and bootstrap confidence intervals alongside parametric tests.

## Business Event Probabilities

| p_coupon_basket | p_basket_over_50 | p_repeat_period |
| --- | --- | --- |
| 0.0617 | 0.1661 | 0.0074 |

These probabilities are empirical rates from the observed sample, not population guarantees.

## Confidence Intervals

- Average basket spend bootstrap 95% CI: (29.007, 29.275)
- Household total spend bootstrap 95% CI: (3102.6, 3350.263)

## Hypothesis Tests

1. Early versus late household-period spend. Null: mean spend is equal. Alternative: mean spend differs. Welch t-statistic -6.157, p-value 0.0. The large sample makes small differences detectable, so business materiality should be evaluated with absolute spend change and margin.
2. High-discount versus low-discount category sales. Null: category sales distributions are equal. Alternative: distributions differ. Mann-Whitney statistic 24631.0, p-value 0.0. This is association only; promotion intensity, category role, and product mix can confound the comparison.

Multiple category and segment comparisons increase false-positive risk. Findings should be used to prioritize investigation, not to make automatic assortment decisions.

## Matrix, Similarity, and PCA

Customer-category matrix sparsity: 0.628. Nearest-neighbor cosine similarity example: 0.423. PCA explained variance: [0.165, 0.04, 0.033, 0.029, 0.025]. Sparse purchase matrices can overstate similarity for narrow category buyers, so nearest neighbors should be interpreted as affinity hypotheses.

## Baseline Model

Temporal baseline model AUC for next-period active flag: 0.874. Top standardized coefficients: [('spend_trend_change', 1.012), ('frequency_baskets', 0.827), ('recency_weeks', -0.666), ('category_diversity', 0.518), ('second_half_spend', 0.462), ('total_units', -0.451), ('top_department_share', 0.213), ('avg_line_sales', 0.205), ('monetary_spend', 0.205), ('first_half_spend', -0.169)]. Logistic regression uses a logit link for a binary outcome and is included for interpretable screening. Future labels and future spend are excluded from features. Calibration and temporal holdout monitoring are required before production use.

## Power / MDE

The MDE chart uses a two-sample household-randomized normal approximation with alpha 0.05 and power 0.80. The recommended experiment should recompute sample size using current eligible-household variance and minimum business-relevant lift. Statistical significance is not the same as business significance.
