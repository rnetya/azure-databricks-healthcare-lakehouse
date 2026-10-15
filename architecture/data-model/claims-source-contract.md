# Claims Source Contract — v1.0

**Project:** Azure Databricks Healthcare Lakehouse

**Milestone:** M2.1 — Healthcare Source Contracts

**Source:** Synthetic Claims Processing System (SQL Server)

**Dataset:** Claims

**Status:** Design Approved — v1.0

## 1. Business Purpose

The Claims source represents synthetic healthcare claims submitted for services provided to enrolled members.

Claims reference members, providers, healthcare programs, and service codes.

The dataset supports claims utilization, financial analysis, claim status monitoring, and incremental data processing.

All records are synthetic. No real Protected Health Information (PHI) is used.

## 2. Delivery and Extraction Contract

| Attribute | Specification |
|---|---|
| Source platform | Microsoft SQL Server |
| Source object | `dbo.Claims` |
| Extraction interface | Spark JDBC |
| Initial extraction | Full baseline |
| Subsequent extraction | Incremental |
| Prototype watermark | `ModifiedAt` |
| Business key | `ClaimId` |
| Update strategy | Upsert using Delta MERGE |
| Delete handling | Not supported by timestamp-only extraction; requires explicit design |
| Extraction frequency | Daily initially |
| Historical changes | Preserved through Bronze ingestion and audit history |

## 3. Source Schema

| Column | SQL Server Type | Required | Description |
|---|---|---|---|
| `ClaimId` | BIGINT | Yes | Unique claim identifier |
| `MemberId` | VARCHAR(20) | Yes | Synthetic member reference |
| `ProviderId` | VARCHAR(20) | Yes | Synthetic provider reference |
| `ProgramCode` | VARCHAR(20) | Yes | Healthcare program code |
| `ServiceCode` | VARCHAR(20) | Yes | Healthcare service code |
| `ServiceDate` | DATE | Yes | Date of service |
| `ClaimStatus` | VARCHAR(20) | Yes | Current claim status |
| `BilledAmount` | DECIMAL(18,2) | Yes | Submitted amount |
| `AllowedAmount` | DECIMAL(18,2) | No | Approved amount |
| `PaidAmount` | DECIMAL(18,2) | No | Paid amount |
| `CreatedAt` | DATETIME2(3) | Yes | Source creation timestamp, UTC |
| `ModifiedAt` | DATETIME2(3) | Yes | Latest source modification timestamp, UTC |
| `SourceChangeVersion` | BIGINT | Yes | Source-assigned change version for investigation and future extraction strategies |

`SourceChangeVersion` is not assumed to be commit-ordered or sufficient for complete change capture.

## 4. Proposed Business Rules

1. `ClaimId` must be unique and non-null.
2. `MemberId` must reference an existing synthetic member, except in controlled invalid-data scenarios.
3. `ProviderId` must reference an existing synthetic provider, except in controlled invalid-data scenarios.
4. `ProgramCode` and `ServiceCode` must belong to approved reference domains.
5. `ServiceDate` must be a valid date.
6. `BilledAmount` must be nonnegative.
7. `AllowedAmount` and `PaidAmount`, when populated, must be nonnegative.
8. `PaidAmount` must not exceed `AllowedAmount` unless an explicitly modeled adjustment or exception applies.
9. `CreatedAt` and `ModifiedAt` must represent UTC timestamps.
10. `ModifiedAt` must not precede `CreatedAt`.

## 5. Claim Status Domain and Lifecycle

Supported claim statuses:

- SUBMITTED
- PENDING
- APPROVED
- DENIED
- PAID
- ADJUSTED

### 5.1 Claim Lifecycle

The synthetic claims system supports the following typical transitions:

- SUBMITTED → PENDING
- PENDING → APPROVED
- PENDING → DENIED
- APPROVED → PAID
- DENIED → PENDING (reprocessing)
- PAID → ADJUSTED
- APPROVED → ADJUSTED

These represent supported scenarios, not an exhaustive list of all possible healthcare claim transitions.

### 5.2 Financial Rules

| Claim Status | AllowedAmount | PaidAmount |
|---|---|---|
| SUBMITTED | NULL | NULL |
| PENDING | NULL or nonnegative calculated amount | NULL |
| APPROVED | Nonnegative | NULL or 0 |
| DENIED | 0 | 0 |
| PAID | Nonnegative | Nonnegative and no greater than AllowedAmount |
| ADJUSTED | Recalculated nonnegative amount | Recalculated nonnegative amount, no greater than AllowedAmount |

Financial exceptions must be explicitly modeled and identified rather than silently accepted.

These are synthetic portfolio rules and do not attempt to represent every real-world adjudication scenario.

## 6. Incremental Extraction

The initial load establishes the source baseline.

The prototype incremental extractor will use `ModifiedAt` with a bounded extraction window.

The extraction design must:

- Capture newly inserted claims.
- Capture updates to existing claims.
- Avoid advancing the watermark before a successful durable write.
- Define timestamp boundary behavior.
- Detect duplicate extraction during replay.
- Evaluate concurrent updates and late commits.
- Document the inability of timestamp-only extraction to identify hard deletes.

The prototype does not guarantee lossless CDC. The final extraction strategy will be validated during M5.

## 7. Claim Adjustments

### 7.1 Adjustment Strategy

Claims v1.0 uses a single SQL Server source table.

Each ClaimId identifies one claim whose current values may change over time.

Claim adjustments update the existing claim record rather than inserting a separate adjustment transaction.

### 7.2 Supported Adjustment Scenarios

- Claim approval
- Claim denial
- Payment posting
- Allowed amount adjustment
- Paid amount adjustment
- Claim reprocessing

### 7.3 Historical Processing

The SQL Server source represents the latest committed state of each claim.

Bronze preserves the states observed during extraction, and Silver maintains the latest accepted state using Delta MERGE.

Multiple source changes occurring between extractions may not all be observed.

A separate adjustment transaction history is outside the scope of Claims v1.0.

### 7.4 Financial Aggregation

Gold claims utilization calculations must use the latest accepted claim state when calculating current financial totals.

Historical extracted states must not be summed together as independent claims, because doing so would double-count amounts.

## 8. Bronze and Silver Requirements

Bronze ingestion must preserve extracted claim data and operational metadata.

Silver processing must:

- Validate claim attributes and references.
- Deduplicate replayed records.
- Identify the latest accepted source state.
- MERGE inserts and updates by `ClaimId`.
- Route invalid records to quarantine.
- Support idempotent reprocessing.

## 9. Synthetic Test Scenarios

The generator must support:

- Initial claim population.
- New claims.
- Existing claim updates.
- Status transitions.
- Payment adjustments.
- Late-arriving claims with historical service dates.
- Duplicate extraction.
- Invalid member references.
- Invalid provider references.
- Invalid financial amounts.
- Equal modification timestamps.
- Replayed extraction windows.

## 10. Generator Requirements

The synthetic Claims generator must:

1. Produce reproducible claim records using configurable random seeds.
2. Support configurable record volumes.
3. Maintain valid Member and Provider relationships for standard scenarios.
4. Populate a local SQL Server source table.
5. Generate inserts and updates across multiple logical processing dates.
6. Preserve stable Claim IDs.
7. Generate controlled invalid-data scenarios.
8. Produce expected results for incremental extraction testing.

## 11. Finalized Decisions and Deferred Design

### Finalized for v1.0

- SQL Server is the synthetic Claims source.
- Initial extraction uses a full baseline.
- Subsequent extraction uses a timestamp-watermark prototype.
- Claims are identified by ClaimId.
- Supported claim statuses are SUBMITTED, PENDING, APPROVED, DENIED, PAID, and ADJUSTED.
- Adjustments update the existing Claims record.
- Gold current-state financial aggregation must avoid counting historical versions multiple times.

### Deferred to M5

- Hard-delete capture and handling.
- Final change-capture mechanism: timestamp watermark, SQL Server Change Tracking, or CDC.
- Commit-consistent extraction boundaries.
- Secure connectivity between local SQL Server and Databricks Serverless.
- Incremental extraction recovery and watermark advancement guarantees.