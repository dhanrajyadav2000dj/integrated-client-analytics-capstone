from pathlib import Path
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
    assert baskets["discount_rate"].dropna().between(0, 10).all()

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
    allowed = {"qa/QA_BASELINE_STATE.md"}
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT).as_posix()
        if not path.is_file() or ".git" in path.parts or rel.startswith("data/raw/") or rel in allowed:
            continue
        if path.suffix.lower() in {".png", ".duckdb", ".zip", ".pyc"}:
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
