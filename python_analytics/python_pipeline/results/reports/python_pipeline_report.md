# Python Data Science Pipeline — Technical Report

**Student 3 — DineIQ Analytics**
**Version:** v1.4 (Final)
**Date:** 2026-09-27

## 1. Overview

Independent Python pipeline for restaurant analytics. Covers customer intelligence, menu intelligence, wastage, pricing, promotions, ratings, anomalies, churn, forecasting, peak periods, slow-moving dishes, and wastage risk modeling.

**Total scripts:** 19 in `python_pipeline/src/`
**Total tests:** 67 pytest (all passing)
**Total parquet outputs:** ~80 files across 18 stage folders

## 2. Stages Summary

- 00_load_data — load 12 tables
- 01_validation — data quality (25 PASS / 3 WARN / 0 FAIL)
- 02_feature_store — customer_features, item_features
- 03_rfm — RFM + behavioral + favorite category + preferred channel + time-of-day preference + freq features
- 04_segmentation — KMeans K=6 (R/F/M core + behavioral extras)
- 05_market_basket — 947 pairwise association rules + 30 bundle suggestions
- 06_wastage — 10 wastage dimension analyses
- 07_price_analysis — univariate + multivariate elasticity + price-revenue/margin/discount/repeat correlations + ratings
- 08_promotion_analysis — 30 campaigns with 5 trap types
- 09_rating_analysis — ratings by item/location/time/promotion + 4 anomaly types
- 10_sales_anomalies — spikes, drops, order values, discounts, duplicates, unexpected demand
- 11_peak_periods — hour, day, weekend, month, location, channel
- 11_churn_model — 3 models with temporal cohort feature cutoff
- 12_slow_moving — slow dishes detection with 7 criteria
- 12_python_forecast — 100-day revenue forecast (chronological split)
- 13_wastage_risk_model — Logistic + Random Forest classifier (no leakage)
- 13_dual_comparison — Spark vs Python comparison (100 cases)
- 14_forecast_demand — 4 models (naive, MA, linear, GB) × 3 levels

## 3. Methodological Decisions

### 3.1 Data Leakage Prevention
- Features computed only up to `2024-09-30`.
- Churn label from `2024-10-01` to `2024-12-31`.
- Forecast uses chronological split only.
- Churn uses temporal cohort with feature cutoff per cohort.
- Wastage Risk uses lag/cumulative-shift features from past only.

### 3.2 Unified Revenue Definition
Agreed with Students 1 and 2:
revenue = SUM(line_total) WHERE order_status='completed' AND quantity>0 AND unit_price>0 AND line_total>=0
Reason: Orders.total_amount not recalculated after anomaly injection.

### 3.3 Customer Segmentation
- KMeans K=6.
- Clustering features: recency, frequency, monetary, aov.
- Post-clustering features: favorite_category, preferred_channel, time_of_day_preference, peak_ratio, weekend_ratio, promo_sensitivity.
- Labels assigned by centroid inspection.
- Segments: high_value_loyal, frequent, at_risk, new, occasional (x2).

### 3.4 Market Basket
- Pairwise Association Rule Mining (2-itemsets).
- Thresholds: support>=0.002, confidence>=0.15, lift>=1.2.
- Self-pairs filtered.
- Bundle suggestions: 30 top pairs by lift.

### 3.5 Price Intelligence
Two approaches:
- Univariate: cov(qty_pct, price_pct) / var(price_pct). Filtered |e|>10.
- Multivariate: log(quantity) = β0 + β1 log(price) + β2 has_promo + β3 weekend + β4 month + ε. Elasticity = β1.
- Classes: high (|e|>=1.5), medium (|e|>=0.5), low (else).
- Additional correlations: price-revenue, price-margin, price-discount, price-repeat.

### 3.6 Promotion Effectiveness and Traps
- Three windows: pre (14d) / during / post (14d).
- Filtered to campaign items only.
- 10 dimensions: revenue, profit, orders, customers, AOV, qty, acquisition, repeat, wastage, post_retention.
- 5 trap types per SRS Step 28:
  1. trap_sales_profit (revenue ↑, profit ↓)
  2. trap_customers_margin (customers ↑, margin ↓ ≥10%)
  3. trap_wastage (wastage ≥50% increase)
  4. trap_promo_only (promo-only ≥95% AND post_retention <20%)
  5. trap_margin_shift (profit_pct < -20%)
- Campaign is a trap if trap_count >= 2.

### 3.7 Rating Analysis
- Ratings vs: item, location, profitability, sales, repeat purchase, time, promotion.
- Anomalies: concentration, spike, drop, identical.
- Inconsistencies: high rating + low sales, or low rating + high sales.

### 3.8 Sales Anomalies
- Spike, drop, order value, discount, duplicate transaction, unexpected demand.

### 3.9 Wastage Risk Model
- Random Forest + Logistic Regression.
- Features (all from past only): lag_demand_7d, lag_demand_30d, hist_wastage_before, dow_num, month_num, is_promo, popularity_rank_train.
- Label: wastage_qty >= Q75.
- Temporal split by date.
- AUC ~ 0.77.

### 3.10 Churn Model
- 3 algorithms: Logistic, Random Forest, Gradient Boosting.
- 15 features from historical windows only.
- Temporal Cohort with Feature Cutoff:
  - Train: features to 2024-06-30, label 2024-07-01 to 2024-09-30
  - Val: features to 2024-08-31, label 2024-09-01 to 2024-10-31
  - Test: features to 2024-09-30, label 2024-10-01 to 2024-12-31
- AUC ~ 0.62.

### 3.11 Forecast
- Revenue Forecast: Linear Regression with time_index (matches Spark).
- Demand Forecast: 4 models compared:
  - Naive baseline (lag_1)
  - Moving Average (rolling_mean_7)
  - Linear Regression
  - Gradient Boosting with lag + calendar features
- Metrics: MAE, RMSE, MAPE, R².

### 3.12 Peak-Period Analysis
- by hour, day, weekend, month, location, channel, location-hour, channel-hour.
- Summary: peak_hour, peak_day, peak_month, peak_channel, peak_location.

### 3.13 Slow-Moving Dishes
7 criteria (SRS Step 32):
1. Low sales volume (Q25)
2. Low purchase frequency (Q25)
3. Long gaps between purchases (Q75)
4. Low repeat purchase (Q25)
5. High wastage (Q75)
6. Weak profitability (Q25)
7. Poor trend (H2 < H1)

Item is slow-moving if criteria_met >= 2.

## 4. Key Results

### 4.1 Bundle Rules (Top 5 by lift)
- Fresh Mint Lemonade + Pancakes — support 0.0051, confidence 0.185, lift 4.73
- Kofta Kebab + Carbonara — support 0.0517, confidence 0.462, lift 4.03
- Lemonade + Foul Medames — support 0.0099, confidence 0.364, lift 3.85
- Hummus + Shakshuka — support 0.0072, confidence 0.162, lift 3.77
- Lamb Kebab + Foul Medames — support 0.0052, confidence 0.351, lift 3.70

### 4.2 Promotion Traps
Total trap campaigns: 7 out of 30.
- trap_sales_profit: 7
- trap_customers_margin: 1
- trap_wastage: 26
- trap_promo_only: 5
- trap_margin_shift: 6

### 4.3 Wastage Risk
Rule-based:
- High: 729 (item, location) pairs
- Medium: 305
- Low: 1,965

ML model:
- Test AUC 0.77 (no leakage)

### 4.4 Churn Model (Temporal Cohort Feature Cutoff)
Cohorts:
- Train: 21,038 customers, churn 0.620
- Val: 26,585 customers, churn 0.778
- Test: 28,534 customers, churn 0.657

Results:
- Logistic: val_auc 0.6243, test_auc 0.6360, test_f1 0.7076
- Random Forest: val_auc 0.6263, test_auc 0.6087, test_f1 0.6967
- Gradient Boosting: val_auc 0.6178, test_auc 0.5924, test_f1 0.7775

### 4.5 Revenue Forecast (Linear Regression, 100-day test)
- Coef 76.29, Intercept 38,790
- MAE 27,961, RMSE 44,850, MAPE 24.09%

### 4.6 Demand Forecast (4 models × 3 levels)

| Level | Model | MAE | R² |
|---|---|---:|---:|
| item | naive_baseline | 23.66 | 0.14 |
| item | **moving_average** | 24.48 | **0.38** |
| item | linear_regression | 39.99 | -6.74 |
| item | gradient_boosting | 30.03 | -2.16 |
| category | naive_baseline | 149.86 | 0.59 |
| category | **moving_average** | 150.56 | **0.64** |
| category | linear_regression | 307.62 | -0.68 |
| category | gradient_boosting | 289.79 | -0.55 |
| location | naive_baseline | 105.20 | 0.36 |
| location | **moving_average** | 84.13 | **0.57** |
| location | linear_regression | 151.84 | -0.55 |
| location | gradient_boosting | 192.70 | -1.27 |

**Honest finding:** Moving Average outperforms Linear Regression and Gradient Boosting on all levels. This is expected on synthetic data with high noise.

### 4.7 Peak Periods
- Peak hour: 16
- Peak day: Saturday
- Peak month: 12
- Peak channel: Dine-in
- Peak location: 9

### 4.8 Slow-Moving Dishes
- 54 slow-moving items out of 150 (criteria_met >= 2)
- Distribution: 0=49, 1=47, 2=14, 3=11, 4=15, 5=13, 6=1

### 4.9 Multivariate Price Elasticity
- 150 items analyzed.
- Distribution: inelastic=147, elastic=2, moderately_elastic=1.
- Price-repeat correlation: 0.006 (no relationship in synthetic data).

## 5. Independence from Spark
- Python uses scikit-learn, Spark uses MLlib.
- Python never reads Spark predictions for training.
- Same revenue definition.
- Same chronological split (266/100) for the shared task.
- Same feature (time_index) for the shared task.
- Comparison only at Stage 13.

## 6. Evidence
All outputs in `python_pipeline/results/parquet/` organized by stage.
- **67/67 pytest tests passing.**
- Every script runs standalone.
- Constants in `config.py`.
- Model versions in `model_versions.json`.

## 7. Limitations
- Synthetic data leads to moderate AUC (~0.62 churn, ~0.77 wastage).
- 100-day test period matches Spark for the shared task.
- `preparation_quantity` not available for wastage analysis.
- Spark comparison pending receipt of `spark_forecast_results.parquet`.
- Price-repeat correlation is near zero due to synthetic data characteristics.

## 8. Handoff
Outputs ready for Student 4 in `handoff_to_student4.md`.

## 9. Threshold Documentation

All thresholds used in this pipeline are **team-selected analytical thresholds**, not universal scientific standards. They are documented in `config.py` and were chosen based on:

- Domain reasoning (e.g., lift > 1.2 for weak association filtering)
- Distribution analysis (e.g., Q75 for high-waste labeling)
- Business interpretability (e.g., 10% match threshold for dual pipeline)

## 10. Temporal Split Documentation

### Churn Model — Temporal Cohort with Feature Cutoff
- Split method: `temporal_cohort_feature_cutoff`
- Train: features to 2024-06-30, label 2024-07-01 → 2024-09-30 (21,038 customers)
- Val: features to 2024-08-31, label 2024-09-01 → 2024-10-31 (26,585 customers)
- Test: features to 2024-09-30, label 2024-10-01 → 2024-12-31 (28,534 customers)
- No random split. No data leakage.
- Each cohort uses a DIFFERENT feature window and label window.

### Wastage Risk Model — Temporal by Date
- Split method: temporal_by_date
- Train: 2024-01-01 to 2024-08-08 (28,492)
- Val: 2024-08-08 to 2024-10-19 (9,497)
- Test: 2024-10-19 to 2024-12-31 (9,498)
- Features use only past information (lag / cumulative shift).
- Popularity rank computed from Train only.

### Forecast (Revenue + Demand)
- Split method: chronological
- Train: 266 days
- Test: 100 days
- No random split.

## 11. Forecast Honest Reporting

### Revenue Forecast (Linear Regression)
- MAE 27,961 | RMSE 44,850 | MAPE 24.09%
- Matches Spark baseline (same features).
- Test cases: 100.

### Demand Forecast — 4 Models Compared

| Level | Model | MAE | R² |
|---|---|---:|---:|
| item | naive_baseline | 23.66 | 0.14 |
| item | **moving_average** | 24.48 | **0.38** |
| item | linear_regression | 39.99 | -6.74 |
| item | gradient_boosting | 30.03 | -2.16 |
| category | naive_baseline | 149.86 | 0.59 |
| category | **moving_average** | 150.56 | **0.64** |
| category | linear_regression | 307.62 | -0.68 |
| category | gradient_boosting | 289.79 | -0.55 |
| location | naive_baseline | 105.20 | 0.36 |
| location | **moving_average** | 84.13 | **0.57** |
| location | linear_regression | 151.84 | -0.55 |
| location | gradient_boosting | 192.70 | -1.27 |

**Honest finding:** Moving Average outperforms Linear Regression and Gradient Boosting on all levels. This is documented without manipulation.

## 12. Churn Model Performance

- Split method: `temporal_cohort_feature_cutoff` (no random split)
- Train: 21,038 | Val: 26,585 | Test: 28,534
- Logistic: val_auc 0.6243, test_auc 0.6360, test_f1 0.7076
- Random Forest: val_auc 0.6263, test_auc 0.6087, test_f1 0.6967
- Gradient Boosting: val_auc 0.6178, test_auc 0.5924, test_f1 0.7775
- Note: AUC around 0.62 reflects the underlying signal in the synthetic dataset. Performance is clearly above random (0.5).

## 13. Wastage Risk Model Performance

- Split method: temporal_by_date
- Train: 28,492 | Val: 9,497 | Test: 9,498
- Logistic: val_auc 0.7715, test_auc 0.7740, test_f1 0.5755
- Random Forest: val_auc 0.7604, test_auc 0.7580, test_f1 0.5654
- All features use past information only (no leakage).
- Popularity rank computed from Train only.

## 14. Price Elasticity — Multivariate Extension

Additional multivariate model:

log(quantity) = β0 + β1 log(price) + β2 has_promo + β3 weekend + β4 month + ε

Elasticity = β1 (coefficient of log price).

Output: `07_price/multivariate_elasticity.parquet`

Columns: menu_item_id, multivariate_elasticity, model_r2, n_days, has_promo_coef, weekend_coef, mv_class.

Distribution: inelastic=147, elastic=2, moderately_elastic=1.

## 15. Slow-Moving Dishes — 7 Criteria

SRS Step 32 criteria implemented:
1. Low sales volume (Q25)
2. Low purchase frequency (Q25)
3. Long gaps between purchases (Q75)
4. Low repeat purchase (Q25)
5. High wastage (Q75)
6. Weak profitability (Q25)
7. Poor trend (H2 < H1)

Item is slow-moving if criteria_met >= 2.

Result: 54 slow-moving items out of 150.

Distribution: 0=49, 1=47, 2=14, 3=11, 4=15, 5=13, 6=1.

## 16. Edge-Case Tests

File: `tests/test_business_edge_cases.py` (14 tests)

Covers SRS Steps 10, 11, 28, 30, 31, 32, 36:
- high-selling loss-making exists
- low-selling high-margin exists
- popular high-wastage exists
- promotion trap sales up profit down
- 5 trap types documented
- churn customers identified
- churn customers have higher recency
- rating anomaly types
- rating inconsistencies
- sales anomaly types
- duplicate + unexpected demand files
- price sensitivity classes
- multivariate elasticity exists
- slow-moving 7 criteria

## 17. Evidence Summary

- Total Python scripts: 19 in `python_pipeline/src/`
- **Total pytest tests: 67 (all passing)**
- Total parquet outputs: ~80 across 18 stage folders
- Total ML models saved: 4 (3 churn + 1 wastage risk)
- Scalers saved: 2 (churn + wastage)
- Metadata files: 1 (model_versions.json)
- Reports: 2 (this report + handoff_to_student4.md)
- AI declaration: 1 (AI_USAGE.md)

## 18. What's Pending

- Spark predictions on the same 100 test cases.
- Dual pipeline comparison completion.
- Agreement percentage calculation.

The Python side is fully ready and the comparison runs automatically once `spark_forecast_results.parquet` is received in `python_pipeline/external/`.