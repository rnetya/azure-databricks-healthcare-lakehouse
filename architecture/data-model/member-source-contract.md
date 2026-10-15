# Member Source Contract — v1.0

**Project:** Azure Databricks Healthcare Lakehouse

**Milestone:** M2.1 — Healthcare Source Contracts

**Source:** Synthetic Enrollment System

**Dataset:** Member

**Status:** Design Approved — v1.0

## 1. Business Purpose

The Member source provides the current enrollment-system representation of each synthetic healthcare member.

It serves as the foundational entity for Eligibility, Claims, and Service Event relationships.

All records are synthetic. No real Protected Health Information (PHI) is used.

## 2. Delivery Contract

| Attribute | Specification |
|---|---|
| Delivery frequency | Daily |
| Delivery type | Full snapshot |
| Format | CSV with header |
| Encoding | UTF-8 |
| Filename | `member_YYYYMMDD.csv` |
| Date format | `YYYY-MM-DD` |
| Timestamp format | ISO 8601 UTC |
| Business key | `MemberId` |
| Expected uniqueness | One row per `MemberId` per snapshot |
| Initial delivery | Complete baseline snapshot |
| Subsequent deliveries | Complete current-state snapshot |

The date embedded in the filename represents the logical snapshot date.

A successful delivery must represent the complete member population for that date.

## 3. Source Schema

| Column | Logical Type | Required | Description |
|---|---|---|---|
| `MemberId` | STRING | Yes | Stable synthetic member identifier |
| `FirstName` | STRING | Yes | Synthetic first name |
| `LastName` | STRING | Yes | Synthetic last name |
| `DateOfBirth` | DATE | Yes | Member birth date |
| `GenderCode` | STRING | Yes | Synthetic demographic code |
| `AddressLine1` | STRING | No | Synthetic street address |
| `City` | STRING | No | City |
| `StateCode` | STRING | Yes | Two-character state code |
| `ZipCode` | STRING | No | Postal code |
| `MemberStatus` | STRING | Yes | Current enrollment-system status |
| `SourceUpdatedAt` | TIMESTAMP | Yes | Most recent source-side record update time |

All CSV values are physically stored as text. Logical types describe downstream parsing expectations.

## 4. Proposed Business Rules

1. `MemberId` must not be null or blank.
2. `MemberId` must be unique within a valid snapshot.
3. `FirstName` and `LastName` must not be blank.
4. `DateOfBirth` must be a valid date and must not be after the snapshot date.
5. `GenderCode` must match the agreed reference-code domain.
6. `StateCode` must be a valid two-character state code.
7. `MemberStatus` must belong to the agreed status domain.
8. `SourceUpdatedAt` must be a valid UTC timestamp.
9. Snapshot filenames must match the configured naming convention.
10. Snapshot completeness must be validated before processing missing-member changes.

Reference-code domains and completeness thresholds will be finalized during source-contract review.

## 5. Snapshot Reconciliation

For two consecutive accepted snapshots:

| Classification | Definition |
|---|---|
| New | Member exists in the current snapshot but not the previous accepted snapshot |
| Changed | Member exists in both snapshots and compared business attributes differ |
| Unchanged | Member exists in both snapshots and compared business attributes match |
| Missing | Member exists in the previous accepted snapshot but not the current snapshot |

Missing members must not automatically be classified as deleted or inactive.

Snapshot completeness, source delivery status, and agreed business rules must be considered before any downstream status changes.

## 6. Ingestion Metadata — Future Bronze Layer

The ingestion framework will add operational metadata separately from the source CSV, including:

- Source filename
- Logical snapshot date
- Ingestion timestamp
- Batch or run identifier
- Record hash

These are platform-generated metadata fields and are not part of the producer's source schema.

## 7. Synthetic Data Test Scenarios

The generator will eventually produce controlled scenarios covering:

- New members
- Updated member demographics
- Status changes
- Unchanged members
- Duplicate member identifiers
- Missing required values
- Invalid reference codes
- Malformed dates and timestamps
- Missing members in a subsequent snapshot
- Incomplete snapshot deliveries

Invalid scenarios will be explicitly identified in generator test expectations so downstream quality rules can be evaluated.

## 8. Downstream Dependencies

Member identifiers will be referenced by:

- Eligibility records
- Claims records
- Service Events

The Member source contract must remain compatible with those future datasets.

## 9. Implementation Boundary

**M2:** Define the contract and generate reproducible synthetic source files.

**M3:** Implement Bronze ingestion and operational metadata capture.

**M4 onward:** Implement validation, reconciliation, quarantine, and downstream transformations.

## 10. Finalized Contract Decisions

| Decision | Specification |
|---|---|
| Member identifier | `M` followed by at least six digits, zero-padded; identifiers remain stable across snapshots |
| Gender domain | `M`, `F`, `U` |
| Member status domain | `ACTIVE`, `INACTIVE` |
| Development population | 10,000 members |
| Performance population | 100,000 members |
| Generator population | Configurable, including smaller test datasets |
| Random seed | Configurable; fixed seed produces reproducible output for identical inputs |
| Snapshot completeness | Validate schema, manifest, expected row count and checksum |
| Snapshot replay | Identical same-date deliveries are idempotent |
| Snapshot correction | Changed same-date content requires an explicit correction version |
| Missing members | Flag for reconciliation; never automatically delete |

### Generator Requirements

The synthetic Member generator must:

1. Accept a configurable population size.
2. Accept a configurable random seed.
3. Accept a logical snapshot date.
4. Generate stable Member IDs across consecutive snapshots.
5. Support controlled new, changed, unchanged and missing-member scenarios.
6. Produce a complete daily CSV snapshot.
7. Generate a delivery manifest containing the snapshot date, expected record count and checksum.
8. Support 10,000-member development datasets and 100,000-member performance datasets.
9. Support repeatable output for identical configuration and input state.
10. Produce only synthetic data.

### Performance Considerations

The generator should support large datasets without unnecessary memory consumption. Generation time, output file size and record count will be measured during performance testing.