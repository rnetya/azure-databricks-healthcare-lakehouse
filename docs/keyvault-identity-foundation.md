
# M1.10 â€” Key Vault and Workload Identity Foundation

**Project:** Azure Databricks Healthcare Lakehouse
**Environment:** DEV
**Status:** Implemented and validated; documentation review pending
**Architecture:** Serverless-first, Unity Catalog governed, identity-first

## 1. Objective

Establish secure secret management, workload identity, and least-privilege authorization for the healthcare lakehouse.

Security principles:

- Prefer managed identities and workload federation over stored credentials.
- Use Key Vault only when credentials cannot be eliminated.
- Separate human administration from automated execution.
- Grant privileges based on actual workload requirements.
- Never commit credentials, secret values, or identity tokens to Git.
- Use synthetic data and synthetic secrets only.

## 2. Azure Key Vault

Resource: `kv-de-healthcare-dev`

Configuration:

| Property | Configuration |
|---|---|
| Resource group | `rg-de-healthcare-dev` |
| Region | East US |
| Tier | Standard |
| Authorization | Azure RBAC |
| Soft delete | Enabled, 90 days |
| Purge protection | Enabled |
| Networking | Public endpoint for DEV |
| Private networking | Deferred until required |

The human administrator has the **Key Vault Secrets Officer** role scoped to the vault.

A synthetic secret, `provider-api-key-validation`, was created and successfully retrieved to validate secret-management permissions.

This test did not use a production credential.

### Architecture decision

The vault remains Azure RBAC-based.

We intentionally did not switch to legacy access policies merely to enable a traditional Azure Key Vault-backed Databricks secret scope.

## 3. Databricks Secret Management

Workspace secret scope: `healthcare-dev`

Backend: `DATABRICKS`

Synthetic validation key: `provider-api-key-validation`

Permissions:

| Principal | Permission |
|---|---|
| healthcare-platform-admins | MANAGE |
| healthcare-data-engineers | READ |
| Individual DEV administrator | MANAGE |
| healthcare-analysts | No explicit access |

The individual administrator permission is retained for the DEV validation environment.

Validation demonstrated:

- Scope discovery through Databricks CLI.
- Secret-key metadata listing without revealing the value.
- Successful `dbutils.secrets.get()` retrieval.
- Databricks notebook output redaction.
- Non-empty synthetic secret retrieval.

Secret redaction is a protective convenience, not a substitute for restricting READ access.

The Azure Key Vault and Databricks-backed scope are separate secret stores. The same synthetic key name does not imply automatic synchronization.

## 4. ADLS Gen2 Authentication

ADLS access uses:

Unity Catalog â†’ Storage Credential â†’ Azure Databricks Access Connector â†’ Managed Identity â†’ Azure RBAC â†’ ADLS Gen2

Key Vault is not required for this storage authentication path.

This eliminates the need for embedded storage account keys, SAS tokens, or connection-string passwords in notebooks.

## 5. Runtime Service Principal

Identity: `sp-healthcare-runtime-dev`

Management: Databricks-managed service principal.

Workspace configuration:

| Entitlement | State |
|---|---|
| Workspace access | Enabled |
| Databricks SQL access | Disabled |
| Consumer access | Disabled |
| Admin access | Disabled |

Service-principal permissions:

| Principal | Permission |
|---|---|
| healthcare-platform-admins | MANAGE |
| healthcare-data-engineers | USE |
| Individual DEV administrator | USE and MANAGE |
| healthcare-analysts | No explicit access |

`MANAGE` does not automatically imply `USE`.

No OAuth client secret was generated for this identity.

## 6. Serverless Job Run As

Validation job: `m1-10-runtime-identity-validation`

Task: `validate_runtime_identity`

Compute: Serverless

Runtime identity: `sp-healthcare-runtime-dev`

Notebook:

`/Workspace/Shared/healthcare-lakehouse/foundation/03_runtime_identity_validation`

The human developer creates and manages the job while the service principal executes the workload.

### UI and CLI validation

The Jobs UI Run As dropdown did not list the service principal, despite its ACTIVE status and confirmed USE permission.

The Databricks CLI successfully updated the persisted job using the service principal's Application ID through the Jobs API.

The Jobs UI subsequently displayed the service principal as the configured Run As identity.

This behavior was observed in the DEV workspace; no general platform-wide UI limitation is asserted.

## 7. Workspace Permission Boundary

Initial run:

- Notebook resided in the developer's personal workspace folder.
- Job executed as the service principal.
- Run failed with `ResourceNotFound` because the runtime identity could not access the notebook.

Remediation:

- Moved the notebook into the shared project foundation directory.
- Granted the service principal `Can Run` on the notebook.
- Updated the job's notebook path.
- Reran successfully.

This demonstrates that a Run As identity does not automatically inherit the job creator's workspace permissions.

## 8. Runtime Identity Validation

The Serverless job executed successfully.

`current_user()` returned the service principal's Application ID rather than its display name.

The identity was verified against the service principal configured for the job.

No Application ID is required in the public validation script.

## 9. Unity Catalog Least-Privilege Validation

Target catalog: `healthcare_dev`

### Before USE CATALOG

`SHOW CATALOGS` did not include `healthcare_dev`.

Result: `Target catalog visible: False`

### After USE CATALOG

Granted only `USE CATALOG` to `sp-healthcare-runtime-dev`.

`SHOW CATALOGS` included `healthcare_dev`.

Result: `Target catalog visible: True`

### Schema boundary

`SHOW SCHEMAS IN healthcare_dev` returned only `information_schema`.

Result: `Bronze schema visible: False`

No `USE SCHEMA`, `SELECT`, `MODIFY`, or `CREATE TABLE` permissions were granted to the runtime identity.

Additional data permissions will be introduced only when a pipeline requires them.

## 10. Security and Cost Decisions

- No permanent classic compute or NAT Gateway was provisioned for these tests.
- Serverless Jobs were invoked manually.
- No recurring schedule is required for validation.
- No real healthcare data or production credentials were used.
- No secrets or tokens are included in this repository.
- Runtime identities receive only workload-specific privileges.
- Temporary validation resources should be reviewed during portfolio cleanup.

## 11. Evidence Summary

| Validation | Outcome |
|---|---|
| Key Vault RBAC secret management | PASS |
| Databricks-backed secret retrieval | PASS |
| Secret-scope ACL verification | PASS |
| Service principal creation and permissions | PASS |
| CLI Run As configuration | PASS |
| Personal notebook access isolation | PASS |
| Shared notebook Can Run execution | PASS |
| Serverless non-human execution | PASS |
| UC catalog visibility before grant | PASS |
| UC catalog visibility after grant | PASS |
| UC schema restriction | PASS |

## 12. Future Work

- Assign schema/table/volume privileges only when actual ingestion workloads require them.
- Evaluate workload-specific identities for pipeline isolation.
- Implement GitHub Actions OIDC/workload federation during CI/CD.
- Review identity permissions and temporary validation assets before production-style packaging.
- Revisit networking only when source connectivity or security requirements justify changes.
