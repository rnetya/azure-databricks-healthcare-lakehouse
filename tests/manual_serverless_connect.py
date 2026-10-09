"""Manual Databricks Connect Serverless smoke test."""

from databricks.connect import DatabricksSession

spark = DatabricksSession.builder.serverless().getOrCreate()

print("Databricks Connect session created")

members = spark.createDataFrame(
    [
        ("MEM001", "Active"),
        ("MEM002", "Inactive"),
        ("MEM003", "Active"),
    ],
    ["MemberId", "EligibilityStatus"],
)

members.show()

print("Total members:", members.count())

spark.stop()
