# Automated Test Results

- Run at: 2026-09-29 04:00
- Python: 3.14.2 on Linux 6.8.0-1064-azure
- Data directory: `/workspaces/dineiq-analytics-data-engineering/full_output`
- pytest exit code: 0

| Passed | Failed | Errors | Skipped |
|---|---|---|---|
| 146 | 0 | 0 | 18 |

| Module | Test | Status | Time (s) | Note |
|---|---|---|---|---|
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Order_Items-1000000] | passed | 0.535 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Customers-50000] | passed | 0.016 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Menu_Items-150] | passed | 0.002 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Menu_Categories-10] | passed | 0.002 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Restaurants-20] | passed | 0.002 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Ratings-100000] | passed | 0.081 |  |
| test_01_volume_and_history | test_row_count_meets_srs_minimum[Wastage-50000] | passed | 0.041 |  |
| test_01_volume_and_history | test_at_least_100k_unique_orders | passed | 0.125 |  |
| test_01_volume_and_history | test_twelve_active_months_of_history | passed | 0.044 |  |
| test_01_volume_and_history | test_multiple_historical_prices | passed | 0.002 |  |
| test_01_volume_and_history | test_multiple_promotion_campaigns | passed | 0.002 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Customers] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Restaurants] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Menu_Categories] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Menu_Items] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Pricing_History] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Promotions] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Promotion_Items] | passed | 0.002 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Orders] | passed | 0.000 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Order_Items] | passed | 0.001 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Ratings] | passed | 0.000 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Inventory] | passed | 0.116 |  |
| test_02_schema | test_raw_csv_has_documented_columns[Wastage] | passed | 0.001 |  |
| test_02_schema | test_parquet_has_documented_columns[Customers] | passed | 0.019 |  |
| test_02_schema | test_parquet_has_documented_columns[Restaurants] | passed | 0.002 |  |
| test_02_schema | test_parquet_has_documented_columns[Menu_Categories] | passed | 0.002 |  |
| test_02_schema | test_parquet_has_documented_columns[Menu_Items] | passed | 0.003 |  |
| test_02_schema | test_parquet_has_documented_columns[Pricing_History] | passed | 0.002 |  |
| test_02_schema | test_parquet_has_documented_columns[Promotions] | passed | 0.003 |  |
| test_02_schema | test_parquet_has_documented_columns[Promotion_Items] | passed | 0.002 |  |
| test_02_schema | test_parquet_has_documented_columns[Orders] | passed | 0.017 |  |
| test_02_schema | test_parquet_has_documented_columns[Order_Items] | passed | 0.080 |  |
| test_02_schema | test_parquet_has_documented_columns[Ratings] | passed | 0.007 |  |
| test_02_schema | test_parquet_has_documented_columns[Inventory] | passed | 0.018 |  |
| test_02_schema | test_parquet_has_documented_columns[Wastage] | passed | 0.006 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Customers] | passed | 0.001 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Restaurants] | passed | 0.001 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Menu_Categories] | passed | 0.001 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Menu_Items] | passed | 0.001 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Pricing_History] | passed | 0.001 |  |
| test_02_schema | test_master_primary_key_is_positive_and_not_null[Promotions] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Customers] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Restaurants] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Menu_Categories] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Menu_Items] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Pricing_History] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Promotions] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Ratings] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Inventory] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_primary_key_is_unique[Wastage] | passed | 0.001 |  |
| test_03_keys_and_relationships | test_promotion_items_composite_key_is_unique | passed | 0.001 |  |
| test_03_keys_and_relationships | test_master_foreign_key_resolves[Menu_Items-category_id-Menu_Categories-category_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_master_foreign_key_resolves[Pricing_History-menu_item_id-Menu_Items-menu_item_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_master_foreign_key_resolves[Promotion_Items-promotion_id-Promotions-promotion_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_master_foreign_key_resolves[Promotion_Items-menu_item_id-Menu_Items-menu_item_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Orders-customer_id-Customers-customer_id] | passed | 0.029 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Orders-restaurant_id-Restaurants-restaurant_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Orders-promotion_id-Promotions-promotion_id] | passed | 0.007 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Order_Items-order_id-Orders-order_id] | passed | 0.036 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Order_Items-menu_item_id-Menu_Items-menu_item_id] | passed | 0.096 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Ratings-menu_item_id-Menu_Items-menu_item_id] | passed | 0.009 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Ratings-restaurant_id-Restaurants-restaurant_id] | passed | 0.007 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Ratings-customer_id-Customers-customer_id] | passed | 0.018 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Inventory-menu_item_id-Menu_Items-menu_item_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Inventory-restaurant_id-Restaurants-restaurant_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Wastage-menu_item_id-Menu_Items-menu_item_id] | passed | 0.002 |  |
| test_03_keys_and_relationships | test_fact_foreign_key_mostly_resolves[Wastage-restaurant_id-Restaurants-restaurant_id] | passed | 0.002 |  |
| test_04_raw_defects | test_defect_is_present[missing_values] | passed | 0.536 |  |
| test_04_raw_defects | test_defect_is_present[duplicate_orders] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[duplicate_order_lines] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[invalid_menu_prices] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[negative_quantities] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[invalid_dates] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[invalid_ratings] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_present[missing_customer_ids] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[missing_menu_ids] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[invalid_restaurant_ids] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[impossible_wastage] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_present[incorrect_discounts] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[cancelled_transactions] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[inconsistent_units] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_present[invalid_location_references] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[missing_values] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_a_minority[duplicate_orders] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_a_minority[duplicate_order_lines] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[invalid_menu_prices] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[negative_quantities] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[invalid_dates] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[invalid_ratings] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[missing_customer_ids] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_a_minority[missing_menu_ids] | passed | 0.001 |  |
| test_04_raw_defects | test_defect_is_a_minority[invalid_restaurant_ids] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[impossible_wastage] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[incorrect_discounts] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[cancelled_transactions] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[inconsistent_units] | passed | 0.000 |  |
| test_04_raw_defects | test_defect_is_a_minority[invalid_location_references] | passed | 0.001 |  |
| test_05_business_rules | test_line_total_formula | passed | 0.021 |  |
| test_05_business_rules | test_order_total_formula | passed | 0.002 |  |
| test_05_business_rules | test_order_channels_are_documented | passed | 0.009 |  |
| test_05_business_rules | test_order_statuses_are_documented | passed | 0.004 |  |
| test_05_business_rules | test_ratings_target_an_item_or_a_location | passed | 0.001 |  |
| test_05_business_rules | test_promotion_end_not_before_start | passed | 0.002 |  |
| test_06_difficult_cases | test_high_selling_loss_making_dish | passed | 0.253 |  |
| test_06_difficult_cases | test_low_selling_high_margin_dish | passed | 0.002 |  |
| test_06_difficult_cases | test_popular_dish_with_excessive_wastage | passed | 0.005 |  |
| test_06_difficult_cases | test_new_menu_item_with_short_history | passed | 0.002 |  |
| test_06_difficult_cases | test_dish_performs_differently_across_locations | passed | 0.119 |  |
| test_06_difficult_cases | test_weekend_only_dish | passed | 0.064 |  |
| test_06_difficult_cases | test_promotion_dependent_dish | passed | 0.131 |  |
| test_06_difficult_cases | test_churned_customers | passed | 0.124 |  |
| test_06_difficult_cases | test_rating_spike | passed | 0.078 |  |
| test_06_difficult_cases | test_sales_spike | passed | 0.065 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Customers] | passed | 0.001 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Restaurants] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Menu_Categories] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Menu_Items] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Pricing_History] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Promotions] | passed | 0.001 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Promotion_Items] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Orders] | passed | 0.001 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Order_Items] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Ratings] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Inventory] | passed | 0.000 |  |
| test_07_parquet_parity | test_parquet_row_count_matches_csv[Wastage] | passed | 0.000 |  |
| test_08_clean_layer | test_orders_have_unique_non_null_ids | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_orders_have_customer_and_restaurant | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_order_lines_have_valid_values | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_ratings_are_whole_stars_1_to_5 | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_wastage_is_not_negative | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Orders-customer_id-Customers-customer_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Orders-restaurant_id-Restaurants-restaurant_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Order_Items-order_id-Orders-order_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Order_Items-menu_item_id-Menu_Items-menu_item_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Ratings-menu_item_id-Menu_Items-menu_item_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Wastage-menu_item_id-Menu_Items-menu_item_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_foreign_keys_fully_resolve[Wastage-restaurant_id-Restaurants-restaurant_id] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_cleaning_never_creates_rows[Orders] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_cleaning_never_creates_rows[Order_Items] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_cleaning_never_creates_rows[Ratings] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_cleaning_never_creates_rows[Inventory] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_cleaning_never_creates_rows[Wastage] | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_08_clean_layer | test_clean_order_lines_still_meet_srs_minimum | skipped | 0.000 | /workspaces/dineiq-analytics-data-engineering/full_output/processed_data/clean not found. Produced by Spark cleaning (Step 5). |
| test_audit | test_audit_requires_auth | passed | 0.342 |  |
| test_audit | test_audit_records_login | passed | 0.584 |  |
| test_auth | test_health | passed | 0.305 |  |
| test_auth | test_register_success | passed | 0.580 |  |
| test_auth | test_register_missing_fields | passed | 0.304 |  |
| test_auth | test_register_short_password | passed | 0.304 |  |
| test_auth | test_register_duplicate_email | passed | 0.577 |  |
| test_auth | test_login_success | passed | 0.579 |  |
| test_auth | test_login_wrong_password | passed | 0.579 |  |
| test_auth | test_me_without_token | passed | 0.307 |  |
| test_auth | test_me_with_token | passed | 0.581 |  |
| test_auth | test_refresh | passed | 0.579 |  |
| test_export | test_export_requires_auth | passed | 0.324 |  |
| test_export | test_export_csv | passed | 0.582 |  |
| test_export | test_export_xlsx | passed | 0.694 |  |
| test_export | test_export_unknown | passed | 0.580 |  |
| test_export | test_export_bad_format | passed | 0.584 |  |
| test_rbac | test_protected_requires_auth | passed | 0.305 |  |
| test_rbac | test_admin_can_list_locations | passed | 0.583 |  |
| test_rbac | test_admin_can_create_location | passed | 0.598 |  |
| test_rbac | test_permission_denied | passed | 0.856 |  |
