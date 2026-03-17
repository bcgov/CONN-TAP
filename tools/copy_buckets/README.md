# Copy S3 Buckets

Copies objects from a **source** S3 bucket to a **destination** S3 bucket. Only objects that do not already exist in the destination (by key) are copied. Optional folder prefixes can be excluded from the source so they are never copied (e.g. `athena_results`).

Useful for replicating bucket contents across accounts or regions (e.g. from a reference environment into a new one).

## Requirements

- Python 3.7+
- `boto3` (`pip install boto3`)

## Environment variables

Set these before running the script. Source and destination can be different accounts and/or regions.

| Variable | Required | Description |
|----------|----------|-------------|
| `SOURCE_AWS_ACCESS_KEY_ID` | Yes | Source account access key |
| `SOURCE_AWS_SECRET_ACCESS_KEY` | Yes | Source account secret key |
| `SOURCE_AWS_SESSION_TOKEN` | Yes | Source account session token (use empty string if not using temporary credentials) |
| `SOURCE_AWS_REGION` | No | Source bucket region (default: `us-east-1`) |
| `SOURCE_BUCKET` | Yes | Source bucket name |
| `DEST_AWS_ACCESS_KEY_ID` | Yes | Destination account access key |
| `DEST_AWS_SECRET_ACCESS_KEY` | Yes | Destination account secret key |
| `DEST_AWS_SESSION_TOKEN` | Yes | Destination account session token (use empty string if not using temporary credentials) |
| `DEST_AWS_REGION` | No | Destination bucket region (default: `us-east-1`) |
| `DEST_BUCKET` | Yes | Destination bucket name |
| `EXCLUDE_PREFIXES` | No | Comma-separated folder prefixes to exclude from copy (default: `athena_results`) |

## Excluding folders

- **Default:** The `athena_results` prefix is excluded so Athena query result files are not copied.
- To exclude more prefixes, set `EXCLUDE_PREFIXES` to a comma-separated list, e.g.  
  `EXCLUDE_PREFIXES=athena_results,temp,logs`
- To exclude nothing, set `EXCLUDE_PREFIXES=` or `EXCLUDE_PREFIXES=""`

A key is skipped if it exactly matches a prefix or starts with that prefix followed by `/` (e.g. `athena_results/query-1.csv`).

## How to run

1. Export or set the environment variables (see above).
2. From the repo root or from `tools/copy_buckets`:

   ```bash
   python tools/copy_buckets/copy_buckets.py
   ```

   Or from inside `tools/copy_buckets`:

   ```bash
   cd tools/copy_buckets
   python copy_buckets.py
   ```

## Example

```bash
export SOURCE_AWS_ACCESS_KEY_ID="AKIA..."
export SOURCE_AWS_SECRET_ACCESS_KEY="..."
export SOURCE_AWS_SESSION_TOKEN=""   # or a temporary session token
export SOURCE_AWS_REGION="ca-central-1"
export SOURCE_BUCKET="my-source-bucket"

export DEST_AWS_ACCESS_KEY_ID="AKIA..."
export DEST_AWS_SECRET_ACCESS_KEY="..."
export DEST_AWS_SESSION_TOKEN=""
export DEST_AWS_REGION="ca-central-1"
export DEST_BUCKET="my-dest-bucket"

# Optional: exclude athena_results and temp
export EXCLUDE_PREFIXES="athena_results,temp"

python tools/copy_buckets/copy_buckets.py
```

## Behaviour

- **Listing:** The script lists all keys in the destination bucket, then lists all keys in the source bucket.
- **Copy:** For each source key, it skips if the key is under an excluded prefix, skips if the key already exists in the destination, otherwise copies the object (full key preserved).
- **No delete:** The script never deletes or overwrites objects in the destination; it only adds missing objects.
