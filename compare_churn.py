import pandas as pd
from pathlib import Path


# Main project folder
BASE = Path(r"D:\DineIQ")

# Prediction files from both pipelines
SPARK_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "external"
    / "spark_forecast_results.parquet"
)

PYTHON_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "external"
    / "python_churn_results.parquet"
)

# Final comparison output
OUTPUT_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "external"
    / "dual_pipeline_comparison.parquet"
)


print("Reading Spark results...")
spark = pd.read_parquet(SPARK_PATH)

print("Reading Python results...")
python = pd.read_parquet(PYTHON_PATH)


# Keep the fields needed for the comparison
spark = spark[
    [
        "record_id",
        "churn",
        "spark_prediction",
        "spark_probability"
    ]
]

python = python[
    [
        "record_id",
        "python_prediction",
        "python_probability"
    ]
]


# Combine both predictions using the test record ID
comparison = spark.merge(
    python,
    on="record_id",
    how="inner"
)


# Rename the actual value for a clearer report
comparison = comparison.rename(
    columns={"churn": "actual_churn"}
)


# Check whether both models produced the same class
comparison["match_status"] = (
    comparison["spark_prediction"]
    == comparison["python_prediction"]
)


# Difference between the predicted classes
comparison["prediction_difference"] = (
    comparison["spark_prediction"]
    - comparison["python_prediction"]
).abs()


# Difference between model probabilities
comparison["probability_difference"] = (
    comparison["spark_probability"]
    - comparison["python_probability"]
).abs()


# Check whether each model predicted the actual class correctly
comparison["spark_correct"] = (
    comparison["spark_prediction"]
    == comparison["actual_churn"]
)

comparison["python_correct"] = (
    comparison["python_prediction"]
    == comparison["actual_churn"]
)


# Add a simple explanation for every case
comparison["disagreement_explanation"] = comparison.apply(
    lambda row:
        "Both models predicted the same class."
        if row["match_status"]
        else (
            f"Predictions differ. "
            f"Spark probability={row['spark_probability']:.4f}, "
            f"Python probability={row['python_probability']:.4f}, "
            f"actual churn={row['actual_churn']}."
        ),
    axis=1
)


# Save the detailed comparison
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

comparison.to_parquet(
    OUTPUT_PATH,
    engine="pyarrow",
    index=False
)


# Summary statistics
total = len(comparison)
matches = int(comparison["match_status"].sum())
mismatches = total - matches

agreement = (matches / total * 100) if total else 0
spark_accuracy = (
    comparison["spark_correct"].mean() * 100
    if total else 0
)
python_accuracy = (
    comparison["python_correct"].mean() * 100
    if total else 0
)


print()
print("=" * 50)
print("DUAL-PIPELINE COMPARISON")
print("=" * 50)

print("Total test cases:", total)
print("Matches:", matches)
print("Mismatches:", mismatches)
print(f"Agreement: {agreement:.2f}%")
print(f"Spark accuracy: {spark_accuracy:.2f}%")
print(f"Python accuracy: {python_accuracy:.2f}%")

print()
print("Comparison saved to:")
print(OUTPUT_PATH)

print()
print("First 10 comparison rows:")
print(comparison.head(10).to_string(index=False))