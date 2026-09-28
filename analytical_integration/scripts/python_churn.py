import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path


# Main project folder
BASE = Path(r"D:\DineIQ")

# Training data prepared by the Python pipeline
TRAIN_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "results"
    / "parquet"
    / "11_churn"
    / "churn_dataset.parquet"
)

# These are the same 100 test cases used by Spark
TEST_PATH = BASE / "dual_test_cases.parquet"

# Save the Python predictions here
OUTPUT_PATH = (
    BASE
    / "python_analytics"
    / "python_pipeline"
    / "external"
    / "python_churn_results.parquet"
)


# Use the same features for both pipelines
FEATURES = [
    "recency",
    "frequency",
    "monetary",
    "aov",
    "distinct_items",
    "r_score",
    "f_score",
    "m_score",
    "promo_sensitivity",
    "peak_ratio",
    "weekend_ratio"
]


print("Reading training data...")
train = pd.read_parquet(TRAIN_PATH)

print("Training rows:", len(train))


print("Reading test data...")
test = pd.read_parquet(TEST_PATH)

print("Test rows:", len(test))


# Separate the input features from the churn label
X_train = train[FEATURES]
y_train = train["churn"]

X_test = test[FEATURES]


print("Training Python Random Forest...")


# Python model
# Settings are kept close to the Spark model
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)


# Train the model using the prepared training data
model.fit(X_train, y_train)

print("Training completed.")


print("Generating Python predictions...")


# Predict churn class for the 100 test records
prediction = model.predict(X_test)

# Get the probability of the customer being churned
probability = model.predict_proba(X_test)[:, 1]


# Keep only the fields needed for the comparison
result = pd.DataFrame({
    "record_id": test["record_id"],
    "churn": test["churn"],
    "python_prediction": prediction,
    "python_probability": probability
})


# Make sure the output folder exists
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# Save results as Parquet
result.to_parquet(
    OUTPUT_PATH,
    engine="pyarrow",
    index=False
)


print()
print("Python churn results saved to:")
print(OUTPUT_PATH)

print("Result rows:", len(result))

print()
print("First 10 predictions:")
print(result.head(10).to_string(index=False))