from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
import os


base_dir = r"D:\DineIQ"

data_path = os.path.join(
    base_dir,
    "student2",
    "results",
    "menu_classification.parquet"
)

models_dir = os.path.join(
    base_dir,
    "student2",
    "results",
    "models"
)


spark = (
    SparkSession.builder
    .appName("DineIQ Model Verification")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


print("=" * 50)
print("DINEIQ - MODEL SAVE / LOAD VERIFICATION")
print("=" * 50)


df = spark.read.parquet(data_path)

print("\nDataset rows:", df.count())


model_paths = {
    "Logistic Regression": os.path.join(
        models_dir, "logistic_regression"
    ),
    "Decision Tree": os.path.join(
        models_dir, "decision_tree"
    ),
    "Random Forest": os.path.join(
        models_dir, "random_forest"
    )
}


verification_rows = []


for model_name, model_path in model_paths.items():

    print("\nMODEL:", model_name)
    print("Path:", model_path)

    if not os.path.exists(model_path):
        print("STATUS: NOT FOUND")
        verification_rows.append(
            (model_name, model_path, False, 0)
        )
        continue

    try:
        model = PipelineModel.load(model_path)

        print("Model loaded successfully.")

        predictions = model.transform(df)
        prediction_count = predictions.count()

        print("Prediction rows:", prediction_count)

        predictions.select(
            "menu_class",
            "prediction"
        ).show(5)

        print("STATUS: VERIFIED")

        verification_rows.append(
            (model_name, model_path, True, prediction_count)
        )

    except Exception as e:

        print("STATUS: FAILED")
        print("ERROR:", str(e))

        verification_rows.append(
            (model_name, model_path, False, 0)
        )


verification_df = spark.createDataFrame(
    verification_rows,
    [
        "model",
        "model_path",
        "load_success",
        "prediction_rows"
    ]
)


print("\nVERIFICATION SUMMARY")
print("=" * 50)

verification_df.show(truncate=False)


output_path = os.path.join(
    base_dir,
    "student2",
    "results",
    "model_verification.csv"
)


verification_df.coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(output_path)


print("\nVerification results saved to:")
print(output_path)

print("\nModel save/load verification completed.")

spark.stop()
