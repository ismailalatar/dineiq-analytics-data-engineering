from __future__ import annotations

import json
import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from .schemas import SCHEMAS


ROOT = Path("D:/APTECH")
RAW = ROOT / "full_output" / "raw_data"
PROCESSED = ROOT / "full_output" / "processed_data"
REPORTS = ROOT / "full_output" / "reports"


def _build_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("DineIQ-U11-Ingestion")
        .master("local[2]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )


def run_ingestion():
    start = time.time()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    spark = _build_spark()
    spark.sparkContext.setLogLevel("WARN")

    report = {
        "tables": {},
        "schema_inference": {},
        "type_validation": {},
        "large_file_loading": {},
        "partition_handling": {},
        "multiple_file_ingestion": {"files_read": []},
    }

    dataframes = {}
    for table_name, schema in SCHEMAS.items():
        csv_path = str(RAW / f"{table_name}.csv")
        df = (
            spark.read
            .option("header", "true")
            .option("mode", "PERMISSIVE")
            .option("nullValue", "")
            .schema(schema)
            .csv(csv_path)
        )
        row_count = df.count()
        dataframes[table_name] = df
        report["tables"][table_name] = {
            "rows": row_count,
            "columns": list(df.columns),
            "schema_source": "explicit",
        }
        report["multiple_file_ingestion"]["files_read"].append(str(csv_path))
        print(f"[explicit] {table_name:<18} rows={row_count:>10,}")

    inferred = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(str(RAW / "Order_Items.csv"))
    )
    report["schema_inference"] = {
        "table": "Order_Items",
        "inferred_types": {f.name: f.dataType.simpleString() for f in inferred.schema.fields},
    }
    print("[inference] Order_Items inferred schema saved to report.")

    mismatches = []
    for table_name, schema in SCHEMAS.items():
        actual = dict(dataframes[table_name].dtypes)
        for field in schema.fields:
            expected_type = field.dataType.simpleString()
            actual_type = actual.get(field.name)
            if actual_type != expected_type:
                mismatches.append({
                    "table": table_name,
                    "column": field.name,
                    "expected": expected_type,
                    "actual": actual_type,
                })
    report["type_validation"] = {
        "total_columns_checked": sum(len(s.fields) for s in SCHEMAS.values()),
        "mismatches": mismatches,
        "passed": len(mismatches) == 0,
    }
    print(f"[types] mismatches={len(mismatches)}")

    large_df = dataframes["Order_Items"]
    large_rows = large_df.count()
    large_partitions = large_df.rdd.getNumPartitions()
    report["large_file_loading"] = {
        "table": "Order_Items",
        "rows": large_rows,
        "partitions_before": large_partitions,
        "loaded_successfully": large_rows > 0,
    }
    print(f"[large] Order_Items rows={large_rows:,} partitions={large_partitions}")

    for table_name, df in dataframes.items():
        out_dir = PROCESSED / f"{table_name}.parquet"
        df.write.mode("overwrite").parquet(str(out_dir))
    print("[parquet] all 12 tables written to processed_data/")

    partitioned_df = large_df.repartition(8, col("order_id"))
    partitioned_path = PROCESSED / "Order_Items_partitioned"
    (
        partitioned_df.write
        .mode("overwrite")
        .partitionBy("order_id")
        .parquet(str(partitioned_path))
    )
    report["partition_handling"] = {
        "table": "Order_Items",
        "partitions_before": large_partitions,
        "partitions_after": partitioned_df.rdd.getNumPartitions(),
        "partitioned_by": "order_id",
        "output_path": str(partitioned_path),
    }
    print(f"[partition] written to {partitioned_path}")

    readback = spark.read.parquet(str(PROCESSED / "Order_Items.parquet"))
    readback_rows = readback.count()
    report["readback_validation"] = {
        "table": "Order_Items",
        "rows_read_back": readback_rows,
        "matches_ingest": readback_rows == large_rows,
    }

    elapsed = time.time() - start
    report["elapsed_seconds"] = round(elapsed, 2)

    with (REPORTS / "step3_ingestion_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nDone in {elapsed:.1f}s.")
    print(f"Report: {REPORTS / 'step3_ingestion_report.json'}")

    spark.stop()
    return report


if __name__ == "__main__":
    run_ingestion()