import boto3
import os

# --- ENV VARS ---
SOURCE_KEY = os.environ["SOURCE_AWS_ACCESS_KEY_ID"]
SOURCE_SECRET = os.environ["SOURCE_AWS_SECRET_ACCESS_KEY"]
SOURCE_SESSION_TOKEN = os.environ["SOURCE_AWS_SESSION_TOKEN"]
SOURCE_REGION = os.getenv("SOURCE_AWS_REGION", "us-east-1")
SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]

DEST_KEY = os.environ["DEST_AWS_ACCESS_KEY_ID"]
DEST_SECRET = os.environ["DEST_AWS_SECRET_ACCESS_KEY"]
DEST_SESSION_TOKEN = os.environ["DEST_AWS_SESSION_TOKEN"]
DEST_REGION = os.getenv("DEST_AWS_REGION", "us-east-1")
DEST_BUCKET = os.environ["DEST_BUCKET"]

# Comma-separated list of folder prefixes to exclude from copy (default: athena_results)
EXCLUDE_PREFIXES_RAW = os.getenv("EXCLUDE_PREFIXES", "athena_results")
EXCLUDE_PREFIXES = [p.strip() for p in EXCLUDE_PREFIXES_RAW.split(",") if p.strip()]


def should_exclude_key(key: str) -> bool:
    """True if key is under an excluded folder prefix."""
    for prefix in EXCLUDE_PREFIXES:
        if key == prefix or key.startswith(prefix + "/"):
            return True
    return False

# --- CLIENTS ---
source_session = boto3.Session(
    aws_access_key_id=SOURCE_KEY,
    aws_secret_access_key=SOURCE_SECRET,
    aws_session_token=SOURCE_SESSION_TOKEN,
    region_name=SOURCE_REGION,
)
source_s3 = source_session.client("s3")

dest_session = boto3.Session(
    aws_access_key_id=DEST_KEY,
    aws_secret_access_key=DEST_SECRET,
    aws_session_token=DEST_SESSION_TOKEN,
    region_name=DEST_REGION,
)
dest_s3 = dest_session.client("s3")

# --- Get all existing keys in destination ---
if EXCLUDE_PREFIXES:
    print(f"🚫 Excluding source folders: {EXCLUDE_PREFIXES}")
dest_keys = set()
print("📥 Fetching existing destination keys...")
dest_paginator = dest_s3.get_paginator("list_objects_v2")
for page in dest_paginator.paginate(Bucket=DEST_BUCKET):
    for obj in page.get("Contents", []):
        dest_keys.add(obj["Key"])
print(f"Found {len(dest_keys)} keys in destination")

# --- Copy missing keys only ---
copied = 0
skipped = 0
src_paginator = source_s3.get_paginator("list_objects_v2")
for page in src_paginator.paginate(Bucket=SOURCE_BUCKET):
    for obj in page.get("Contents", []):
        key = obj["Key"]

        if should_exclude_key(key):
            skipped += 1
            print(f"⏭️ Skipping {key} (excluded prefix)")
            continue

        if key in dest_keys:
            skipped += 1
            print(f"✅ Skipping {key}, already exists")
            continue

        print(f"⬆️ Copying {key}...")
        response = source_s3.get_object(Bucket=SOURCE_BUCKET, Key=key)
        body = response["Body"]
        dest_s3.upload_fileobj(body, DEST_BUCKET, key)
        copied += 1

print(f"🎉 Done! Copied {copied} new objects, skipped {skipped}")
