
# Databricks notebook source
# M1.10 — Runtime Identity and Unity Catalog Validation
# Execute as a Databricks Job using sp-healthcare-runtime-dev.
# Synthetic portfolio validation only.

# COMMAND ----------

# 1. Identify the effective SQL execution principal.

identity_df = spark.sql("""
    SELECT
        current_user() AS execution_identity,
        current_catalog() AS current_catalog,
        current_schema() AS current_schema
""")

display(identity_df)

execution_identity = identity_df.first()["execution_identity"]

print("Runtime identity validation")
print("---------------------------")
print("Identity returned:", execution_identity)
print("Human-style identity:", "@" in execution_identity)
print("Non-human-style identity:", "@" not in execution_identity)

# Note:
# The string-format check is diagnostic only.
# An identity without '@' is not automatically a trusted
# service principal. Verify the returned identity against
# the job's configured Run As principal.

# COMMAND ----------

# 2. Inspect catalog visibility.

target_catalog = "healthcare_dev"

catalog_df = spark.sql("SHOW CATALOGS")
visible_catalogs = [row.catalog for row in catalog_df.collect()]

print("Target catalog:", target_catalog)
print("Target catalog visible:", target_catalog in visible_catalogs)

# COMMAND ----------

# 3. Inspect schema visibility.

target_schema = "bronze"

schema_df = spark.sql("SHOW SCHEMAS IN healthcare_dev")
visible_schemas = [
    row.databaseName for row in schema_df.collect()
]

print("Target schema:", f"{target_catalog}.{target_schema}")
print("Bronze schema visible:", target_schema in visible_schemas)
print("Visible schemas:", visible_schemas)

# COMMAND ----------

# 4. Summary

print("M1.10 Security Validation")
print("------------------------")
print("Runtime identity query: PASS")
print("Catalog visibility check: COMPLETE")
print("Schema visibility check: COMPLETE")

# Expected baseline after M1.10.6:
# - Job Run As: sp-healthcare-runtime-dev
# - healthcare_dev visible: True
# - bronze visible: False
#
# Do not grant additional permissions solely to change
# a negative authorization result into a positive one.
