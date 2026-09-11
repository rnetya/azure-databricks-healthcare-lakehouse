# Azure Cost Guardrails

## Purpose

This document defines the cost-control standards for the Healthcare Lakehouse portfolio environment.

The objective is to demonstrate production-relevant Azure and Databricks engineering practices while maintaining a strict portfolio cost ceiling.

The guiding principle is:

> Learn and demonstrate the engineering principle at minimal cost.

---

## Budget Baseline

Azure subscription budget:

- Budget name: `Healthcare-Portfolio-Monthly-Budget`
- Budget amount: `$75`
- Reset period: `Monthly`
- Budget scope: Healthcare portfolio Azure subscription

Actual-cost notifications are configured at:

- 50% — Early warning
- 75% — Attention required
- 90% — Urgent review
- 100% — Budget reached

The budget is an alerting mechanism and does not automatically stop Azure resources.

Personal notification addresses and subscription identifiers are intentionally excluded from this public repository.

---

## Operating Cost Rules

### Databricks Compute

- Interactive compute must use auto-termination.
- Job compute should be ephemeral whenever practical.
- Databricks compute must not be intentionally left running overnight.
- Start with the smallest practical compute configuration.
- Scale compute only when workload evidence justifies the change.

### Environment Strategy

Only the DEV environment is physically implemented during the initial portfolio build.

UAT and PRD remain logical deployment targets until physical environments are justified.

This preserves the enterprise deployment model without unnecessarily tripling infrastructure cost.

### Local and On-Demand Services

Services remain local or on-demand where Azure hosting does not provide additional learning value.

Examples:

- Apache Kafka runs locally.
- The Claims relational database remains local or on-demand initially.

### Temporary Resources

Temporary resources used for experiments, validation, or demonstrations must be stopped or deleted when no longer required.

Resources should not remain deployed solely because they may be useful later.

### New Azure Resource Review

Before introducing a new paid Azure resource, determine:

1. What does the service cost?
2. Does it continue billing while idle?
3. Can it be stopped?
4. Can it be safely deleted and recreated?
5. What engineering capability does it demonstrate?
6. Is there a lower-cost approach that teaches substantially the same engineering principle?

### Portfolio Demonstration Mode

After active development is complete:

- recurring schedules are paused by default
- compute is terminated when not in use
- pipelines execute on demand for demos, testing, or release validation
- CI/CD runs only when code changes require deployment
- measured operating cost replaces initial estimates

---

## Cost Monitoring Process

Cost should be reviewed regularly through Azure Cost Management.

Unexpected cost acceleration must be investigated before additional resources are provisioned.

During active implementation, cost reviews should consider:

- current monthly spend
- spend by resource
- spend by service
- spend by resource group
- cost attribution using project and environment tags
- unexpected idle resources

---

## Tagging Alignment

Cost attribution uses the mandatory Azure resource tags defined by the project naming and tagging standard:

- `Project`
- `Environment`
- `Purpose`
- `Owner`
- `CostCenter`
- `Region`

These tags support resource ownership, environment identification, and cost analysis.

---

## Active Development Cost Target

The portfolio architecture targets approximately:

`$30–$75 per month`

during active development.

The `$75` Azure budget is a guardrail rather than a spending target.

Actual spend should remain materially below the budget whenever practical.

---

## Cost-Control Principle

If two approaches teach substantially the same engineering skill, prefer the lower-cost implementation.