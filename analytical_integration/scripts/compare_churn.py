import pandas as pd
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# Project paths

BASE = Path(r"D:\DineIQ")

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

OUTPUT_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "external"
    / "dual_pipeline_comparison.parquet"
)


# Read Spark and Python results

print("Reading Spark results...")

spark = pd.read_parquet(SPARK_PATH)

print("Reading Python results...")

python = pd.read_parquet(PYTHON_PATH)


# Keep the columns needed for comparison

spark = spark[
    [
        "record_id",
        "churn",
        "spark_prediction",
        "spark_probability",
    ]
].copy()

python = python[
    [
        "record_id",
        "python_prediction",
        "python_probability",
    ]
].copy()


# Check the test cases

print()
print("=" * 60)
print("VALIDATING TEST CASES")
print("=" * 60)

spark_ids = set(spark["record_id"])
python_ids = set(python["record_id"])

only_spark = spark_ids - python_ids
only_python = python_ids - spark_ids

print("Spark rows:", len(spark))
print("Python rows:", len(python))
print("Spark unique IDs:", spark["record_id"].nunique())
print("Python unique IDs:", python["record_id"].nunique())

print("IDs only in Spark:", len(only_spark))
print("IDs only in Python:", len(only_python))


# Combine both results using record_id

comparison = spark.merge(
    python,
    on="record_id",
    how="inner",
)


# Rename the actual churn label

comparison = comparison.rename(
    columns={
        "churn": "actual_churn"
    }
)


# Make prediction columns integer values

comparison["actual_churn"] = (
    comparison["actual_churn"]
    .astype(int)
)

comparison["spark_prediction"] = (
    comparison["spark_prediction"]
    .astype(int)
)

comparison["python_prediction"] = (
    comparison["python_prediction"]
    .astype(int)
)


# Check whether both models agree

comparison["match_status"] = (
    comparison["spark_prediction"]
    ==
    comparison["python_prediction"]
)


comparison["prediction_difference"] = (
    comparison["spark_prediction"]
    -
    comparison["python_prediction"]
).abs()


comparison["probability_difference"] = (
    comparison["spark_probability"]
    -
    comparison["python_probability"]
).abs()


# Check whether each prediction is correct

comparison["spark_correct"] = (
    comparison["spark_prediction"]
    ==
    comparison["actual_churn"]
)


comparison["python_correct"] = (
    comparison["python_prediction"]
    ==
    comparison["actual_churn"]
)


# Explain cases where the models disagree

comparison["disagreement_explanation"] = comparison.apply(
    lambda row:
        "Both models predicted the same class."
        if row["match_status"]
        else (
            "Predictions differ. "
            f"Spark probability="
            f"{row['spark_probability']:.4f}, "
            f"Python probability="
            f"{row['python_probability']:.4f}, "
            f"actual churn="
            f"{row['actual_churn']}."
        ),
    axis=1,
)


# Calculate agreement between the two models

total = len(comparison)

matches = int(
    comparison["match_status"].sum()
)

mismatches = total - matches

agreement = (
    matches / total * 100
    if total
    else 0
)


# Prepare actual labels and predictions

y_true = comparison["actual_churn"]

spark_pred = comparison["spark_prediction"]

python_pred = comparison["python_prediction"]


# Calculate Spark model metrics

spark_accuracy = accuracy_score(
    y_true,
    spark_pred,
)

spark_precision = precision_score(
    y_true,
    spark_pred,
    zero_division=0,
)

spark_recall = recall_score(
    y_true,
    spark_pred,
    zero_division=0,
)

spark_f1 = f1_score(
    y_true,
    spark_pred,
    zero_division=0,
)

spark_macro_f1 = f1_score(
    y_true,
    spark_pred,
    average="macro",
    zero_division=0,
)

spark_cm = confusion_matrix(
    y_true,
    spark_pred,
    labels=[0, 1],
)


# Calculate Python model metrics

python_accuracy = accuracy_score(
    y_true,
    python_pred,
)

python_precision = precision_score(
    y_true,
    python_pred,
    zero_division=0,
)

python_recall = recall_score(
    y_true,
    python_pred,
    zero_division=0,
)

python_f1 = f1_score(
    y_true,
    python_pred,
    zero_division=0,
)

python_macro_f1 = f1_score(
    y_true,
    python_pred,
    average="macro",
    zero_division=0,
)

python_cm = confusion_matrix(
    y_true,
    python_pred,
    labels=[0, 1],
)


# Save the comparison results

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)


comparison.to_parquet(
    OUTPUT_PATH,
    engine="pyarrow",
    index=False,
)


# Print the comparison report

print()
print("=" * 60)
print("DUAL-PIPELINE COMPARISON")
print("=" * 60)

print()
print("TEST CASES")
print("-" * 60)

print("Total test cases:", total)
print("Matches:", matches)
print("Mismatches:", mismatches)
print(f"Agreement: {agreement:.2f}%")

print()
print("SPARK RANDOM FOREST")
print("-" * 60)

print(
    f"Accuracy:  {spark_accuracy * 100:.2f}%"
)

print(
    f"Precision: {spark_precision * 100:.2f}%"
)

print(
    f"Recall:    {spark_recall * 100:.2f}%"
)

print(
    f"F1:        {spark_f1 * 100:.2f}%"
)

print(
    f"Macro F1:  {spark_macro_f1 * 100:.2f}%"
)

print("Confusion Matrix:")
print(spark_cm)


print()
print("PYTHON ORIGINAL RANDOM FOREST")
print("-" * 60)

print(
    f"Accuracy:  {python_accuracy * 100:.2f}%"
)

print(
    f"Precision: {python_precision * 100:.2f}%"
)

print(
    f"Recall:    {python_recall * 100:.2f}%"
)

print(
    f"F1:        {python_f1 * 100:.2f}%"
)

print(
    f"Macro F1:  {python_macro_f1 * 100:.2f}%"
)

print("Confusion Matrix:")
print(python_cm)


print()
print("PIPELINE DIFFERENCE")
print("-" * 60)

print(
    f"Accuracy difference: "
    f"{abs(spark_accuracy - python_accuracy) * 100:.2f} percentage points"
)

print(
    f"Macro F1 difference: "
    f"{abs(spark_macro_f1 - python_macro_f1) * 100:.2f} percentage points"
)

print(
    f"Prediction agreement: "
    f"{agreement:.2f}%"
)


print()
print("OUTPUT")
print("-" * 60)

print(
    "Comparison saved to:"
)

print(OUTPUT_PATH)


# Find cases where the predictions are different

disagreements = comparison[
    ~comparison["match_status"]
]

print()
print("=" * 60)
print("DISAGREEMENTS")
print("=" * 60)

print(
    "Number of disagreements:",
    len(disagreements)
)

if len(disagreements) > 0:
    print()

    print(
        disagreements[
            [
                "record_id",
                "actual_churn",
                "spark_prediction",
                "python_prediction",
                "spark_probability",
                "python_probability",
            ]
        ]
        .to_string(index=False)
    )


# Show the first 10 comparison rows

print()
print("=" * 60)
print("FIRST 10 COMPARISON ROWS")
print("=" * 60)

print(
    comparison
    .head(10)
    .to_string(index=False)
)