\# DineIQ Analytics — Data Dictionary



\*\*Project:\*\* DineIQ Analytics · MenuMatrix Dining Intelligence · Data Science Intelligence Arena  

\*\*Source:\*\* DineIQ Analytics SRS v1.0  

\*\*Schema version:\*\* 1.0 (approved in U2 v1.2)  

\*\*Generated data:\*\* `full\_output/raw\_data/` (CSV) and `full\_output/parquet\_data/` (Parquet)



\---



\## Overview



This document describes all columns in the 12 tables that make up the DineIQ dataset:

11 business tables from SRS p.25, plus the technical `Promotion\_Items` junction table derived from SRS FR viii.



Two layers are distinguished throughout:



\- \*\*Raw layer\*\* (`raw\_data/`) — contains intentional data-quality defects required by SRS Step 4 (missing values, duplicates, invalid prices, etc.).

\- \*\*Cleaned layer\*\* (produced in a later stage) — enforces integrity constraints listed below.



The `Nullable` column below describes the \*\*Cleaned Layer\*\* expectation.



\---



\## 1. Customers



\*\*Purpose:\*\* Customer identifiers and registration dates used for customer lifecycle and segmentation analytics.  

\*\*Primary key:\*\* `customer\_id`  

\*\*Foreign keys:\*\* none.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| customer\_id | BIGINT | NO | PK | Unique customer identifier. | Positive integer |

| registration\_date | DATE | YES | | Date the customer registered. Supports new-customer and churn-risk detection. | Any valid date |



\---



\## 2. Restaurants



\*\*Purpose:\*\* Restaurant / location master data used for multi-location intelligence.  

\*\*Primary key:\*\* `restaurant\_id`  

\*\*Foreign keys:\*\* none.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| restaurant\_id | BIGINT | NO | PK | Unique restaurant / location identifier. | Positive integer |

| restaurant\_name | VARCHAR | YES | | Display name of the restaurant location. | Free text |

| city | VARCHAR | YES | | City where the location operates. | Free text |



\---



\## 3. Menu\_Categories



\*\*Purpose:\*\* Menu item categories.  

\*\*Primary key:\*\* `category\_id`  

\*\*Foreign keys:\*\* none.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| category\_id | BIGINT | NO | PK | Unique category identifier. | Positive integer |

| category\_name | VARCHAR | YES | | Category name. | Appetizers, Main Course, Grills, Seafood, Beverages, Desserts, Salads, Breakfast, Pasta, Rice \& Sides |



\---



\## 4. Menu\_Items



\*\*Purpose:\*\* Menu item master data: names, categories, prices, costs, availability.  

\*\*Primary key:\*\* `menu\_item\_id`  

\*\*Foreign keys:\*\* `category\_id` → `Menu\_Categories.category\_id`



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| menu\_item\_id | BIGINT | NO | PK | Unique menu item identifier. | Positive integer |

| category\_id | BIGINT | NO | FK | Foreign key to Menu\_Categories. | Existing category\_id |

| item\_name | VARCHAR | YES | | Menu item name. | Free text |

| description | VARCHAR | YES | | Menu item description. | Free text |

| base\_price | DECIMAL(10,2) | YES | | Current / base selling price. | > 0 |

| standard\_cost | DECIMAL(10,2) | YES | | Current standard cost. | > 0 |

| availability | BOOLEAN | YES | | Whether the item is currently sellable. | true, false |

| unit\_of\_measure | VARCHAR | YES | | Unit of measure for quantities. | portion, plate, bowl, glass, piece |



\---



\## 5. Pricing\_History



\*\*Purpose:\*\* Historical price records per menu item; drives price-change analytics.  

\*\*Primary key:\*\* `pricing\_history\_id`  

\*\*Foreign keys:\*\* `menu\_item\_id` → `Menu\_Items.menu\_item\_id`



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| pricing\_history\_id | BIGINT | NO | PK | Surrogate key. | Positive integer |

| menu\_item\_id | BIGINT | NO | FK | Foreign key to Menu\_Items. | Existing menu\_item\_id |

| effective\_date | DATE | YES | | Date on which this price becomes effective. | Any valid date |

| unit\_price | DECIMAL(10,2) | YES | | Selling price in effect from this date. | > 0 |



\---



\## 6. Promotions



\*\*Purpose:\*\* Promotion campaigns: discounts, coupons, campaign periods.  

\*\*Primary key:\*\* `promotion\_id`  

\*\*Foreign keys:\*\* none.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| promotion\_id | BIGINT | NO | PK | Unique promotion identifier. | Positive integer |

| promotion\_name | VARCHAR | YES | | Promotion campaign name. | Free text |

| discount\_type | VARCHAR | YES | | Type of discount applied. | percentage, fixed\_amount |

| discount\_value | DECIMAL(10,2) | YES | | Discount amount or percentage. | > 0 |

| coupon\_code | VARCHAR | YES | | Optional coupon code. | Free text or NULL |

| start\_date | DATE | YES | | Promotion start date. | Any valid date |

| end\_date | DATE | YES | | Promotion end date. | Any valid date >= start\_date |



\---



\## 7. Promotion\_Items



\*\*Purpose:\*\* Technical junction linking promotions to the menu items they apply to.  

\*\*Primary key:\*\* `(promotion\_id, menu\_item\_id)`  

\*\*Foreign keys:\*\* both columns are foreign keys.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| promotion\_id | BIGINT | NO | PK, FK | Foreign key to Promotions. | Existing promotion\_id |

| menu\_item\_id | BIGINT | NO | PK, FK | Foreign key to Menu\_Items. | Existing menu\_item\_id |



\---



\## 8. Orders



\*\*Purpose:\*\* Order header data: customer, restaurant, promotion, channel, status, monetary totals.  

\*\*Primary key:\*\* `order\_id`  

\*\*Foreign keys:\*\* `customer\_id`, `restaurant\_id`, `promotion\_id` (nullable).



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| order\_id | BIGINT | NO | PK | Unique order identifier. | Positive integer |

| customer\_id | BIGINT | YES | FK | Customer who placed the order. | Existing customer\_id or NULL (raw) |

| restaurant\_id | BIGINT | YES | FK | Restaurant fulfilling the order. | Existing restaurant\_id or NULL (raw) |

| promotion\_id | BIGINT | YES | FK | Promotion applied to the order. | Existing promotion\_id or NULL |

| order\_timestamp | TIMESTAMP | YES | | Exact date and time of the order. | Any valid timestamp |

| order\_channel | VARCHAR | YES | | Ordering channel. | Dine-in, Takeaway, Restaurant Website/App, Third-party delivery platforms, Other supported channels |

| order\_status | VARCHAR | YES | | Order status. | completed, cancelled, refunded, pending |

| subtotal | DECIMAL(12,2) | YES | | Sum of line gross values (pre-discount). | >= 0 |

| discount\_total | DECIMAL(12,2) | YES | | Sum of line discount amounts. | >= 0 |

| total\_amount | DECIMAL(12,2) | YES | | subtotal - discount\_total. | Any decimal (raw may include anomalies) |



\---



\## 9. Order\_Items



\*\*Purpose:\*\* Order line detail: quantity, price, cost, discount, line total.  

\*\*Primary key:\*\* `order\_item\_id`  

\*\*Foreign keys:\*\* `order\_id`, `menu\_item\_id`



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| order\_item\_id | BIGINT | NO | PK | Unique order-line identifier. | Positive integer |

| order\_id | BIGINT | YES | FK | Parent order. | Existing order\_id or NULL (raw) |

| menu\_item\_id | BIGINT | YES | FK | Menu item sold. | Existing menu\_item\_id or NULL (raw) |

| quantity | DECIMAL(10,2) | YES | | Quantity sold in Menu\_Items.unit\_of\_measure. | > 0 |

| unit\_price | DECIMAL(10,2) | YES | | Actual selling price at order time (from Pricing\_History). | > 0 |

| unit\_cost | DECIMAL(10,2) | YES | | Actual cost at order time. | > 0 |

| discount\_amount | DECIMAL(12,2) | YES | | Discount applied to this line. | >= 0 |

| line\_total | DECIMAL(12,2) | YES | | quantity \* unit\_price - discount\_amount. | Any decimal (raw may include anomalies) |



\---



\## 10. Ratings



\*\*Purpose:\*\* Customer ratings for menu items and/or restaurant locations.  

\*\*Primary key:\*\* `rating\_id`  

\*\*Foreign keys:\*\* `customer\_id`, `menu\_item\_id` (nullable), `restaurant\_id` (nullable).  

\*\*Cleaned-layer rule:\*\* at least one of `menu\_item\_id` / `restaurant\_id` must be non-null.



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| rating\_id | BIGINT | NO | PK | Unique rating identifier. | Positive integer |

| customer\_id | BIGINT | YES | FK | Customer who submitted the rating. | Existing customer\_id or NULL |

| menu\_item\_id | BIGINT | YES | FK | Rated menu item. | Existing menu\_item\_id or NULL |

| restaurant\_id | BIGINT | YES | FK | Rated restaurant location. | Existing restaurant\_id or NULL |

| rating\_value | INTEGER | YES | | Star rating value. | 1 to 5 (raw may contain invalid values) |

| rating\_timestamp | TIMESTAMP | YES | | When the rating was submitted. | Any valid timestamp |



\---



\## 11. Inventory



\*\*Purpose:\*\* Weekly inventory snapshots per menu item and restaurant.  

\*\*Primary key:\*\* `inventory\_id`  

\*\*Foreign keys:\*\* `menu\_item\_id`, `restaurant\_id`



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| inventory\_id | BIGINT | NO | PK | Unique snapshot identifier. | Positive integer |

| menu\_item\_id | BIGINT | NO | FK | Item tracked. | Existing menu\_item\_id |

| restaurant\_id | BIGINT | NO | FK | Location holding the inventory. | Existing restaurant\_id |

| inventory\_date | DATE | YES | | Week start date of the snapshot. | Any valid date |

| opening\_quantity | DECIMAL(12,3) | YES | | Quantity at start of the week. | >= 0 |

| replenishment\_quantity | DECIMAL(12,3) | YES | | Quantity replenished during the week. | >= 0 |

| consumption\_quantity | DECIMAL(12,3) | YES | | Quantity consumed (derived from orders). | >= 0 |

| closing\_quantity | DECIMAL(12,3) | YES | | Quantity at end of the week. | >= 0 |

| unit\_of\_measure | VARCHAR | YES | | Unit of measure (matches Menu\_Items). | portion, plate, bowl, glass, piece |



\---



\## 12. Wastage



\*\*Purpose:\*\* Food wastage records: quantity, cost, reason, item, location, date.  

\*\*Primary key:\*\* `wastage\_id`  

\*\*Foreign keys:\*\* `menu\_item\_id`, `restaurant\_id`



| Column | Type | Nullable | Key | Description | Allowed / Expected values |

|---|---|---|---|---|---|

| wastage\_id | BIGINT | NO | PK | Unique wastage record identifier. | Positive integer |

| menu\_item\_id | BIGINT | NO | FK | Wasted menu item. | Existing menu\_item\_id |

| restaurant\_id | BIGINT | NO | FK | Location where the waste occurred. | Existing restaurant\_id |

| wastage\_date | DATE | YES | | Date of the waste record. | Any valid date |

| quantity\_wasted | DECIMAL(12,3) | YES | | Quantity wasted (may exceed inventory in raw). | >= 0 |

| unit\_of\_measure | VARCHAR | YES | | Unit of measure (matches Menu\_Items). | portion, plate, bowl, glass, piece |

| wastage\_cost | DECIMAL(10,2) | YES | | Cost of the wasted quantity. | >= 0 |

| wastage\_reason | VARCHAR | YES | | Reason for the waste. | spoilage, expired, preparation error, overproduction, quality issue |



\---



\*\*End of Data Dictionary.\*\*

