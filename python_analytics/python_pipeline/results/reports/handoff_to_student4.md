# Handoff to Student 4 — Python Pipeline Results

**From:** Student 3 — Python Data Science
**To:** Student 4 — Dashboard & Recommendations
**Date:** 2026-09-26

## 1. What You Receive

### 1.1 Customer Intelligence
- results/parquet/03_rfm/customer_rfm.parquet — RFM + behavioral + favorite category + preferred channel + time-of-day preference
- results/parquet/04_segmentation/customer_segments.parquet — 6 segments
- results/parquet/04_segmentation/segment_profiles.parquet — cluster profiles with top_channel, top_tod, top_category

### 1.2 Menu Intelligence
- results/parquet/02_feature_store/item_features.parquet — 141 items
- results/parquet/05_basket/basket_rules.parquet — 947 association rules
- results/parquet/05_basket/basket_top20.parquet — top 20 pairs
- results/parquet/05_basket/bundle_suggestions.parquet — 30 bundle suggestions
- results/parquet/12_slow_moving/slow_moving_dishes.parquet — 26 slow items

### 1.3 Wastage Intelligence
- results/parquet/06_wastage/ — 10 files by dimension
- results/parquet/06_wastage/wastage_risk.parquet — rule-based risk tiers
- results/parquet/13_wastage_risk_model/wastage_risk_predictions.parquet — ML predicted risk probability per (item, location, date)

### 1.4 Pricing and Promotions
- results/parquet/07_price/price_elasticity.parquet — 146 items with sensitivity + correlations + rating + repeat
- results/parquet/08_promotion/promo_effectiveness.parquet — 30 campaigns with 8 dimensions
- results/parquet/08_promotion/promo_traps.parquet — 7 trap campaigns
- results/parquet/08_promotion/promo_traps_summary.parquet — 5 trap types

### 1.5 Ratings and Anomalies
- results/parquet/09_ratings/ratings_by_item.parquet — rating vs profitability, sales, repeat
- results/parquet/09_ratings/ratings_by_location.parquet
- results/parquet/09_ratings/ratings_by_time.parquet — month x day_of_week
- results/parquet/09_ratings/ratings_by_promotion.parquet
- results/parquet/09_ratings/rating_anomalies.parquet — 549 anomalies
- results/parquet/09_ratings/rating_inconsistencies.parquet — 9 cases
- results/parquet/10_anomalies/sales_anomalies.parquet — 6,329
- results/parquet/10_anomalies/order_value_anomalies.parquet — 41
- results/parquet/10_anomalies/discount_anomalies.parquet — 2,194
- results/parquet/10_anomalies/duplicate_transactions.parquet — 0
- results/parquet/10_anomalies/unexpected_demand.parquet — 369

### 1.6 Peak Periods
- results/parquet/11_peak_periods/peaks_by_hour.parquet
- results/parquet/11_peak_periods/peaks_by_day.parquet
- results/parquet/11_peak_periods/peaks_by_weekend.parquet
- results/parquet/11_peak_periods/peaks_by_month.parquet
- results/parquet/11_peak_periods/peaks_by_location.parquet
- results/parquet/11_peak_periods/peaks_location_hour.parquet
- results/parquet/11_peak_periods/peaks_by_channel.parquet
- results/parquet/11_peak_periods/peaks_channel_hour.parquet
- results/parquet/11_peak_periods/peaks_summary.parquet

### 1.7 Churn and Forecast
- results/parquet/11_churn/churn_metrics.parquet — 3 models with val/test metrics
- results/parquet/11_churn/churn_feature_importance.parquet
- results/parquet/11_churn/churn_predictions_sample.parquet — 100 samples
- results/parquet/12_python_forecast/python_forecast.parquet — 73 days
- results/parquet/14_forecast_demand/forecast_item.parquet
- results/parquet/14_forecast_demand/forecast_category.parquet
- results/parquet/14_forecast_demand/forecast_location.parquet
- results/parquet/14_forecast_demand/forecast_summary.parquet — Gradient Boosting vs Naive baseline
- results/parquet/14_forecast_demand/metrics_item.parquet, metrics_category.parquet, metrics_location.parquet

### 1.8 Dual Pipeline
- results/parquet/13_dual_comparison/dual_pipeline_comparison.parquet — 73 rows with explanation column (spark pending)
- results/parquet/13_dual_comparison/dual_pipeline_summary.parquet

## 2. Key Recommendations

### 2.1 Bundle Suggestions (Top 5 by lift)
- Fresh Mint Lemonade + Pancakes — lift 4.73
- Kofta Kebab + Carbonara — lift 4.03
- Lemonade + Foul Medames — lift 3.85
- Hummus + Shakshuka — lift 3.77
- Lamb Kebab + Foul Medames — lift 3.70

### 2.2 Promotion Traps to Fix
7 campaigns out of 30 classified as traps (trap_count >= 2):
- Campaign 15: +220,565 revenue / -17,174 profit
- Campaign 28: +122,261 revenue / -13,713 profit
- Campaign 14: +97,443 revenue / -18,051 profit
- Campaign 1: +85,659 revenue / -14,795 profit
- Campaign 24: +43,383 revenue / -6,842 profit
- Campaign 5: +38,653 revenue / -451 profit
- Campaign 7: +14,996 revenue / -601 profit

### 2.3 High-Risk Wastage
- 729 (item, location) pairs at high risk
- ML model predicts risk per (item, location, date) with AUC 0.79

### 2.4 At-Risk Customers
- 3,166 customers in at_risk segment

### 2.5 Churn Model
- Best: Gradient Boosting (F1 = 0.756, AUC = 0.645)
- Key features: AOV (0.238), Recency (0.194), Monetary (0.186)

### 2.6 Demand Forecast
- Naive baseline outperforms Gradient Boosting due to synthetic data noise
- Best R2: category level (0.59)

### 2.7 Slow-Moving Dishes
- 26 items classified as slow-moving

### 2.8 Peak Periods
- Peak hour: 16 | Peak day: Saturday | Peak month: December | Peak channel: Dine-in

## 3. Suggested Dashboards

- Executive — segment_profiles + churn_metrics + peaks_summary
- Menu Intelligence — item_features + price_elasticity + slow_moving_dishes + bundle_suggestions
- Customer RFM — customer_segments
- Wastage — wastage_risk + wastage_risk_predictions + wastage_by_item
- Forecast — python_forecast + forecast_item + forecast_category + forecast_location
- Promotions — promo_effectiveness + promo_traps + promo_traps_summary
- Ratings — ratings_by_item + rating_anomalies + rating_inconsistencies
- Anomalies — sales_anomalies + order_value_anomalies + discount_anomalies + unexpected_demand
- Peak Periods — peaks_by_hour + peaks_by_day + peaks_location_hour

## 4. Data Source
All outputs derived from full_output/processed_data/clean/ filtered by unified revenue definition.

## 5. Questions
Contact Student 3 for clarifications.

Student 3
Python Data Science Pipeline — DineIQ Analytics