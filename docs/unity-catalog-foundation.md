# Unity Catalog Foundation — M1.9

## 1. Purpose

This document records the implemented Unity Catalog foundation for the
Azure Databricks Healthcare Lakehouse portfolio.

The objective of M1.9 is to establish a governed data layer that separates:

- Compute from persistent storage
- Managed data from externally managed files
- Engineering access from analytical consumption
- Human identities from Azure storage authentication
- Data ownership from individual users

The implementation follows a Serverless-first Azure Databricks architecture
with Unity Catalog as the primary governance layer and Azure Data Lake
Storage Gen2 (ADLS Gen2) as the persistent storage layer.

---

## 2. Architecture Overview

The implemented foundation follows this model:

    Source Systems
          |
          v
    Ingestion / Landing
          |
          v
    Azure Databricks Serverless
          |
          v
    Unity Catalog
          |
          v
    healthcare_dev
          |
          +-- bronze
          +-- silver
          +-- gold
          +-- quarantine
          +-- operational
          |
          v
    ADLS Gen2

Core architectural responsibility:

- Databricks Serverless provides compute.
- Unity Catalog governs data and access.
- ADLS Gen2 provides persistent storage.

This separation allows the Databricks workspace and compute layer to evolve
without coupling the lifecycle of governed data to individual compute
resources.

---

## 3. Unity Catalog Object Model

The DEV environment uses the following Unity Catalog hierarchy:

    healthcare_dev
    |
    +-- bronze
    +-- silver
    +-- gold
    +-- quarantine
    +-- operational

### Schema Responsibilities

| Schema | Responsibility |
|---|---|
| `bronze` | Source-faithful ingestion and replayable data |
| `silver` | Validated, typed, deduplicated, and standardized data |
| `gold` | Curated business-facing data products |
| `quarantine` | Invalid or rejected records requiring investigation or controlled reprocessing |
| `operational` | Pipeline metadata, audit information, checkpoints, and operational state |

The schemas represent logical governance and processing boundaries rather
than separate physical storage accounts.

---

## 4. Azure Storage Integration

Unity Catalog accesses portfolio storage using managed identity rather than
embedded credentials, storage keys, or SAS tokens.

Implemented authentication chain:

    Unity Catalog
          |
          v
    Storage Credential
          |
          v
    Azure Databricks Access Connector
          |
          v
    Managed Identity
          |
          v
    Azure RBAC
          |
          v
    ADLS Gen2

The DEV storage credential is:

    sc-de-healthcare-dev

The Azure Databricks Access Connector is:

    ac-de-healthcare-dev

This design avoids embedding Azure storage credentials inside notebooks,
SQL scripts, or pipeline code.

---

## 5. Managed Storage

The `healthcare_dev` catalog uses governed managed storage backed by the
portfolio ADLS Gen2 `managed` container.

Unity Catalog controls the physical storage lifecycle of managed tables.

Conceptually:

    Serverless Spark / SQL
          |
          v
    Unity Catalog Managed Table
          |
          v
    healthcare_dev.<schema>
          |
          v
    ADLS managed/__unitystorage

A temporary managed Delta table was created, written, queried, and removed
during validation.

The validation demonstrated that:

- Serverless Spark can create Unity Catalog managed Delta tables.
- Data is persisted in the catalog-managed ADLS location.
- Notebook code does not require storage credentials or physical storage paths.
- Dropping the temporary validation object cleans up the governed test object.

Managed tables are the preferred storage model for Bronze, Silver, and Gold
Delta tables unless an engineering requirement specifically requires
externally managed storage.

---

## 6. External Storage and Volumes

External storage is used where the physical file location must remain
explicitly controlled.

The raw landing container is governed through the external location:

    el-de-healthcare-raw-dev

The first permanent external volume is:

    healthcare_dev.bronze.member_raw

It maps to the Member raw landing directory in ADLS Gen2.

Databricks workloads access this storage through the Unity Catalog Volume
namespace:

    /Volumes/healthcare_dev/bronze/member_raw/

rather than embedding an ABFSS path in application code.

Validation included:

1. Listing the empty external Volume from Serverless Spark.
2. Writing a temporary validation file through `/Volumes`.
3. Listing the file using Databricks filesystem utilities.
4. Confirming the same file through Catalog Explorer.
5. Removing the validation file.
6. Confirming the Volume returned to an empty state.

The permanent `member_raw` Volume remains in place for future Member CSV
ingestion.

Conceptually:

    Serverless Spark
          |
          v
    /Volumes/healthcare_dev/bronze/member_raw/
          |
          v
    Unity Catalog External Volume
          |
          v
    External Location
          |
          v
    Storage Credential
          |
          v
    Access Connector / Managed Identity
          |
          v
    ADLS raw/member/

This separates governed file access from direct cloud-storage authentication.

---

## 7. External Location Strategy

The initial DEV foundation contains governed external-location coverage for:

- Managed catalog storage
- Raw source landing storage

External-location coverage for `quarantine` and `operational` storage is
intentionally deferred.

These objects will be introduced when an engineering requirement requires
them, for example:

- Quarantine output from data-quality processing
- Structured Streaming checkpoints
- Operational metadata
- Pipeline audit data

Architectural principle:

> Create infrastructure when an engineering requirement demands it, not
> simply because it can be created.

External volumes should map to intentional subdirectories beneath governed
external locations rather than overlapping storage roots.

---

## 8. Identity and Access Model

Three account-level groups establish the initial role-based access model:

    healthcare-platform-admins
    healthcare-data-engineers
    healthcare-analysts

The groups are assigned to the DEV Databricks workspace.

For portfolio validation, the project owner can belong to multiple groups.
Privileges are nevertheless assigned to groups rather than directly to an
individual user.

Conceptually:

    User
      |
      v
    Account Group
      |
      v
    Unity Catalog Privilege
      |
      v
    Governed Data Object

This provides a foundation that can later support separate engineering,
platform, analytical, and service identities.

---

## 9. Permission Matrix

### Catalog

| Principal | Privileges |
|---|---|
| `healthcare-platform-admins` | `USE CATALOG`, `MANAGE`, Catalog Owner |
| `healthcare-data-engineers` | `USE CATALOG` |
| `healthcare-analysts` | `USE CATALOG` |

Catalog ownership was transferred from an individual identity to:

    healthcare-platform-admins

This prevents the governed data domain from depending on ownership by one
individual user.

### Data Engineer Access

`healthcare-data-engineers` receives the following privileges across the
engineering schemas:

| Schema | Privileges |
|---|---|
| `bronze` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` |
| `silver` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` |
| `gold` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` |
| `quarantine` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` |
| `operational` | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, `MODIFY` |

For the external Member landing Volume:

| Object | Privileges |
|---|---|
| `healthcare_dev.bronze.member_raw` | `READ VOLUME`, `WRITE VOLUME` |

### Analyst Access

`healthcare-analysts` is intentionally restricted to the curated Gold layer:

| Object | Privileges |
|---|---|
| `healthcare_dev` | `USE CATALOG` |
| `healthcare_dev.gold` | `USE SCHEMA`, `SELECT` |

Analysts receive no direct access to:

- Bronze
- Silver
- Quarantine
- Operational
- Raw external Volumes

This establishes Gold as the approved analytical consumption layer.

---

## 10. Least-Privilege Principles

The permission model deliberately avoids broad grants.

The implementation does not rely on:

- `ALL PRIVILEGES` for engineering groups
- Workspace administrator rights for Data Engineers or Analysts
- Direct analyst access to source landing files
- Direct analyst access to Bronze or Silver
- Storage account keys
- SAS tokens embedded in notebooks
- Individual-user grants for normal data access

Privileges are assigned according to workload responsibility.

---

## 11. SQL and Catalog Explorer Validation

The governance model was validated independently through both Catalog
Explorer and Databricks SQL.

Catalog-level validation confirmed:

    healthcare-analysts        -> USE CATALOG
    healthcare-data-engineers  -> USE CATALOG
    healthcare-platform-admins -> USE CATALOG, MANAGE

Gold validation confirmed:

    healthcare-analysts
      -> USE SCHEMA
      -> SELECT

    healthcare-data-engineers
      -> USE SCHEMA
      -> CREATE TABLE
      -> SELECT
      -> MODIFY

Bronze validation confirmed:

    healthcare-data-engineers
      -> USE SCHEMA
      -> CREATE TABLE
      -> SELECT
      -> MODIFY

and no Analyst Bronze access.

External Volume validation confirmed:

    healthcare-data-engineers
      -> READ VOLUME
      -> WRITE VOLUME

and no Analyst access to the raw Member Volume.

Catalog ownership was validated using:

    DESCRIBE CATALOG EXTENDED healthcare_dev;

The result confirmed:

    Owner = healthcare-platform-admins

The SQL results matched the permissions displayed through Catalog Explorer.

---

## 12. Serverless Architecture Validation

The Unity Catalog foundation was validated from Azure Databricks Serverless
compute.

Serverless Spark validation demonstrated:

- Spark execution
- Unity Catalog catalog/schema resolution
- Managed Delta table creation and query
- Governed ADLS-backed storage
- External Volume access
- External file write/read/delete operations

Serverless SQL validation demonstrated:

- Catalog resolution
- Schema resolution
- Unity Catalog privilege inspection
- Catalog ownership inspection
- Governed SQL access

The architecture therefore maintains the following separation:

    Databricks Serverless = Compute
    Unity Catalog         = Governance
    ADLS Gen2             = Persistent Storage

---

## 13. Deferred Decisions

The following items are intentionally deferred until required by later
implementation milestones:

- Quarantine external location / Volume implementation
- Operational external location / Volume implementation
- Streaming checkpoint storage implementation
- Additional source-specific raw Volumes
- Service-principal runtime identities
- CI/CD deployment identity
- Production-oriented DEV/UAT/PRD privilege separation
- Row filters and column masking
- Data classification
- Additional data-quality governance controls

These are architectural requirements to be introduced when their associated
workloads are implemented.

---

## 14. M1.9 Completion Status

The following Unity Catalog foundation capabilities have been implemented
and validated:

- Unity Catalog architecture and object model
- Metastore and catalog baseline
- Azure managed-identity storage integration
- Storage credential
- External-location foundation
- `healthcare_dev` catalog
- Bronze, Silver, Gold, Quarantine, and Operational schemas
- Managed Delta storage validation
- External Volume validation
- Role-based account groups
- Least-privilege catalog and schema permissions
- Group-based catalog ownership
- SQL-based permission validation
- Catalog Explorer validation
- Serverless Spark integration
- Serverless SQL integration

M1.9 establishes the governed storage and access foundation required for
subsequent ingestion, transformation, streaming, orchestration, data-quality,
and analytics milestones.