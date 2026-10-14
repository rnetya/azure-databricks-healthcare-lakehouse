# Foundation Architecture — DEV

**Project:** Azure Databricks Healthcare Lakehouse

**Status:** Implemented foundation with planned data-processing components shown separately

## Implemented Foundation

```mermaid
flowchart TB
    DEV["VS Code + Python 3.12"]
    GIT["GitHub Repository"]
    SDK["Databricks SDK / CLI / Connect"]

    subgraph AZURE["Azure DEV Environment — East US"]
        subgraph DBX["Azure Databricks — Serverless"]
            SPARK["Serverless Spark"]
            UC["Unity Catalog: healthcare_dev"]
            SECRET["Databricks Secret Scope"]
        end

        ADLS["ADLS Gen2: stdehealthcaredev"]
        KV["Azure Key Vault"]
        ID["Microsoft Entra ID"]
    end

    DEV --> SDK
    DEV --> GIT
    SDK --> DBX
    SPARK --> UC
    UC -->|"Governed external volume"| ADLS
    SECRET -->|"Key Vault-backed"| KV
    ID -.->|"Authentication and identities"| DBX
    ID -.->|"Managed identity"| ADLS
```

The diagram represents the configured foundation and its logical integration boundaries. Individual network and authorization paths are simplified.

## Planned Data Processing Architecture

```mermaid
flowchart LR
    SRC["Synthetic Healthcare Sources"]
    LAND["Landing"]
    BRONZE["Bronze"]
    SILVER["Silver"]
    GOLD["Gold"]
    BI["Analytics"]

    QUAR["Quarantine"]
    OPS["Operational Monitoring"]

    SRC --> LAND --> BRONZE --> SILVER --> GOLD --> BI
    BRONZE -.-> QUAR
    SILVER -.-> QUAR
    BRONZE -.-> OPS
    SILVER -.-> OPS
    GOLD -.-> OPS
```

These pipelines are not yet implemented. They represent the target processing architecture for subsequent project milestones.

## Architecture Notes

- The current foundation uses one physical DEV environment.
- Azure Databricks Serverless is preferred to minimize infrastructure overhead.
- Unity Catalog provides governance for catalog objects and registered storage locations.
- The existing external volume `healthcare_dev.bronze.member_raw` maps to the ADLS Gen2 `raw/member` location.
- Developer authentication and automated runtime identities are separate.
- The Key Vault-backed secret scope is configured.
- CI/CD automation, Terraform provisioning, and production-style healthcare pipelines remain future work.

See [Architecture Overview](../architecture-overview.md) for detailed architecture decisions and implementation boundaries.
