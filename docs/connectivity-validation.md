# M1.12 — Connectivity Validation

**Project:** Azure Databricks Healthcare Lakehouse

**Environment:** DEV

**Status:** Validation completed; documentation and PR pending

**Validation date:** October 14, 2026

## 1. Objective

Validate connectivity between the local Python development environment, Azure Databricks, Unity Catalog, and ADLS Gen2 using existing infrastructure.

The validation prioritizes secure authentication, least-privilege access, reproducibility, and minimal cloud compute costs.

## 2. Validation Results

| Checkpoint | Test | Result |
|---|---|---|
| M1.12.1 | Git branch, clean working tree, Python dependencies | PASS |
| M1.12.2 | Databricks Python SDK authentication | PASS |
| M1.12.3 | Unity Catalog metadata and explicit grants | PASS |
| M1.12.4 | Databricks Connect Serverless Spark SQL | PASS |
| M1.12.5 | External volume metadata, directory listing, file lifecycle | PASS |
| M1.12.6 | Runtime service principal identity and grant inspection | PASS — metadata checks only |

## 3. Python SDK Connectivity

- Authentication profile: `healthcare-dev`
- SDK package: `databricks-sdk==0.150.0`
- Workspace API identity check: successful
- Authenticated user status: active

This validates programmatic workspace API connectivity without starting Spark compute.

## 4. Unity Catalog Connectivity

**Catalog:** `healthcare_dev`

Verified schemas:

- `bronze`
- `silver`
- `gold`
- `quarantine`
- `operational`

Additional schemas discovered: `default`, `information_schema`.

The `healthcare-data-engineers` group has the following explicit privileges on `healthcare_dev.bronze`:

- `USE_SCHEMA`
- `CREATE_TABLE`
- `SELECT`
- `MODIFY`

Catalog and schema metadata discovery completed successfully.

## 5. Serverless Spark Connectivity

Databricks Connect successfully established a remote Serverless Spark session.

Validated:

- Execution of `SELECT current_catalog()`
- Execution of `SHOW TABLES IN healthcare_dev.bronze`
- Successful session completion

The session's default catalog differed from `healthcare_dev`; the Bronze metadata query used a fully qualified schema reference.

**Result:** PASS

**Cost consideration:** Serverless Spark execution may incur compute charges.

## 6. ADLS Gen2 Connectivity

**Unity Catalog volume:** `healthcare_dev.bronze.member_raw`

**Volume type:** External

**Storage location:**

`abfss://raw@stdehealthcaredev.dfs.core.windows.net/member`

Validation performed through the Databricks Files API:

| Operation | Result |
|---|---|
| Volume metadata lookup | PASS |
| Directory listing | PASS — zero entries |
| Create synthetic test file | PASS |
| Download and verify exact file contents | PASS |
| Delete temporary test file | PASS |

A unique test filename was used to prevent overwriting existing files.

The temporary file was successfully deleted.

No Spark compute was required for these Files API operations.

## 7. Identity and Security Validation

**Runtime identity:** `sp-healthcare-runtime-dev`

Validated that:

1. The runtime service principal's application ID matches the principal assigned permissions on `healthcare_dev`.
2. The runtime principal has an explicit `USE_CATALOG` grant.
3. No direct Bronze schema grant was returned for the runtime principal.
4. No effective Bronze schema grant entry was returned specifically for the runtime principal.

Other catalog assignments include the `healthcare-analysts`, `healthcare-data-engineers`, and `healthcare-platform-admins` groups.

**Security limitation:** Grant inspection is not equivalent to executing as the runtime identity. Group-derived permissions, ownership, and other effective authorization factors have not been conclusively ruled out.

A runtime identity-based denial test remains deferred.

## 8. Security Follow-Up

The Databricks CLI OAuth token cache was previously identified as using plaintext storage on the local development workstation.

Follow-up actions:

- Verify supported secure credential storage options.
- Review local token-cache file permissions.
- Keep authentication caches, tokens, and credentials outside version control.
- Avoid printing or committing secrets.

Do not change the current authentication configuration without validating the supported replacement.

## 9. Cost Controls

- Reused existing Azure and Databricks resources.
- Used SDK metadata and Files API requests wherever possible.
- Limited Spark execution to a small read-only connectivity test.
- Created no new Azure infrastructure.
- Used synthetic test content only.

## 10. Conclusion

M1.12 successfully validated local development connectivity to Azure Databricks, Unity Catalog metadata, Serverless Spark, and an ADLS Gen2 external volume.

The identity configuration is consistent with the intended least-privilege design based on the grant metadata inspected.

Remaining security-hardening and runtime authorization testing are explicitly documented as follow-up work.

**Next milestone:** M1.13 — Foundation Documentation, Evidence & Freeze.