# Reference Data Source Contract — v1.0

**Project:** Azure Databricks Healthcare Lakehouse

**Milestone:** M2.1 — Healthcare Source Contracts

**Source:** Synthetic Reference Data Generator

**Status:** Design Approved — v1.0

## 1. Business Purpose

The Reference Data source provides controlled code sets used for validation, enrichment, and consistent analytics across Member, Eligibility, Claims, Provider, and Service Events.

All reference data is synthetic or based on non-sensitive standardized classifications.

## 2. Delivery Contract

| Attribute | Specification |
|---|---|
| Source system | Python Reference Data Generator |
| File formats | CSV and Parquet |
| Delivery type | Full snapshot |
| Default frequency | On demand / when changed |
| Character encoding | UTF-8 for CSV |
| Storage destination | ADLS Gen2 raw/reference |
| Business key | ReferenceDomain + ReferenceCode |
| Version tracking | ReferenceVersion |
| Effective dating | EffectiveStartDate / EffectiveEndDate |

Files follow this naming convention:

`reference_<domain>_YYYYMMDD.csv`

or

`reference_<domain>_YYYYMMDD.parquet`

The initial generator produces reproducible reference datasets.

## 3. Reference Domains

| Domain | Used By | Purpose |
|---|---|---|
| PROGRAM_CODE | Eligibility, Claims | Healthcare program classification |
| PROVIDER_TYPE | Provider | Provider classification |
| SPECIALTY_CODE | Provider | Provider specialties |
| SERVICE_CODE | Claims, Service Events | Healthcare service classification |
| GENDER_CODE | Member | Member gender-code validation |
| STATE_CODE | Member, Provider | State-code validation |
| CLAIM_STATUS | Claims | Claim lifecycle status |
| ELIGIBILITY_STATUS | Eligibility | Coverage status |
| MEMBER_STATUS | Member | Member status |
| SERVICE_EVENT_TYPE | Service Events | Event lifecycle classification |

## 4. Standard Reference Schema

| Field | Type | Required | Description |
|---|---|---|---|
| ReferenceDomain | STRING | Yes | Code-set identifier |
| ReferenceCode | STRING | Yes | Code value |
| ReferenceDescription | STRING | Yes | Human-readable meaning |
| IsActive | BOOLEAN | Yes | Active status |
| EffectiveStartDate | DATE | Yes | Business validity start |
| EffectiveEndDate | DATE | No | Business validity end |
| ReferenceVersion | STRING | Yes | Published reference version |
| SourceUpdatedAt | TIMESTAMP | Yes | Source update timestamp |

The business identity is ReferenceDomain + ReferenceCode. Multiple effective-dated versions may exist for the same identity, but their validity intervals must not overlap.

ReferenceDomain + ReferenceCode identifies a logical reference value. ReferenceDomain + ReferenceCode + EffectiveStartDate uniquely identifies an effective-dated version. Effective periods for the same logical reference value must not overlap.

## 5. Initial Program Codes

- MEDICAID
- CHIP
- THIP
- ABD
- LTSS
- HCBS

These codes must align with the Eligibility source contract.

## 6. Provider Type Codes

- INDIVIDUAL
- CLINIC
- HOSPITAL
- GROUP
- FACILITY
- LABORATORY

## 7. Specialty Codes

- PRIMARY_CARE
- FAMILY_MEDICINE
- PEDIATRICS
- CARDIOLOGY
- BEHAVIORAL_HEALTH
- ORTHOPEDICS
- NEUROLOGY
- RADIOLOGY
- LAB_SERVICES
- HOME_HEALTH

## 8. Service Codes

Initial synthetic service classifications:

| Code | Description |
|---|---|
| OFFICE_VISIT | Office-based medical visit |
| EMERGENCY_VISIT | Emergency department visit |
| INPATIENT_STAY | Inpatient hospital service |
| LAB_TEST | Laboratory testing |
| IMAGING | Diagnostic imaging |
| THERAPY | Therapy service |
| HOME_VISIT | Home healthcare visit |
| PREVENTIVE_CARE | Preventive service |

These are synthetic portfolio codes, not official CPT or HCPCS billing codes.

## 9. Status Domains

**Member status:** ACTIVE, INACTIVE

**Eligibility status:** ACTIVE, TERMINATED, PENDING

**Claim status:** SUBMITTED, PENDING, APPROVED, DENIED, PAID, ADJUSTED

**Service event types:** SCHEDULED, CHECKED_IN, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW

**Gender codes:** M, F, U

The STATE_CODE domain will contain valid US state codes, with any additional jurisdictions explicitly documented.

## 10. Data Quality Rules

1. ReferenceDomain must not be null.
2. ReferenceCode must not be null or blank.
3. ReferenceDescription must not be blank.
4. IsActive must be a valid Boolean.
5. EffectiveStartDate must be valid.
6. EffectiveEndDate must be null or greater than or equal to EffectiveStartDate.
7. Effective-dated records for the same domain and code must not have overlapping validity periods.
8. ReferenceVersion must be populated.
9. Duplicate records within the same snapshot must be flagged.
10. Invalid cross-source reference values must be quarantined or explicitly flagged.

## 11. Effective-Dated Lookup Rules

A reference value is valid for a business date when:

- The date is on or after EffectiveStartDate.
- EffectiveEndDate is null or the date is on or before EffectiveEndDate.

The pipeline must preserve historical reference versions so previously valid codes remain interpretable.

An inactive code may remain valid for historical records when its effective dates support that interpretation.

## 12. Snapshot and Replay Rules

- Each reference delivery represents a full snapshot for the specified domain.
- The generator must support deterministic output.
- A manifest records domain, snapshot date, version, record count, and checksum.
- Reprocessing an identical snapshot must be idempotent.
- Changed content under an existing snapshot identity requires an explicit correction version.
- Missing expected domains must be flagged.
- Source snapshots must remain auditable.

## 13. Bronze, Silver and Gold Responsibilities

### Bronze

Preserve raw reference deliveries, file metadata, and manifest details.

### Silver

Enforce schema, effective-date validity, uniqueness, domain consistency, and approved code-set rules.

### Gold

Support descriptive labels, historical interpretation, and consistent analytical dimensions.

## 14. Synthetic Test Scenarios

- Valid reference snapshots.
- Duplicate codes.
- Unknown reference domains.
- Invalid code values.
- Inactive codes.
- Expired codes.
- Future-effective codes.
- Overlapping effective dates.
- Missing reference domains.
- Corrected snapshot delivery.
- CSV and Parquet schema compatibility.
- Historical reference-version lookups.

## 15. Finalized Design Decisions

- Reference data is delivered through CSV and Parquet.
- Reference datasets use full-snapshot delivery.
- ReferenceDomain + ReferenceCode identifies a logical reference value.
- Effective-dated versions support historical interpretation.
- The Reference dataset owns the approved provider types, specialties, programs, services, and status domains.
- Raw deliveries and their manifests must be replayable.

## 16. Deferred Implementation Decisions

- Final generator directory structure.
- CSV versus Parquet assignment for individual domains.
- Snapshot retention periods.
- Detailed historical-reference merge strategy.
- Additional reference domains.
- Automated cross-contract consistency tests.