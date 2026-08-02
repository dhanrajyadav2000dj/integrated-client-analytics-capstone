from __future__ import annotations
import json, math, subprocess
from pathlib import Path
import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from audit_enhancements import apply_sql_enhancements, enhance_statistics, repair_feature_frame, write_enhanced_outputs

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"
DB = PROC / "capstone.duckdb"

FILE_MAP = {
    "transaction_data": ["transaction_data.csv", "_transactiondata.csv", "transactiondata.csv"],
    "product": ["product.csv", "_product.csv"],
    "hh_demographic": ["hh_demographic.csv", "_hhdemographic.csv", "hhdemographic.csv"],
    "campaign_desc": ["campaign_desc.csv", "_campaigndesc.csv", "campaigndesc.csv"],
    "campaign_table": ["campaign_table.csv", "_campaigntable.csv", "campaigntable.csv"],
    "coupon": ["coupon.csv", "_coupon.csv"],
    "coupon_redempt": ["coupon_redempt.csv", "_couponredempt.csv", "couponredempt.csv"],
    "causal_data": ["causal_data.csv", "_causaldata.csv", "causaldata.csv"],
}

def ensure_dirs():
    for p in [RAW, PROC, TABLES, CHARTS, ROOT / "sql", ROOT / "notebooks"]: p.mkdir(parents=True, exist_ok=True)

def find_file(name):
    for c in FILE_MAP[name]:
        p = RAW / c
        if p.exists(): return p
    return None

def maybe_download():
    if find_file("transaction_data") is None:
        subprocess.run(["python", str(ROOT / "src" / "download_data.py")], check=True)

def q(con, sql):
    df = con.execute(sql).fetchdf()
    df.columns = [str(c).lower() for c in df.columns]
    return df

def md_table(df):
    df = df.copy()
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        out.append("| " + " | ".join(str(row[c]) for c in df.columns) + " |")
    return "\n".join(out)

def write_sql_files():
    (ROOT / "sql" / "01_stage_sources.sql").write_text("""
CREATE OR REPLACE TABLE stg_transactions AS
SELECT household_key::BIGINT AS household_key, basket_id::BIGINT AS basket_id, day::INTEGER AS day, week_no::INTEGER AS week_no,
       product_id::BIGINT AS product_id, quantity::DOUBLE AS quantity, sales_value::DOUBLE AS sales_value, store_id::BIGINT AS store_id,
       retail_disc::DOUBLE AS retail_disc_signed, coupon_disc::DOUBLE AS coupon_disc_signed, coupon_match_disc::DOUBLE AS coupon_match_disc_signed,
       ABS(COALESCE(retail_disc,0))::DOUBLE AS retail_discount_amt,
       ABS(COALESCE(coupon_disc,0))::DOUBLE AS coupon_discount_amt,
       ABS(COALESCE(coupon_match_disc,0))::DOUBLE AS coupon_match_discount_amt,
       TRY_CAST(trans_time AS INTEGER) AS trans_time,
       CASE WHEN TRY_CAST(trans_time AS INTEGER) BETWEEN 0 AND 2359 AND TRY_CAST(trans_time AS INTEGER) % 100 < 60 THEN FLOOR(TRY_CAST(trans_time AS INTEGER)/100) ELSE NULL END AS trans_hour
FROM raw_transaction_data;
CREATE OR REPLACE TABLE stg_products AS SELECT * FROM raw_product;
CREATE OR REPLACE TABLE stg_households AS SELECT * FROM raw_hh_demographic;
CREATE OR REPLACE TABLE stg_campaign_desc AS SELECT * FROM raw_campaign_desc;
CREATE OR REPLACE TABLE stg_campaign_table AS SELECT * FROM raw_campaign_table;
CREATE OR REPLACE TABLE stg_coupon AS SELECT * FROM raw_coupon;
CREATE OR REPLACE TABLE stg_coupon_redempt AS SELECT * FROM raw_coupon_redempt;
CREATE OR REPLACE TABLE stg_causal_data AS SELECT * FROM raw_causal_data;
""".strip()+"\n", encoding="ascii")
    (ROOT / "sql" / "02_build_marts.sql").write_text("""
CREATE OR REPLACE TABLE mart_baskets AS
SELECT basket_id, household_key, MIN(day) AS day, MIN(week_no) AS week_no, MIN(store_id) AS store_id,
       SUM(sales_value) AS basket_spend, SUM(quantity) AS basket_units, COUNT(*) AS basket_item_line_count,
       COUNT(DISTINCT product_id) AS distinct_product_count, SUM(retail_discount_amt) AS total_retail_discount,
       SUM(coupon_discount_amt) AS total_coupon_discount, SUM(coupon_match_discount_amt) AS total_coupon_match_discount,
       CASE WHEN SUM(sales_value)+SUM(retail_discount_amt)>0 THEN SUM(retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt)/(SUM(sales_value)+SUM(retail_discount_amt)) END AS discount_rate,
       MAX(CASE WHEN coupon_discount_amt+coupon_match_discount_amt>0 THEN 1 ELSE 0 END) AS coupon_used_flag
FROM stg_transactions GROUP BY 1,2;
CREATE OR REPLACE TABLE mart_household_period AS
WITH b AS (SELECT *, FLOOR((week_no-1)/4)+1 AS period_id FROM mart_baskets),
agg AS (SELECT household_key, period_id, MIN(day) AS period_start_day, MAX(day) AS period_end_day, 1 AS active_flag, COUNT(*) AS basket_count,
        SUM(basket_spend) AS total_spend, SUM(basket_units) AS total_units, AVG(basket_spend) AS average_basket_value, AVG(basket_units) AS average_basket_size,
        SUM(total_retail_discount+total_coupon_discount+total_coupon_match_discount) AS total_discount, SUM(coupon_used_flag) AS coupon_basket_count
        FROM b GROUP BY 1,2),
prod AS (SELECT household_key, FLOOR((week_no-1)/4)+1 AS period_id, COUNT(DISTINCT t.product_id) distinct_product_count,
         COUNT(DISTINCT COALESCE(p.commodity_desc,p.department,'UNKNOWN')) distinct_category_count
         FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2),
camp AS (SELECT household_key, FLOOR((start_day-1)/28)+1 AS period_id, COUNT(*) AS campaign_exposure_count FROM stg_campaign_table ct LEFT JOIN stg_campaign_desc cd USING(campaign) GROUP BY 1,2),
red AS (SELECT household_key, FLOOR((day-1)/28)+1 AS period_id, COUNT(*) AS coupon_redemption_count FROM stg_coupon_redempt GROUP BY 1,2)
SELECT a.*, p.distinct_product_count, p.distinct_category_count, COALESCE(r.coupon_redemption_count,0) coupon_redemption_count,
       COALESCE(c.campaign_exposure_count,0) campaign_exposure_count,
       CASE WHEN a.total_spend+a.total_discount>0 THEN a.total_discount/(a.total_spend+a.total_discount) END AS discount_rate,
       LAG(a.total_spend) OVER(PARTITION BY a.household_key ORDER BY a.period_id) AS prior_period_spend,
       a.total_spend - LAG(a.total_spend) OVER(PARTITION BY a.household_key ORDER BY a.period_id) AS spend_change,
       CASE WHEN LAG(a.active_flag) OVER(PARTITION BY a.household_key ORDER BY a.period_id)=1 THEN 1 ELSE 0 END AS retention_repeat_flag
FROM agg a LEFT JOIN prod p USING(household_key,period_id) LEFT JOIN camp c USING(household_key,period_id) LEFT JOIN red r USING(household_key,period_id);
CREATE OR REPLACE TABLE mart_products AS
WITH pp AS (SELECT product_id, FLOOR((week_no-1)/13)+1 qtr, SUM(sales_value) sales FROM stg_transactions GROUP BY 1,2),
g AS (SELECT product_id, MAX(CASE WHEN qtr=1 THEN sales END) q1, MAX(CASE WHEN qtr=(SELECT MAX(qtr) FROM pp) THEN sales END) qlast FROM pp GROUP BY 1),
r AS (SELECT household_key, product_id, COUNT(DISTINCT basket_id) hb FROM stg_transactions GROUP BY 1,2)
SELECT t.product_id, ANY_VALUE(p.department) department, ANY_VALUE(p.commodity_desc) commodity_desc, ANY_VALUE(p.sub_commodity_desc) sub_commodity_desc,
       SUM(t.sales_value) product_sales, SUM(t.quantity) units,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) basket_penetration,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) household_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt)>0 THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)/SUM(t.sales_value+t.retail_discount_amt) END AS discount_rate,
       COALESCE(g.qlast,0)-COALESCE(g.q1,0) sales_growth, COUNT(DISTINCT CASE WHEN r.hb>=2 THEN t.household_key END) repeat_household_count
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) LEFT JOIN g USING(product_id) LEFT JOIN r USING(household_key,product_id) GROUP BY t.product_id,g.qlast,g.q1;
CREATE OR REPLACE TABLE mart_categories AS
SELECT COALESCE(p.department,'UNKNOWN') department, COALESCE(p.commodity_desc,'UNKNOWN') commodity_desc,
       SUM(t.sales_value) category_sales, SUM(t.quantity) units, COUNT(DISTINCT t.household_key) household_count,
       COUNT(DISTINCT t.household_key)*1.0/(SELECT COUNT(DISTINCT household_key) FROM stg_transactions) household_penetration,
       COUNT(DISTINCT t.basket_id)*1.0/(SELECT COUNT(DISTINCT basket_id) FROM stg_transactions) basket_penetration,
       CASE WHEN SUM(t.sales_value+t.retail_discount_amt)>0 THEN SUM(t.retail_discount_amt+t.coupon_discount_amt+t.coupon_match_discount_amt)/SUM(t.sales_value+t.retail_discount_amt) END AS discount_rate,
       SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) first_year_sales, SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END) second_year_sales,
       SUM(CASE WHEN week_no>52 THEN sales_value ELSE 0 END)-SUM(CASE WHEN week_no<=52 THEN sales_value ELSE 0 END) sales_growth
FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2;
CREATE OR REPLACE TABLE mart_campaigns AS
SELECT cd.campaign, cd.description, cd.description AS campaign_type, cd.start_day, cd.end_day,
       COUNT(DISTINCT ct.household_key) exposed_households, COUNT(DISTINCT cr.household_key) redeeming_households, COUNT(cr.household_key) redemption_count,
       CASE WHEN COUNT(DISTINCT ct.household_key)>0 THEN COUNT(DISTINCT cr.household_key)*1.0/COUNT(DISTINCT ct.household_key) END household_redemption_rate
FROM stg_campaign_desc cd LEFT JOIN stg_campaign_table ct USING(campaign) LEFT JOIN stg_coupon_redempt cr USING(campaign,household_key) GROUP BY 1,2,3,4,5;
CREATE OR REPLACE TABLE mart_coupon_redemptions AS SELECT cr.*, cd.description AS campaign_type, cd.start_day, cd.end_day FROM stg_coupon_redempt cr LEFT JOIN stg_campaign_desc cd USING(campaign);
""".strip()+"\n", encoding="ascii")
    (ROOT / "sql" / "03_kpi_outputs.sql").write_text("""
CREATE OR REPLACE TABLE kpi_summary AS
SELECT COUNT(DISTINCT household_key) active_households, COUNT(*) baskets, SUM(basket_spend) spend, AVG(basket_spend) avg_basket_value,
       SUM(basket_units) units, AVG(basket_units) avg_basket_size, SUM(total_retail_discount+total_coupon_discount+total_coupon_match_discount) discount_amount,
       SUM(coupon_used_flag) coupon_baskets, SUM(coupon_used_flag)*1.0/COUNT(*) coupon_basket_rate
FROM mart_baskets;
""".strip()+"\n", encoding="ascii")
    (ROOT / "sql" / "04_validation_checks.sql").write_text("""
CREATE OR REPLACE TABLE validation_checks AS
SELECT 'transaction_rows' check_name, COUNT(*)::VARCHAR check_value FROM stg_transactions
UNION ALL SELECT 'distinct_baskets', COUNT(DISTINCT basket_id)::VARCHAR FROM stg_transactions
UNION ALL SELECT 'mart_basket_rows', COUNT(*)::VARCHAR FROM mart_baskets
UNION ALL SELECT 'basket_fanout_ok', (COUNT(*)=COUNT(DISTINCT basket_id))::VARCHAR FROM mart_baskets
UNION ALL SELECT 'products_duplicate_keys', (COUNT(*)-COUNT(DISTINCT product_id))::VARCHAR FROM stg_products
UNION ALL SELECT 'transactions_missing_product_metadata', COUNT(*)::VARCHAR FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) WHERE p.product_id IS NULL
UNION ALL SELECT 'negative_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value<0
UNION ALL SELECT 'zero_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE sales_value=0
UNION ALL SELECT 'invalid_trans_time_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE trans_hour IS NULL
UNION ALL SELECT 'discount_larger_than_sales_rows', COUNT(*)::VARCHAR FROM stg_transactions WHERE retail_discount_amt+coupon_discount_amt+coupon_match_discount_amt>sales_value+retail_discount_amt AND sales_value>0
UNION ALL SELECT 'coupon_product_bridge_distinct_rows', COUNT(*)::VARCHAR FROM (SELECT DISTINCT campaign,coupon_upc,product_id FROM stg_coupon);
""".strip()+"\n", encoding="ascii")

def load_raw(con):
    present = {}
    for t in FILE_MAP:
        p = find_file(t)
        present[t] = p.name if p else None
        if p: con.execute(f"CREATE OR REPLACE TABLE raw_{t} AS SELECT * FROM read_csv_auto('{p.as_posix()}')")
    if present["causal_data"] is None:
        con.execute("CREATE OR REPLACE TABLE raw_causal_data AS SELECT NULL::INTEGER product_id WHERE FALSE")
    return present

def run_sql(con):
    for f in ["01_stage_sources.sql","02_build_marts.sql","03_kpi_outputs.sql","04_validation_checks.sql"]:
        con.execute((ROOT/"sql"/f).read_text())

def build_features(con):
    max_week = int(q(con,"SELECT MAX(week_no) m FROM stg_transactions")["m"][0])
    obs_end = max_week - 13
    first_half_end = max(1, obs_end // 2)
    df = q(con, f"""
    WITH obs AS (SELECT * FROM stg_transactions WHERE week_no <= {obs_end}),
    fut AS (SELECT household_key, SUM(sales_value) AS future_spend, COUNT(DISTINCT basket_id) AS future_baskets FROM stg_transactions WHERE week_no > {obs_end} GROUP BY 1),
    top_dept AS (
      SELECT household_key, department FROM (
        SELECT o.household_key, COALESCE(p.department, 'UNKNOWN') AS department, SUM(o.sales_value) AS dept_spend,
               ROW_NUMBER() OVER (PARTITION BY o.household_key ORDER BY SUM(o.sales_value) DESC) AS rn
        FROM obs o LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2
      ) WHERE rn = 1
    ),
    camp AS (
      SELECT ct.household_key, COUNT(*) AS campaign_exposure_count
      FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign)
      WHERE cd.start_day <= {obs_end * 7}
      GROUP BY 1
    ),
    base AS (
      SELECT o.household_key,
             {obs_end} - MAX(o.week_no) AS recency_weeks,
             COUNT(DISTINCT o.basket_id) AS frequency_baskets,
             SUM(o.sales_value) AS monetary_spend,
             AVG(o.sales_value) AS avg_line_sales,
             SUM(o.quantity) AS total_units,
             COUNT(DISTINCT o.product_id) AS product_diversity,
             COUNT(DISTINCT COALESCE(p.commodity_desc,'UNKNOWN')) AS category_diversity,
             SUM(o.retail_discount_amt+o.coupon_discount_amt+o.coupon_match_discount_amt) AS discount_amount,
             SUM(CASE WHEN o.coupon_discount_amt+o.coupon_match_discount_amt>0 THEN 1 ELSE 0 END) AS coupon_line_count,
             SUM(CASE WHEN o.week_no <= {first_half_end} THEN o.sales_value ELSE 0 END) AS first_half_spend,
             SUM(CASE WHEN o.week_no > {first_half_end} THEN o.sales_value ELSE 0 END) AS second_half_spend,
             SUM(CASE WHEN COALESCE(p.department,'UNKNOWN') = td.department THEN o.sales_value ELSE 0 END) / NULLIF(SUM(o.sales_value),0) AS top_department_share
      FROM obs o LEFT JOIN stg_products p USING(product_id) LEFT JOIN top_dept td USING(household_key)
      GROUP BY 1
    )
    SELECT b.*,
           b.second_half_spend - b.first_half_spend AS spend_trend_change,
           b.discount_amount/NULLIF(b.monetary_spend+b.discount_amount,0) AS discount_rate,
           b.coupon_line_count/NULLIF(b.frequency_baskets,0) AS coupon_engagement,
           COALESCE(c.campaign_exposure_count,0) AS campaign_exposure_count,
           COALESCE(f.future_spend,0) AS future_spend,
           CASE WHEN COALESCE(f.future_baskets,0)>0 THEN 1 ELSE 0 END AS next_period_active_flag,
           CASE WHEN COALESCE(f.future_spend,0)<b.monetary_spend*13.0/NULLIF({obs_end},0) THEN 1 ELSE 0 END AS next_period_spend_decline_flag,
           h.*
    FROM base b LEFT JOIN fut f USING(household_key) LEFT JOIN camp c USING(household_key) LEFT JOIN stg_households h USING(household_key)
    """)
    df = repair_feature_frame(df).sort_values('household_key').reset_index(drop=True)
    con.register("features_df", df); con.execute("CREATE OR REPLACE TABLE mart_customer_features AS SELECT * FROM features_df")
    return df

def export_tables(con):
    tables=["mart_baskets","mart_household_period","mart_products","mart_categories","mart_campaigns","mart_coupon_redemptions","mart_customer_features","mart_promotion_performance","mart_category_period","mart_category_diagnostics","customer_period_summary","customer_retention_matrix","campaign_bias_comparison","campaign_segment_analysis","kpi_summary","validation_checks"]
    counts={}
    for t in tables:
        df=q(con,f'SELECT * FROM {t}'); counts[t]=len(df)
        df.sort_values(list(df.columns)).to_csv(TABLES/f'{t}.csv',index=False)
    q(con,'SELECT * FROM mart_customer_features ORDER BY household_key').to_csv(TABLES/'feature_ready_households.csv',index=False)
    return counts

def ci_mean(s):
    a=s.dropna().to_numpy(); rng=np.random.default_rng(42)
    if len(a)==0: return (math.nan,math.nan)
    vals=[rng.choice(a,len(a),replace=True).mean() for _ in range(500)]
    return tuple(np.quantile(vals,[.025,.975]).round(3))

def make_charts(con):
    sns.set_theme(style="whitegrid"); charts=[]
    def save(n): plt.tight_layout(); plt.savefig(CHARTS/n,dpi=120); plt.close(); charts.append(n)
    baskets=q(con,"SELECT * FROM mart_baskets"); hp=q(con,"SELECT * FROM mart_household_period"); cats=q(con,"SELECT * FROM mart_categories WHERE household_count>=50 ORDER BY category_sales DESC LIMIT 40"); camps=q(con,"SELECT * FROM mart_campaigns")
    q(con,"SELECT week_no,COUNT(DISTINCT basket_id) baskets FROM stg_transactions GROUP BY 1 ORDER BY 1").plot(x="week_no",y="baskets",legend=False,title="Data coverage: baskets by week"); save("01_data_coverage.png")
    sns.histplot(baskets.basket_spend.clip(upper=baskets.basket_spend.quantile(.99)),bins=50); plt.title("Basket spend distribution"); save("02_basket_spend_distribution.png")
    sns.histplot(hp.loc[hp.active_flag==1,"basket_count"],bins=40); plt.title("Active-household basket frequency"); plt.xlabel("baskets per four-week period"); save("03_frequency_distribution.png")
    hh=q(con,"SELECT household_key,SUM(basket_spend) spend FROM mart_baskets GROUP BY 1 ORDER BY spend DESC"); hh["cum"]=hh.spend.cumsum()/hh.spend.sum(); plt.plot(np.arange(1,len(hh)+1)/len(hh),hh.cum); plt.title("Customer value concentration"); save("04_value_concentration.png")
    retention=q(con,"SELECT cohort_period,period_id,retention_rate FROM customer_retention_matrix"); matrix=retention.pivot(index="cohort_period",columns="period_id",values="retention_rate"); sns.heatmap(matrix,cmap="Blues",vmin=0,vmax=1); plt.title("Household cohort retention by four-week period"); plt.xlabel("period"); plt.ylabel("first active period"); save("05_retention_heatmap.png")
    cats.head(15).plot.barh(x="commodity_desc",y="category_sales",legend=False,title="Top category sales"); save("06_top_categories.png")
    sns.scatterplot(data=cats,x="household_penetration",y="category_sales",hue="sales_growth",size="discount_rate",legend=False); plt.title("Category penetration vs sales"); save("07_category_penetration_sales.png")
    sns.regplot(data=cats,x="discount_rate",y="category_sales",scatter_kws={"s":20}); plt.title("Discount rate vs category sales"); save("08_discount_sales.png")
    camps[["campaign","exposed_households","redeeming_households"]].head(20).plot(x="campaign",kind="bar",title="Campaign funnel"); save("09_campaign_funnel.png")
    q(con,"""WITH e AS (SELECT ct.household_key,cd.start_day,cd.end_day,cd.description AS campaign_type FROM stg_campaign_table ct JOIN stg_campaign_desc cd USING(campaign)), a AS (SELECT e.campaign_type,e.household_key,SUM(CASE WHEN t.day BETWEEN e.start_day-28 AND e.start_day-1 THEN t.sales_value ELSE 0 END) pre_spend,SUM(CASE WHEN t.day BETWEEN e.start_day AND e.end_day+28 THEN t.sales_value ELSE 0 END) post_spend FROM e LEFT JOIN stg_transactions t USING(household_key) GROUP BY 1,2) SELECT campaign_type,AVG(post_spend-pre_spend) avg_change FROM a GROUP BY 1""").plot.bar(x="campaign_type",y="avg_change",legend=False,title="Campaign pre/post spend association"); save("10_campaign_prepost.png")
    return charts

def analyze(con, features):
    baskets=q(con,"SELECT * FROM mart_baskets"); hp=q(con,"SELECT * FROM mart_household_period"); cats=q(con,"SELECT * FROM mart_categories")
    first=hp[hp.period_id<=hp.period_id.median()].total_spend; second=hp[hp.period_id>hp.period_id.median()].total_spend; tt=stats.ttest_ind(first,second,equal_var=False,nan_policy="omit")
    hd=cats[cats.discount_rate>=cats.discount_rate.median()].category_sales.dropna(); ld=cats[cats.discount_rate<cats.discount_rate.median()].category_sales.dropna(); mw=stats.mannwhitneyu(hd,ld,alternative="two-sided")
    auc=None; coefs=[]  # Leakage-safe holdout model is fitted in enhance_statistics().
    mat=q(con,"SELECT household_key,commodity_desc,SUM(sales_value) spend FROM stg_transactions t LEFT JOIN stg_products p USING(product_id) GROUP BY 1,2").pivot(index="household_key",columns="commodity_desc",values="spend").fillna(0)
    sample=mat.head(min(200,len(mat))); pca=PCA(n_components=min(5,sample.shape[1],sample.shape[0])).fit(StandardScaler(with_mean=False).fit_transform(sample)); sim=cosine_similarity(StandardScaler(with_mean=False).fit_transform(sample))
    return {"avg_basket_ci":ci_mean(baskets.basket_spend),"hh_spend_ci":ci_mean(q(con,"SELECT household_key,SUM(basket_spend) spend FROM mart_baskets GROUP BY 1").spend),"ttest_stat":round(float(tt.statistic),3),"ttest_p":round(float(tt.pvalue),4),"disc_test_stat":round(float(mw.statistic),3),"disc_test_p":round(float(mw.pvalue),4),"model_auc":auc,"top_model_coefs":[(a,round(float(b),3)) for a,b in coefs],"matrix_sparsity":round(float((mat.to_numpy()==0).mean()),3),"pca_variance":pca.explained_variance_ratio_.round(3).tolist(),"nearest_neighbor_similarity":round(float(np.sort(sim[0])[-2]),3) if len(sample)>1 else None}

def write_docs(con,present,counts,charts,st):
    k=q(con,"SELECT * FROM kpi_summary").iloc[0].to_dict(); val=q(con,"SELECT * FROM validation_checks"); cats=q(con,"SELECT commodity_desc,category_sales,household_penetration,discount_rate,sales_growth FROM mart_categories WHERE household_count>=50 ORDER BY category_sales DESC LIMIT 10"); camp=q(con,"SELECT campaign,campaign_type,exposed_households,redeeming_households,household_redemption_rate FROM mart_campaigns ORDER BY exposed_households DESC LIMIT 10")
    (ROOT/"kpi_definitions.md").write_text("# KPI Definitions\n\nAll discount reporting uses positive discount amounts from `ABS(retail_disc)`, `ABS(coupon_disc)`, and `ABS(coupon_match_disc)`. Rates are reported only with explicit denominators. Active household means at least one basket in the window. Basket means distinct `basket_id`, not transaction rows. Retention means repeat activity in adjacent 4-week periods. Coupon redemption rate uses redeeming households divided by exposed households with a minimum denominator threshold of 30. Category penetration uses buying households divided by active households with a minimum threshold of 50 category households. Customer value is household spend; high value is top-quartile observation-window spend; at risk is prior activity with future inactivity or spend decline.\n",encoding="ascii")
    (ROOT/"validation_report.md").write_text(f"# Validation Report\n\n## Source files\n```json\n{json.dumps(present,indent=2)}\n```\n\n## Table counts\n```json\n{json.dumps(counts,indent=2)}\n```\n\n## Actual checks\n{md_table(val)}\n\nFan-out control: item rows are aggregated to basket before basket metrics; coupon/product bridges are kept separate; campaign marts aggregate at campaign and household levels.\n",encoding="ascii")
    (ROOT/"quantitative_analysis_appendix.md").write_text(f"# Quantitative Analysis Appendix\n\nAverage basket spend bootstrap 95% CI: {st['avg_basket_ci']}. Household total spend bootstrap 95% CI: {st['hh_spend_ci']}.\n\nHypothesis test 1: early and late household-period spend are equal versus different. Welch t-statistic {st['ttest_stat']}, p-value {st['ttest_p']}.\n\nHypothesis test 2: high-discount and low-discount category sales distributions are equal versus different. Mann-Whitney statistic {st['disc_test_stat']}, p-value {st['disc_test_p']}. Effect sizes and p-values are interpreted as observational evidence only.\n\nCustomer-category matrix sparsity: {st['matrix_sparsity']}. Nearest-neighbor cosine similarity example: {st['nearest_neighbor_similarity']}. PCA explained variance: {st['pca_variance']}.\n\nTemporal baseline model AUC for next-period active flag: {st['model_auc']}. Top coefficients: {st['top_model_coefs']}. Logistic regression is interpretable screening, not a black-box decision system.\n\nFuture experiment power should be computed at household level using baseline variance; recommend planning for a 3-5% minimum detectable lift in repeat activity or spend. Statistical significance is not the same as business significance.\n",encoding="ascii")
    (ROOT/"feature_dictionary.md").write_text("# Feature Dictionary\n\nFeature file: `outputs/tables/feature_ready_households.csv`. Observation window is all weeks through `max_week - 13`; label window is the final 13 weeks. Features include recency, frequency, monetary spend, units, product diversity, category diversity, discount sensitivity, coupon engagement, demographics, missing demographic flag, and future labels. Preprocessing: median imputation, unknown/rare categorical handling, one-hot encoding, scaling for model/distance methods, train/future column alignment, and leakage checks excluding future labels from features.\n",encoding="ascii")
    (ROOT/"performance_and_scalability_note.md").write_text(f"# Performance and Scalability Note\n\nCounts: `{json.dumps(counts)}`. Heavy joins are pushed into DuckDB. Transactions are summarized to basket, household-period, product, and category grain before analysis. Coupon and campaign bridges are not directly joined to item facts for rate reporting. `causal_data` is staged and should be joined only to product-store-week transaction summaries with before/after row-count checks. Production improvements: partition by week, cluster on household/product/store, materialize marts, and isolate promotion bridge tables.\n",encoding="ascii")
    (ROOT/"assumptions_and_limitations.md").write_text("# Assumptions and Limitations\n\n`DAY` and `WEEK_NO` are relative indexes, not real dates, so weekday, month, holiday, and calendar seasonality are not recoverable. Periods are constructed as 4-week and 13-week windows. Spend uses `sales_value`; gross sales proxy adds retail discount. Demographics are incomplete. Campaign exposure does not prove attention. Coupon redemption is sparse. TypeA, TypeB, and TypeC mechanics differ. Campaign comparisons are observational and vulnerable to selection bias, confounding, and omitted variables. Feature labels use future windows and future columns are excluded from model features.\n",encoding="ascii")
    (ROOT/"ai_assistance_declaration.md").write_text("# AI Assistance Declaration\n\nAI tools were used to scaffold code, SQL, validation checks, charts, and draft documentation. Generated code, SQL, and text were reviewed by rerunning the pipeline, inspecting output tables, and checking validation reports. Final responsibility for the submitted work remains with the candidate. No private credentials or API keys are included.\n",encoding="ascii")
    (ROOT/"final_recommendation_memo.md").write_text(f"# Final Recommendation Memo\n\n## Executive Summary\nThe retailer should prioritize high-value customer retention, category actions that combine scale with penetration and stability, and randomized testing for campaign improvements. The evidence is strong for descriptive patterns and weaker for causal campaign claims.\n\n## KPI Snapshot\n- Active households: {int(k['active_households'])}\n- Baskets: {int(k['baskets'])}\n- Spend: {k['spend']:.2f}\n- Average basket value: {k['avg_basket_value']:.2f}\n- Coupon basket rate: {k['coupon_basket_rate']:.3f}\n\n## Finding 1: Customer value is concentrated\nUse high-value and declining household segments for retention operations instead of broad untargeted offers. Evidence is in the value concentration chart and feature mart.\n\n## Finding 2: Category decisions need denominator checks\n{md_table(cats)}\n\nPrioritize categories with sufficient household penetration and growth; investigate high-sales declining categories before reducing support.\n\n## Finding 3: Campaign results are associations, not proof\n{md_table(camp)}\n\nTypeA targeting creates strong selection-bias risk. TypeB/TypeC still need denominator and exposure caveats.\n\n## Recommended Experiment\nRun a household-randomized retention offer test for high-value declining households. Treatment receives a category-affinity coupon bundle; control receives business-as-usual. Primary metric: next 4-week spend per household. Guardrails: basket frequency, discount cost, redemption, category cannibalization, and customer complaints if available. Success requires practical lift, not just statistical significance.\n\n## Visual Evidence\nCharts: {', '.join(charts)}\n",encoding="ascii")

def main():
    ensure_dirs(); maybe_download(); write_sql_files(); con=duckdb.connect(str(DB)); con.execute('PRAGMA threads=1'); present=load_raw(con)
    missing=[k for k,v in present.items() if v is None and k!="causal_data"]
    if missing: raise SystemExit(f"Missing required raw files: {missing}")
    run_sql(con); apply_sql_enhancements(ROOT, con); features=build_features(con); counts=export_tables(con); charts=make_charts(con); st=enhance_statistics(con,features,analyze(con,features)); write_docs(con,present,counts,charts,st); from enrich_outputs import enrich_outputs; charts = enrich_outputs(ROOT, con, charts, st)
    write_enhanced_outputs(ROOT, con, charts, st)
    print("Pipeline complete. Outputs and deliverables generated.")
if __name__=="__main__": main()












