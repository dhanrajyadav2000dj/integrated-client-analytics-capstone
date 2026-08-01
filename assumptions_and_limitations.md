# Assumptions And Limitations

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
