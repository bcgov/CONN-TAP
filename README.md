# Data Management Platform (DMP)

This repository contains:
- AWS Glue ingestion scripts (Python + Glue-ready code)
- Terraform Infrastructure as Code (IaC) for AWS resources (S3, Glue, Lambda, IAM, Athena integration, and EC2 for PowerBI)

## Table of Contents
- [Overview](#overview)
- [Contributing](docs/CONTRIBUTING.MD)
- [Code Of Conduct](docs/CODE_OF_CONDUCT.md)
- [Repository Contents](#repository-contents)
- [Documentation](#documentation)
- [Deployment](#deployment)
- [Development Notes](#development-notes)

## Overview
DMP ingestion is event-driven: raw data lands in S3, triggers AWS Lambda, which starts AWS Glue jobs. Athena tables provide query access to the processed data, and a PowerBI EC2 instance enables reporting where applicable.

## Repository Contents
- `glue_scripts/`: Core Glue job scripts used for ingestion and transformations
- `lambda/`: Lambda handler code that triggers Glue jobs
- `infra/`: Terraform configuration for provisioning AWS infrastructure
- `tools/`: Utility scripts (e.g., S3 copy/replication helpers)
- `local-dev/`: Local development helpers

## Documentation
- [Deploying Infrastructure](docs/deploying_infrastructure.md)
- [Ingestion Scripts](docs/ingestion_scripts.md)

## Deployment
For full setup instructions (including required `TF_VAR_*` environment variables and Terraform commands), see:
- `docs/deploying_infrastructure.md`

## Development Notes
- Keep Glue/Lambda source in the repo; Terraform uploads the required artifacts to the Glue assets bucket.
- Configuration is environment-scoped under `infra/envs/<env>`.