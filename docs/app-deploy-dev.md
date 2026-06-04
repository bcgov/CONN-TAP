# Dev app deploy (GitHub Actions)

Workflows: [app-build](../.github/workflows/app-build.yaml) → [app-deploy-dev](../.github/workflows/app-deploy-dev.yml).

Public URL: `https://tap.<license>-dev.stratus.cloud.gov.bc.ca` (shared dev slot).

## Automatic deploy (main)

Every successful **app-build** on `main` triggers **app-deploy-dev** and updates the shared dev environment with the merge commit SHA.

No label or flag is required.

## Optional PR deploy (opt-in, default off)

Use this to test your branch on **shared dev** before merging. Only one PR should use dev at a time.

### 1. Enable the feature (once per repo)

Set a repository or **dev** environment variable:

| Variable | Value |
|----------|--------|
| `ALLOW_PR_DEV_DEPLOY` | `true` |

If unset or not `true`, PRs never deploy (only `main` does).

### 2. Opt in on your PR

Add the GitHub label **`deploy-dev`** to your pull request.

Create the label under **Issues → Labels** if it does not exist (any color).

### 3. What runs

1. **app-build** runs on the PR and pushes images tagged with the PR head SHA.
2. **app-deploy-dev** runs when:
   - **app-build** completes (`workflow_run`), or
   - you add/remove **`deploy-dev`** or push new commits (`pull_request` events).
3. The gate job deploys only if `ALLOW_PR_DEV_DEPLOY=true` **and** the PR has **`deploy-dev`**.

### 4. Manual deploy

**Actions → app-deploy-dev → Run workflow** always deploys (uses the selected branch’s latest commit; ensure images exist in ECR).

## Coordination

PR deploys replace whatever is currently on shared dev. Coordinate with your team so two PRs do not fight for the same URL.

After merge to `main`, the main pipeline redeploys dev with the merged code.

## Required configuration

See [github_action_and_aws.md](./github_action_and_aws.md) for AWS OIDC, secrets, and `LICENSE_PLATE`.

Dev secrets: `AWS_DEPLOY_ROLE_ARN`, `KEYCLOAK_CLIENT_SECRET`, `SESSION_SECRET`, `TOKEN_ENCRYPTION_KEY`.
