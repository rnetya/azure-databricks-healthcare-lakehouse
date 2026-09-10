# Azure Databricks Healthcare Lakehouse

## Project Overview

This project is an end-to-end Data Engineering portfolio platform built on Azure Databricks and designed around a production-inspired healthcare analytics use case.

The platform demonstrates how heterogeneous batch, database, API, and streaming data sources can be ingested, validated, transformed, governed, orchestrated, and delivered as trusted analytical data products using a Medallion Architecture.

The project uses synthetic healthcare data only. No real Protected Health Information (PHI) is used.

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

Detailed architecture diagrams and Architecture Decision Records (ADRs) will be maintained under the `architecture/` directory.

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

The planned delivery model separates source-control validation from environment deployment.

Feature branches may be validated and deployed to development and test targets. Production deployments must originate from the protected `main` branch after successful validation and pull-request approval.

```text
Feature Branch
      |
      v
     CI
      |
      v
     DEV
      |
      v
    TEST
      |
      v
PR Approval
      |
      v
Merge to main
      |
      v
    PROD
```

## Implementation Roadmap

The platform is being implemented incrementally through the following major milestones:

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

**Current Phase:** Foundation and Environment

The architecture and scope blueprint has been completed. Repository and platform foundations are currently being established before Azure data-platform resources and processing pipelines are implemented.

Implementation evidence, architecture diagrams, technical decisions, test results, and demonstration artifacts will be added progressively as each milestone is completed.

---

**Author:** Ronald Netya
