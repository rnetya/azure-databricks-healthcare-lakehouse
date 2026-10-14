# Azure Databricks Healthcare Lakehouse

## Project Overview

This project is an end-to-end Data Engineering portfolio platform built on Azure Databricks and designed around a production-inspired healthcare analytics use case.

The platform demonstrates how heterogeneous batch, database, API, and streaming data sources can be ingested, validated, transformed, governed, orchestrated, and delivered as trusted analytical data products using a Medallion Architecture.

The project uses synthetic healthcare data only. No real Protected Health Information (PHI) is used.

## Implementation Status

**Current phase:** M1.13 — Foundation Documentation, Evidence & Freeze

The Azure and Databricks foundation has been established and validated through M1.12. The project is now consolidating architecture documentation, validation evidence, and implementation readiness before beginning synthetic healthcare data development.

### Completed Foundation Capabilities

| Area | Implemented and Validated |
|---|---|
| Azure environment | Dedicated DEV subscription, resource group, East US region, naming standards, and budget alerts |
| ADLS Gen2 | Hierarchical namespace storage, containers, and landing directory structure |
| Azure Databricks | Premium workspace with Serverless Spark and SQL capabilities |
| Unity Catalog | `healthcare_dev` catalog, Medallion schemas, governance baseline, and external volume |
| Identity and security | Microsoft Entra ID, Azure Key Vault, Databricks secret scope, and runtime service principal configuration |
| Local development | Python 3.12, VS Code, Databricks CLI/SDK, Databricks Connect, pytest, and Ruff |
| Connectivity | Databricks APIs, Serverless Spark, Unity Catalog, and governed ADLS file operations |
| Source control | Protected `main` branch, feature branches, pull requests, and documented Git workflow |

### Upcoming Engineering Work

The next phase will introduce synthetic healthcare datasets, followed by batch and incremental ingestion, transformation, data quality, streaming, analytical products, orchestration, and automated deployment.

These processing capabilities are planned and are not yet represented as completed implementations.

### Foundation Evidence

- [Architecture Overview](architecture/architecture-overview.md)
- [Foundation Architecture Diagram](architecture/diagrams/foundation-architecture.md)
- [Connectivity Validation](docs/connectivity-validation.md)
- [Local Development and Testing](docs/local-development.md)
- [Unity Catalog Foundation](docs/unity-catalog-foundation.md)
- [Identity and Key Vault Foundation](docs/keyvault-identity-foundation.md)
- [Azure Cost Guardrails](docs/azure-cost-guardrails.md)

## Business Scenario

A healthcare organization receives member, eligibility, claims, provider, service-event, and reference data from multiple internal and external systems.

The platform is designed to:

* centralize heterogeneous source data;
* preserve source-faithful records;
* validate and standardize incoming data;
* quarantine invalid records;
* integrate healthcare entities;
* support incremental and streaming processing;
* maintain historical eligibility information;
* provide trusted analytical datasets;
* expose pipeline health and data-quality metrics.

## Target Architecture

The platform follows the logical processing pattern:

**Source Systems → Ingestion / Landing → Bronze → Silver + Quarantine → Gold → Analytics / Consumption**

The architecture is designed around Azure Databricks, Delta Lake, Unity Catalog, ADLS Gen2, Lakeflow, Apache Spark, and supporting Azure services.

The [Architecture Overview](architecture/architecture-overview.md) describes the implemented Azure foundation and planned healthcare processing architecture. The [Foundation Architecture Diagram](architecture/diagrams/foundation-architecture.md) provides a visual representation of both.

Detailed Architecture Decision Records (ADRs) and healthcare data models will be added as the relevant engineering milestones are implemented.

## Data Sources

The portfolio is designed to demonstrate multiple ingestion patterns:

| Source                 | Data                     | Pattern                |
| ---------------------- | ------------------------ | ---------------------- |
| Enrollment System      | Member                   | CSV batch              |
| Eligibility Partner    | Eligibility              | Parquet batch          |
| Claims Database        | Claims                   | JDBC incremental       |
| Provider Directory     | Provider                 | REST / nested JSON     |
| Service Event Platform | Service events           | Apache Kafka streaming |
| Reference Data         | Programs / service codes | CSV / Delta            |
| Databricks Platform    | Operational telemetry    | Delta                  |

All portfolio datasets are synthetic.

## Technology Stack

Core technologies planned for the implementation include:

* Azure Databricks
* Apache Spark / PySpark
* Delta Lake
* Unity Catalog
* ADLS Gen2
* Lakeflow Spark Declarative Pipelines
* Lakeflow Jobs
* Databricks SQL
* Apache Kafka
* Azure Data Factory
* Azure Key Vault
* GitHub Actions
* Databricks Declarative Automation Bundles
* Python
* SQL

## Repository Structure

```text
.github/workflows/   GitHub Actions CI/CD workflows
architecture/        Architecture diagrams, ADRs, and data models
src/                 Data Engineering source code
pipelines/           Declarative pipeline implementation
workflows/           Workflow and job implementation
resources/           Databricks bundle resource definitions
sql/                 SQL and analytical scripts
infrastructure/      Azure infrastructure-as-code
deployment/          Deployment support and release tooling
config/              Non-secret environment configuration
tests/               Unit and integration tests
sample-data/         Small synthetic sample datasets
kafka/               Local Kafka configuration and producer support
adf/                 Azure Data Factory artifacts
docs/                Engineering, operational, and portfolio documentation
```

## CI/CD Strategy

**Current state:** Git feature branches, pull requests, protected `main`, and local validation are implemented.

**Planned state:** GitHub Actions, automated testing, Databricks deployment automation, and controlled environment promotion.

The intended delivery workflow is:

```text
Feature Branch
      |
      v
Automated CI Validation
      |
      v
DEV Deployment / Validation
      |
      v
Pull Request Review and Approval
      |
      v
Merge to Protected main
      |
      v
Controlled UAT / PRD Promotion
```

This represents the target CI/CD architecture, not an existing automated deployment pipeline.

Environment deployment, release approvals, and promotion controls will be implemented and validated during the CI/CD milestone.

## Implementation Roadmap

The following is a high-level delivery roadmap. Detailed milestone definitions and sequencing are maintained separately in the project implementation plan.:

1. Foundation and Environment
2. Synthetic Data Platform
3. Batch Bronze Ingestion
4. Silver Transformation and Data Quality
5. Incremental Claims Processing
6. REST API Provider Ingestion
7. Kafka Streaming
8. Gold Analytical Products
9. Orchestration
10. Security and Governance
11. Testing and Observability
12. CI/CD and Deployment
13. Analytics and Dashboard
14. Portfolio Packaging

## Development Workflow

Repository changes are developed on short-lived working branches and integrated through pull requests into the protected `main` branch.

Current repository workflow:

```text
Working Branch
      |
      v
Local Development
      |
      v
Commit and Push
      |
      v
Pull Request
      |
      v
Validation
      |
      v
Protected main
```

Branch naming conventions:

* `feature/...` for new engineering capabilities
* `fix/...` for bug fixes
* `docs/...` for documentation changes
* `chore/...` for repository and tooling maintenance

The target CI/CD model will later extend this workflow to include automated validation, development and test deployments, and controlled production promotion.


## Project Status

**Current milestone:** M1.13 — Foundation Documentation, Evidence & Freeze

**Completed:** M1.1–M1.12 — Azure environment, storage, Databricks workspace, Unity Catalog, identity foundation, local development tooling, and connectivity validation.

**In progress:** Architecture consolidation, foundation documentation, reproducibility review, and final foundation freeze.

**Next phase:** Synthetic Healthcare Data Platform.

The project currently has a validated cloud and development foundation. Healthcare ingestion pipelines, Silver and Gold processing, streaming workloads, automated CI/CD, and infrastructure-as-code remain planned engineering deliverables.

---

**Author:** Ronald Netya
