# Local Development and Testing

## Overview

This document describes the local development environment for the Azure Databricks Healthcare Lakehouse portfolio.

The project uses Python 3.12, VS Code, pytest, Ruff, the Databricks SDK, and Databricks Connect.

## Environment Setup

Create and activate a Python virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the pinned development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
python -m pip check
```

## Local Quality Checks

Run unit tests:

```powershell
python -m pytest -q
```

Run linting and formatting validation:

```powershell
python -m ruff check .
python -m ruff format --check .
```

Local unit tests do not require Databricks compute.

Previously validated foundation notebooks are excluded from Ruff formatting to preserve their existing source formatting.

## Databricks Authentication

The development workspace uses the Databricks CLI OAuth profile `healthcare-dev`.

```powershell
databricks auth login --profile healthcare-dev
databricks auth profiles
```

Never commit access tokens, authentication caches, or credential files.

Interactive developer authentication is separate from workload authentication used by automated jobs and CI/CD.

## Databricks Connect

The project uses Databricks Connect 17.3.14 with Python 3.12.

A manual Serverless connectivity smoke test is available at:

`tests/manual_serverless_connect.py`

Configure the intended workspace profile and Serverless environment before running the test:

```powershell
$env:DATABRICKS_CONFIG_PROFILE = "healthcare-dev"
$env:DATABRICKS_SERVERLESS_COMPUTE_ID = "auto"
$env:DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION = "4"
```

Execute the manual test:

```powershell
python tests/manual_serverless_connect.py
```

The test creates a small synthetic healthcare-member DataFrame and verifies remote Spark execution.

Remote Spark execution can incur Databricks Serverless compute charges. Run this test intentionally, not as part of automated unit testing.

## Git Workflow

Development changes are made on feature branches and merged into the protected `main` branch through GitHub pull requests.

Before committing:

```powershell
git status --short
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

Only source code, tests, configuration, and documentation should be committed. Local environments, caches, and credentials must remain excluded.