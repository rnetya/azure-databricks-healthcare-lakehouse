# Azure Naming and Tagging Standards

## Purpose

This document defines the Azure resource naming, environment, regional, and tagging standards for the Azure Databricks Healthcare Lakehouse portfolio.

The objective is to establish a consistent and scalable convention before Azure resources are provisioned.

These standards support:

- clear environment isolation;
- predictable resource identification;
- cost management;
- resource ownership;
- governance;
- CI/CD automation;
- operational support;
- future expansion of the platform.

---

## 1. Naming Philosophy

Azure resources should use names that are:

- predictable;
- concise;
- human-readable;
- environment-aware;
- automation-friendly;
- consistent across the platform.

The standard naming pattern is:

```text
<resource-abbreviation>-de-healthcare-<environment>
```

Where:

- `<resource-abbreviation>` identifies the Azure resource type;
- `de` identifies the Data Engineering workload;
- `healthcare` identifies the Healthcare Lakehouse portfolio;
- `<environment>` identifies the deployment environment.

Example:

```text
dbw-de-healthcare-dev
```

This represents:

```text
dbw        = Azure Databricks Workspace
de         = Data Engineering
healthcare = Healthcare Lakehouse
dev        = Development environment
```

---

## 2. Environment Convention

The portfolio uses three logical deployment environments:

```text
DEV → UAT → PRD
```

The corresponding naming codes are:

| Environment | Code |
|---|---|
| Development | `dev` |
| User Acceptance Testing | `uat` |
| Production | `prd` |

Environment codes should use lowercase characters when included in Azure resource names.

Examples:

```text
dbw-de-healthcare-dev
dbw-de-healthcare-uat
dbw-de-healthcare-prd
```

The initial physical portfolio implementation provisions only the DEV environment.

UAT and PRD remain part of the target architecture and deployment model and will be physically provisioned only when justified by engineering or demonstration requirements.

---

## 3. Environment Isolation

Azure resources should be organized by environment rather than placing DEV, UAT, and PRD resources into one shared resource group.

The target resource-group structure is:

```text
DE-Healthcare-Portfolio
│
├── rg-de-healthcare-dev
│
├── rg-de-healthcare-uat
│
└── rg-de-healthcare-prd
```

During initial implementation:

```text
DE-Healthcare-Portfolio
│
└── rg-de-healthcare-dev
```

will be physically provisioned.

This design provides clear boundaries for:

- resource lifecycle management;
- RBAC;
- cost analysis;
- deployment automation;
- troubleshooting;
- future environment expansion.

---

## 4. Resource Abbreviations

The following resource abbreviations are standardized for the portfolio.

| Azure Resource | Abbreviation | DEV Example |
|---|---|---|
| Resource Group | `rg` | `rg-de-healthcare-dev` |
| Azure Databricks Workspace | `dbw` | `dbw-de-healthcare-dev` |
| Azure Key Vault | `kv` | `kv-de-healthcare-dev` |
| Azure Data Factory | `adf` | `adf-de-healthcare-dev` |
| Azure Storage Account | `st` | `stdehealthcaredev` |
| Managed Identity | `mi` | `mi-de-healthcare-dev` |
| Log Analytics Workspace | `law` | `law-de-healthcare-dev` |
| Application Insights | `appi` | `appi-de-healthcare-dev` |

The core resources currently expected are:

```text
rg
dbw
kv
adf
st
mi
```

The following abbreviations are reserved for future use if the corresponding resources are justified:

```text
law
appi
```

A single abbreviation should be used consistently for each resource type across DEV, UAT, and PRD.

---

## 5. DEV Resource Naming Baseline

The initial DEV environment uses the following logical naming baseline:

```text
rg-de-healthcare-dev
│
├── dbw-de-healthcare-dev
├── kv-de-healthcare-dev
├── adf-de-healthcare-dev
├── stdehealthcaredev
└── mi-de-healthcare-dev
```

Not every resource shown above must be provisioned immediately.

Resources should be created only when required by the implementation milestone.

---

## 6. Storage Account Naming

Azure Storage accounts have more restrictive naming requirements than many other Azure resources.

Therefore, the standard hyphenated naming pattern cannot be used.

The preferred DEV storage account name is:

```text
stdehealthcaredev
```

The equivalent logical environment progression is:

```text
stdehealthcaredev
stdehealthcareuat
stdehealthcareprd
```

If the preferred storage account name is unavailable because of Azure global-name uniqueness requirements, a deterministic suffix may be added.

Example:

```text
stdehealthcaredev01
```

Random or difficult-to-understand suffixes should be avoided when a predictable suffix can satisfy the uniqueness requirement.

---

## 7. Region Convention

The primary Azure deployment region is:

```text
East US (eastus)
```

The region is intentionally not included in standard resource names because the portfolio currently uses a single primary region.

Therefore, the preferred naming convention is:

```text
dbw-de-healthcare-dev
```

rather than:

```text
dbw-de-healthcare-dev-eastus
```

The region will instead be recorded through Azure resource metadata/tags and project documentation.

If the architecture later becomes multi-region, the region may be introduced into resource names when required to distinguish otherwise equivalent resources.

For example:

```text
dbw-de-healthcare-prd-eastus
dbw-de-healthcare-prd-westus2
```

Such a change should be driven by an actual architectural requirement and documented through the project's architecture decision process.

---

## 8. Globally Unique Azure Resource Names

Some Azure resource types require names that are globally unique.

The preferred logical name should always be attempted first.

If Azure reports that the name is unavailable, a deterministic uniqueness suffix may be introduced.

Example:

```text
kv-de-healthcare-dev
```

may become:

```text
kv-de-healthcare-dev-01
```

where supported by the Azure resource's naming rules.

Similarly:

```text
stdehealthcaredev
```

may become:

```text
stdehealthcaredev01
```

The uniqueness strategy should preserve readability and should not alter the overall naming philosophy.

---

## 9. Mandatory Azure Tags

Portfolio Azure resources should use the following mandatory tags where the Azure resource type supports tagging.

| Tag | Standard Value / Pattern | Purpose |
|---|---|---|
| `Project` | `Healthcare-Lakehouse` | Identifies the portfolio |
| `Environment` | `DEV`, `UAT`, or `PRD` | Identifies deployment environment |
| `Purpose` | Resource-specific | Describes why the resource exists |
| `Owner` | `Ronald-Netya` | Identifies resource accountability |
| `CostCenter` | `Portfolio` | Supports cost classification |
| `Region` | `eastus` | Records the primary deployment region |

---

## 10. DEV Tagging Example

An Azure Databricks DEV workspace may use:

```text
Project     = Healthcare-Lakehouse
Environment = DEV
Purpose     = Data-Engineering-Lakehouse
Owner       = Ronald-Netya
CostCenter  = Portfolio
Region      = eastus
```

A DEV storage account may use:

```text
Project     = Healthcare-Lakehouse
Environment = DEV
Purpose     = Lakehouse-Storage
Owner       = Ronald-Netya
CostCenter  = Portfolio
Region      = eastus
```

The `Purpose` value should describe the responsibility of the individual resource rather than repeating the project name.

---

## 11. Optional Future Tags

Additional tags may be introduced only when they provide meaningful governance or operational value.

Potential future tags include:

```text
ManagedBy
DataClassification
Lifecycle
```

These are not mandatory during the initial foundation implementation.

The project should avoid creating tags merely for completeness when they do not support an actual engineering, governance, operational, or cost-management requirement.

---

## 12. Databricks and Medallion Alignment

Azure resource naming and Databricks data organization represent different architectural layers.

The Azure environment model is:

```text
DEV → UAT → PRD
```

The Databricks catalog model is:

```text
healthcare_dev
healthcare_uat
healthcare_prd
```

Each environment-specific catalog contains its own complete data architecture:

```text
bronze
silver
gold
quarantine
operational
```

For example:

```text
healthcare_dev.bronze.member
healthcare_dev.silver.member
healthcare_dev.gold.member_eligibility_snapshot
```

Conceptually:

```text
Azure Subscription
        │
        ▼
Environment
        │
        ▼
Azure Resource Group
        │
        ▼
Azure Databricks
        │
        ▼
Unity Catalog Catalog
        │
        ├── bronze
        ├── silver
        ├── gold
        ├── quarantine
        └── operational
```

DEV, UAT, and PRD are deployment environments.

Bronze, Silver, and Gold are data-refinement layers.

They must not be treated as equivalent architectural concepts.

---

## 13. Naming and CI/CD Alignment

The naming standard supports the planned deployment progression:

```text
Feature Branch
      │
      ▼
DEV
      │
      ▼
UAT
      │
      ▼
PR Approval
      │
      ▼
Merge to main
      │
      ▼
PRD
```

Environment-specific configuration should determine the deployment target without requiring environment-specific copies of application or data-engineering source code.

Examples:

```text
healthcare_dev
healthcare_uat
healthcare_prd
```

should represent environment configuration rather than separate implementations of the same engineering logic.

---

## 14. Cost and Lifecycle Alignment

Naming and tagging standards must support the project's cost-control strategy.

The portfolio follows the principle:

> Learn and demonstrate the engineering principle at minimal cost.

Therefore:

- DEV is provisioned first;
- UAT and PRD remain logical until physically required;
- resources should be attributable to the Healthcare Lakehouse portfolio;
- resources should have clear ownership;
- unnecessary resources should not be created simply to mirror an enterprise production footprint;
- resource naming should make environment and purpose immediately understandable;
- tags should support cost analysis and future cleanup.

---

## 15. Standard Summary

The primary naming convention is:

```text
<resource-abbreviation>-de-healthcare-<environment>
```

Environment codes:

```text
dev
uat
prd
```

Primary region:

```text
eastus
```

Core abbreviations:

```text
rg
dbw
kv
adf
st
mi
```

Reserved abbreviations:

```text
law
appi
```

Initial DEV resource baseline:

```text
rg-de-healthcare-dev
dbw-de-healthcare-dev
kv-de-healthcare-dev
adf-de-healthcare-dev
stdehealthcaredev
mi-de-healthcare-dev
```

Mandatory tags:

```text
Project
Environment
Purpose
Owner
CostCenter
Region
```

These standards should be applied consistently as Azure resources are introduced throughout the remaining Foundation and Environment milestones.