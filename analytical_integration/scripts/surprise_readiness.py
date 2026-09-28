import os
import pandas as pd
import surprise_config as config


BASE_PATH = r"D:\DineIQ\spark_analytics\results\menu_profitability.parquet"
OUTPUT_DIR = r"D:\DineIQ\analytical_integration\results"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "surprise_modification_readiness.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Reading existing analytical output...")

df = pd.read_parquet(BASE_PATH)

# Convert profit percentage to numeric
df["profit_pct"] = pd.to_numeric(
    df["profit_pct"], errors="coerce"
).fillna(0)

# Convert revenue to numeric
df["revenue"] = pd.to_numeric(
    df["revenue"], errors="coerce"
).fillna(0)


# Check the profit threshold setting

df["above_profit_threshold"] = (
    df["profit_pct"] >= config.PROFIT_THRESHOLD
)


# Check if the extra feature exists

extra_feature_available = (
    config.EXTRA_FEATURE in df.columns
)


# Get the forecast window from the config

forecast_window_days = config.FORECAST_WINDOW_DAYS


# Get the anomaly rule from the config

anomaly_rule = config.ANOMALY_RULE


# Check if the selected KPI is available

kpi_available = config.KPI_NAME in df.columns


# Create a summary of the modification readiness

summary = pd.DataFrame([
    {
        "modification": "Profit threshold",
        "parameter": "PROFIT_THRESHOLD",
        "current_value": config.PROFIT_THRESHOLD,
        "status": "READY"
    },
    {
        "modification": "Extra feature",
        "parameter": "EXTRA_FEATURE",
        "current_value": config.EXTRA_FEATURE,
        "status": (
            "READY"
            if extra_feature_available
            else "NOT AVAILABLE"
        )
    },
    {
        "modification": "Forecast window",
        "parameter": "FORECAST_WINDOW_DAYS",
        "current_value": forecast_window_days,
        "status": "READY"
    },
    {
        "modification": "Anomaly rule",
        "parameter": "ANOMALY_RULE",
        "current_value": anomaly_rule,
        "status": "READY"
    },
    {
        "modification": "KPI",
        "parameter": "KPI_NAME",
        "current_value": config.KPI_NAME,
        "status": (
            "READY"
            if kpi_available
            else "NOT AVAILABLE"
        )
    }
])

# Save the readiness summary

summary.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 60)
print("SURPRISE MODIFICATION READINESS")
print("=" * 60)

print(summary.to_string(index=False))

print()
print("Output:")
print(OUTPUT_FILE)
