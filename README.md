# Integrated Client Analytics Capstone

End-to-end retail analytics capstone using the dunnhumby / 84.51 "The Complete Journey" dataset.

## Objective
Build a reviewable analytics package from raw retail data to decision-ready recommendations across customer value, category performance, campaign/coupon effectiveness, validation, feature engineering, and quantitative evidence.

## Dataset
Kaggle dataset: `frtgnn/dunnhumby-the-complete-journey`.

Expected raw files in `data/raw/`: `transaction_data.csv`, `product.csv`, `hh_demographic.csv`, `campaign_desc.csv`, `campaign_table.csv`, `coupon.csv`, `coupon_redempt.csv`, `causal_data.csv`.

Supported alternate names: `_transactiondata.csv`, `_hhdemographic.csv`, `_campaigndesc.csv`, `_campaigntable.csv`, `_couponredempt.csv`, plus common un-underscored variants. The loader maps those names to the canonical source tables.

Raw data is intentionally ignored by Git. Use `python src/download_data.py` to download it with Kaggle credentials, or place the expected CSV files in `data/raw/`.

## Setup
```powershell
python -m pip install -r requirements.txt
```

## Run
```powershell
python src/download_data.py
python src/run_pipeline.py
python -m pytest -q
```

SQL dialect: DuckDB. Python stack: pandas, NumPy, matplotlib/seaborn, scipy, scikit-learn, pytest, Kaggle CLI.

## Outputs
The pipeline creates SQL files, mart CSVs in `outputs/tables/`, charts in `outputs/charts/`, and all required markdown deliverables at the project root.

## Deliverables
- SQL transformations: `sql/`
- Orchestration script: `src/run_pipeline.py`
- Notebook wrapper: `notebooks/integrated_client_analytics_capstone.ipynb`
- Mart tables and feature dataset: `outputs/tables/`
- Visual evidence: `outputs/charts/`
- Validation, KPI, feature, quantitative, performance, assumptions, AI, and final memo markdown files
- QA audit artifacts: `qa/`
- Automated tests: `tests/`

Depth tracks: customer value/retention, product/category performance, and campaign/coupon effectiveness.

## Known Limitations
`DAY` and `WEEK_NO` are relative indexes, not real calendar dates. Campaign/coupon evidence is observational and should not be interpreted as causal proof. Demographic coverage is incomplete.
