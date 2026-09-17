# Azure Databricks Workspace Foundation

## 1. Purpose

This document describes the Azure Databricks workspace foundation implemented for the Healthcare Lakehouse portfolio.

The workspace provides the Databricks execution environment for the portfolio's Medallion Architecture and supports hands-on implementation of distributed data processing, Delta Lake, Unity Catalog, batch and streaming ingestion, orchestration, governance, observability, and CI/CD.

The initial workspace design prioritizes:

- Production-inspired architecture
- Secure classic compute using Secure Cluster Connectivity (SCC)
- Unity Catalog compatibility
- Cost-controlled development
- Ephemeral compute
- Infrastructure and Spark runtime observability
- Incremental security and networking hardening driven by architectural requirements

The implementation initially uses a single physical DEV environment to minimize portfolio operating cost while preserving DEV, UAT, and PRD as logical deployment environments.

---

## 2. Workspace Architecture

| Setting | DEV Baseline |
|---|---|
| Workspace | `dbw-de-healthcare-dev` |
| Azure Region | East US |
| Databricks SKU | Premium |
| Compute Mode | Hybrid / Classic |
| Unity Catalog | Enabled |
| Secure Cluster Connectivity | Enabled |
| Public IP on compute nodes | Disabled |
| Public workspace access | Enabled |
| Network | Databricks-managed VNet |
| VNet Injection | Deferred |
| Private Link | Deferred |

The workspace uses Azure Databricks Premium to support the governance, security, and Unity Catalog capabilities required by the portfolio.

Hybrid/classic architecture was intentionally selected for the initial implementation so the project can demonstrate both Spark data engineering and the underlying Azure infrastructure associated with classic Databricks compute.

The workspace uses Secure Cluster Connectivity (SCC), also referred to as No Public IP. Classic compute nodes therefore operate without public IP addresses and establish outbound connectivity through the Databricks-managed networking infrastructure.

Public workspace access remains enabled for development access to the Databricks UI and APIs. Private Link and VNet injection are deferred until an architectural requirement justifies the additional networking complexity and cost.

---

## 3. Azure Networking Baseline

Azure Databricks automatically created a managed resource group containing the infrastructure required by the workspace.

Validated managed infrastructure includes:

- Databricks-managed virtual network
- Public and private worker subnets
- Network Security Group
- NAT Gateway
- NAT public IP
- Managed identity
- Unity Catalog access connector
- Databricks-managed storage resources

The managed VNet uses the following address space:

- VNet: `10.139.0.0/16`
- Public subnet: `10.139.0.0/18`
- Private subnet: `10.139.64.0/18`

Runtime validation confirmed that the Spark driver and executor received private addresses and did not expose public DNS endpoints.

The NAT Gateway provides outbound connectivity for classic compute while maintaining the No Public IP security model.

> **Cost optimization note:** The NAT Gateway represents persistent networking infrastructure and can continue generating cost while classic compute is terminated. Its cost contribution is actively monitored. Future workloads may use Databricks serverless compute where appropriate to reduce dependence on persistent classic infrastructure without weakening the validated security baseline.

The Databricks-managed resource group is treated as a platform-owned boundary. Its individual resources are not manually modified or deleted.

---

## 4. Workspace Administration and CLI Access

Workspace access was validated through both the Azure Databricks web interface and the standalone Databricks CLI.

Validated administrative capabilities include:

- Successful Databricks workspace launch
- Workspace Admin access
- Catalog Explorer access
- Workspace filesystem navigation
- Databricks CLI authentication
- Databricks CLI workspace and compute queries

A dedicated Databricks CLI profile was configured:

`healthcare-dev`

Interactive CLI authentication uses OAuth user-to-machine (U2M) authentication rather than manually managed personal access tokens.

The CLI configuration was validated by successfully querying workspace paths and compute resources from PowerShell.

### Local Authentication Consideration

During initial Windows configuration, Databricks CLI authentication encountered a Windows secure-storage compatibility issue.

The CLI authentication storage mode was explicitly configured at the Windows user level to provide consistent authentication across new PowerShell sessions.

Authentication credentials and token-cache contents are never stored in the Git repository.

This local configuration is intended for interactive developer access only. Automated CI/CD authentication will use a non-human workload identity and does not depend on the developer's interactive OAuth session.

---

## 5. Classic Compute Baseline

A distributed classic Spark cluster was provisioned to validate Azure infrastructure, Spark execution, Photon, networking, quota consumption, and compute lifecycle behavior.

| Setting | Validated Configuration |
|---|---|
| Cluster | `healthcare-dev-classic` |
| Databricks Runtime | 18 LTS |
| Spark | 4.1.0 |
| Scala | 2.13 |
| Runtime Engine | Photon |
| Access Mode | Standard |
| Data Security Mode | `USER_ISOLATION` |
| Worker Node | `Standard_F4ads_v7` |
| Driver Node | `Standard_F4ads_v7` |
| Workers | 1 |
| Autoscaling | Disabled |
| Spot Instances | Disabled |
| Single Node | Disabled |
| Total Capacity | 8 vCPU / 32 GB |
| Auto-Termination | 15 minutes |

The cluster intentionally uses one driver and one worker rather than single-node compute. This provides a small but genuinely distributed Spark environment suitable for observing driver/executor behavior, partitions, tasks, stages, and shuffle operations.

The cluster uses fixed-size on-demand compute to keep the initial execution model predictable while learning and validating the platform.

### Azure Compute Quota

The DEV subscription had the following validated East US quota baseline:

| Quota | Limit |
|---|---:|
| Total Regional vCPUs | 10 |
| Standard Fadsv7 Family vCPUs | 10 |

The classic cluster required 8 vCPUs while running, leaving 2 regional vCPUs available.

After cluster termination, Azure quota utilization returned to:

- Total Regional vCPUs: `0 / 10`
- Standard Fadsv7 Family vCPUs: `0 / 10`

This demonstrated that the ephemeral Databricks compute allocation was successfully released after termination.

### Compute Selection Lesson

Databricks node types reported as available through the API are not necessarily selectable for every cluster configuration in the Databricks UI.

Initial investigation identified smaller 2-vCPU node types through the API, but the smallest selectable nodes for the chosen distributed classic configuration were 4-vCPU options.

`Standard_F4ads_v7` was selected after validating both Databricks availability and the corresponding Azure VM-family quota.

---

## 6. Spark Runtime Validation

The classic cluster was validated with a PySpark workload that generated and processed 1,000,000 synthetic records.

The validation workload:

1. Generated one million records using `spark.range`.
2. Created eight input partitions.
3. Derived synthetic member-group and claim-amount attributes.
4. Grouped records by ten member groups.
5. Calculated count, sum, and average claim metrics.
6. Ordered and displayed the aggregated result.

The resulting dataset contained ten member groups with 100,000 records per group.

### Spark UI Evidence

Spark UI inspection provided physical execution evidence beyond successful notebook output.

Validated observations included:

- Eight input partitions
- Eight successful tasks in the initial shuffle stage
- 125,000 records processed per task
- Photon execution
- A `PhotonShuffleMapStage`
- Shuffle activity caused by the grouping operation
- Partial aggregation before shuffle
- Reuse/skipping of previously generated stage output during subsequent execution
- Task execution on the worker/executor private IP

The eight-task distribution corresponded directly to the eight input partitions:

`1,000,000 records / 8 partitions = 125,000 records per task`

The grouping operation produced only ten grouping keys. Partial aggregation substantially reduced the amount of data written during the shuffle compared with the original one-million-row input.

This validation demonstrated the relationship between:

`Spark partitions -> stages -> tasks -> executor execution -> shuffle -> result`

It also demonstrated that application code does not map one-to-one to physical Spark stages. Spark's optimizer determines the physical execution plan.

### Photon Validation

Photon execution was confirmed through Spark UI components including `PhotonShuffleMapStage` and Photon execution references.

Photon was therefore validated through runtime execution evidence rather than assumed solely from cluster configuration.

---

## 7. Compute Lifecycle and Cost Controls

The DEV Databricks environment follows an ephemeral compute operating model.

Interactive classic compute is started only when required for development or validation and should be manually terminated when work is complete. A 15-minute auto-termination policy provides an additional protection against idle compute.

During validation, the `healthcare-dev-classic` cluster automatically terminated after 15 minutes of inactivity.

The lifecycle was independently verified through the Databricks CLI and Azure quota utilization:

`RUNNING -> workload execution -> inactivity -> TERMINATED -> Azure vCPU allocation released`

This confirmed that the configured cost-control mechanism operated as expected.

### Azure Budget Guardrail

The portfolio subscription has a monthly Azure budget of:

**$75 USD**

Budget notifications are configured at:

- 50%
- 75%
- 90%
- 100%

The budget provides monitoring and notification rather than automatic resource shutdown.

### Initial Measured Cost Observation

After the first Databricks infrastructure and compute validation activities, Azure Cost Management reported approximately **$4.91** in accumulated portfolio cost.

The largest visible service categories at that snapshot included:

| Service | Approximate Cost |
|---|---:|
| NAT Gateway | $2.15 |
| Azure Databricks | $2.07 |
| Virtual Machines | $0.41 |
| Virtual Network | $0.23 |
| Storage | $0.05 |

These values represent an early cost snapshot and should not be interpreted as the isolated cost of the Spark validation workload.

The observation demonstrated that classic Azure Databricks cost includes more than Spark compute. Platform, networking, virtual-machine, and storage infrastructure can contribute independently to total operating cost.

### NAT Gateway Cost Watch

The NAT Gateway is currently a significant component of the DEV environment's observed cost.

It supports outbound connectivity for the classic No Public IP architecture and can incur cost independently of active Spark compute.

The project will therefore continue evaluating whether workloads require classic compute or can use Databricks serverless capabilities while preserving the engineering objective and security requirements.

The security baseline will not be weakened solely to reduce portfolio cost.

---

## 8. Deferred Architecture Decisions

The initial workspace deliberately avoids implementing infrastructure that is not yet required by a demonstrated workload or security requirement.

The following capabilities remain deferred:

- Customer-managed VNet / VNet injection
- Azure Private Link
- Custom Databricks compute policies
- Expanded serverless workload adoption
- CI/CD workload identity
- Advanced compliance configuration
- Production-scale compute
- Additional physical UAT and PRD workspaces

These are not considered missing capabilities in the DEV foundation. They are controlled architecture decisions that will be introduced when implementation requirements justify their complexity, security value, or cost.

This follows the portfolio principle:

> **Architectural changes should be driven by requirements, not by the availability of platform features.**

---

## 9. Engineering Lessons Validated

The workspace implementation established several practical engineering lessons:

1. Databricks compute availability must be validated against both Databricks configuration constraints and Azure VM-family quota.
2. API-visible node types are not necessarily selectable for every compute configuration.
3. Secure Cluster Connectivity removes public IP addresses from classic compute nodes but still requires an outbound networking path.
4. A Databricks-managed VNet introduces Azure infrastructure that can generate cost independently of active Spark compute.
5. DBU consumption is only one component of the total classic Azure Databricks operating cost.
6. Spark partitions directly influence task parallelism within a stage.
7. Transformations such as `groupBy` can introduce shuffle boundaries and additional stages.
8. Partial aggregation can significantly reduce shuffle volume.
9. Photon should be verified through runtime execution evidence rather than inferred only from configuration.
10. Auto-termination is a cost-protection mechanism, not a substitute for deliberate compute lifecycle management.
11. Classic and serverless compute should be selected based on workload, learning objective, security, operational control, and cost rather than treated as mutually exclusive platform choices.

---

## 10. Validated DEV Workspace State

The Azure Databricks DEV workspace foundation has been successfully provisioned and validated.

The completed foundation demonstrates:

- Azure Databricks Premium workspace provisioning
- Unity Catalog enablement
- Secure Cluster Connectivity / No Public IP
- Databricks-managed VNet architecture
- Azure quota validation
- OAuth-based developer CLI access
- Distributed classic Spark compute
- Photon execution
- Spark UI runtime analysis
- Ephemeral compute lifecycle
- Automatic idle termination
- Azure compute quota release
- Azure budget monitoring
- Initial infrastructure cost analysis

The workspace is ready to support the next implementation stages of the Healthcare Lakehouse portfolio, including Unity Catalog configuration, identity and storage integration, ingestion pipelines, Delta Lake processing, streaming, orchestration, governance, testing, observability, and CI/CD.

---

## 11. Operating Rules

The following rules apply to the DEV workspace:

- Use classic compute only when the workload or learning objective requires it.
- Prefer ephemeral compute over persistent clusters.
- Manually terminate interactive compute when work is complete.
- Retain 15-minute auto-termination as a fallback control.
- Do not leave development compute running overnight.
- Monitor Azure Cost Management throughout implementation.
- Continue monitoring persistent NAT Gateway cost.
- Evaluate serverless compute for appropriate future workloads.
- Do not manually modify resources in the Databricks-managed resource group.
- Do not commit credentials, OAuth tokens, secrets, personal identifiers, or authentication caches to Git.
- Introduce additional networking and security infrastructure only when justified by an architectural requirement.