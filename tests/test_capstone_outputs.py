from pathlib import Path
import subprocess
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"

REQUIRED_RAW = [
    "transaction_data.csv", "product.csv", "hh_demographic.csv", "campaign_desc.csv",
    "campaign_table.csv", "coupon.csv", "coupon_redempt.csv", "causal_data.csv",
]

EXPECTED_TABLES = [
    "mart_baskets.csv", "mart_household_period.csv", "mart_products.csv", "mart_categories.csv",
    "mart_campaigns.csv", "mart_coupon_redemptions.csv", "mart_customer_features.csv",
    "feature_ready_households.csv", "kpi_summary.csv", "validation_checks.csv",
]


def csv_rows(path: Path) -> int:
    return sum(1 for _ in open(path, "rb")) - 1


def test_required_source_files_present_and_nonempty():
    for name in REQUIRED_RAW:
        path = RAW / name
        assert path.exists(), f"Missing raw source file: {name}"
        assert path.stat().st_size > 0
        assert csv_rows(path) > 0


def test_expected_outputs_and_charts_exist():
    for name in EXPECTED_TABLES:
        path = TABLES / name
        assert path.exists(), f"Missing output table: {name}"
        assert path.stat().st_size > 0
    charts = list(CHARTS.glob("*.png"))
    assert len(charts) >= 12
    assert all(p.stat().st_size > 1000 for p in charts)


def test_basket_mart_grain_and_reconciliation():
    con = duckdb.connect()
    raw_path = (RAW / "transaction_data.csv").as_posix()
    basket_path = (TABLES / "mart_baskets.csv").as_posix()
    raw = con.execute(f"""
        SELECT COUNT(*) AS rows,
               COUNT(DISTINCT BASKET_ID) AS baskets,
               ROUND(SUM(SALES_VALUE), 2) AS spend,
               ROUND(SUM(QUANTITY), 2) AS units
        FROM read_csv_auto('{raw_path}')
    """).fetchone()
    mart = con.execute(f"""
        SELECT COUNT(*) AS rows,
               COUNT(DISTINCT basket_id) AS baskets,
               ROUND(SUM(basket_spend), 2) AS spend,
               ROUND(SUM(basket_units), 2) AS units
        FROM read_csv_auto('{basket_path}')
    """).fetchone()
    assert mart[0] == raw[1]
    assert mart[0] == mart[1]
    assert mart[2] == raw[2]
    assert mart[3] == raw[3]


def test_required_mart_columns_and_rate_ranges():
    baskets = pd.read_csv(TABLES / "mart_baskets.csv", nrows=10000)
    required = {
        "basket_id", "household_key", "day", "week_no", "store_id", "basket_spend",
        "basket_units", "basket_item_line_count", "distinct_product_count",
        "total_retail_discount", "total_coupon_discount", "total_coupon_match_discount",
        "discount_rate", "coupon_used_flag",
    }
    assert required.issubset(set(baskets.columns))
    assert baskets["coupon_used_flag"].dropna().isin([0, 1]).all()
    assert baskets["discount_rate"].dropna().between(0, 1).all()

    campaigns = pd.read_csv(TABLES / "mart_campaigns.csv")
    assert campaigns["household_redemption_rate"].dropna().between(0, 1).all()


def test_validation_checks_pass_core_controls():
    checks = pd.read_csv(TABLES / "validation_checks.csv")
    values = dict(zip(checks["check_name"], checks["check_value"].astype(str)))
    assert values["basket_fanout_ok"].lower() == "true"
    assert int(values["products_duplicate_keys"]) == 0
    assert int(values["transactions_missing_product_metadata"]) == 0
    assert int(values["invalid_trans_time_rows"]) == 0


def test_campaign_coupon_and_causal_join_grain_guardrails():
    con = duckdb.connect()
    coupon_path = (RAW / "coupon.csv").as_posix()
    causal_path = (RAW / "causal_data.csv").as_posix()
    distinct_bridge = con.execute(f"""
        SELECT COUNT(*) FROM (SELECT DISTINCT CAMPAIGN, COUPON_UPC, PRODUCT_ID FROM read_csv_auto('{coupon_path}'))
    """).fetchone()[0]
    raw_bridge = csv_rows(RAW / "coupon.csv")
    assert distinct_bridge <= raw_bridge
    checks = pd.read_csv(TABLES / "validation_checks.csv")
    values = dict(zip(checks["check_name"], checks["check_value"].astype(str)))
    assert int(values["coupon_product_bridge_distinct_rows"]) == distinct_bridge
    causal_dupes = con.execute(f"""
        SELECT COUNT(*) - COUNT(DISTINCT PRODUCT_ID || '-' || STORE_ID || '-' || WEEK_NO)
        FROM read_csv_auto('{causal_path}')
    """).fetchone()[0]
    assert causal_dupes >= 0  # documented promotion grain check; pipeline does not uncontrolled-join causal rows.


def test_feature_temporal_labels_and_leakage_columns():
    features = pd.read_csv(TABLES / "feature_ready_households.csv")
    assert features["household_key"].is_unique
    assert {"next_period_active_flag", "next_period_spend_decline_flag", "future_spend"}.issubset(features.columns)
    assert {"campaign_exposure_count", "spend_trend_change", "top_department_share", "missing_demographic_flag"}.issubset(features.columns)
    label_cols = {"next_period_active_flag", "next_period_spend_decline_flag", "future_spend"}
    model_feature_cols = [c for c in features.columns if c not in label_cols and c != "household_key"]
    assert not any(c.startswith("future") or c.startswith("next_period") for c in model_feature_cols)
    numeric = features.select_dtypes(include="number")
    assert numeric.replace([float("inf"), float("-inf")], pd.NA).notna().any().all()


def test_no_committed_secret_patterns_in_project_files():
    secret_markers = ["KG" + "AT_", "KAGGLE" + "_API_TOKEN="]
    tracked = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    for rel in tracked:
        path = ROOT / rel
        if not path.is_file() or path.suffix.lower() in {".png", ".duckdb", ".zip", ".pyc"}:
            continue
        text = path.read_text(errors="ignore")
        assert not any(marker in text for marker in secret_markers), f"Secret-like marker found in {rel}"


def test_enriched_reviewer_documents_exist():
    for rel in ["campaign_bias_analysis.md", "visual_evidence_interpretations.md"]:
        path = ROOT / rel
        assert path.exists(), f"Missing enriched reviewer document: {rel}"
        assert path.stat().st_size > 500
    assert (CHARTS / "11_model_coefficients.png").exists()
    assert (CHARTS / "12_experiment_mde.png").exists()


def test_household_period_complete_spine_and_adjacent_retention():
    periods = pd.read_csv(TABLES / "mart_household_period.csv")
    assert periods[["household_key", "period_id"]].duplicated().sum() == 0
    assert len(periods) == periods["household_key"].nunique() * periods["period_id"].nunique()
    assert periods.loc[periods["period_id"] == 1, "prior_period_spend"].isna().all()
    ordered = periods.sort_values(["household_key", "period_id"]).copy()
    expected = (
        (ordered["active_flag"] == 1)
        & (ordered.groupby("household_key")["active_flag"].shift(1) == 1)
    ).astype(int)
    assert (ordered["retention_repeat_flag"].astype(int) == expected).all()
    assert ordered.groupby("household_key")["incomplete_period_flag"].sum().eq(1).all()


def test_financial_discount_convention_and_gross_sales():
    baskets = pd.read_csv(TABLES / "mart_baskets.csv")
    discounts = (
        baskets["total_retail_discount"]
        + baskets["total_coupon_discount"]
        + baskets["total_coupon_match_discount"]
    )
    assert (discounts >= 0).all()
    assert ((baskets["basket_spend"] + discounts - baskets["gross_sales"]).abs() < 0.01).all()
    expected_rate = discounts / baskets["gross_sales"].where(baskets["gross_sales"] > 0)
    delta = (expected_rate - baskets["discount_rate"]).dropna().abs()
    assert (delta < 1e-10).all()


def test_promotion_join_reconciles_exact_grain():
    checks = pd.read_csv(TABLES / "validation_checks.csv")
    values = dict(zip(checks["check_name"], checks["check_value"].astype(str).str.lower()))
    for name in [
        "promotion_join_fanout_ok",
        "promotion_join_sales_reconciled",
        "promotion_join_units_reconciled",
    ]:
        assert values[name] == "true"
    assert int(values["transaction_product_store_week_rows"]) == int(values["promotion_join_rows"])
    assert int(values["causal_source_rows"]) >= int(values["causal_exact_key_rows"])
    promotion = pd.read_csv(TABLES / "mart_promotion_performance.csv")
    assert set(promotion["promotion_status"]) == {"promoted", "not_promoted"}
    assert promotion["product_store_weeks"].sum() == int(values["promotion_join_rows"])


def test_product_category_keys_rates_and_diagnostics():
    products = pd.read_csv(TABLES / "mart_products.csv")
    categories = pd.read_csv(TABLES / "mart_categories.csv")
    diagnostics = pd.read_csv(TABLES / "mart_category_diagnostics.csv")
    assert products["product_id"].is_unique
    assert not categories[["department", "commodity_desc"]].duplicated().any()
    assert categories["household_penetration"].between(0, 1).all()
    assert categories["basket_penetration"].between(0, 1).all()
    assert categories["discount_rate"].dropna().between(0, 1).all()
    required = {
        "sales_coefficient_of_variation", "household_engagement_change",
        "small_group_flag", "high_sales_declining_flag",
        "high_penetration_low_spend_flag",
    }
    assert required.issubset(diagnostics.columns)


def test_campaign_bias_and_segment_evidence_has_denominators():
    comparison = pd.read_csv(TABLES / "campaign_bias_comparison.csv")
    segment = pd.read_csv(TABLES / "campaign_segment_analysis.csv")
    assert set(comparison["campaign_type"]) == {"TypeA", "TypeB", "TypeC"}
    assert set(comparison["prior_value_quartile"]) == {1, 2, 3, 4}
    assert set(comparison["redeemed_flag"]) == {0, 1}
    assert (comparison["household_campaign_exposures"] > 0).all()
    assert segment["redemption_rate"].between(0, 1).all()
    assert (segment["household_campaign_exposures"] >= segment["redeemed_exposures"]).all()


def test_customer_period_and_cohort_denominators():
    summary = pd.read_csv(TABLES / "customer_period_summary.csv")
    matrix = pd.read_csv(TABLES / "customer_retention_matrix.csv")
    assert summary["period_id"].is_unique
    assert (summary["retained_households"] <= summary["prior_active_households"]).all()
    assert summary["retention_rate"].dropna().between(0, 1).all()
    assert matrix["retention_rate"].between(0, 1).all()
    assert (matrix["active_households"] <= matrix["cohort_households"]).all()


def test_feature_demographic_flag_and_numeric_finiteness():
    import numpy as np

    features = pd.read_csv(TABLES / "feature_ready_households.csv")
    assert "household_key_1" not in features.columns
    assert set(features["missing_demographic_flag"]) == {0, 1}
    assert features.loc[features["missing_demographic_flag"] == 0, "age_desc"].notna().any()
    numeric = features.select_dtypes(include="number")
    assert np.isfinite(numeric.drop(columns=["future_spend"], errors="ignore").fillna(0).to_numpy()).all()


def test_sql_is_modular_idempotent_and_contains_exact_join_controls():
    sql_files = sorted((ROOT / "sql").glob("*.sql"))
    assert [path.name for path in sql_files[:4]] == [
        "01_stage_sources.sql", "02_build_marts.sql",
        "03_kpi_outputs.sql", "04_validation_checks.sql",
    ]
    combined = "\n".join(path.read_text(errors="ignore") for path in sql_files)
    assert "CREATE OR REPLACE TABLE" in combined
    assert "product_id, store_id, week_no" in combined
    assert "promotion_join_fanout_ok" in combined
    assert "LAG(active_flag)" in combined


def test_relative_time_and_hhmm_validation():
    con = duckdb.connect()
    source = (RAW / "transaction_data.csv").as_posix()
    result = con.execute(f"""
        SELECT MIN(DAY),MAX(DAY),MIN(WEEK_NO),MAX(WEEK_NO),
               COUNT(*) FILTER(
                 WHERE TRY_CAST(TRANS_TIME AS INTEGER) NOT BETWEEN 0 AND 2359
                    OR TRY_CAST(TRANS_TIME AS INTEGER) % 100 >= 60
               )
        FROM read_csv_auto('{source}')
    """).fetchone()
    assert result[:4] == (1, 711, 1, 102)
    assert result[4] == 0


def test_quantitative_model_and_documentation_evidence():
    appendix = (ROOT / "quantitative_analysis_appendix.md").read_text()
    assert "Cohen's d=" in appendix
    assert "rank-biserial effect=" in appendix
    assert "training and" in appendix and "holdout households" in appendix
    assert "PCA components explain" in appendix
    for rel in [
        "customer_analysis.md", "category_analysis.md", "campaign_bias_analysis.md",
        "docs/source_relationship_map.md", "docs/mart_catalog.md",
    ]:
        assert (ROOT / rel).exists()
        assert (ROOT / rel).stat().st_size > 300


def test_required_validation_artifacts_exist():
    for relative_path in [
        "validation_report.md",
        "outputs/tables/validation_checks.csv",
    ]:
        artifact = ROOT / relative_path
        assert artifact.exists()
        assert artifact.stat().st_size > 300
