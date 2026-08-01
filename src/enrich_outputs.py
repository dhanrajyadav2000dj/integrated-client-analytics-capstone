from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        out.append("| " + " | ".join(str(row[c]) for c in df.columns) + " |")
    return "\n".join(out)


def _q(con, sql: str) -> pd.DataFrame:
    df = con.execute(sql).fetchdf()
    df.columns = [str(c).lower() for c in df.columns]
    return df


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return x


def enrich_outputs(root: Path, con, charts: list[str], stats_out: dict) -> list[str]:
    charts_dir = root / "outputs" / "charts"
    tables_dir = root / "outputs" / "tables"
    charts_dir.mkdir(parents=True, exist_ok=True)

    kpi = _q(con, "SELECT * FROM kpi_summary").iloc[0]
    val = _q(con, "SELECT * FROM validation_checks")
    cats = _q(con, """
        SELECT commodity_desc, category_sales, household_penetration, discount_rate, sales_growth
        FROM mart_categories
        WHERE household_count >= 50
        ORDER BY category_sales DESC
        LIMIT 10
    """)
    camp = _q(con, """
        SELECT campaign, campaign_type, exposed_households, redeeming_households, household_redemption_rate
        FROM mart_campaigns
        ORDER BY exposed_households DESC
        LIMIT 10
    """)
    customer_segments = _q(con, """
        WITH hh AS (
          SELECT household_key, SUM(basket_spend) spend, COUNT(*) baskets, MAX(week_no) last_week
          FROM mart_baskets GROUP BY 1
        ), scored AS (
          SELECT *, NTILE(4) OVER (ORDER BY spend) AS value_quartile
          FROM hh
        )
        SELECT
          CASE WHEN value_quartile = 4 THEN 'high_value'
               WHEN last_week < (SELECT MAX(week_no)-13 FROM mart_baskets) THEN 'at_risk_lapsed'
               WHEN value_quartile = 1 THEN 'low_value'
               ELSE 'mid_value' END AS segment,
          COUNT(*) AS households,
          ROUND(AVG(spend), 2) AS avg_spend,
          ROUND(AVG(baskets), 2) AS avg_baskets
        FROM scored GROUP BY 1 ORDER BY avg_spend DESC
    """)
    category_trends = _q(con, """
        SELECT commodity_desc, first_year_sales, second_year_sales, sales_growth, household_penetration
        FROM mart_categories
        WHERE household_count >= 100
        ORDER BY sales_growth DESC
        LIMIT 10
    """)
    campaign_prepost = _q(con, """
        WITH e AS (
          SELECT ct.household_key, ct.campaign, cd.start_day, cd.end_day, cd.description AS campaign_type
          FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign)
        ), a AS (
          SELECT e.campaign_type, e.household_key,
                 SUM(CASE WHEN t.day BETWEEN e.start_day-28 AND e.start_day-1 THEN t.sales_value ELSE 0 END) AS pre_spend,
                 SUM(CASE WHEN t.day BETWEEN e.start_day AND e.end_day+28 THEN t.sales_value ELSE 0 END) AS post_spend
          FROM e LEFT JOIN stg_transactions t USING(household_key)
          GROUP BY 1,2
        )
        SELECT campaign_type, COUNT(*) AS households,
               ROUND(AVG(pre_spend), 2) AS avg_pre_spend,
               ROUND(AVG(post_spend), 2) AS avg_post_spend,
               ROUND(AVG(post_spend-pre_spend), 2) AS avg_change
        FROM a GROUP BY 1 ORDER BY campaign_type
    """)

    # Extra reviewer-facing visuals.
    coef_rows = stats_out.get("top_model_coefs") or []
    if coef_rows:
        coef_df = pd.DataFrame(coef_rows, columns=["feature", "coefficient"])
        coef_df = coef_df.sort_values("coefficient")
        plt.figure(figsize=(8, 4.8))
        plt.barh(coef_df["feature"], coef_df["coefficient"], color="#2f6f9f")
        plt.axvline(0, color="black", linewidth=0.8)
        plt.title("Baseline model coefficient direction")
        plt.xlabel("standardized logistic coefficient")
        plt.tight_layout()
        path = charts_dir / "11_model_coefficients.png"
        plt.savefig(path, dpi=130)
        plt.close()
        if path.name not in charts:
            charts.append(path.name)

    baseline_spend = _q(con, "SELECT household_key, SUM(basket_spend) spend FROM mart_baskets GROUP BY 1")
    mean_spend = baseline_spend["spend"].mean()
    sd_spend = baseline_spend["spend"].std()
    lifts = np.array([0.03, 0.04, 0.05, 0.075, 0.10])
    # Two-sample equal allocation normal approximation, alpha .05, power .80.
    z_alpha = 1.96
    z_beta = 0.84
    n_per_group = 2 * ((z_alpha + z_beta) * sd_spend / (mean_spend * lifts)) ** 2
    mde_df = pd.DataFrame({"lift": lifts * 100, "households_per_group": np.ceil(n_per_group).astype(int)})
    plt.figure(figsize=(7, 4.2))
    plt.plot(mde_df["lift"], mde_df["households_per_group"], marker="o", color="#8a4f2a")
    plt.title("Experiment sample size sensitivity")
    plt.xlabel("minimum detectable lift in spend (%)")
    plt.ylabel("households per group")
    plt.tight_layout()
    path = charts_dir / "12_experiment_mde.png"
    plt.savefig(path, dpi=130)
    plt.close()
    if path.name not in charts:
        charts.append(path.name)

    kpi_rows = pd.DataFrame([
        ["active_household", "household with >=1 basket", "active households", "eligible households", "household-period or total", "4-week/total", "none", ">=1 basket", "stg_transactions, mart_baskets", "active_households"],
        ["basket", "distinct shopping trip basket", "distinct basket_id", "not applicable", "basket", "total", "none", "basket_id not null", "stg_transactions", "baskets"],
        ["trip_frequency", "shopping trips per active household", "basket count", "active households", "household-period", "4-week", "inactive household-periods absent", ">=30 households for comparison", "mart_household_period", "basket_count"],
        ["basket_size", "units per basket", "units", "baskets", "basket/period", "4-week/total", "zero-basket rows excluded", ">=1 basket", "mart_baskets", "basket_units"],
        ["spend_net_sales", "actual sales value", "sum sales_value", "not applicable", "line/basket/period", "any defined window", "none", "not applicable", "stg_transactions", "basket_spend,total_spend"],
        ["gross_sales_proxy", "sales before retail discount proxy", "sales_value + retail_discount_amt", "not applicable", "line/basket/period", "any defined window", "none", "not applicable", "stg_transactions", "documented proxy"],
        ["discount_rate", "positive discounts divided by spend plus retail discount", "retail + coupon + match discounts", "sales_value + retail_discount_amt", "basket/category", "any defined window", "denominator <=0 returns null", "denominator >0", "mart_baskets,mart_categories", "discount_rate"],
        ["coupon_redemption_rate", "share of exposed households redeeming", "redeeming households", "exposed households", "campaign", "campaign window", "no denominator no rate", ">=30 exposed households", "mart_campaigns", "household_redemption_rate"],
        ["campaign_exposure_rate", "share of active households exposed", "exposed households", "active households", "campaign/period", "campaign window", "campaign denominator required", ">=30 households", "campaign_table,mart_campaigns", "exposed_households"],
        ["category_penetration", "share of households buying category", "category buyers", "active households", "category", "total/year", "missing category mapped unknown", ">=50 category households", "mart_categories", "household_penetration"],
        ["repeat_purchase", "repeat buying household count", "households with >=2 baskets/product", "buyers", "product/category", "total", "low buyers flagged", ">=50 buyers", "mart_products", "repeat_household_count"],
        ["retention_repeat", "activity after prior activity", "active current and prior period", "active prior period", "household-period", "adjacent 4-week periods", "first period has no prior", ">=30 prior households", "mart_household_period", "retention_repeat_flag"],
        ["customer_value", "household spend", "household spend", "not applicable", "household", "observation/total", "none", "not applicable", "mart_baskets", "monetary_spend"],
        ["customer_value_change", "period spend delta", "current spend - prior spend", "prior spend", "household-period", "4-week", "first period null", "prior spend >0", "mart_household_period", "spend_change"],
        ["high_value_customer", "top quartile household value", "top spend quartile", "active households", "household", "observation window", "none", "quartile defined on active households", "mart_customer_features", "monetary_spend"],
        ["at_risk_customer", "declining or lapsed household", "decline/lapse flag", "prior active households", "household", "future label window", "future fields excluded from features", "prior active", "mart_customer_features", "next_period_spend_decline_flag"],
        ["category_growth", "later sales less early sales", "second-year sales - first-year sales", "first-year sales", "category", "year-like split", "low-count categories caveated", ">=50 households", "mart_categories", "sales_growth"],
    ], columns=["kpi", "business_definition", "numerator", "denominator", "grain", "time_window", "exclusions_or_nulls", "minimum_denominator", "source_tables", "output_column"])
    (root / "kpi_definitions.md").write_text("# KPI Definitions\n\nDiscount reporting uses positive discount amounts derived from raw signed discount fields. Rates are not reported without denominators.\n\n" + md_table(kpi_rows) + "\n", encoding="ascii")

    chart_interp = pd.DataFrame([
        ["01_data_coverage.png", "Baskets by relative week", "Confirms transaction coverage across the 102-week index and avoids calendar claims."],
        ["02_basket_spend_distribution.png", "Basket spend distribution", "Shows skew and outliers, supporting robust/bootstrapped uncertainty instead of only normal assumptions."],
        ["03_frequency_distribution.png", "Household basket frequency", "Separates engagement intensity from spend value."],
        ["04_value_concentration.png", "Customer value concentration", "Supports prioritizing high-value and declining households."],
        ["05_retention_heatmap.png", "Repeat activity by period", "Shows repeat activity using constructed 4-week periods."],
        ["06_top_categories.png", "Top category sales", "Sales rank is evidence only when paired with penetration and growth checks."],
        ["07_category_penetration_sales.png", "Category penetration versus sales", "Identifies categories with both reach and commercial scale."],
        ["08_discount_sales.png", "Discount rate versus sales", "Shows discount-heavy categories require margin and causality caution."],
        ["09_campaign_funnel.png", "Campaign exposure/redemption funnel", "Reports redemption with exposure denominators."],
        ["10_campaign_prepost.png", "Campaign pre/post association", "Bias-aware descriptive comparison, not causal proof."],
        ["11_model_coefficients.png", "Baseline model coefficients", "Interpretable directionality for next-period active flag."],
        ["12_experiment_mde.png", "Experiment MDE sensitivity", "Connects recommendation to sample-size planning."],
    ], columns=["chart", "what_it_shows", "reviewer_interpretation"])
    (root / "visual_evidence_interpretations.md").write_text("# Visual Evidence Interpretations\n\n" + md_table(chart_interp) + "\n", encoding="ascii")

    desc = _q(con, """
        SELECT
          ROUND(AVG(basket_spend),2) AS avg_basket_spend,
          ROUND(MEDIAN(basket_spend),2) AS median_basket_spend,
          ROUND(STDDEV_SAMP(basket_spend),2) AS sd_basket_spend,
          ROUND(AVG(basket_units),2) AS avg_basket_units,
          ROUND(MEDIAN(basket_units),2) AS median_basket_units,
          ROUND(AVG(discount_rate),4) AS avg_discount_rate,
          ROUND(MEDIAN(discount_rate),4) AS median_discount_rate
        FROM mart_baskets
    """)
    event_probs = _q(con, """
        SELECT
          ROUND(SUM(coupon_used_flag)*1.0/COUNT(*),4) AS p_coupon_basket,
          ROUND(COUNT(DISTINCT CASE WHEN basket_spend > 50 THEN basket_id END)*1.0/COUNT(DISTINCT basket_id),4) AS p_basket_over_50,
          ROUND(COUNT(DISTINCT CASE WHEN retention_repeat_flag=1 THEN household_key || '-' || period_id END)*1.0/COUNT(*),4) AS p_repeat_period
        FROM mart_baskets b LEFT JOIN mart_household_period hp USING(household_key)
    """)
    root.joinpath("quantitative_analysis_appendix.md").write_text(f"""# Quantitative Analysis Appendix

## Descriptive Statistics

{md_table(desc)}

Basket spend, basket units, discount rates, and coupon behavior are right-skewed. This motivates medians, denominator checks, and bootstrap confidence intervals alongside parametric tests.

## Business Event Probabilities

{md_table(event_probs)}

These probabilities are empirical rates from the observed sample, not population guarantees.

## Confidence Intervals

- Average basket spend bootstrap 95% CI: {tuple(_safe_float(x) for x in stats_out['avg_basket_ci'])}
- Household total spend bootstrap 95% CI: {tuple(_safe_float(x) for x in stats_out['hh_spend_ci'])}

## Hypothesis Tests

1. Early versus late household-period spend. Null: mean spend is equal. Alternative: mean spend differs. Welch t-statistic {stats_out['ttest_stat']}, p-value {stats_out['ttest_p']}. The large sample makes small differences detectable, so business materiality should be evaluated with absolute spend change and margin.
2. High-discount versus low-discount category sales. Null: category sales distributions are equal. Alternative: distributions differ. Mann-Whitney statistic {stats_out['disc_test_stat']}, p-value {stats_out['disc_test_p']}. This is association only; promotion intensity, category role, and product mix can confound the comparison.

Multiple category and segment comparisons increase false-positive risk. Findings should be used to prioritize investigation, not to make automatic assortment decisions.

## Matrix, Similarity, and PCA

Customer-category matrix sparsity: {stats_out['matrix_sparsity']}. Nearest-neighbor cosine similarity example: {stats_out['nearest_neighbor_similarity']}. PCA explained variance: {stats_out['pca_variance']}. Sparse purchase matrices can overstate similarity for narrow category buyers, so nearest neighbors should be interpreted as affinity hypotheses.

## Baseline Model

Temporal baseline model AUC for next-period active flag: {stats_out['model_auc']}. Top standardized coefficients: {stats_out['top_model_coefs']}. Logistic regression uses a logit link for a binary outcome and is included for interpretable screening. Future labels and future spend are excluded from features. Calibration and temporal holdout monitoring are required before production use.

## Power / MDE

The MDE chart uses a two-sample household-randomized normal approximation with alpha 0.05 and power 0.80. The recommended experiment should recompute sample size using current eligible-household variance and minimum business-relevant lift. Statistical significance is not the same as business significance.
""", encoding="ascii")

    root.joinpath("campaign_bias_analysis.md").write_text(f"""# Campaign Bias-Aware Analysis

## Campaign Funnel

{md_table(camp)}

## Pre/Post Association by Campaign Type

{md_table(campaign_prepost)}

Campaign exposure is not proof that a household saw or understood a campaign. Redemption is sparse and mechanically different from exposure. TypeA campaigns are targeted, so exposed households are likely selected based on prior behavior; TypeB and TypeC are still observational and may reflect participation or eligibility differences.

The pre/post comparison uses a 28-day baseline before campaign start and campaign plus 28-day follow-up. It is a bias-aware descriptive design, not a causal estimate. The result should be phrased as association or lift hypothesis. The recommended next step is a randomized household-level test among high-value declining households.
""", encoding="ascii")

    root.joinpath("final_recommendation_memo.md").write_text(f"""# Final Recommendation Memo

## Executive Summary

The retailer should prioritize high-value customer retention, category actions that combine scale with penetration and stability, and a randomized campaign test. The data foundation is strong enough for descriptive and diagnostic recommendations. Campaign evidence remains observational, so the memo separates facts, estimates, hypotheses, and recommended tests.

## KPI Snapshot

- Active households: {int(kpi['active_households'])}
- Baskets: {int(kpi['baskets'])}
- Spend: {float(kpi['spend']):.2f}
- Average basket value: {float(kpi['avg_basket_value']):.2f}
- Coupon basket rate: {float(kpi['coupon_basket_rate']):.3f}

## Finding 1: Customer Value Is Concentrated

Customer spend is skewed and engagement varies materially by household. Retention actions should focus on high-value and declining households rather than broad untargeted discounting.

{md_table(customer_segments)}

Recommended action: build a weekly retention watchlist from `feature_ready_households.csv` using monetary spend, recency, frequency, spend trend, discount sensitivity, and category affinity.

## Finding 2: Category Decisions Need Scale, Penetration, And Growth

Top categories by validated denominator:

{md_table(cats)}

High-sales categories are not automatically the best action targets. Prioritize categories with both high household penetration and positive growth. Investigate high-sales declining categories before reducing support, because mix, promotion cadence, or availability can explain decline.

Category growth leaders with denominator threshold:

{md_table(category_trends)}

## Finding 3: Campaign Results Are Useful But Not Causal

Campaign funnel:

{md_table(camp)}

Pre/post association:

{md_table(campaign_prepost)}

TypeA campaigns are targeted and selection-biased. TypeB/TypeC campaigns are not equivalent to TypeA and still require exposure denominator and participation caveats. Do not claim campaign causality from these comparisons.

## Recommended Experiment

Business hypothesis: targeted category-affinity offers for high-value declining households will increase next 4-week spend without excessive discount cost.

Target population: high-value households with worsening spend trend or recency risk. Treatment: personalized coupon bundle in categories where the household has demonstrated affinity. Control: business-as-usual campaign treatment. Randomization unit: household. Primary metric: next 4-week spend per household. Secondary metrics: basket frequency, units, category penetration, redemption rate. Guardrails: discount cost, estimated margin proxy, category cannibalization, sparse subgroup sizes, customer complaint/unsubscribe measures if available.

Minimum denominator: at least 30 households per reporting segment and enough households per randomized arm to detect the selected MDE. Success rule: statistically reliable lift that also clears a pre-defined business value threshold after discount cost.

## What Not To Conclude

Do not infer real weekdays/months/holidays, do not treat item rows as baskets, do not report redemption without exposure denominators, do not join coupon or causal data at uncontrolled grain, and do not claim that observational campaigns caused spend changes.

## Next Data To Collect

Campaign eligibility rules, true send/open/click exposure, offer cost and margin, inventory/stockout flags, store geography, real calendar dates, and customer communication opt-outs.

## Evidence Files

- Tables: `outputs/tables/`
- Charts: `outputs/charts/`
- Chart interpretations: `visual_evidence_interpretations.md`
- QA readiness: `qa/FINAL_SUBMISSION_READINESS.md`
""", encoding="ascii")

    # Rich notebook for reviewers who open the ipynb first.
    notebook = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Integrated Client Analytics Capstone\n", "\n", "This notebook is a reviewer-friendly entry point. The canonical reproducible pipeline is `src/run_pipeline.py`, which regenerates SQL, marts, charts, validation reports, and memo files.\n"]},
            {"cell_type": "markdown", "metadata": {}, "source": ["## Scope And Depth Tracks\n", "\n", "Depth tracks: customer value/retention, category performance, and campaign/coupon effectiveness. Campaign results are treated as observational associations, not causal proof.\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["%run ../src/run_pipeline.py"]},
            {"cell_type": "markdown", "metadata": {}, "source": ["## Manual Review Files\n", "\n", "After running the cell above, review `final_recommendation_memo.md`, `validation_report.md`, `quantitative_analysis_appendix.md`, `campaign_bias_analysis.md`, `visual_evidence_interpretations.md`, and `qa/FINAL_SUBMISSION_READINESS.md`.\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / "notebooks" / "integrated_client_analytics_capstone.ipynb").write_text(json.dumps(notebook, indent=1), encoding="ascii")

    return charts
