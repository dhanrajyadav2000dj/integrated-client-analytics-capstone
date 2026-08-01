# Submission Guide

Review in this order:

1. README.md
2. final_recommendation_memo.md
3. validation_report.md
4. quantitative_analysis_appendix.md
5. customer_analysis.md, category_analysis.md, and campaign_bias_analysis.md
6. outputs/charts and outputs/tables
7. qa/07_FINAL_SUBMISSION_READINESS.md

Reproduce with:

python -m pip install -r requirements.txt
python src/download_data.py
python src/run_pipeline.py
python src/execute_notebook.py
python -m pytest -q
python qa/strict_audit.py

Raw data is local and ignored by Git. Never commit Kaggle credentials.
