# README_IaC

This repo uses **Terraform** to manage AWS infrastructure for the DMP platform.

Infrastructure is organized by **environment** and **shared modules**.

---

## Repository Structure

infra/
  envs/
    prod/
    test/
  modules/
    dmp_shared/
    s3_bucket/

**envs/**
- Environment-specific configuration
- Each environment has its own backend, variables, and root module

**modules/**
- Reusable infrastructure components
- `dmp_shared` → Glue, Lambda, IAM, Athena, EC2
- `s3_bucket` → reusable S3 bucket module

---

## Prerequisites

Install:

Terraform >= 1.5  
AWS CLI

Configure AWS access:
"aws login" - to use BC SSO.

---

## Deploy Infrastructure

1. Navigate to the environment you want to manage:

cd infra/envs/test  
or  
cd infra/envs/prod

2. Initialize Terraform (downloads providers and configures backend):

terraform init

3. Review the planned changes:

terraform plan

4. Apply the infrastructure:

terraform apply ---- DO NOT RUN

---

## Adding a New Environment

To create a new environment (for example `dev`):

1. Copy an existing environment directory:

infra/envs/test → infra/envs/dev

2. Update the following files in the new environment:

**backend.tf**
- Update the remote state configuration
- Use a unique state key for the new environment

Example:

key = "dmp/dev/terraform.tfstate"

**terraform.tfvars**
- Update environment-specific values such as:
  - bucket names
  - environment identifiers
  - account-specific values

Example:

environment = "dev"

3. Initialize Terraform for the new environment:

cd infra/envs/dev  
terraform init

4. Review the plan:

terraform plan

5. Deploy the environment:

terraform apply

---

## Environment Configuration

Each environment uses its own variables file:

infra/envs/test/terraform.tfvars  
infra/envs/prod/terraform.tfvars

These define environment-specific values such as:
- bucket names
- instance settings
- feature flags

---

## Notes

- Always review `terraform plan` before applying.
- Do not manually modify AWS resources managed by Terraform.