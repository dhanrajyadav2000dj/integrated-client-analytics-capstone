# Source Relationship Map

## Source Grains

| Source | Row grain | Likely key | Main relationships |
| --- | --- | --- | --- |
| transaction_data | Item-receipt line | No guaranteed line key; basket_id repeats | household, basket, product, store, week |
| product | Product | product_id | One product to many item lines |
| hh_demographic | Covered household | household_key | Optional subset join to household |
| campaign_desc | Campaign | campaign | Campaign type and indexed start/end day |
| campaign_table | Household-campaign exposure | household_key, campaign | Many households per campaign |
| coupon | Campaign-coupon-product mapping | campaign, coupon_upc, product_id after deduplication | Many products per coupon |
| coupon_redempt | Redemption event | household_key, campaign, coupon_upc, day | Sparse event context |
| causal_data | Product-store-week merchandising observation | product_id, store_id, week_no after deduplication | Exact-grain promotion bridge |

## Controlled Flow

transaction item lines -> baskets -> household-period mart

transaction item lines + product metadata -> product/category marts

campaign description + household exposure + redemption -> campaign marts

transaction product-store-week aggregate + deduplicated causal product-store-week -> promotion mart

observation-window transactions + static demographics -> household features -> future-window labels

## Explicit Join Risks

Item lines are not baskets. Campaign-to-household, campaign-to-coupon, and coupon-to-product are one-to-many. Coupon and causal sources contain duplicate exact keys. Demographics cover only a subset. Redemption is sparse. Directly joining campaign, coupon, product, or causal rows to item facts can multiply rows and money. The pipeline pre-aggregates each bridge and records row, sales, and unit reconciliation.
