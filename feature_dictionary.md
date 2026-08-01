# Feature Dictionary

Feature file: `outputs/tables/feature_ready_households.csv`. Observation window is all weeks through `max_week - 13`; label window is the final 13 weeks. Features include recency, frequency, monetary spend, units, product diversity, category diversity, discount sensitivity, coupon engagement, demographics, missing demographic flag, and future labels. Preprocessing: median imputation, unknown/rare categorical handling, one-hot encoding, scaling for model/distance methods, train/future column alignment, and leakage checks excluding future labels from features.
