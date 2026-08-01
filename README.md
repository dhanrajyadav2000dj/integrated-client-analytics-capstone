# Integrated Client Analytics Capstone

End-to-end retail analytics capstone using the dunnhumby / 84.51 "The Complete Journey" dataset.

## Objective
Build a reviewable analytics package from raw retail data to decision-ready recommendations across customer value, category performance, campaign/coupon effectiveness, validation, feature engineering, and quantitative evidence.

## Dataset
Kaggle dataset: `frtgnn/dunnhumby-the-complete-journey`.

Expected raw files in `data/raw/`: `transaction_data.csv`, `product.csv`, `hh_demographic.csv`, `campaign_desc.csv`, `campaign_table.csv`, `coupon.csv`, `coupon_redempt.csv`, `causal_data.csv`.

## Setup
```powershell
python -m pip install -r requirements.txt
```

## Run
```powershell
python src/download_data.py
python src/run_pipeline.py
```

SQL dialect: DuckDB. Python stack: pandas, NumPy, matplotlib/seaborn, scipy, statsmodels, scikit-learn.

## Deliverables
The pipeline creates SQL files, mart CSVs in `outputs/tables/`, charts in `outputs/charts/`, and all required markdown deliverables at the project root.

Depth tracks: customer value/retention, product/category performance, and campaign/coupon effectiveness.
