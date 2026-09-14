# ADLS Gen2 Foundation

## Overview

This document describes the Azure Data Lake Storage Gen2 foundation for the Healthcare Lakehouse portfolio.

The storage architecture is designed to provide a secure, cost-conscious, and scalable physical data layer for the Azure Databricks platform while maintaining a clear separation between physical cloud storage and the logical Medallion Architecture governed through Unity Catalog.

## Storage Account

| Property | Configuration |
|---|---|
| Storage account | `stdehealthcaredev` |
| Resource group | `rg-de-healthcare-dev` |
| Region | East US |
| Account kind | StorageV2 |
| Performance tier | Standard |
| Redundancy | LRS |
| Hierarchical namespace | Enabled |
| Minimum TLS version | TLS 1.2 |
| Public blob access | Disabled |
| Shared Key access | Disabled |
| Primary authentication | Microsoft Entra ID |

Hierarchical namespace is enabled so the storage account provides ADLS Gen2 filesystem semantics, including hierarchical directories and support for fine-grained access control.

## Environment and Cost Decision

The physical implementation currently represents the DEV environment.

LRS was selected for the portfolio DEV environment because the datasets are synthetic and reproducible. The objective is to demonstrate the engineering architecture while minimizing unnecessary recurring cost.

A production implementation would evaluate ZRS or another redundancy model based on availability, durability, SLA, and disaster-recovery requirements.

## Physical Storage Architecture

The storage account contains four top-level ADLS Gen2 file systems:

stdehealthcaredev
|
+-- raw
|   +-- claims
|   +-- eligibility
|   +-- member
|   +-- provider
|   +-- reference
|   `-- service-events
|
+-- managed
|
+-- quarantine
|   +-- claims
|   +-- eligibility
|   +-- member
|   +-- provider
|   `-- service-events
|
`-- operational
    +-- audit
    +-- checkpoints
    `-- metadata