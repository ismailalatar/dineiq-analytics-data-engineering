import os
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

STUDENT2_RESULTS_DIR = os.path.join(
    BASE_DIR,
    "student2",
    "results"
)

OUTPUT_PATH = os.path.join(
    SPARK_RESULTS_DIR,
    "spark_handoff_summary.csv"
)


print("=" * 60)
print("DINEIQ - FINAL SPARK HANDOFF")
print("=" * 60)

records = []


# ============================================================
# MLlib classification results
# ============================================================

metrics_candidates = [
    os.path.join(
        SPARK_RESULTS_DIR,
        "mllib_model_metrics.csv"
    ),
    os.path.join(
        STUDENT2_RESULTS_DIR,
        "mllib_model_metrics.csv"
    )
]

metrics_path = next(
    (
        path
        for path in metrics_candidates
        if os.path.exists(path)
    ),
    None
)

if metrics_path:

    try:
        metrics = pd.read_csv(metrics_path)

        print("\nMLlib Results:")
        print(metrics.to_string(index=False))

        for _, row in metrics.iterrows():

            records.append(
                (
                    "MLlib Classification",
                    str(row["model"]),
                    str(row["accuracy"]),
                    str(row["f1_score"]),
                    "Completed"
                )
            )

    except Exception as exc:

        print(
            "\nMLlib results could not be loaded:",
            exc
        )

else:

    print("\nMLlib metrics file not found.")


# ============================================================
# Item-level demand forecasting
# ============================================================

forecast_path = os.path.join(
    SPARK_RESULTS_DIR,
    "forecast_metrics.csv"
)

if os.path.exists(forecast_path):

    forecast = pd.read_csv(
        forecast_path
    )

    print("\nForecast Results:")
    print(forecast.to_string(index=False))

    forecast_rows = forecast[
        forecast["model_version"].astype(str)
        == "v2.0"
    ]

    if not forecast_rows.empty:

        forecast_row = forecast_rows.iloc[0]

        records.append(
            (
                "Item-Level Demand Forecasting",
                "Random Forest",
                str(forecast_row["MAE"]),
                str(forecast_row["RMSE"]),
                "Completed"
            )
        )

else:

    print("\nForecast metrics file not found.")


# ============================================================
# Model verification results
# ============================================================

verification_candidates = [
    os.path.join(
        SPARK_RESULTS_DIR,
        "model_verification.csv"
    ),
    os.path.join(
        STUDENT2_RESULTS_DIR,
        "model_verification.csv"
    )
]

verification_path = next(
    (
        path
        for path in verification_candidates
        if os.path.exists(path)
    ),
    None
)

if verification_path:

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
                .astype(bool)
                .sum()
            )

        else:

            verified_count = 0

        total_models = len(
            verification
        )

        records.append(
            (
                "Model Verification",
                "Saved Models",
                str(verified_count),
                str(total_models),
                "Completed"
            )
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
# Create final handoff summary
# ============================================================

if records:

    generated_at = datetime.now().isoformat(
        timespec="seconds"
    )

    summary = pd.DataFrame(
        records,
        columns=[
            "component",
            "model_or_method",
            "metric_1",
            "metric_2",
            "status"
        ]
    )

    summary["generated_at"] = generated_at

    print("\nFinal Handoff Summary:")
    print(
        summary.to_string(
            index=False
        )
    )

    summary.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        "\nHandoff summary saved to:"
    )
    print(OUTPUT_PATH)

else:

    print(
        "\nNo previous result files were found."
    )


print(
    "\nFinal Spark handoff completed."
)