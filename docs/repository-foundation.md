# Repository Foundation

## Purpose

This document records the repository standards and source-control decisions established during the foundation phase of the Azure Databricks Healthcare Lakehouse project.

The objective is to maintain a professional, auditable, and scalable Git workflow while keeping the implementation appropriate for a solo Data Engineering portfolio project.

## Repository

Repository:

`azure-databricks-healthcare-lakehouse`

The repository serves as the primary source of truth for application code, Data Engineering pipelines, infrastructure definitions, configuration, tests, architecture documentation, and deployment artifacts.

## Repository Structure

The repository is organized around clear engineering responsibilities:

```text
.github/workflows/   GitHub Actions CI/CD workflows
architecture/        Architecture diagrams, ADRs, and data models
src/                 Data Engineering source code
pipelines/           Declarative pipeline implementation
workflows/           Workflow and job definitions
resources/           Databricks deployment resource definitions
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

Empty implementation directories are initially preserved using `.gitkeep` files and will progressively contain real project artifacts as the platform is implemented.

## Branch Strategy

The repository uses `main` as the protected integration branch.

Development is performed using short-lived working branches.

Branch naming conventions:

* `feature/...` — new engineering capabilities
* `fix/...` — defect corrections
* `docs/...` — documentation changes
* `chore/...` — repository, tooling, or maintenance changes

The current workflow is:

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

Direct development on `main` is avoided after repository bootstrap.

## Main Branch Protection

A GitHub branch ruleset named:

`main-branch-protection`

is applied to the default branch.

The initial ruleset includes:

* restriction of branch deletion;
* pull requests required before merging;
* force pushes blocked.

Additional approval requirements are currently not enabled because the repository is maintained by a single developer.

Required CI status checks are intentionally deferred until automated CI workflows are implemented.

## Merge Strategy

The default merge strategy for normal development pull requests is:

**Squash and merge**

This keeps the `main` branch history concise by representing each completed pull request as a single logical change.

Merge commits may be used later when preserving the detailed history of a branch provides meaningful engineering value.

## Line Ending Policy

A repository-level `.gitattributes` file defines consistent line-ending behavior across Windows development environments and Linux-based automation environments.

Cross-platform source and configuration files use LF line endings where appropriate, while Windows-native scripts may use CRLF.

This prevents unnecessary Git diffs caused solely by operating-system line-ending differences.

## Repository Safety

The `.gitignore` configuration excludes local or sensitive development artifacts including:

* Python virtual environments;
* local environment-variable files;
* secret files;
* Databricks local state;
* Terraform state and variable files;
* Azure CLI local artifacts;
* generated and large datasets;
* Kafka runtime data;
* logs;
* IDE metadata;
* test and build artifacts.

Secrets must never be committed to the repository.

## Initial Repository Validation

The repository foundation was validated through the following workflow:

1. Repository created in GitHub.
2. Repository cloned locally.
3. Local branch standardized to `main`.
4. Project directory structure established.
5. `.gitignore` and `.gitattributes` policies established.
6. Initial README created.
7. Repository foundation committed.
8. Local `main` pushed and linked to `origin/main`.
9. GitHub `main` branch protection ruleset activated.
10. A documentation branch was created to validate the development workflow.
11. The branch was committed and pushed independently.
12. Pull Request #1 was opened against `main`.
13. The pull request was successfully validated and squash merged.
14. Remote and local working branches were removed.
15. Local `main` was synchronized with `origin/main`.
16. Final working tree validation confirmed a clean repository state.

## CI/CD Evolution

The current repository workflow establishes source-control governance before automated deployment infrastructure exists.

The target CI/CD model will evolve toward:

```text
Feature Branch
      |
      v
CI Validation
      |
      v
DEV Deployment
      |
      v
DEV Validation
      |
      v
TEST Deployment
      |
      v
TEST Validation
      |
      v
Pull Request Approval
      |
      v
Merge to main
      |
      v
PROD Deployment
```

Feature branches may deploy to development and test environments for validation.

Production deployments must originate from the protected `main` branch after required validation has completed.

CI/CD status checks and deployment controls will be introduced when the corresponding Databricks and Azure resources are implemented.

## Foundation Outcome

The repository foundation provides:

* protected source control;
* clean branch governance;
* consistent repository organization;
* cross-platform file handling;
* secure handling of local development artifacts;
* documented pull-request workflow;
* scalable preparation for CI/CD;
* an auditable engineering history.

This foundation will support the remaining Azure Databricks Healthcare Lakehouse implementation milestones.
