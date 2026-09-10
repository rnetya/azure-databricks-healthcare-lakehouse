# Azure Subscription and Tenant Baseline

## Purpose

This document records the Azure subscription, tenant, access-control, regional, and environment decisions established for the Azure Databricks Healthcare Lakehouse portfolio.

The objective is to provide a controlled Azure administrative boundary before provisioning data-platform resources.

## Azure Subscription

The project uses a dedicated Azure subscription:

**Subscription Name:** `DE-Healthcare-Portfolio`

The subscription is dedicated exclusively to the Healthcare Lakehouse portfolio and should not contain unrelated personal projects, experiments, or training workloads.

Azure CLI validation confirmed that the subscription is:

* enabled;
* accessible to the project owner;
* configured as the default Azure CLI subscription for portfolio development.

Using a dedicated subscription provides a clear boundary for:

* resource ownership;
* cost tracking;
* Azure RBAC;
* resource governance;
* lifecycle management;
* portfolio cleanup.

## Microsoft Entra Tenant

The portfolio subscription is associated with a single Microsoft Entra tenant.

The tenant provides the identity boundary used by Azure services and will support identities required by the platform, including human users, managed identities, and CI/CD service identities.

The tenant relationship was validated through Azure CLI before resource provisioning.

## RBAC Baseline

The project owner currently has the Azure RBAC role:

**Owner**

at the subscription scope.

This provides the permissions required during the initial platform-foundation phase, including resource creation, access-control configuration, and infrastructure administration.

Workload identities introduced later in the project will follow least-privilege principles rather than inheriting Owner access.

Examples include:

* CI/CD deployment identity;
* Azure Data Factory managed identity;
* Databricks storage-access identities;
* other workload-specific managed identities or service principals where required.

## Primary Azure Region

The primary deployment region is:

**East US (`eastus`)**

Azure CLI validation confirmed that East US is available to the subscription and is supported for Azure Databricks workspace deployment.

The portfolio will prefer a single primary region unless a later engineering requirement justifies introducing another region.

This minimizes unnecessary:

* cost;
* networking complexity;
* data-transfer considerations;
* operational overhead.

## Environment Strategy

The portfolio uses the following logical environment progression:

```text
DEV
 |
 v
UAT
 |
 v
PRD
```

All environments belong to the dedicated `DE-Healthcare-Portfolio` subscription.

Environment isolation will be achieved through combinations of:

* resource naming;
* resource groups;
* Databricks catalogs;
* configuration;
* identities and permissions;
* deployment targets.

Separate Azure subscriptions for DEV, UAT, and PRD are not required for the portfolio implementation.

## Physical Environment Strategy

The architecture defines DEV, UAT, and PRD, but the initial physical implementation will provision only:

**DEV**

UAT and PRD remain valid architectural and deployment targets but will be physically provisioned only when they provide meaningful engineering or demonstration value.

This supports the project principle:

> Learn and demonstrate the engineering principle at minimal cost.

## Databricks Environment Model

Each environment is designed to have its own Databricks catalog.

```text
healthcare_dev
healthcare_uat
healthcare_prd
```

Each catalog can contain the complete logical data architecture:

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

and conceptually in production:

```text
healthcare_prd.bronze.member
healthcare_prd.silver.member
healthcare_prd.gold.member_eligibility_snapshot
```

DEV / UAT / PRD represent **deployment environments**.

Bronze / Silver / Gold represent **data refinement layers**.

These are separate architectural dimensions.

## Azure and Databricks Relationship

The logical hierarchy is:

```text
Azure Tenant
    |
    v
Azure Subscription
    |
    v
Environment
    |
    v
Azure Resources
    |
    v
Databricks Catalog
    |
    v
Medallion / Operational Schemas
    |
    v
Tables and Views
```

Azure provides the administrative and infrastructure boundary.

Azure Databricks provides the Lakehouse processing, governance, orchestration, and analytical platform.

The Medallion Architecture defines how data progresses from source-faithful ingestion to validated and business-ready data products.

## Resource Scope Boundary

Resources belonging to the Healthcare Lakehouse may include:

* Azure Resource Groups;
* Azure Databricks;
* ADLS Gen2;
* Azure Key Vault;
* Azure Data Factory;
* managed identities and service principals;
* monitoring and cost-management resources;
* supporting configuration and networking resources where required.

The initial physical DEV environment is expected to contain only the resources required to demonstrate the architecture effectively.

UAT and PRD resources will not be provisioned automatically simply because the logical environments exist.

## Environment Resource Model

Conceptually, Azure resource organization may evolve toward:

```text
DE-Healthcare-Portfolio
|
+-- DEV
|   +-- DEV resource group(s)
|   +-- DEV ADLS Gen2
|   +-- DEV Azure Databricks
|   +-- DEV Key Vault
|   +-- Supporting DEV services
|
+-- UAT
|   +-- Logical / future initially
|
+-- PRD
    +-- Logical / future initially
```

Exact resource names will be established separately under the project's naming and tagging standards.

## CI/CD Alignment

The environment strategy supports the target deployment flow:

```text
Feature Branch
      |
      v
DEV Deployment
      |
      v
DEV Validation
      |
      v
UAT Deployment
      |
      v
UAT Validation
      |
      v
Pull Request Approval
      |
      v
Merge to main
      |
      v
PRD Deployment
```

Feature branches may deploy to DEV and UAT for validation.

PRD deployment must originate from the protected `main` branch after the required validation and pull-request process has completed.

The physical portfolio implementation may initially execute only the DEV portion while preserving the complete deployment architecture in configuration and documentation.

## Cost-Control Principle

Environment design must not automatically result in duplicated infrastructure.

The portfolio will:

* provision DEV first;
* create UAT and PRD resources only when justified;
* prefer ephemeral or on-demand compute;
* avoid permanent infrastructure without demonstrated value;
* monitor costs at the subscription level;
* maintain clear resource ownership and lifecycle decisions.

## Baseline Outcome

The Azure administrative foundation now establishes:

* a dedicated portfolio subscription;
* a validated Microsoft Entra tenant relationship;
* subscription-level Owner access for initial platform setup;
* East US as the primary Azure region;
* DEV → UAT → PRD as the environment progression;
* DEV as the initial physical implementation;
* environment-specific Databricks catalog design;
* a defined resource-scope boundary;
* alignment between Azure environments, Databricks governance, Medallion Architecture, and future CI/CD.

This baseline must be maintained as Azure resources are introduced during subsequent foundation milestones.
