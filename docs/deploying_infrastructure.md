# Deploying Infrastructure

This document describes the steps required to deploy the Data Management Platform infrastructure using Terraform.

---

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5.0
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials for the target account
- Access to the target AWS environment
- If you are not using test, or prod a public key generated in the form of public-[env].pub in the test folder

---

## Step 1 — Set Environment Variables

All required Terraform inputs and the backend bucket name are driven by three environment variables. Set these in your shell session or inject them as pipeline secrets.

```bash
export TF_VAR_license="<license>"   # e.g. dd5a29
export TF_VAR_env="<env>"           # tools | dev | test | prod
export TF_VAR_aws_region="ca-central-1"
```

> These variables are automatically picked up by Terraform as `var.license`, `var.env`, and `var.aws_region`. All resource names (S3 buckets, EC2 key pair, instance name, etc.) are derived from them — no edits to `.tfvars` are required.

---

## Step 2 — Bootstrap the Remote State Bucket

This step only needs to be run **once per environment**. If the state bucket already exists, skip to Step 3.

```bash
# Create the bucket
aws s3api create-bucket \
  --bucket "terraform-remote-state-${TF_VAR_license}-${TF_VAR_env}" \
  --region "${TF_VAR_aws_region}" \
  --create-bucket-configuration LocationConstraint="${TF_VAR_aws_region}"

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket "terraform-remote-state-${TF_VAR_license}-${TF_VAR_env}" \
  --versioning-configuration Status=Enabled
```

---

## Step 3 — Navigate to the Environment Directory

```bash
cd infra/envs/${TF_VAR_env}
```

---

## Step 4 — Initialize Terraform

The backend bucket name is constructed from your environment variables at init time.

```bash
terraform init \
  -backend-config="bucket=terraform-remote-state-${TF_VAR_license}-${TF_VAR_env}"
```

---

## Step 6 — Plan

Review the changes Terraform will make before applying.

```bash
terraform plan
```

---

## Step 7 — Apply

```bash
terraform apply
```

Confirm with `yes` when prompted, or add `-auto-approve` for non-interactive pipelines.

---

## Destroying Infrastructure

To tear down all resources in an environment:

```bash
terraform destroy
```

> **Note:** S3 buckets are protected with `prevent_destroy = true`. They must be emptied and the lifecycle rule removed manually before they can be destroyed.

---

## Optional Overrides

The following variables have sensible defaults and do not need to be set unless you want to override them. Add them to `terraform.tfvars` or export as `TF_VAR_*`:

| Variable | Default | Description |
|---|---|---|
| `ec2_security_group_names` | `["App"]` | Security groups attached to the PowerBI EC2 instance |
| `powerbi_instance_type` | `t3.large` | EC2 instance type |
| `powerbi_ami_id` | `ami-067abc25c5d2e14af` | Windows AMI for PowerBI Desktop |
| `assets_dir` | `../../..` | Path to repo root (containing `glue_scripts/` and `lambda/`), relative to the environment directory |
| `powerbi_alert_email` | *(none)* | Email address to receive an alert when the PowerBI EC2 instance has been running for more than 8 hours. Omit or leave unset to disable. Recipient must confirm the SNS subscription via the link sent to the inbox. |
