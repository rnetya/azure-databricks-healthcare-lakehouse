# Databricks notebook source
from pyspark.sql import functions as F

print("Spark version:", spark.version)

df = spark.range(1, 1_000_001)

result = (
    df
    .withColumn("group_id", F.col("id") % 10)
    .groupBy("group_id")
    .agg(F.count("*").alias("record_count"))
    .orderBy("group_id")
)

display(result)

# COMMAND ----------

catalog_name = "healthcare_dev"
schema_name = "bronze"

spark.sql(f"USE CATALOG {catalog_name}")
spark.sql(f"USE SCHEMA {schema_name}")

print("Current catalog:", spark.sql("SELECT current_catalog()").first()[0])
print("Current schema :", spark.sql("SELECT current_schema()").first()[0])

spark.sql("SHOW TABLES").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Step 4 — Prove the physical ADLS write path

# COMMAND ----------

validation_data = [
    (1, "Serverless", "PASS"),
    (2, "Unity Catalog", "PASS"),
    (3, "ADLS Gen2", "PASS")
]

df_validation = spark.createDataFrame(
    validation_data,
    ["validation_id", "component", "status"]
)

df_validation.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("healthcare_dev.bronze.serverless_managed_validation")

display(
    spark.table("healthcare_dev.bronze.serverless_managed_validation")
)

# COMMAND ----------

# MAGIC %md
# MAGIC **Clean up the validation table**

# COMMAND ----------

spark.sql("""
DROP TABLE IF EXISTS healthcare_dev.bronze.serverless_managed_validation
""")

print("Serverless managed-table validation cleanup complete.")

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 5 — prove it with Serverless Spark**

# COMMAND ----------

member_volume_path = "/Volumes/healthcare_dev/bronze/member_raw/"

files = dbutils.fs.ls(member_volume_path)

print(f"Volume path: {member_volume_path}")
print(f"Files found: {len(files)}")

for file in files:
    print(file.path)

# COMMAND ----------

# MAGIC %md
# MAGIC **Step 6 — Write a tiny file through the Volume**

# COMMAND ----------

volume_path = "/Volumes/healthcare_dev/bronze/member_raw/"
test_file = f"{volume_path}_volume_validation.txt"

dbutils.fs.put(
    test_file,
    "M1.9.7.2 external volume validation - PASS",
    overwrite=True
)

print("Created:", test_file)

# COMMAND ----------

files = dbutils.fs.ls(volume_path)

for file in files:
    print(
        "Name:", file.name,
        "| Size:", file.size,
        "| Path:", file.path
    )

# COMMAND ----------

test_file = "/Volumes/healthcare_dev/bronze/member_raw/_volume_validation.txt"

dbutils.fs.rm(test_file)

remaining_files = dbutils.fs.ls(
    "/Volumes/healthcare_dev/bronze/member_raw/"
)

print("Validation file deleted.")
print("Remaining files:", len(remaining_files))