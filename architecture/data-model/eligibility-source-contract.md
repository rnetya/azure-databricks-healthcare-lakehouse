# Eligibility Source Contract — v1.0

**Project:** Azure Databricks Healthcare Lakehouse
**Milestone:** M2.1 — Healthcare Source Contracts
**Source:** Synthetic Eligibility Partner
**Dataset:** Eligibility
**Status:** Design Approved — v1.0

## 1. Business Purpose

The Eligibility dataset represents effective-dated healthcare program coverage for synthetic members.

A member may have multiple eligibility periods, and eligibility records may be corrected retroactively.

All records are synthetic. No real Protected Health Information (PHI) is used.

## 2. Delivery Contract

| Attribute | Specification |
|---|---|
| Delivery frequency | Daily |
| Delivery format | Parquet |
| Initial delivery | Full baseline |
| Subsequent deliveries | Incremental change feed |
| Filename | `eligibility_YYYYMMDD.parquet` for deliveries containing records |
| Business key | `EligibilityId` |
| Event key | `SourceChangeSequence` within the source event stream |
| Member relationship | Many eligibility records to one member |
| Change identification | `OperationType`, `SourceUpdatedAt`, `SourceChangeSequence` |
| Reprocessing | Idempotent using source event identity and deterministic ordering |
| Empty delivery | Manifest with zero changes; Parquet file not required |

## 3. Source Schema

| Column | Logical Type | Required | Description |
|---|---|---|---|
| `EligibilityId` | STRING | Yes | Stable coverage-record identifier |
| `MemberId` | STRING | INSERT/UPDATE | References Member |
| `ProgramCode` | STRING | INSERT/UPDATE | Healthcare program code |
| `CoverageStartDate` | DATE | INSERT/UPDATE | Business-effective coverage start |
| `CoverageEndDate` | DATE | No | Business-effective coverage end; null means no recorded end date |
| `EligibilityStatus` | STRING | INSERT/UPDATE | Eligibility record status |
| `SourceUpdatedAt` | TIMESTAMP | Yes | Source-side modification timestamp, in UTC |
| `OperationType` | STRING | Yes | INSERT, UPDATE, or DELETE |
| `SourceChangeSequence` | LONG | Yes | Unique, monotonically increasing source event sequence |

INSERT and UPDATE events must carry the complete required business record. DELETE events require only `EligibilityId`, `OperationType`, `SourceUpdatedAt`, and `SourceChangeSequence`; other business attributes may be null. `CoverageEndDate` is optional for INSERT and UPDATE events.

Parquet physical types and nullability for tombstones will be finalized during implementation.

## 4. Business Rules

Business attribute validation rules apply to INSERT and UPDATE events. DELETE events are validated against the minimal tombstone schema in Section 10.5.

1. `EligibilityId` must not be null or blank for any event.
2. `MemberId` must reference a valid synthetic member, except in controlled invalid-data scenarios.
3. `ProgramCode` must belong to the approved reference domain.
4. `CoverageStartDate` must be valid.
5. `CoverageEndDate`, when populated, must not precede `CoverageStartDate`.
6. `EligibilityStatus` must belong to the approved status domain.
7. `SourceUpdatedAt` must be a valid UTC timestamp for every event.
8. `OperationType` must be INSERT, UPDATE, or DELETE for every event.
9. `SourceChangeSequence` must uniquely identify an event and increase monotonically within the source event stream.
10. An open-ended coverage period does not automatically establish current eligibility.
11. Overlapping coverage periods must be evaluated according to program-specific rules.

## 5. Incremental Processing

The initial baseline establishes the starting eligibility population. Every baseline record uses `OperationType = INSERT` and receives a unique, increasing `SourceChangeSequence`.

Subsequent daily deliveries contain source changes:

- **INSERT:** A new eligibility record.
- **UPDATE:** A modification to an existing eligibility record.
- **DELETE:** Removal of a source record; not necessarily termination of healthcare coverage.

Each change event is uniquely identified by `SourceChangeSequence`. Incremental events continue after the highest baseline sequence, and the sequence is not reset between daily deliveries within the same source stream.

Changes are logically applied in `SourceChangeSequence` order. The generator must preserve sequence consistency across delivery dates. The processing platform must detect out-of-order or replayed events and handle them without duplicating state or history.

Each delivery must be identifiable for replay and audit purposes.

## 6. Effective-Dated History

`CoverageStartDate` and `CoverageEndDate` represent the business-effective coverage period.

`SourceUpdatedAt` represents when the source record was last modified.

These dates serve different purposes and must not be treated interchangeably. A retroactive correction may alter a historical coverage period even when the source change arrives later.

## 7. SCD Type 2 Requirements

Downstream Silver processing must support:

- Preserving prior versions of corrected eligibility records.
- Identifying the current known version.
- Recording system-version validity periods.
- Supporting historical as-of queries.
- Handling retroactive corrections.
- Avoiding duplicate versions during replay.

System-version columns will be added by the processing platform rather than the source producer.

## 8. Synthetic Test Scenarios

The generator must support:

- New eligibility records.
- Coverage termination.
- Coverage renewal.
- Program changes.
- Coverage gaps.
- Overlapping coverage periods.
- Retroactive corrections.
- Duplicate change events.
- Out-of-order changes.
- Invalid member references.
- Invalid date ranges.
- Replayed incremental deliveries.

Invalid scenarios must be explicitly identified in test expectations so downstream validation and quarantine behavior can be verified.

## 9. Generator Requirements

The generator must:

1. Produce a reproducible initial baseline.
2. Generate daily incremental changes.
3. Use stable Eligibility IDs.
4. Maintain referential relationships with synthetic Member records, except in controlled anomaly scenarios.
5. Support configurable data volumes and random seeds.
6. Produce typed Parquet columns.
7. Support deterministic replay.
8. Produce delivery metadata for validation and audit.
9. Maintain a unique, increasing source event sequence across baseline and incremental deliveries.

## 10. Finalized Contract Decisions

### 10.1 Program Code Domain

The synthetic Eligibility source supports six program codes:

| ProgramCode | Description |
|---|---|
| `MEDICAID` | Medicaid coverage |
| `CHIP` | Children's Health Insurance Program |
| `THIP` | Synthetic THIP program |
| `ABD` | Aged, Blind, and Disabled |
| `LTSS` | Long-Term Services and Supports |
| `HCBS` | Home and Community-Based Services |

Program codes will be maintained in the Reference dataset. These are synthetic classifications for the portfolio; they are not assumed to be mutually exclusive or to correspond to distinct insurance products in every real-world system.

### 10.2 Eligibility Status Domain

Supported values:

- `ACTIVE`
- `TERMINATED`
- `PENDING`

Eligibility status and coverage effective dates must both be evaluated when determining eligibility on a particular date.

### 10.3 Coverage Overlap Rules

- Coverage periods for different programs may overlap.
- Overlapping periods for the same `MemberId` and `ProgramCode` must be flagged for review.
- Overlaps must not be automatically rejected or silently corrected.
- Retroactive corrections must preserve historical traceability.

### 10.4 Incremental Change Ordering

Every source change must include:

- `EligibilityId`
- `OperationType`
- `SourceUpdatedAt`
- `SourceChangeSequence`

`SourceChangeSequence` must be unique and monotonically increasing within the source event stream. It provides deterministic ordering when multiple changes share the same timestamp.

`EligibilityId` identifies a coverage record, while `SourceChangeSequence` identifies an individual change event.

### 10.5 DELETE Event Contract

DELETE events must include:

- `EligibilityId`
- `OperationType = DELETE`
- `SourceUpdatedAt`
- `SourceChangeSequence`

Other business attributes may be null. A DELETE event represents removal of a source record and must not automatically be interpreted as termination of healthcare coverage.

### 10.6 Empty Incremental Deliveries

If no eligibility changes occur on a delivery date:

- Produce a delivery manifest indicating zero changes.
- Do not require an empty Parquet file.
- Record the delivery as successfully completed with zero changes.

### 10.7 Replay and Idempotency

- Reprocessing the same source change must not create duplicate current-state records or historical versions.
- Changes must be applied according to `SourceChangeSequence`.
- Out-of-order deliveries must be detected and handled according to the downstream replay strategy.
- Conflicting payloads for an existing `SourceChangeSequence` must be flagged for investigation.

### 10.8 Open Implementation Details

The following will be finalized during generator and ingestion development:

- Parquet physical schema and nullability for tombstone events.
- Manifest schema and checksum calculation.
- Late-arriving change handling and replay strategy.
- Reference-data effective dates and program-specific overlap exceptions.
