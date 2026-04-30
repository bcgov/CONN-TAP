# GitHub Actions and AWS

This document explains how the [terraform-deploy](../.github/workflows/terraform-deploy.yml)
workflow authenticates to AWS, what it deploys, and how to set the project up
the first time.

The configuration follows the [BC Gov LZA CI/CD guide][lza] and uses GitHub
OpenID Connect (OIDC) — there are **no long-lived AWS access keys** stored in
GitHub.

[lza]: https://developer.gov.bc.ca/docs/default/component/public-cloud-techdocs/aws/LZA/best-practices/iac-and-ci-cd/

---

## Architecture

```
GitHub Actions runner
        │  (OIDC id-token, signed by token.actions.githubusercontent.com)
        ▼
AWS IAM OIDC provider  (per AWS account)
        │  sts:AssumeRoleWithWebIdentity
        ▼
IAM Role  <license>-<env>-github-actions  (per env, per AWS account)
        │
        ▼
Terraform plan/apply against ca-central-1
```

Each environment (`dev`, `test`, `prod`) is its own AWS account. Each account
has:

- **One** GitHub OIDC identity provider for `token.actions.githubusercontent.com`.
- **One** IAM role (`<license>-<env>-github-actions`) with a trust policy that
  only allows assumption from this repository, with subject claims scoped per
  env (see [Trust scoping](#trust-scoping)).

Both are created by the [github_actions_oidc](../infra/modules/github_actions_oidc/main.tf)
Terraform module and wired into each env via `infra/envs/<env>/github_oidc.tf`.

---

## Terraform module: `github_actions_oidc`

Source: [infra/modules/github_actions_oidc](../infra/modules/github_actions_oidc/main.tf).

| Input                      | Default                                    | Notes                                                                                         |
| -------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `github_repositories`      | _required_                                 | List of `owner/repo`. Per-env wiring sets this from `var.github_owner` + `var.github_repository`. |
| `allowed_subjects`         | `[]`                                       | Explicit list of `sub` claims (StringLike). When empty, `repo:<owner>/<repo>:*` is used.       |
| `role_name`                | _required_                                 | IAM role name. Per-env wiring defaults to `<license>-<env>-github-actions`.                    |
| `managed_policy_arns`      | `[]`                                       | Managed policy ARNs to attach. Envs default to `AdministratorAccess`.                         |
| `inline_policy_json`       | `null`                                     | Optional inline policy.                                                                       |
| `max_session_duration`     | `3600`                                     | STS session TTL (seconds).                                                                    |
| `create_oidc_provider`     | `true`                                     | Create the account-level OIDC provider. Set `false` if one already exists.                    |
| `oidc_thumbprints`         | GitHub published thumbprints               | AWS no longer enforces strict validation but the field is required.                           |

Outputs: `role_arn`, `role_name`, `oidc_provider_arn`.

### Trust scoping

| Env  | Default `sub` patterns                                                                  |
| ---- | -------------------------------------------------------------------------------------- |
| dev  | `repo:bcgov/Data-Management-Platform:*`                                                |
| test | `repo:bcgov/Data-Management-Platform:*`                                                |
| prod | `repo:bcgov/Data-Management-Platform:ref:refs/heads/main`<br>`repo:bcgov/Data-Management-Platform:environment:prod` |

Override per env via `github_actions_allowed_subjects` (a list, e.g. `["repo:owner/repo:ref:refs/heads/main"]`).

GitHub OIDC `sub` claim formats commonly used:

- `repo:OWNER/REPO:ref:refs/heads/BRANCH`
- `repo:OWNER/REPO:ref:refs/tags/TAG`
- `repo:OWNER/REPO:environment:NAME` (only set when the workflow declares `environment:` and a deployment job runs)
- `repo:OWNER/REPO:pull_request`

See the [GitHub OIDC reference][gh-oidc].

[gh-oidc]: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#example-subject-claims

---

## First-time setup

### 1. Decide whether to create the OIDC provider

LZA accounts may already contain
`arn:aws:iam::<acct>:oidc-provider/token.actions.githubusercontent.com`. Only
**one** OIDC provider for that issuer is allowed per account.

Check from the AWS console (IAM → Identity providers) or CLI:

```bash
aws iam list-open-id-connect-providers
```

If a provider exists, set in that env's `terraform.tfvars`:

```hcl
github_actions_create_oidc_provider = false
```

…or import it after the first plan fails:

```bash
terraform -chdir=infra/envs/<env> import \
  'module.github_actions_oidc.aws_iam_openid_connect_provider.github[0]' \
  arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com
```

### 2. First Terraform apply (from a workstation)

Bootstrap once locally with SSO credentials:

```bash
cd infra/envs/dev
export TF_VAR_license=dd5a29
export TF_VAR_env=dev
export TF_VAR_aws_region=ca-central-1
terraform init -backend-config=backend.hcl
terraform apply
```

Capture the role ARN:

```bash
terraform output -raw github_actions_role_arn
# arn:aws:iam::<dev-account-id>:role/dd5a29-dev-github-actions
```

Repeat for `test` and `prod`.

### 3. Configure GitHub repository

For each environment, create a [GitHub Environment][gh-env] (`dev`, `test`,
`prod`) in repository **Settings → Environments**.

[gh-env]: https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

Per environment:

| Setting                               | Recommended                                                                                  |
| ------------------------------------- | -------------------------------------------------------------------------------------------- |
| Environment secret `AWS_DEPLOY_ROLE_ARN` | The role ARN from `terraform output github_actions_role_arn` for that env's AWS account.    |
| Required reviewers                    | _(prod only)_ at least one approver from the platform team.                                  |
| Deployment branches                   | _(prod only)_ "Selected branches" → `main`.                                                  |
| Wait timer                            | _(prod only, optional)_ 5–15 minutes for cancel windows.                                     |

Also create a repository **variable** named `LICENSE_PLATE` (Settings →
Secrets and variables → Actions → Variables tab) set to your license plate
prefix (e.g. `dd5a29`). The workflow passes this as `TF_VAR_license`.

### 4. Confirm the workflow runs

- Open a pull request that touches `infra/**`. The `plan` job runs against
  dev/test/prod in parallel and uploads `tfplan` artifacts.
- Merge to `main`. The `apply-dev → apply-test → apply-prod` chain runs. Prod
  pauses for the required reviewer if you configured one.
- Manual runs: **Actions → terraform-deploy → Run workflow** → pick
  `env` and `action` (`plan`, `apply`, or `destroy`).

---

## Workflow reference

File: [.github/workflows/terraform-deploy.yml](../.github/workflows/terraform-deploy.yml).

### Triggers

| Trigger              | Behaviour                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `pull_request` to `main` (paths `infra/**`)  | Runs `terraform plan` for **all three envs** in parallel and uploads each `tfplan` as a build artifact (7-day retention).  |
| `push` to `main` (paths `infra/**`)          | Sequentially `apply-dev → apply-test → apply-prod`. Each job runs inside its GitHub Environment so reviewers/branch rules apply. |
| `workflow_dispatch`                          | Manual run; pick `env` (`dev` / `test` / `prod`) and `action` (`plan` / `apply` / `destroy`).                              |

### Concurrency

The job uses a per-env concurrency group with `cancel-in-progress: false` so
two applies cannot race on the same Terraform state.

### Permissions

- `id-token: write` — required to mint the GitHub OIDC JWT.
- `contents: read` — for `actions/checkout`.
- `pull-requests: write` — placeholder for future plan-summary comments.

### Region

`AWS_REGION` is hard-coded to `ca-central-1` (LZA constraint), and each env's
`var.aws_region` carries a Terraform validation block that fails plan if any
other region is supplied.

### Authentication step

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
    role-session-name: gha-<env>-${{ github.run_id }}
    aws-region: ca-central-1
```

The action exchanges the GitHub OIDC token for short-lived AWS credentials
via `sts:AssumeRoleWithWebIdentity`. Those credentials are written to the job
environment as `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN`, which Terraform's AWS provider picks up automatically.

### Variables passed to Terraform

| Variable                | Source                          |
| ----------------------- | ------------------------------- |
| `TF_VAR_aws_region`     | Hard-coded `ca-central-1`       |
| `TF_VAR_env`            | The job's target environment    |
| `TF_VAR_license`        | Repository variable `LICENSE_PLATE` |

Other inputs use the defaults declared in
`infra/envs/<env>/eks_variables.tf` and `github_oidc_variables.tf`. Override
by setting `TF_VAR_*` Environment secrets where necessary.

---

## Tightening the role permissions

By default the env modules attach `AdministratorAccess`. This is the simplest
working baseline because Terraform creates IAM roles, OIDC providers, KMS-
encrypted RDS, EKS, etc. To narrow:

1. Author a custom managed or inline policy covering the
   resources Terraform actually touches in this repo (EKS, RDS, IAM, EC2 SG,
   Secrets Manager, S3 backend bucket access, KMS).
2. Override per env in `terraform.tfvars`:
   ```hcl
   github_actions_managed_policy_arns = [
     "arn:aws:iam::<acct>:policy/dmp-terraform-deploy",
   ]
   ```
3. For higher assurance, split into a **plan** role (read-only) used on PRs
   and an **apply** role used on `main` pushes only — duplicate the module
   call with two different `role_name`s and set `AWS_DEPLOY_ROLE_ARN`
   separately for plan and apply jobs.

---

## Troubleshooting

| Symptom                                                                                              | Likely cause                                                                                                       | Fix                                                                                                                                |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `Error: error creating IAM OIDC Provider … EntityAlreadyExists`                                      | LZA already provisioned the GitHub OIDC provider in the account.                                                   | Set `github_actions_create_oidc_provider = false` or import it (see [First-time setup](#first-time-setup)).                       |
| `Error: failed to assume role … Not authorized to perform sts:AssumeRoleWithWebIdentity`             | The `sub` claim doesn't match `allowed_subjects`, or the workflow isn't running in the matching GitHub Environment.| Verify the workflow declares `environment: <env>`, the run is on the expected branch, and the trust policy allows that subject.   |
| `Error: configure AWS credentials … No OpenIDConnect provider found`                                 | OIDC provider missing in the AWS account.                                                                          | Apply with `github_actions_create_oidc_provider = true` (default), or contact the platform team.                                  |
| Plan succeeds but apply fails with permission errors mid-run                                         | Custom managed policy is too narrow.                                                                               | Re-attach `AdministratorAccess` temporarily, capture the missing actions from CloudTrail, then add them to the custom policy.     |
| `Error: ... an existing aws_db_instance ... cannot be modified` (Multi-AZ flip)                      | First prod apply enables `multi_az`/`deletion_protection`.                                                          | This is normal — RDS performs an online modification. Allow the run to take ~10–20 min.                                          |
| Workflow runs but no AWS resources change                                                            | `paths` filter excluded the change, or running on a non-`main` branch (apply jobs are gated on `refs/heads/main`).  | Trigger the workflow manually via `workflow_dispatch`, or push the change on `main`.                                              |

---

## Related files

- Module: [infra/modules/github_actions_oidc](../infra/modules/github_actions_oidc/main.tf)
- Per-env wiring: [infra/envs/dev/github_oidc.tf](../infra/envs/dev/github_oidc.tf), [test](../infra/envs/test/github_oidc.tf), [prod](../infra/envs/prod/github_oidc.tf)
- Workflow: [.github/workflows/terraform-deploy.yml](../.github/workflows/terraform-deploy.yml)
- BC Gov LZA reference: <https://developer.gov.bc.ca/docs/default/component/public-cloud-techdocs/aws/LZA/best-practices/iac-and-ci-cd/>
