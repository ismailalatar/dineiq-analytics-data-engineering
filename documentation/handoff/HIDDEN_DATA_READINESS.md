\# Hidden-Data Readiness — Data Engineering



\*\*Purpose:\*\* Document how the Data Engineering pipeline handles data that

was not visible during development, as required by SRS Section 3 (p.41).



\---



\## 1. Scope



The SRS (Section 1.8, p.35) states:

> "The application will be tested using a hidden restaurant dataset

> unavailable before final evaluation. Hidden datasets may contain:

> missing values, duplicate orders, unknown menu items, new restaurant

> locations, price changes, unusual promotions, extreme wastage,

> seasonal changes."



The pipeline described in this package handles those scenarios without

code changes.



\---



\## 2. Expected Schema



The pipeline uses \*\*explicit schemas\*\* defined in

`spark\_jobs/ingestion/schemas.py`. Every table has a declared StructType.



When hidden data arrives:



1\. The Spark reader will attempt to match the declared schema.

2\. Type mismatches fail fast (no silent coercion).

3\. Missing columns are logged as `NULL`.

4\. Additional columns are ignored.

5\. All values are read with `mode="PERMISSIVE"` so malformed rows are not

&#x20;  silently dropped — they become NULL and are caught by the quality rules.



\### Table-by-table expected schema



See `documentation/data\_dictionary/data\_dictionary.json` for the complete

column list, types, nullability, and allowed values.



\---



\## 3. Handling Each Hidden-Data Scenario



\### 3.1 Missing values



\- Quality rule: `DQ1 - Missing values` counts NULL in critical columns.

\- Cleaning rule: `clean\_missing\_values` quarantines rows with NULL in

&#x20; required Orders columns.

\- Result: NULL rows are separated into `quarantine/`, the rest continues.



\### 3.2 Duplicate orders / lines



\- Quality rule: `DQ2`, `DQ3` count duplicates by `order\_id` /

&#x20; `order\_item\_id`.

\- Cleaning rule: `clean\_duplicate\_orders` and `clean\_duplicate\_order\_items`

&#x20; keep the first occurrence, quarantine the rest.

\- Result: unique keys guaranteed in Clean.



\### 3.3 Unknown menu items (menu\_item\_id not in Menu\_Items)



\- Quality rule: `DQ9 - Missing menu IDs` counts NULL.

\- Cleaning rule: `clean\_missing\_ids` quarantines rows.

\- Additionally, feature engineering uses LEFT JOINs so unknown items do

&#x20; not crash the pipeline — they simply lack item\_features.



\### 3.4 New restaurant locations



\- Quality rule: `DQ10` and `DQ15` detect restaurant\_id values not in the

&#x20; Restaurants table.

\- Cleaning rule: `clean\_invalid\_restaurant\_ids` quarantines those orders.

\- Result: no orphan references reach the cleaned layer.



\### 3.5 Price changes



\- The pipeline treats price as an attribute of each transaction line

&#x20; (`Order\_Items.unit\_price`).

\- Feature `price\_change\_pct` computes `(max\_price - min\_price) / min\_price`

&#x20; per item.

\- No hard-coded price ranges exist; any positive price is valid.



\### 3.6 Unusual promotions



\- The pipeline does not require promotions to exist. If a new promotion

&#x20; ID appears in Orders but not Promotions, the `promotion\_id` will be

&#x20; NULL after the LEFT JOIN during integration.

\- Promotion dependency is computed from `Orders.promotion\_id IS NOT NULL`.



\### 3.7 Extreme wastage



\- Quality rule: `DQ11 - Impossible wastage` compares each wastage record

&#x20; to the maximum closing quantity ever observed for the same

&#x20; (menu\_item\_id, restaurant\_id).

\- Cleaning rule: `clean\_impossible\_wastage` caps the value at the max.

\- Result: no impossible quantities survive cleaning.



\### 3.8 Seasonal changes



\- The pipeline does not assume specific months. Day-of-week and

&#x20; month-of-year are extracted from timestamps.

\- Any seasonal pattern present in the data will be picked up by

&#x20; feature engineering without modification.



\---



\## 4. What the Pipeline Guarantees



When hidden data is loaded:



1\. \*\*No hard-coded categories\*\* — statuses, channels, and units are read

&#x20;  as strings. The cleaning rules tolerate new values.

2\. \*\*No assumption about distribution\*\* — percentile-based thresholds

&#x20;  (Q75/Q25) are computed from the actual data.

3\. \*\*No assumption about dates\*\* — the pipeline uses relative logic

&#x20;  (`datediff`, `hour`, `dayofweek`) rather than absolute dates.

4\. \*\*No silent drops\*\* — every rejected row goes to `quarantine/`.

5\. \*\*Feature schema stability\*\* — the feature columns remain the same

&#x20;  regardless of the input data.



\---



\## 5. How to Run on Hidden Data



```bash

\# 1. Place hidden data as CSV in a new folder, keeping the same filenames.

\#    (Customers.csv, Orders.csv, Order\_Items.csv, ...)



\# 2. Point the pipeline at that folder by editing the paths in:

\#    spark\_jobs/ingestion/ingest.py -> RAW

\#    spark\_jobs/quality/engine.py  -> RAW

\#    spark\_jobs/cleaning/engine.py -> RAW

\#    spark\_jobs/features/joins.py  -> CLEAN



\# 3. Run the pipeline:

python -m spark\_jobs.tests.test\_u11\_ingestion

python -m spark\_jobs.tests.test\_u12\_quality

python -m spark\_jobs.tests.test\_u13\_cleaning

python -m spark\_jobs.tests.test\_u14\_features

python -m spark\_jobs.tests.test\_u15\_feature\_coverage



\# 4. Inspect reports and quarantine folder.

