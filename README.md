# Integrated Client Analytics Capstone

End-to-end retail analytics using the dunnhumby / 84.51 The Complete Journey dataset. The package builds a validated DuckDB analytics layer and decision-ready evidence for customer value and retention, product/category performance, and campaign/coupon/promotion effectiveness.

## Dataset And Inputs

Primary source: https://www.dunnhumby.com/source-files/

Kaggle mirror: https://www.kaggle.com/datasets/frtgnn/dunnhumby-the-complete-journey

Expected files in data/raw:

- transaction_data.csv
- product.csv
- hh_demographic.csv
- campaign_desc.csv
- campaign_table.csv
- coupon.csv
- coupon_redempt.csv
- causal_data.csv

Alternate names supported by the loader include _transactiondata.csv, _hhdemographic.csv, _campaigndesc.csv, _campaigntable.csv, _couponredempt.csv, and common un-underscored variants. Raw data and the local DuckDB database are intentionally excluded from Git.

## Environment

Python 3.12.6 was used for the final audit. Dependencies are exactly pinned in requirements.txt. SQL dialect is DuckDB SQL.

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Configure Kaggle credentials outside the repository. Then download, or manually place the eight CSV files in data/raw:

    python src/download_data.py

## Reproduce

    python src/run_pipeline.py
    python src/execute_notebook.py
    python -m pytest -q

The canonical pipeline writes and executes SQL in numeric order, exports all marts and evidence tables, generates 12 charts, performs quantitative and leakage-safe model analysis, and regenerates the memo and documentation. The notebook is a reviewer entry point around that same pipeline; execute_notebook.py records an executed copy without requiring Jupyter.

## SQL Layer

- sql/01_stage_sources.sql: typed sources and positive discount fields
- sql/02_build_marts.sql: required basket, household, product, category, campaign, and coupon marts
- sql/03_kpi_outputs.sql: top-level KPI output
- sql/04_validation_checks.sql: baseline controls
- sql/05_strengthen_analytics_and_validation.sql: corrected adjacent-period spine, category stability, exact-grain promotion analysis, bias-aware campaign tables, and expanded reconciliations

SQL uses deterministic CREATE OR REPLACE statements, stable export ordering, and fixed random seeds, so reruns do not append duplicates or reshuffle model inputs.

## Outputs

outputs/tables contains required marts plus customer period/cohort evidence, category diagnostics, campaign stratification, promotion performance, experiment MDE, KPI, and validation files. outputs/charts contains 12 labelled visuals. Root markdown files contain KPI contracts, feature/leakage definitions, quantitative evidence, assumptions, validation, and the final recommendation memo.

Source grains and fan-out risks are in docs/source_relationship_map.md. Mart grains and keys are in docs/mart_catalog.md. Required validation evidence is in validation_report.md and outputs/tables/validation_checks.csv.

## Core Conventions

A basket is a distinct basket_id, never an item row. Four-week periods are constructed from WEEK_NO and are not calendar months. DAY and WEEK_NO have no real calendar anchor, so weekday, month, holiday, and season cannot be inferred. TRANS_TIME is HHMM, not a timestamp.

sales_value is net customer spend. Raw discount fields are signed; reporting uses positive absolute discount amounts. Gross sales equals net spend plus retail, coupon, and matched-coupon discounts. Campaign and promotion findings are observational associations, not causal proof. TypeA targeting is analyzed separately, rates always retain denominators, and causal data joins only after exact product-store-week aggregation.

## Limitations

Demographic coverage is incomplete, coupon redemption is sparse, campaign exposure does not prove viewing, product/store promotion assignment is confounded, extreme source quantities exist, and the final four-week period is incomplete. The recommended causal next step is a household-randomized experiment with true eligibility, delivery, cost, margin, and inventory data.
