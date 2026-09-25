# Development Log — Data Engineering

Chronological tracking of work completed, dataset changes, failures,
fixes, and performance improvements during the Data Engineering phase
(SRS Steps 1–7).

**Role:** Data Engineering & Big Data Foundation
**Team Member:** 
**SRS Reference:** DineIQ Analytics SRS v1.0
**Final Seed:** 42

---

## Phase 1 — Requirements and Data Model

**Work completed:**
- Extracted all SRS requirements relevant to Steps 1–7.
- Designed the 12-table data model:
  11 business tables (Customers, Restaurants, Menu_Categories, Menu_Items,
  Pricing_History, Promotions, Orders, Order_Items, Ratings, Inventory,
  Wastage) plus 1 technical junction table (Promotion_Items) derived from
  SRS FR viii — "applicable menu items".
- Documented all PK/FK relationships and cardinalities.
- Produced the Entity-Relationship Diagram.
- Locked the schema before any code was written.

**Dataset changes:** None (design phase).

**Failures:** None.

---

## Phase 2 — Dataset Generator

**Work completed:**
- Built `data_generator/` as a reproducible Python package (seed=42).
- Implemented 8 generator modules:
  dimensions, pricing, promotions, orders, ratings, inventory, wastage,
  anomalies.
- Implemented a validation engine with 53 checks derived directly from
  SRS requirements.
- Generated the full dataset:
  - 100,000 unique orders
  - 1,068,101 order lines
  - 50,000 customers
  - 150 menu items across 10 categories
  - 20 restaurant locations
  - 100,512 ratings
  - 50,000 wastage records
  - 687 pricing history records
  - 30 promotion campaigns
  - 365 days of transaction history (2024-01-01 → 2024-12-31)

**Dataset changes made during development:**
- Initial `order_channel` values (`Delivery`, `Mobile App`) were replaced
  with the exact SRS Step 35 wording:
  `Third-party delivery platforms` and `Restaurant Website/App`.
- Sales anomaly "drop" multiplier was strengthened from 0.05 to 0.01 so
  the drop is statistically detectable using ratio-based checks.
- Weekend and seasonal weights were added to the day-selection logic.
- `customer_id` was added to the Ratings table to support per-customer
  rating anomaly detection (SRS Step 30).
- `Pricing_History.unit_cost` was removed because SRS FR v only requires
  historical *prices*, not historical *costs*.
- `launch_date` was added to `Menu_Items`. Rationale: SRS Step 11
  requires distinguishing a genuinely new item ("new menu item with
  insufficient history") from an old item whose first order simply occurred
  late. `_first_available_date` alone is circular — it reflects the first
  order date, not the launch date. `launch_date` is a proper column saved
  in the cleaned dataset, with the constraint:
  `launch_date <= first order date`.

**Failures encountered and resolved:**
1. `DatetimeIndex.dt` AttributeError on the registration-date column —
   replaced `.dt.date` with direct `.date`.
2. Loss-making flag conflicted with profitable-low-selling on the same item
   — resolved via a **mutual-exclusion rule** (see section below).
3. Promo orders were being assigned outside the promotion window — fixed
   by comparing day indices and treating the end date as inclusive of the
   entire day.
4. Sales drops were not detectable using z-score — strengthened the drop
   multiplier and switched to ratio-based detection.
5. New items with insufficient history were not detectable — expanded
   their sampling weight and reduced the reference window.
6. `Int64` extension dtype not understood by NumPy — replaced
   `.astype("Int64")` with `pd.array(..., dtype="Int64")`.

**Tests performed (all PASS):**
- U3 (Dimensions): 30 PASS / 0 FAIL
- U4 (Pricing + Promotions): 23 PASS / 0 FAIL
- U5 (Orders + Lines): 22 PASS / 0 FAIL
- U6 (Ratings + Inventory + Wastage): 19 PASS / 0 FAIL
- U7 (Anomaly Injection): 18 PASS / 0 FAIL
- U8 (Full Validation): 53 PASS / 0 FAIL
- U10 (Data Dictionary): 72 PASS / 0 FAIL

### Mutual Exclusion Logic (not a hard-coded insight)

A design rule was applied during dimension generation:

    flags["_is_loss_making"][loss_idx] = True
    flags["_is_profitable_low_selling"][flags["_is_loss_making"]] = False

Reasoning:
- `_is_loss_making` = (standard_cost > base_price) — a mathematical
  definition.
- `_is_profitable_low_selling` = (high margin AND low quantity) — also a
  mathematical definition.
- The two conditions are mutually exclusive: if cost > price, margin
  cannot be positive.
- Applying this rule removes a logical contradiction, not a statistical
  pattern.

This is NOT a hard-coded insight. It is a mutual-exclusion constraint
derived strictly from the definitions. No external thresholds or external
decisions are involved.

---

## Phase 3 — Spark Pipeline

**Work completed:**
- Built `spark_jobs/` package with 4 stages:
  ingestion, quality, cleaning, features.
- Implemented explicit schemas for all 12 tables.
- Implemented 15 data-quality rules matching SRS Step 4 (all 15 defects
  detected).
- Implemented 13 documented cleaning rules with a quarantine directory
  for every rejected row.
- Implemented the 10 required joins from SRS Step 6.
- Implemented the 22 required features from SRS Step 7.
- Wrote Parquet outputs for all intermediate and final stages.

**Failures encountered and resolved:**
1. `HADOOP_HOME and hadoop.home.dir are unset` on Windows — resolved by
   installing `winutils.exe` and `hadoop.dll` in `D:\hadoop\bin` and
   setting `HADOOP_HOME=D:\hadoop`.
2. `log_step()` attempted to call `.count()` on Python strings for
   multi-table steps — fixed with a `_count_any` helper that safely
   handles DataFrames, tuples, None, and strings.
3. `customer_features` returned only 41,201 rows (INNER JOIN dropped
   customers whose orders were all quarantined) — fixed by using
   LEFT JOIN from the Customers dimension so all 50,000 customers appear
   with `monetary = 0` and recency measured from registration. Required
   for SRS Step 36 (Churn Analysis).
4. DQ15 "Invalid location references" was a duplicate of DQ10 (both
   checked `Orders.restaurant_id` only) — fixed by broadening DQ15 to
   cover Orders + Inventory + Wastage.

**Feature Engineering corrections (after external audit):**

1. `repeat_purchase_rate` was `distinct_customers / distinct_orders`
   (wrong) — corrected to
   `customers_with_2+_orders / total_customers`.
2. `peak_hour_frequency` was a global hourly count — corrected to a
   per-order `is_peak_hour` flag in `order_features`.
3. `basket_size` was a customer-grain average — corrected to a
   per-order line count in `order_features`.
4. `location_performance` was revenue per location — corrected to
   per-(location, item) in `location_item_features`.
5. `channel_preference` was orders per channel — corrected to a
   per-customer `preferred_channel` in `customer_features`.
6. `rating_trend` was missing — added as
   `(recent_half_avg - early_half_avg)` per item.

**Tests performed (all PASS):**
- U11 (Spark Ingestion): 16 PASS / 0 FAIL
- U12 (Data Quality): 17 PASS / 0 FAIL
- U13 (Cleaning): 30 PASS / 0 FAIL
- U14 (Features): 15 PASS / 0 FAIL
- U15 (Feature Coverage): 69 PASS / 0 FAIL

---

## Performance

| Stage | Runtime |
|---|---:|
| Dataset generation (full) | ~26 s |
| Spark ingestion | ~166 s |
| Data quality (Spark) | ~27 s |
| Cleaning (Spark) | ~76 s |
| Feature engineering (Spark) | ~48 s |
| Feature coverage (pandas) | ~5 s |

---

## Assumptions and Limitations

- All data is synthetic; generation is seed-controlled (seed=42).
- The transaction window is calendar year 2024
  (2024-01-01 → 2024-12-31).
- Data-quality defects are intentional and required by SRS Step 4.
- Q75/Q25 percentiles are used as classification thresholds for the
  "difficult business cases". This is a design decision, not an SRS
  requirement. It is documented in the Data Dictionary.
- Timezone is treated as local restaurant time.
- Currency is unspecified; all monetary values use the same unit.

---

## Change Summary vs Previous Version

| Change | Reason | Impact |
|---|---|---|
| Added `launch_date` to Menu_Items | SRS Step 11 — new-item detection | Schema update; regenerated dataset |
| Fixed 5 features in engineering.py | External audit found wrong formulas | Feature tables rewritten |
| Broadened DQ15 | Duplicate of DQ10 | Data quality report updated |
| LEFT JOIN for customer_features | Churn analysis completeness | 50,000 rows (was 41,201) |
| Strengthened sales drop multiplier | Detection threshold | Sales anomalies now visible |

---

## Final State

All Data Engineering deliverables for SRS Steps 1–7 are complete,
tested, and reproducible. The full pipeline runs end-to-end from a single
seed and produces:

- Raw CSV (12 tables)
- Raw Parquet (12 tables)
- Spark-processed Parquet (12 tables)
- Cleaned Parquet (12 tables)
- Quarantine Parquet (per cleaning rule)
- Feature Parquet (5 tables)
- JSON reports for each stage

Every artifact is reproducible by re-running the pipeline with seed=42.