from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum


# Start Spark
spark = (
    SparkSession.builder
    .appName("DineIQ Feature Check")
    .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem")
    .config("spark.hadoop.fs.AbstractFileSystem.file.impl", "org.apache.hadoop.fs.local.LocalFs")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# Path to the feature datasets
BASE_PATH = r"D:\DineIQ\full_output\processed_data\features"

datasets = {
    "item_features": f"{BASE_PATH}/item_features.parquet",
    "customer_features": f"{BASE_PATH}/customer_features.parquet",
    "order_features": f"{BASE_PATH}/order_features.parquet",
    "location_item_features": f"{BASE_PATH}/location_item_features.parquet",
    "time_features": f"{BASE_PATH}/time_features.parquet"
}


# Check each feature dataset
for name, path in datasets.items():

    print("\n" + "=" * 50)
    print("DATASET:", name)
    print("=" * 50)

    df = spark.read.parquet(path)

    # Show number of rows
    print("Rows:", df.count())

    # Show columns and data types
    print("\nSchema:")
    df.printSchema()

    # Show a few records
    print("\nSample:")
    df.show(5, truncate=False)

    # Check for null values
    print("\nNull values:")

    null_counts = df.select([
        sum(col(c).isNull().cast("int")).alias(c)
        for c in df.columns
    ])

    null_counts.show()


print("\nFeature dataset check completed.")

spark.stop()
