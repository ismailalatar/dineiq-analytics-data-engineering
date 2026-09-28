import os
import json
import shutil
from datetime import datetime

# ============================================================
# Windows / PySpark environment
# ============================================================

PYTHON_EXE = r"C:\Users\acer\AppData\Local\Programs\Python\Python312\python.exe"

os.environ["PYSPARK_PYTHON"] = PYTHON_EXE
os.environ["PYSPARK_DRIVER_PYTHON"] = PYTHON_EXE
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, count


# ============================================================
# Project paths
# ============================================================

BASE_DIR = r"D:\DineIQ"

DATA_PATH = os.path.join(
    BASE_DIR,
    "full_output",
    "processed_data",
    "features",
    "order_features.parquet"
)

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "spark_analytics",
    "results"
)

LOG_PATH = os.path.join(
    RESULTS_DIR,
    "spark_execution_log.json"
)


# ============================================================
# Start Spark
# ============================================================

spark = (
    SparkSession.builder
    .appName("DineIQ Spark Monitoring")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

sc = spark.sparkContext

print("=" * 70)
print("DINEIQ - SPARK JOB MONITORING")
print("=" * 70)

print("\nApplication ID:", sc.applicationId)
print("Application Name:", sc.appName)
print("Spark Version:", spark.version)


# ============================================================
# Monitoring start
# ============================================================

start_time = datetime.now()


# ============================================================
# Read input dataset
# ============================================================

df = spark.read.parquet(DATA_PATH)

row_count = df.count()

print("\nInput rows:", row_count)


# ============================================================
# Main Spark operation
# ============================================================

print("\nRunning monitored Spark aggregation...")

summary = (
    df.filter(col("order_status") == "completed")
    .groupBy("restaurant_id")
    .agg(
        count("*").alias("completed_orders"),
        spark_sum("order_total").alias("revenue")
    )
    .orderBy(col("revenue").desc())
)

summary.show(10)


# ============================================================
# Monitoring end
# ============================================================

end_time = datetime.now()

duration_seconds = (
    end_time - start_time
).total_seconds()


# ============================================================
# Retrieve Spark execution information
# ============================================================

status_tracker = sc.statusTracker()

job_ids = list(
    status_tracker.getJobIdsForGroup(None)
)

jobs = []

for job_id in job_ids:

    try:
        job_info = status_tracker.getJobInfo(job_id)

        if job_info is None:
            continue

        stage_ids = list(job_info.stageIds)

        job_status = str(
            job_info.status
        )

        jobs.append(
            {
                "job_id": int(job_id),
                "status": job_status,
                "stage_ids": stage_ids,
                "stage_count": len(stage_ids)
            }
        )

    except Exception as e:

        jobs.append(
            {
                "job_id": int(job_id),
                "status": "UNKNOWN",
                "stage_ids": [],
                "stage_count": 0,
                "error": str(e)
            }
        )


# ============================================================
# Retrieve Stage information
# ============================================================

stages = []

for job in jobs:

    for stage_id in job["stage_ids"]:

        try:

            stage_info = status_tracker.getStageInfo(
                stage_id
            )

            if stage_info is None:
                continue

            stages.append(
                {
                    "stage_id": int(stage_id),
                    "name": str(stage_info.name),
                    "num_tasks": int(stage_info.numTasks),
                    "active_tasks": int(stage_info.numActiveTasks),
                    "completed_tasks": int(
                        stage_info.numCompletedTasks
                    ),
                    "failed_tasks": int(
                        stage_info.numFailedTasks
                    )
                }
            )

        except Exception as e:

            stages.append(
                {
                    "stage_id": int(stage_id),
                    "name": "UNKNOWN",
                    "num_tasks": 0,
                    "active_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "error": str(e)
                }
            )


# ============================================================
# Build task-level evidence
# ============================================================

tasks = []

# Build task-level evidence.
# The Spark StatusTracker may report zero completed tasks
# even after the parent Job has already succeeded.
# Therefore, task status is based on actual failed tasks,
# while the parent Job status is used as overall execution evidence.

job_status_by_stage = {}

for job in jobs:
    for stage_id in job["stage_ids"]:
        job_status_by_stage[stage_id] = job["status"]


for stage in stages:

    parent_job_status = job_status_by_stage.get(
        stage["stage_id"],
        "UNKNOWN"
    )

    if stage["failed_tasks"] > 0:
        task_status = "FAILED"

    elif parent_job_status == "SUCCEEDED":
        task_status = "COMPLETED"

    elif parent_job_status == "SKIPPED":
        task_status = "SKIPPED"

    else:
        task_status = "UNKNOWN"


    tasks.append(
        {
            "stage_id": stage["stage_id"],
            "task_count": stage["num_tasks"],
            "completed_tasks": stage["completed_tasks"],
            "failed_tasks": stage["failed_tasks"],
            "parent_job_status": parent_job_status,
            "status": task_status
        }
    )


# ============================================================
# Overall execution status
# ============================================================

failed_jobs = [
    job for job in jobs
    if job["status"] not in ["SUCCEEDED", "SKIPPED"]
]

failed_stages = [
    stage for stage in stages
    if stage["failed_tasks"] > 0
]

if not failed_jobs and not failed_stages:
    overall_status = "COMPLETED"
else:
    overall_status = "FAILED_OR_INCOMPLETE"


# ============================================================
# Execution evidence
# ============================================================

execution_info = {
    "application_id": sc.applicationId,
    "application_name": sc.appName,
    "spark_version": spark.version,

    "input_path": DATA_PATH,
    "input_rows": row_count,

    "start_time": start_time.isoformat(),
    "end_time": end_time.isoformat(),
    "duration_seconds": duration_seconds,

    "operation": (
        "Completed order aggregation by restaurant"
    ),

    "status": overall_status,

    "jobs": jobs,
    "stages": stages,
    "tasks": tasks,

    "monitoring_summary": {
        "job_count": len(jobs),
        "stage_count": len(stages),
        "task_groups": len(tasks),
        "failed_jobs": len(failed_jobs),
        "failed_stages": len(failed_stages)
    }
}


# ============================================================
# Save execution evidence
# ============================================================

os.makedirs(
    RESULTS_DIR,
    exist_ok=True
)

if os.path.isdir(LOG_PATH):
    shutil.rmtree(LOG_PATH)

with open(
    LOG_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        execution_info,
        f,
        indent=4
    )


# ============================================================
# Print execution evidence
# ============================================================

print("\n" + "=" * 70)
print("EXECUTION EVIDENCE")
print("=" * 70)

print("Application ID:", sc.applicationId)
print("Spark Version:", spark.version)
print("Status:", overall_status)
print("Input Rows:", row_count)
print("Duration:", duration_seconds, "seconds")

print("\nJobs:", len(jobs))

for job in jobs:

    print(
        "  Job",
        job["job_id"],
        "| Status:",
        job["status"],
        "| Stages:",
        job["stage_ids"]
    )


print("\nStages:", len(stages))

for stage in stages:

    print(
        "  Stage",
        stage["stage_id"],
        "|",
        stage["name"],
        "| Tasks:",
        stage["num_tasks"],
        "| Completed:",
        stage["completed_tasks"],
        "| Failed:",
        stage["failed_tasks"]
    )


print("\nTask Evidence:", len(tasks))

for task in tasks:

    print(
        "  Stage",
        task["stage_id"],
        "| Task Count:",
        task["task_count"],
        "| Completed:",
        task["completed_tasks"],
        "| Failed:",
        task["failed_tasks"],
        "| Status:",
        task["status"]
    )


print("\nExecution log saved to:")
print(LOG_PATH)

print("\nSpark monitoring completed successfully.")


# ============================================================
# Stop Spark
# ============================================================

spark.stop()
