# Healthcare Lakehouse — Architecture Overview

**Project:** Azure Databricks Healthcare Lakehouse

**Environment:** DEV

**Architecture status:** Foundation implemented; data pipelines planned

**Last reviewed:** October 14, 2026

## 1. Architecture Objective

Build a production-inspired healthcare analytical platform that consolidates synthetic Member, Eligibility, Claims, Provider, Service Event, and Reference data into governed analytical data products.

The platform demonstrates heterogeneous ingestion, Delta Lake processing, data quality, incremental processing, streaming, historical tracking, observability, security, and controlled deployment.

The project uses synthetic data only.

## 2. Architecture Principles

- Separate ingestion, transformation, and analytical responsibilities.
- Preserve source-faithful records in Bronze.
- Enforce quality and integration rules in Silver.
- Deliver business-ready analytical products in Gold.
- Quarantine invalid records with traceable reasons.
- Support idempotency, replay, incremental processing, and historical changes.
- Apply least-privilege access through Unity Catalog and Microsoft Entra ID.
- Prefer Serverless and ephemeral compute to control cost.
- Keep development reproducible through Git, Python tooling, and documented validation.

## 3. Implemented Azure Foundation

The following components have been configured or validated during M1.1–M1.12.

| Component | Implementation |
|---|---|
| Azure environment | Dedicated DEV subscription and resource group in East US |
| ADLS Gen2 | `stdehealthcaredev` |
| Storage containers | `raw`, `managed`, `quarantine`, `operational` |
| Azure Databricks | `dbw-de-healthcare-dev`, Serverless-first |
| Unity Catalog | `healthcare_dev` |
| Unity Catalog schemas | `bronze`, `silver`, `gold`, `quarantine`, `operational` |
| External volume | `healthcare_dev.bronze.member_raw` |
| Key Vault | `kv-de-healthcare-dev` |
| Databricks secret scope | `healthcare-dev` |
| Runtime identity | `sp-healthcare-runtime-dev` |
| Development tooling | VS Code, Python 3.12, Databricks SDK, Databricks Connect, pytest, Ruff |
| Source control | GitHub feature branches, pull requests, protected `main` |

Infrastructure-as-code, automated deployment workflows, and production-style data pipelines remain future implementation work.

## 4. Logical Data Architecture — Planned

The intended data flow is:

**Source Systems → Landing → Bronze → Silver → Gold → Analytics**

Invalid records are routed to Quarantine, while operational metadata captures pipeline execution and data-quality results.

### Data Sources

| Source | Format / Access Pattern | Intended Processing |
|---|---|---|
| Member | CSV batch | Daily ingestion |
| Eligibility | Parquet batch | Effective-dated history |
| Claims | JDBC | Incremental watermark and MERGE |
| Provider | REST API / nested JSON | API ingestion and flattening |
| Service Events | Kafka JSON / Avro | Structured Streaming |
| Reference | CSV / Parquet | Lookup and enrichment |

### Medallion Layers

**Bronze:** Source-aligned, traceable ingestion with schema controls and processing metadata.

**Silver:** Validated, deduplicated, standardized, and integrated healthcare entities.

**Gold:** Analytical data products optimized for reporting and business consumption.

**Quarantine:** Invalid or rejected records with validation reasons and replay support.

**Operational:** Execution logs, ingestion checkpoints, data-quality metrics, and pipeline observability.

These processing capabilities are planned; they should not be represented as completed pipelines.

## 5. Planned Gold Data Products

1. `gold.member_eligibility_snapshot`
2. `gold.claims_utilization`
3. `gold.provider_performance`
4. `gold.program_summary`
5. `gold.data_quality_metrics`

These are the target analytical contracts. Their physical implementations will be developed in subsequent milestones.

## 6. Identity and Security Architecture

The platform separates human development access from automated workload execution.

**Developer authentication:** Databricks CLI OAuth profile `healthcare-dev`.

**Runtime identity:** `sp-healthcare-runtime-dev`, intended for controlled Serverless Jobs execution.

**Governance:** Unity Catalog catalogs, schemas, volumes, privileges, and storage integration.

**Secrets:** Azure Key Vault and Databricks-backed secret scope.

M1.12 verified the runtime principal's identity and catalog grant, and found no direct or principal-specific effective Bronze schema grant entries.

A runtime execution-based authorization denial test remains outstanding.

The local OAuth token cache also requires a separate secure-storage review.

## 7. Connectivity Evidence

M1.12 validated:

- Local Python SDK authentication to the Databricks Workspace API.
- Unity Catalog catalog and schema metadata discovery.
- Serverless Spark SQL execution through Databricks Connect.
- External Unity Catalog volume mapping to ADLS Gen2.
- File creation, download, content verification, and cleanup.
- Runtime service principal identity and grant inspection.

See [Connectivity Validation](../docs/connectivity-validation.md).

## 8. Cost and Environment Strategy

The initial implementation uses one physical DEV environment with logical DEV, UAT, and PRD promotion targets as appropriate.

Cost controls include:

- Monthly Azure budget of $75 with alerts.
- Target development spend of approximately $30–$75 per month.
- Serverless-first execution.
- Minimal test workloads.
- Avoidance of continuously running compute.
- Reuse of existing infrastructure.
- No production PHI.

See [Azure Cost Guardrails](../docs/azure-cost-guardrails.md).

## 9. Planned Engineering Capabilities

Later implementation milestones will introduce:

- Auto Loader and batch ingestion.
- JDBC incremental extraction.
- REST API ingestion.
- Kafka and Structured Streaming.
- Delta MERGE and change processing.
- Effective-dated history.
- Lakeflow pipelines and orchestration.
- Data-quality expectations and quarantine.
- Observability and replay.
- Automated testing and CI/CD.
- Infrastructure-as-code.
- Analytics and demonstration artifacts.

## 10. Implementation Boundaries

**Completed foundation:** Azure resources, security and governance baseline, local development tooling, and connectivity validation.

**Not yet implemented:** End-to-end ingestion pipelines, Silver transformations, Gold analytical products, Kafka processing, automated CI/CD deployment, and Terraform provisioning.

This distinction is maintained to ensure the repository accurately represents the engineering work completed.

## 11. Supporting Documentation

- [Azure Subscription Baseline](../docs/azure-subscription-baseline.md)
- [ADLS Gen2 Foundation](../docs/adls-gen2-foundation.md)
- [Databricks Workspace Foundation](../docs/azure-databricks-workspace-foundation.md)
- [Unity Catalog Foundation](../docs/unity-catalog-foundation.md)
- [Key Vault and Workload Identity](../docs/keyvault-identity-foundation.md)
- [Local Development](../docs/local-development.md)
- [Connectivity Validation](../docs/connectivity-validation.md)
- [Azure Cost Guardrails](../docs/azure-cost-guardrails.md)

## 12. Foundation Exit Criteria

The Foundation phase is ready for freeze when:

- Azure and Databricks baseline resources are documented.
- Governance and identity boundaries are documented.
- Connectivity evidence is committed.
- Architecture documentation and diagrams are available.
- README accurately reflects implementation status.
- Known risks and deferred work are recorded.
- Local quality checks pass.
- Final changes are merged through the protected `main` branch.

**Next phase:** Synthetic Healthcare Data Platform.