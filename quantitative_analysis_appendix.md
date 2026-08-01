# Quantitative Analysis Appendix

## Distribution And Probability Evidence

Basket spend and units are right-skewed. Extreme source quantities make medians important alongside means.

| mean_basket_spend | median_basket_spend | sd_basket_spend | mean_basket_units | median_basket_units | mean_discount_rate | median_discount_rate |
| --- | --- | --- | --- | --- | --- | --- |
| 29.1426 | 17.07 | 36.1013 | 942.8597 | 8.0 | 0.1346 | 0.1136 |

Empirical event probabilities use distinct baskets or prior-active household-periods as documented denominators:

| coupon_basket_probability | basket_over_50_probability | adjacent_retention_probability |
| --- | --- | --- |
| 0.0606 | 0.1661 | 0.886 |

- Average basket spend bootstrap 95% CI: (np.float64(28.997), np.float64(29.277))
- Household total spend bootstrap 95% CI: (np.float64(3102.6), np.float64(3350.263))
- Spearman correlations: {'basket_spend': {'basket_spend': 1.0, 'basket_units': 0.8148, 'discount_rate': 0.1274}, 'basket_units': {'basket_spend': 0.8148, 'basket_units': 1.0, 'discount_rate': 0.1426}, 'discount_rate': {'basket_spend': 0.1274, 'basket_units': 0.1426, 'discount_rate': 1.0}}
- Covariance matrix: {'basket_spend': {'basket_spend': 1303.3039, 'basket_units': 3071.8982, 'discount_rate': 0.1846}, 'basket_units': {'basket_spend': 3071.8982, 'basket_units': 11699286.6465, 'discount_rate': -94.6533}, 'discount_rate': {'basket_spend': 0.1846, 'basket_units': -94.6533, 'discount_rate': 0.0145}}

Correlation is not causation. Extreme quantities, customer value, product mix, and promotion exposure can confound relationships.

## Hypothesis Tests And Effect Sizes

1. H0: mean household-period spend is equal in early and late constructed periods. H1: means differ. Welch t=-19.228, p=0.0, Cohen's d=0.1508.
2. H0: eligible high- and low-discount category sales come from equal distributions. H1: distributions differ. Mann-Whitney U=24599.0, p=0.0, rank-biserial effect=0.4786.

Large samples can make small effects significant. Decisions require a business threshold after discount cost. Multiple comparisons raise false-positive risk.

## Matrix, Similarity, And PCA

The customer-category matrix has 2500 household rows and 308 category columns, sparsity 0.6282, and standardized inputs. Five PCA components explain [0.1652, 0.0319, 0.0262, 0.0168, 0.015] individually and 0.2551 cumulatively. This information loss makes PCA diagnostic only. Sampled nearest households [21, 90] have cosine similarity 0.8449; sparse purchasing can inflate similarity.

## Leakage-Safe Baseline Model

Logistic regression predicts final-13-week activity from earlier features. A deterministic stratified split has 1874 training and 625 holdout households. Imputation, rare and unknown-safe encoding, scaling, and fitting use training households only. Future-period holdout AUC is 0.91 across 62 columns. Top coefficients: [('categorical__age_desc_65+', -2.214), ('categorical__income_desc_125-149K', -1.885), ('categorical__age_desc_45-54', 1.757), ('categorical__age_desc_19-24', -1.493), ('categorical__homeowner_desc_Unknown', -1.412), ('categorical__hh_comp_desc_2 Adults Kids', 1.298), ('categorical__age_desc_25-34', 1.282), ('categorical__income_desc_75-99K', -1.172), ('categorical__hh_comp_desc_2 Adults No Kids', -1.158), ('numeric__spend_trend_change', 1.084)]. AUC is not calibration or causal impact.

## Experiment Power

Baseline four-week spend mean=126.417 and SD=172.027. Two-sided alpha=0.05, power=0.80, equal allocation, and a normal approximation produce:

| households_per_arm | mde_spend | mde_percent |
| --- | --- | --- |
| 250.0 | 43.08 | 34.08 |
| 500.0 | 30.46 | 24.1 |
| 1000.0 | 21.54 | 17.04 |
| 1500.0 | 17.59 | 13.91 |

Success requires a pre-registered net-value threshold.
