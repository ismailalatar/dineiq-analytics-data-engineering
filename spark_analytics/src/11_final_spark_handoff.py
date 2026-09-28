import os
import glob
import shutil
import pandas as pd
from datetime import datetime


# ============================================================
# Project paths
# ============================================================

BASE_DIR = r"D:\DineIQ"

SPARK_RESULTS_DIR = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "results"
)

OUTPUT_PATH = os.path.join(
    SPARK_RESULTS_DIR,
    "spark_handoff_summary.csv"
)


print("=" * 70)
print("DINEIQ - FINAL SPARK HANDOFF")
print("=" * 70)

records = []


# ============================================================
# 1. MLlib classification results
# ============================================================

metrics_dir = os.path.join(
    SPARK_RESULTS_DIR,
    "mllib_model_metrics.csv"
)

metrics_files = glob.glob(
    os.path.join(
        metrics_dir,
        "part-*.csv"
    )
)

if metrics_files:

    try:

        metrics_path = metrics_files[0]

        metrics = pd.read_csv(
            metrics_path
        )

        print("\nMLlib Results:")
        print(
            metrics.to_string(
                index=False
            )
        )

        for _, row in metrics.iterrows():

            records.append(
                {
                    "component": "MLlib Classification",
                    "model_or_method": str(
                        row["model"]
                    ),
                    "model_version": str(
                        row["model_version"]
                    ),
                    "dataset_version": str(
                        row["dataset_version"]
                    ),
                    "feature_version": str(
                        row["feature_version"]
                    ),
                    "metric_1_name": "Test Accuracy",
                    "metric_1": float(
                        row["test_accuracy"]
                    ),
                    "metric_2_name": "Test F1",
                    "metric_2": float(
                        row["test_f1"]
                    ),
                    "status": "Completed"
                }
            )

    except Exception as exc:

        print(
            "\nMLlib results could not be loaded:",
            exc
        )

else:

    print(
        "\nCurrent MLlib metrics were not found."
    )


# ============================================================
# 2. Item-level demand forecasting
# ============================================================

forecast_path = os.path.join(
    SPARK_RESULTS_DIR,
    "forecast_metrics.csv"
)

if os.path.isfile(forecast_path):

    try:

        forecast = pd.read_csv(
            forecast_path
        )

        print("\nForecast Results:")
        print(
            forecast.to_string(
                index=False
            )
        )

        forecast_rows = forecast[
            forecast["model_version"].astype(str)
            == "v2.0"
        ]

        if not forecast_rows.empty:

            forecast_row = forecast_rows.iloc[0]

            records.append(
                {
                    "component":
                        "Item-Level Demand Forecasting",

                    "model_or_method":
                        str(
                            forecast_row["model"]
                        ),

                    "model_version":
                        str(
                            forecast_row["model_version"]
                        ),

                    "dataset_version":
                        "DineIQ-2024-v1",

                    "feature_version":
                        "features-v1",

                    "metric_1_name":
                        "MAE",

                    "metric_1":
                        float(
                            forecast_row["MAE"]
                        ),

                    "metric_2_name":
                        "RMSE",

                    "metric_2":
                        float(
                            forecast_row["RMSE"]
                        ),

                    "status":
                        "Completed"
                }
            )

    except Exception as exc:

        print(
            "\nForecast results could not be loaded:",
            exc
        )

else:

    print(
        "\nForecast metrics file not found."
    )


# ============================================================
# 3. Model verification results
# ============================================================

verification_path = os.path.join(
    SPARK_RESULTS_DIR,
    "model_verification.csv"
)

if os.path.isfile(verification_path):

    try:

        verification = pd.read_csv(
            verification_path
        )

        print("\nModel Verification:")
        print(
            verification.to_string(
                index=False
            )
        )

        if "load_success" in verification.columns:

            verified_count = int(
                verification["load_success"]
                .astype(str)
                .str.lower()
                .eq("true")
                .sum()
            )

        else:

            verified_count = 0

        total_models = len(
            verification
        )

        verification_status = (
            "Completed"
            if verified_count == total_models
            and total_models > 0
            else "Failed or Incomplete"
        )

        records.append(
            {
                "component":
                    "Model Verification",

                "model_or_method":
                    "Saved Models",

                "model_version":
                    "v1.1",

                "dataset_version":
                    "DineIQ-2024-v1",

                "feature_version":
                    "features-v1",

                "metric_1_name":
                    "Verified Models",

                "metric_1":
                    verified_count,

                "metric_2_name":
                    "Total Models",

                "metric_2":
                    total_models,

                "status":
                    verification_status
            }
        )

    except Exception as exc:

        print(
            "\nModel verification could not be loaded:",
            exc
        )

else:

    print(
        "\nModel verification file not found."
    )


# ============================================================
# 4. Spark monitoring evidence
# ============================================================

monitoring_path = os.path.join(
    SPARK_RESULTS_DIR,
    "spark_execution_log.json"
)

if os.path.isfile(monitoring_path):

    try:

        import json

        with open(
            monitoring_path,
            "r",
            encoding="utf-8"
        ) as f:

            monitoring = json.load(f)

        records.append(
            {
                "component":
                    "Spark Job Monitoring",

                "model_or_method":
                    monitoring.get(
                        "operation",
                        "Spark Aggregation"
                    ),

                "model_version":
                    "N/A",

                "dataset_version":
                    "DineIQ-2024-v1",

                "feature_version":
                    "features-v1",

                "metric_1_name":
                    "Duration Seconds",

                "metric_1":
                    float(
                        monitoring.get(
                            "duration_seconds",
                            0
                        )
                    ),

                "metric_2_name":
                    "Jobs",

                "metric_2":
                    int(
                        monitoring.get(
                            "monitoring_summary",
                            {}
                        ).get(
                            "job_count",
                            0
                        )
                    ),

                "status":
                    monitoring.get(
                        "status",
                        "UNKNOWN"
                    )
            }
        )

    except Exception as exc:

        print(
            "\nSpark monitoring could not be loaded:",
            exc
        )


# ============================================================
# 5. Create final handoff summary
# ============================================================

if records:

    generated_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    summary = pd.DataFrame(
        records
    )

    summary["generated_at"] = generated_at


    # Ensure consistent column order

    columns = [
        "component",
        "model_or_method",
        "model_version",
        "dataset_version",
        "feature_version",
        "metric_1_name",
        "metric_1",
        "metric_2_name",
        "metric_2",
        "status",
        "generated_at"
    ]

    summary = summary[
        columns
    ]


    print("\n" + "=" * 70)
    print("FINAL HANDOFF SUMMARY")
    print("=" * 70)

    print(
        summary.to_string(
            index=False
        )
    )


    # Remove old file/directory safely

    if os.path.isdir(OUTPUT_PATH):
        shutil.rmtree(
            OUTPUT_PATH
        )

    elif os.path.isfile(OUTPUT_PATH):
        os.remove(
            OUTPUT_PATH
        )


    # Write a real single CSV file

    summary.to_csv(
        OUTPUT_PATH,
        index=False
    )


    print(
        "\nHandoff summary saved to:"
    )

    print(
        OUTPUT_PATH
    )

else:

    print(
        "\nNo current Spark result files were found."
    )


print(
    "\nFinal Spark handoff completed successfully."
)
