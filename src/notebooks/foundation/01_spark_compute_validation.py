# Databricks notebook source
# Historical foundation validation originally executed on classic compute.
# Retained as evidence of the initial Spark validation performed before
# the portfolio migrated to the current Serverless-first architecture.
from pyspark.sql import functions as F

df = (
    spark.range(0, 1_000_000, numPartitions=8)
    .withColumn("member_group", F.col("id") % 10)
    .withColumn("claim_amount", (F.col("id") % 500) + 50)
)

df.groupBy("member_group") \
  .agg(
      F.count("*").alias("claim_count"),
      F.sum("claim_amount").alias("total_claim_amount"),
      F.avg("claim_amount").alias("avg_claim_amount")
  ) \
  .orderBy("member_group") \
  .display()