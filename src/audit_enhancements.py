from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def q(con, sql):
    frame = con.execute(sql).fetchdf()
    frame.columns = [str(column).lower() for column in frame.columns]
    return frame


def md(frame, decimals=4):
    display = frame.copy()
    for column in display.select_dtypes(include=[np.number]).columns:
        display[column] = display[column].round(decimals)
    headers = [str(column) for column in display.columns]
    rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in display.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in display.columns) + " |")
    return "\n".join(rows)


def apply_sql_enhancements(root: Path, con):
    con.execute((root / "sql" / "05_strengthen_analytics_and_validation.sql").read_text(encoding="ascii"))


def repair_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.drop(columns=["household_key_1"], errors="ignore")
    demographic_columns = [
        column for column in [
            "age_desc", "marital_status_code", "income_desc", "homeowner_desc",
            "hh_comp_desc", "household_size_desc", "kid_category_desc",
        ] if column in frame.columns
    ]
    frame["missing_demographic_flag"] = (
        frame[demographic_columns].isna().all(axis=1).astype(int)
        if demographic_columns else 1
    )
    return frame


def enhance_statistics(con, features: pd.DataFrame, base_stats: dict) -> dict:
    result = dict(base_stats)
    features = features.sort_values('household_key').reset_index(drop=True)
    labels = ["future_spend", "next_period_active_flag", "next_period_spend_decline_flag"]
    predictors = features.drop(columns=labels + ["household_key", "household_key_1"], errors="ignore")
    numeric_columns = predictors.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = [column for column in predictors.columns if column not in numeric_columns]
    preprocessing = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric_columns),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20)),
        ]), categorical_columns),
    ])
    model = Pipeline([
        ("preprocessing", preprocessing),
        ('model', LogisticRegression(max_iter=2000, class_weight='balanced', random_state=42)),
    ])
    y = features["next_period_active_flag"].astype(int)
    indices = np.arange(len(features))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.25, random_state=42, stratify=y
    )
    model.fit(predictors.iloc[train_idx], y.iloc[train_idx])
    probabilities = model.predict_proba(predictors.iloc[test_idx])[:, 1]
    result["model_auc"] = round(float(roc_auc_score(y.iloc[test_idx], probabilities)), 3)
    result["model_train_rows"] = int(len(train_idx))
    result["model_test_rows"] = int(len(test_idx))
    names = model.named_steps["preprocessing"].get_feature_names_out()
    coefficients = model.named_steps["model"].coef_[0]
    top = sorted(zip(names, coefficients), key=lambda value: abs(value[1]), reverse=True)[:10]
    result["top_model_coefs"] = [(str(name), round(float(value), 3)) for name, value in top]
    result["model_feature_count"] = int(len(names))

    household_period = q(con, "SELECT * FROM mart_household_period")
    midpoint = household_period["period_id"].median()
    early = household_period.loc[household_period.period_id <= midpoint, "total_spend"]
    late = household_period.loc[household_period.period_id > midpoint, "total_spend"]
    pooled_sd = math.sqrt((early.var(ddof=1) + late.var(ddof=1)) / 2)
    result["spend_effect_size_cohens_d"] = round(float((late.mean() - early.mean()) / pooled_sd), 4)

    categories = q(con, "SELECT * FROM mart_categories WHERE household_count>=50")
    median_discount = categories.discount_rate.median()
    high = categories.loc[categories.discount_rate >= median_discount, "category_sales"].dropna()
    low = categories.loc[categories.discount_rate < median_discount, "category_sales"].dropna()
    u_stat = stats.mannwhitneyu(high, low, alternative="two-sided").statistic
    result["discount_rank_biserial"] = round(float(2 * u_stat / (len(high) * len(low)) - 1), 4)

    basket_metrics = q(con, "SELECT basket_spend,basket_units,discount_rate FROM mart_baskets")
    result["basket_correlations"] = basket_metrics.corr(method="spearman").round(4).to_dict()
    result["basket_covariance"] = basket_metrics.cov().round(4).to_dict()

    matrix = q(con, """
        SELECT household_key, COALESCE(p.commodity_desc,'UNKNOWN') AS commodity_desc,
               SUM(sales_value) AS spend
        FROM stg_transactions t LEFT JOIN stg_products p USING(product_id)
        GROUP BY 1,2
    """).pivot(index="household_key", columns="commodity_desc", values="spend").fillna(0)
    scaled = StandardScaler(with_mean=False).fit_transform(matrix)
    component_count = min(5, scaled.shape[0], scaled.shape[1])
    pca = PCA(n_components=component_count, random_state=42).fit(scaled)
    similarity_sample = scaled[: min(250, scaled.shape[0])]
    similarities = cosine_similarity(similarity_sample)
    np.fill_diagonal(similarities, -1)
    nearest_position = np.unravel_index(np.argmax(similarities), similarities.shape)
    result.update({
        "matrix_rows": int(matrix.shape[0]),
        "matrix_columns": int(matrix.shape[1]),
        "matrix_sparsity": round(float((matrix.to_numpy() == 0).mean()), 4),
        "pca_variance": pca.explained_variance_ratio_.round(4).tolist(),
        "pca_cumulative_variance": round(float(pca.explained_variance_ratio_.sum()), 4),
        "nearest_neighbor_similarity": round(float(similarities[nearest_position]), 4),
        "nearest_neighbor_households": [
            int(matrix.index[nearest_position[0]]), int(matrix.index[nearest_position[1]])
        ],
    })

    period_spend = household_period.loc[
        household_period.period_id < household_period.period_id.max(), "total_spend"
    ]
    mean_spend = float(period_spend.mean())
    sd_spend = float(period_spend.std(ddof=1))
    result["experiment_baseline_mean"] = round(mean_spend, 3)
    result["experiment_baseline_sd"] = round(sd_spend, 3)
    result["mde_rows"] = [
        {
            "households_per_arm": n,
            "mde_spend": round((1.96 + 0.84) * math.sqrt(2) * sd_spend / math.sqrt(n), 2),
            "mde_percent": round(
                100 * (1.96 + 0.84) * math.sqrt(2) * sd_spend / math.sqrt(n) / mean_spend, 2
            ),
        }
        for n in [250, 500, 1000, 1500]
    ]
    return result


def write_enhanced_outputs(root: Path, con, charts: list[str], metrics: dict):
    tables_dir = root / "outputs" / "tables"
    extra_tables = [
        "mart_promotion_performance", "mart_category_period", "mart_category_diagnostics",
        "customer_period_summary", "customer_retention_matrix",
        "campaign_bias_comparison", "campaign_segment_analysis",
    ]
    for table in extra_tables:
        frame = q(con, f'SELECT * FROM {table}')
        frame.sort_values(list(frame.columns)).to_csv(
            tables_dir / f'{table}.csv', index=False
        )

    descriptive = q(con, """
        SELECT AVG(basket_spend) AS mean_basket_spend, MEDIAN(basket_spend) AS median_basket_spend,
               STDDEV_SAMP(basket_spend) AS sd_basket_spend,
               AVG(basket_units) AS mean_basket_units, MEDIAN(basket_units) AS median_basket_units,
               AVG(discount_rate) AS mean_discount_rate, MEDIAN(discount_rate) AS median_discount_rate
        FROM mart_baskets
    """)
    event_probabilities = q(con, """
        SELECT SUM(coupon_used_flag)*1.0/COUNT(*) AS coupon_basket_probability,
               COUNT(*) FILTER(WHERE basket_spend>50)*1.0/COUNT(*) AS basket_over_50_probability,
               (SELECT SUM(retained_households)*1.0/NULLIF(SUM(prior_active_households),0)
                FROM customer_period_summary) AS adjacent_retention_probability
        FROM mart_baskets
    """)
    validation = q(con, "SELECT * FROM validation_checks")
    promotions = q(con, "SELECT * FROM mart_promotion_performance ORDER BY promotion_status")
    campaign_funnel = q(con, """
        SELECT campaign,campaign_type,exposed_households,redeeming_households,
               redemption_count,household_redemption_rate
        FROM mart_campaigns ORDER BY exposed_households DESC LIMIT 10
    """)
    category_sample = q(con, """
        SELECT department,commodity_desc,category_sales,household_count,household_penetration,
               sales_growth,sales_growth_rate,sales_coefficient_of_variation,
               household_engagement_change,high_sales_declining_flag
        FROM mart_category_diagnostics WHERE household_count>=50
        ORDER BY category_sales DESC LIMIT 15
    """)
    segments = q(con, """
        WITH hh AS (
          SELECT household_key,SUM(basket_spend) spend,COUNT(*) baskets,MAX(week_no) last_week
          FROM mart_baskets GROUP BY 1
        ), scored AS (SELECT *,NTILE(4) OVER(ORDER BY spend) value_quartile FROM hh)
        SELECT CASE WHEN value_quartile=4 THEN 'high_value'
                    WHEN last_week<(SELECT MAX(week_no)-13 FROM mart_baskets) THEN 'at_risk_lapsed'
                    WHEN value_quartile=1 THEN 'low_value' ELSE 'mid_value' END AS segment,
               COUNT(*) households,AVG(spend) avg_spend,AVG(baskets) avg_baskets
        FROM scored GROUP BY 1 ORDER BY avg_spend DESC
    """)
    kpi = q(con, "SELECT * FROM kpi_summary").iloc[0]
    mde = pd.DataFrame(metrics["mde_rows"])
    mde.to_csv(tables_dir / "experiment_mde.csv", index=False)

    root.joinpath("quantitative_analysis_appendix.md").write_text(f"""# Quantitative Analysis Appendix

## Distribution And Probability Evidence

Basket spend and units are right-skewed. Extreme source quantities make medians important alongside means.

{md(descriptive)}

Empirical event probabilities use distinct baskets or prior-active household-periods as documented denominators:

{md(event_probabilities)}

- Average basket spend bootstrap 95% CI: {metrics['avg_basket_ci']}
- Household total spend bootstrap 95% CI: {metrics['hh_spend_ci']}
- Spearman correlations: {metrics['basket_correlations']}
- Covariance matrix: {metrics['basket_covariance']}

Correlation is not causation. Extreme quantities, customer value, product mix, and promotion exposure can confound relationships.

## Hypothesis Tests And Effect Sizes

1. H0: mean household-period spend is equal in early and late constructed periods. H1: means differ. Welch t={metrics['ttest_stat']}, p={metrics['ttest_p']}, Cohen's d={metrics['spend_effect_size_cohens_d']}.
2. H0: eligible high- and low-discount category sales come from equal distributions. H1: distributions differ. Mann-Whitney U={metrics['disc_test_stat']}, p={metrics['disc_test_p']}, rank-biserial effect={metrics['discount_rank_biserial']}.

Large samples can make small effects significant. Decisions require a business threshold after discount cost. Multiple comparisons raise false-positive risk.

## Matrix, Similarity, And PCA

The customer-category matrix has {metrics['matrix_rows']} household rows and {metrics['matrix_columns']} category columns, sparsity {metrics['matrix_sparsity']}, and standardized inputs. Five PCA components explain {metrics['pca_variance']} individually and {metrics['pca_cumulative_variance']} cumulatively. This information loss makes PCA diagnostic only. Sampled nearest households {metrics['nearest_neighbor_households']} have cosine similarity {metrics['nearest_neighbor_similarity']}; sparse purchasing can inflate similarity.

## Leakage-Safe Baseline Model

Logistic regression predicts final-13-week activity from earlier features. A deterministic stratified split has {metrics['model_train_rows']} training and {metrics['model_test_rows']} holdout households. Imputation, rare and unknown-safe encoding, scaling, and fitting use training households only. Future-period holdout AUC is {metrics['model_auc']} across {metrics['model_feature_count']} columns. Top coefficients: {metrics['top_model_coefs']}. AUC is not calibration or causal impact.

## Experiment Power

Baseline four-week spend mean={metrics['experiment_baseline_mean']} and SD={metrics['experiment_baseline_sd']}. Two-sided alpha=0.05, power=0.80, equal allocation, and a normal approximation produce:

{md(mde, 2)}

Success requires a pre-registered net-value threshold.
""", encoding="ascii")

    root.joinpath("campaign_bias_analysis.md").write_text(f"""# Campaign, Coupon, And Promotion Analysis

## Validated Funnel

{md(campaign_funnel)}

Rates divide distinct redeeming households by distinct exposed households. TypeA is separate because targeting creates stronger selection. TypeB and TypeC remain non-random. Exposure is not proof of viewing, and sparse redemption requires denominators.

## Bias-Aware Comparison

campaign_bias_comparison.csv uses equal 28-day pre and post windows and stratifies by campaign type, prior-spend quartile, and redemption status. campaign_segment_analysis.csv reports redemption by customer segment. These controls do not remove self-selection, regression to the mean, unobserved eligibility, inventory, or concurrent activity. Results are associations, not causal lift.

## Promotion Evidence

{md(promotions)}

Causal data is deduplicated to product-store-week before joining transactions aggregated at exactly that grain. Product, store, timing, and merchandising selection confound the promoted comparison. Row, sales, and unit reconciliation is recorded in validation_checks.csv.
""", encoding="ascii")

    root.joinpath("customer_analysis.md").write_text(f"""# Customer Value And Retention Analysis

Four-week periods come from WEEK_NO and are not calendar months. The household-period mart includes inactive periods; retention requires activity in two adjacent periods. The incomplete final period is flagged.

{md(segments, 2)}

customer_period_summary.csv contains active, new, returning, prior-active, retained counts, and denominators. customer_retention_matrix.csv contains cohort retention. Bootstrap intervals are in the quantitative appendix.
""", encoding="ascii")

    root.joinpath("category_analysis.md").write_text(f"""# Product And Category Analysis

Categories use department plus commodity. Comparisons require at least 50 buying households. Growth compares weeks 1-52 with weeks 53-102; the latter window is shorter, so growth is descriptive.

{md(category_sample)}

mart_category_diagnostics.csv adds penetration, growth rate, engagement change, period-sales variation, small-group flags, and declining flags. Recommendations combine scale, reach, direction, and stability.
""", encoding="ascii")

    root.joinpath("validation_report.md").write_text(f"""# Validation Report

All values are calculated from current raw files. Boolean controls must be true; issue counts remain visible.

{md(validation)}

## Data-Quality Decisions

| Finding | Action | Treatment |
| --- | --- | --- |
| Signed discounts | Fixed in staging | Positive amounts; gross equals net plus all discounts |
| Zero sales or quantity | Flagged and retained | Visible; no blind deletion |
| Extreme quantities | Retained with caveat | Medians and bootstrap used |
| Missing demographics | Retained with indicator | No blanket dropna |
| Duplicate bridge keys | Pre-aggregated | Exact-grain fan-out controls |
| Sparse categories and redemption | Thresholded | Denominators documented |
| Incomplete final period | Flagged | No unqualified comparison |

Financial reconciliations use tolerance 0.01. TRANS_TIME is HHMM only. DAY and WEEK_NO are unanchored indexes.
""", encoding="ascii")

    root.joinpath("feature_dictionary.md").write_text("""# Feature Dictionary And Leakage Contract

Scoring grain is one household. Observation weeks end 13 weeks before max week; labels use only the final 13 weeks.

| Group | Columns | Use |
| --- | --- | --- |
| Recency, frequency, value | recency_weeks, frequency_baskets, monetary_spend, avg_line_sales | Observation |
| Composition | total_units, product_diversity, category_diversity, top_department_share | Observation |
| Discount and engagement | discount_amount, discount_rate, coupon_line_count, coupon_engagement, campaign_exposure_count | Observation |
| Trend | first_half_spend, second_half_spend, spend_trend_change | Observation |
| Demographics | age, income, home, household fields, missing_demographic_flag | Static subset |
| Labels | future_spend, next_period_active_flag, next_period_spend_decline_flag | Outcome only |

A stratified household holdout is used. Numeric median imputation, categorical imputation, rare grouping with minimum frequency 20, unknown-safe one-hot encoding, and scaling fit training households only. The fitted transformer aligns holdout columns. Duplicate households and infinite values are tested.
""", encoding="ascii")

    root.joinpath("performance_and_scalability_note.md").write_text("""# Performance And Scalability Note

The largest source is causal_data with 36,786,524 rows; transactions have 2,595,732 item lines. DuckDB handles heavy staging and aggregation. Transactions reduce to product-store-week before promotion joins, and duplicate causal keys collapse at the same grain. Row, sales, and unit controls prevent fan-out.

Production should partition by week, cluster by product-store-week and household-week, materialize staging, refresh incrementally, enforce bridge uniqueness, and monitor workloads. Do not load full causal data into pandas or join coupons directly to item rows.
""", encoding="ascii")

    root.joinpath("assumptions_and_limitations.md").write_text("""# Assumptions And Limitations

- DAY and WEEK_NO are relative indexes; real dates, weekdays, months, holidays, and seasons cannot be inferred.
- Four-week and 13-week windows are constructed; the incomplete final period is flagged.
- Sales value is net spend. Positive discounts are absolute raw values. Gross sales is net plus all discounts.
- Active means at least one basket. Retention means active in adjacent four-week periods.
- Categories use department plus commodity; unknowns remain.
- Demographics cover a subset and use a missingness indicator.
- Exposure does not prove viewing. TypeA has stronger targeting bias than TypeB or TypeC.
- Coupon and causal bridges are pre-aggregated before fact joins.
- Campaign and promotion comparisons are observational and vulnerable to confounding.
- Labels use the final 13 weeks; predictors stop earlier and preprocessing fits training households only.
- Sparse groups, extreme quantities, and local compute limit inference. Randomization is required for causality.
""", encoding="ascii")

    root.joinpath("final_recommendation_memo.md").write_text(f"""# Final Recommendation Memo

## Executive Summary

Prioritize a retention test for high-value declining households, manage categories using scale plus stability, and treat marketing results as hypotheses. The corrected layer contains {int(kpi.active_households)} active households, {int(kpi.baskets)} baskets, net spend {float(kpi.spend):.2f}, and average basket value {float(kpi.avg_basket_value):.2f}.

## Customer Finding

{md(segments, 2)}

The complete period spine measures adjacent retention and flags the incomplete final period. Operate a watchlist from recency, frequency, value, trend, discount sensitivity, and affinity.

## Category Finding

Use mart_category_diagnostics.csv to require adequate counts, penetration, direction, and stability. High sales alone is insufficient. The second comparison window is shorter, so investigate availability, mix, and promotions before acting.

## Marketing Finding

{md(campaign_funnel)}

Campaign windows are equal length and stratified by prior value. Promotion joins use exact product-store-week keys and reconcile totals. Selection and product/store mix prevent causal claims.

## Recommended Experiment

Hypothesis: affinity offers increase next four-week spend among eligible high-value declining households after discount cost. Randomize households to offer or business-as-usual. Primary metric is spend per eligible household. Secondary metrics are baskets, units, penetration, and redemption. Guardrails are discount cost, margin proxy, cannibalization, complaints, opt-outs, sample-ratio mismatch, missing outcomes, and contamination.

Use alpha 0.05, power 0.80, and experiment_mde.csv for sizing. Require 30 households in reported segments. Success requires statistical reliability and a pre-registered net-value threshold.

## Do Not Conclude And Next Data

Do not infer calendar seasonality, equate lines with baskets, report rates without denominators, or claim campaign causality. Collect delivery/open data, eligibility, cost and margin, inventory, geography, dates, opt-outs, and randomized assignment.
""", encoding="ascii")
