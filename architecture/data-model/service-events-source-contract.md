# Service Events — Kafka Source Contract v1.0

**Project:** Azure Databricks Healthcare Lakehouse

**Milestone:** M2.1 — Healthcare Source Contracts

**Source:** Synthetic Healthcare Service Event Simulator

**Delivery:** Apache Kafka

**Status:** Design Approved — v1.0

## 1. Business Purpose

The Service Events source simulates healthcare service encounters and their lifecycle changes.

It supports event-driven ingestion, real-time processing, late-arriving data, deduplication, and service utilization analytics.

All data is synthetic.

## 2. Source Delivery Contract

| Attribute | Specification |
|---|---|
| Source system | Python Service Event Simulator |
| Messaging platform | Local Apache Kafka |
| Topic | `healthcare.service-events.v1` |
| Kafka message key | `ServiceId` |
| Event identifier | `EventId` |
| Logical event format | JSON |
| Kafka value encoding | Avro |
| Schema version | 1 |
| Delivery expectation | At least once |
| Event-time field | `EventTimestamp` |
| Publication-time field | `PublishedAt` |
| Processing mode | Streaming and controlled replay |

The simulator generates JSON-compatible records and serializes them to Avro before publication.

Local Kafka-to-Databricks connectivity will be evaluated during implementation. Where direct secure connectivity is impractical, the simulator will also support staging serialized event batches to ADLS for reproducible pipeline testing.

## 3. Event Schema

| Field | Logical Type | Required | Description |
|---|---|---|---|
| EventId | STRING | Yes | Stable unique event identifier |
| ServiceId | STRING | Yes | Service encounter identifier |
| MemberId | STRING | Yes | Member reference |
| ProviderId | STRING | Yes | Provider reference |
| ServiceCode | STRING | Yes | Reference service code |
| EventType | STRING | Yes | Service lifecycle event |
| EventTimestamp | TIMESTAMP | Yes | Business event occurrence time |
| PublishedAt | TIMESTAMP | Yes | Producer publication time |
| EventVersion | INT | Yes | Payload schema version |
| Payload | STRUCT | Yes | Event-specific attributes |

Timestamps use UTC and are represented as ISO 8601 values in logical JSON. Avro serialization will use an explicitly defined timestamp representation.

EventVersion identifies the event payload schema version. It is not an event sequence number or a service lifecycle ordering field. Business-event chronology is determined using EventTimestamp, with deterministic tie handling defined during implementation.

## 4. Service Lifecycle

Supported event types:

| EventType | Description |
|---|---|
| SCHEDULED | Service appointment created |
| CHECKED_IN | Member checked in |
| IN_PROGRESS | Service started |
| COMPLETED | Service completed |
| CANCELLED | Service cancelled |
| NO_SHOW | Member did not attend |

Typical progression:

`SCHEDULED → CHECKED_IN → IN_PROGRESS → COMPLETED`

Alternative outcomes include:

`SCHEDULED → CANCELLED`

`SCHEDULED → NO_SHOW`

Not all encounters must contain every intermediate event. Invalid or unusual transitions may be generated deliberately for data-quality testing.

## 5. Example Logical JSON Event

```json
{
  "EventId": "EV000001",
  "ServiceId": "SV000001",
  "MemberId": "M000001",
  "ProviderId": "P000001",
  "ServiceCode": "OFFICE_VISIT",
  "EventType": "CHECKED_IN",
  "EventTimestamp": "2026-10-15T09:00:00Z",
  "PublishedAt": "2026-10-15T09:15:00Z",
  "EventVersion": 1,
  "Payload": {
    "LocationType": "CLINIC",
    "Notes": "Synthetic check-in event"
  }
}
```

## 6. Kafka Partitioning and Ordering

- Kafka message key: `ServiceId`.
- Events with the same key are routed to the same partition while topic partitioning configuration remains stable.
- Kafka preserves record order within each partition.
- Kafka arrival order is not necessarily business-event order.
- `EventTimestamp` determines business-event chronology.
- `EventId` identifies logical events independently of Kafka offsets.

Changes to partition count or partitioning strategy may affect key-to-partition mapping and must be evaluated.

## 7. Deduplication and Idempotency

The simulator supports at-least-once delivery, meaning an event may be published more than once.

Deduplication rules:

1. `EventId` is the logical deduplication key.
2. Replayed copies retain the same `EventId`.
3. Bronze preserves raw event delivery information for audit and replay.
4. Silver applies event-level deduplication.
5. Conflicting payloads sharing the same `EventId` are flagged for investigation.
6. Streaming state retention and watermark configuration must be considered when evaluating duplicate handling.

Deduplication beyond the configured streaming state horizon requires additional persistent-state or reconciliation controls.

## 8. Event Time and Late-Arriving Data

`EventTimestamp` represents when a service event occurred.

`PublishedAt` represents when the producer published it.

The pipeline must support:

- Events arriving after their business-event timestamp.
- Events arriving out of chronological order.
- Event-time windowing.
- Watermark-based state management.
- Explicit handling of events beyond the accepted lateness threshold.

An initial watermark configuration will be selected and tested during streaming implementation rather than assumed in this contract.

## 9. Data Quality Rules

- `EventId` must be non-null and nonblank.
- `ServiceId` must be non-null and nonblank.
- `MemberId` must reference a valid synthetic member unless intentionally invalid.
- `ProviderId` must reference a valid synthetic provider unless intentionally invalid.
- `ServiceCode` must belong to the approved Reference dataset.
- `EventType` must belong to the supported lifecycle domain.
- `EventTimestamp` and `PublishedAt` must be valid timestamps.
- `EventVersion` must be a supported schema version.
- `Payload` must conform to the versioned event schema.
- Unexpected lifecycle transitions are flagged for review.

Invalid events will be routed to quarantine or another explicit exception path, with their raw content and failure reasons preserved.

## 10. Schema Management

Version 1 uses an explicitly defined Avro writer schema.

The ingestion process must retain enough schema information to decode historical messages.

Schema evolution scenarios will include:

- Adding an optional field.
- Handling missing optional fields.
- Rejecting incompatible type changes.
- Reading messages written with supported historical schemas.

A Schema Registry is optional for the initial local implementation. If omitted, the producer and consumer must use a documented, versioned schema-management mechanism.

`EventVersion` is a payload contract version and does not replace Avro writer-schema identification.

## 11. Synthetic Test Scenarios

The simulator must support:

1. Normal service lifecycle.
2. Duplicate event publication.
3. Out-of-order events.
4. Late-arriving events.
5. Invalid member references.
6. Invalid provider references.
7. Unknown service codes.
8. Unsupported event types.
9. Invalid or missing required fields.
10. Controlled schema evolution.
11. Producer restart and event replay.
12. Different event volumes for performance testing.

## 12. Bronze, Silver and Gold Responsibilities

### Bronze

- Preserve raw Kafka payload or staged equivalent.
- Capture topic, partition, offset and ingestion metadata when available.
- Preserve event identity and schema metadata.
- Support audit and replay.

### Silver

- Decode and validate Avro records.
- Normalize event fields.
- Apply deduplication and quality checks.
- Handle event-time semantics and late-arriving data.
- Quarantine invalid events.

### Gold

- Produce service utilization and program-level analytical measures.
- Avoid double-counting duplicated events.
- Support encounter lifecycle and completion metrics.

## 13. Deferred Implementation Decisions

- Kafka broker and topic partition configuration.
- Exact Avro schema definition and encoding.
- Schema Registry versus versioned schema files.
- Streaming watermark threshold.
- Late-event reconciliation strategy.
- Checkpoint locations and retention.
- Secure Kafka-to-Databricks connectivity.
- Performance testing volumes and throughput targets.

## 14. Finalized Design Decisions

- `ServiceId` is the Kafka message key.
- `EventId` is the event-level deduplication key.
- The simulator uses synthetic healthcare events only.
- Logical JSON records are serialized to Avro for Kafka delivery.
- The initial pipeline assumes at-least-once delivery.
- Event-time and publication-time semantics remain distinct