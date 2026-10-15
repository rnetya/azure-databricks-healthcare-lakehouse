# Provider REST API Source Contract — v1.0

**Project:** Azure Databricks Healthcare Lakehouse

**Milestone:** M2.1 — Healthcare Source Contracts

**Source:** Synthetic Provider Directory API

**Dataset:** Provider

**Status:** Design Approved — v1.0

## 1. Business Purpose

The Provider source represents synthetic healthcare providers, their locations, specialties, and participation status.

Provider identifiers are referenced by the Claims dataset and will support provider-performance analytics.

All provider information is synthetic. No real Protected Health Information (PHI) or real provider identities are used.

## 2. API Delivery Contract

| Attribute | Specification |
|---|---|
| API framework | Python FastAPI |
| Protocol | HTTP REST |
| Response format | JSON |
| API version | v1 |
| Default population | 1,000 providers |
| Performance population | 10,000+ providers |
| Default page size | 100 |
| Maximum page size | 500 |
| Primary key | ProviderId |
| Initial extraction | Full paginated retrieval |
| Subsequent extraction | Updated-record synchronization prototype |
| Authentication | Configurable API key for local testing |
| Error handling | HTTP status codes, retries and bounded backoff |

## 3. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/v1/providers` | Paginated provider retrieval |
| GET | `/api/v1/providers/{provider_id}` | Retrieve a provider by ID |
| GET | `/api/v1/providers?updated_since=...` | Filter by update timestamp |

## 4. Provider JSON Schema

| Field | Logical Type | Required | Description |
|---|---|---|---|
| providerId | STRING | Yes | Stable provider identifier |
| providerName | STRING | Yes | Synthetic provider name |
| providerType | STRING | Yes | Provider classification |
| status | STRING | Yes | ACTIVE or INACTIVE |
| address | OBJECT | Yes | Nested location attributes |
| specialties | ARRAY[STRING] | Yes | Provider specialties |
| lastUpdatedAt | TIMESTAMP | Yes | Source update time in UTC |

### 4.1 Nested Address Object

| Field | Type | Required |
|---|---|---|
| addressLine1 | STRING | Yes |
| city | STRING | Yes |
| state | STRING | Yes |
| zipCode | STRING | Yes |

### 4.2 Example Provider Record

```json
{
  "providerId": "P000001",
  "providerName": "Synthetic Care Clinic",
  "providerType": "CLINIC",
  "status": "ACTIVE",
  "address": {
    "addressLine1": "100 Example Street",
    "city": "Wilmington",
    "state": "DE",
    "zipCode": "19801"
  },
  "specialties": [
    "PRIMARY_CARE",
    "FAMILY_MEDICINE"
  ],
  "lastUpdatedAt": "2026-10-15T14:30:00Z"
}
```

## 5. Pagination Contract

The Provider API uses page-based pagination for v1.0.

Query parameters:

- page: Positive integer, default 1.
- page_size: Integer between 1 and 500, default 100.
- updated_since: Optional ISO 8601 UTC timestamp.

The response envelope contains:

- items: Array of provider records.
- page: Current page number.
- pageSize: Requested page size.
- totalCount: Number of matching records.
- hasNextPage: Whether additional pages exist.

Results must be ordered deterministically by providerId.

Pagination across a changing dataset may produce duplicates or omissions. A consistent snapshot or cursor-based pagination strategy will be evaluated before treating incremental synchronization as lossless.

## 6. Business Rules

1. providerId must be unique and non-null.
2. providerName must not be blank.
3. providerType must belong to the approved reference domain.
4. status must be ACTIVE or INACTIVE.
5. address.state must be a valid two-character state code.
6. address.zipCode must be a valid five-character synthetic US ZIP code.
7. specialties must be a valid array of approved specialty codes.
8. lastUpdatedAt must be a valid UTC timestamp.
9. Claims ProviderId values must reference valid provider records except in controlled invalid-data scenarios.

## 7. Incremental Synchronization

The initial extraction retrieves the full provider population.

Subsequent requests may use updated_since to retrieve records modified after a specified timestamp.

The client must support:

- Configurable extraction boundaries.
- Deduplication by providerId and source update metadata.
- Safe replay of previously retrieved pages.
- Detection of timestamp ties.
- Logging of API request and response metadata.
- Retry handling for transient failures.

Timestamp filtering alone does not guarantee complete change capture. Hard deletes require a separate mechanism, such as explicit tombstones or periodic full reconciliation.

## 8. API Error Handling

The API and ingestion client will support testing of:

- HTTP 400 — Invalid query parameters.
- HTTP 401 — Missing or invalid API key.
- HTTP 404 — Provider not found.
- HTTP 429 — Rate limit exceeded.
- HTTP 500 — Simulated server failure.
- Network timeout — Simulated request delay.

Retries should be bounded, apply to transient failures, respect Retry-After where appropriate, and avoid retrying permanent client errors.

## 9. Synthetic Test Scenarios

The generator and API must support:

- Provider creation.
- Provider status changes.
- Address changes.
- Specialty updates.
- Multiple specialties per provider.
- Nested JSON validation.
- Multi-page retrieval.
- Duplicate retrieval during overlapping windows.
- Invalid provider references in Claims.
- API rate limiting.
- Transient API failures.
- Replayed extraction requests.

## 10. Generator and API Requirements

1. Generate reproducible synthetic provider records.
2. Support configurable provider population and random seed.
3. Use stable provider identifiers.
4. Expose records through FastAPI endpoints.
5. Provide automatic OpenAPI documentation.
6. Implement page-based pagination.
7. Support updated_since filtering.
8. Support deterministic local API tests.
9. Avoid exposing local development services publicly by default.
10. Preserve compatibility with the Claims source contract.

## 11. Finalized Provider Contract Decisions

### 11.1 Provider Type Domain

The following provider types are supported:

| ProviderType | Description |
|---|---|
| INDIVIDUAL | Individual healthcare practitioner |
| CLINIC | Outpatient medical clinic |
| HOSPITAL | Hospital or medical facility |
| GROUP | Group medical practice |
| FACILITY | Other healthcare facility |
| LABORATORY | Diagnostic laboratory |

### 11.2 Specialty Code Domain

The following specialties are supported:

| SpecialtyCode | Description |
|---|---|
| PRIMARY_CARE | General primary care |
| FAMILY_MEDICINE | Family medicine |
| PEDIATRICS | Pediatric care |
| CARDIOLOGY | Cardiovascular care |
| BEHAVIORAL_HEALTH | Behavioral health services |
| ORTHOPEDICS | Musculoskeletal care |
| NEUROLOGY | Neurological care |
| RADIOLOGY | Diagnostic imaging |
| LAB_SERVICES | Laboratory services |
| HOME_HEALTH | Home-based healthcare |

Provider types and specialties will be maintained in the Reference dataset.

### 11.3 Provider Identifier

- ProviderId uses the format `P000001`.
- Provider identifiers remain stable across updates.
- ProviderId must be unique within the source.

### 11.4 Specialty Rules

- Each provider must have at least one specialty.
- Multiple specialties are supported.
- Duplicate specialties within one provider record are not permitted.
- Every specialty must exist in the approved reference domain.

### 11.5 Pagination

- Default page size: 100.
- Maximum page size: 500.
- Default page number: 1.
- Results are ordered by ProviderId.
- Invalid pagination parameters return HTTP 400.

### 11.6 Incremental Synchronization

- Initial ingestion retrieves the full provider population.
- Subsequent ingestion may filter by lastUpdatedAt.
- An overlapping extraction window and deduplication will be used for the prototype.
- Timestamp ties must be handled.
- Pagination consistency must be evaluated when records change during extraction.
- The prototype is not guaranteed to provide lossless change capture.

### 11.7 Authentication and Security

- Local development uses configurable API-key authentication.
- API keys must not be committed to Git.
- The API binds to localhost by default.
- Secure cloud connectivity will be evaluated during Provider ingestion implementation.

### 11.8 Deletion Strategy

- Providers are initially deactivated using status = INACTIVE.
- Hard-delete capture is deferred.
- Provider records referenced by historical claims must remain available for historical analysis.

## 12. Deferred Implementation Decisions

- Cursor-based pagination.
- Consistent-snapshot extraction.
- Hard-delete tombstones.
- Production-grade authentication.
- Secure Databricks-to-API connectivity.
- Final incremental synchronization guarantees.
