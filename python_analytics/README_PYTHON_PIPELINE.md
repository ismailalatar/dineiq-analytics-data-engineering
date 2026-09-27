# Python Data Science Pipeline — Student 3

**Project:** DineIQ Analytics
**Role:** Python Data Science & Business Analytics

## Overview

Independent Python pipeline for restaurant analytics. Reads clean data from Student 1. Uses scikit-learn only. Never consumes Spark predictions. Comparison performed only at Stage 13.

## Requirements

- Python 3.11+
- pandas, numpy, scikit-learn, pyarrow, pytest

## Setup

pip install -r requirements.txt

## Running

Run stages in order:

python -m python_pipeline.src.00_load_data
python -m python_pipeline.src.01_validation
python -m python_pipeline.src.02_feature_store
python -m python_pipeline.src.03_rfm
python -m python_pipeline.src.04_segmentation
python -m python_pipeline.src.05_market_basket
python -m python_pipeline.src.06_wastage
python -m python_pipeline.src.07_price_analysis
python -m python_pipeline.src.08_promotion_analysis
python -m python_pipeline.src.09_rating_analysis
python -m python_pipeline.src.10_sales_anomalies
python -m python_pipeline.src.11_peak_periods
python -m python_pipeline.src.11_churn_model
python -m python_pipeline.src.12_slow_moving
python -m python_pipeline.src.12_python_forecast
python -m python_pipeline.src.13_wastage_risk_model
python -m python_pipeline.src.13_dual_comparison
python -m python_pipeline.src.14_forecast_demand

Run tests:

pytest python_pipeline/tests/ -v

## Structure

python_pipeline/
  config.py
  lib/utils.py
  lib/io_helpers.py
  src/00-14
  tests/
  external/
  results/parquet/
  results/models/
  results/reports/

## Data Leakage Prevention

- Features computed only up to 2024-09-30
- Churn label from 2024-10-01 to 2024-12-31
- Forecast uses chronological split only

## Unified Revenue Definition

revenue = SUM(line_total) WHERE order_status='completed' AND quantity>0 AND unit_price>0 AND line_total>=0

## Independence from Spark

- Python uses scikit-learn, Spark uses MLlib
- Python never reads Spark predictions
- Both use the same revenue definition
- Comparison only at Stage 13

## Outputs

All outputs in python_pipeline/results/ organized by stage.

## Test Coverage

50 pytest tests across:
- Data loading and validation
- RFM and segmentation
- Market basket and bundles
- Wastage analysis and risk model
- Price elasticity
- Promotion effectiveness and traps
- Rating analysis and anomalies
- Sales anomalies
- Peak periods
- Slow-moving dishes
- Churn model
- Forecast (revenue and demand)
- Dual pipeline comparison

## Student

Student 3 — Python Data Science
DineIQ Analytics — 2026-09-26