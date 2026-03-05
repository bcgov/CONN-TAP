import json, subprocess
from pathlib import Path

def sh(cmd):
    return subprocess.check_output(cmd, text=True)

tf = json.loads(sh(["terraform", "show", "-json"]))
resources = list(tf["values"]["root_module"].get("resources", []))
for child in tf["values"]["root_module"].get("child_modules", []):
    resources.extend(child.get("resources", []))

def load_lines(path, col=None):
    p = Path(path)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if col is None:
            out.add(line)
        else:
            parts = line.split()
            if len(parts) > col:
                out.add(parts[col])
    return out

tf_s3, tf_glue, tf_iam, tf_redshift, tf_ec2 = set(), set(), set(), set(), set()

for r in resources:
    t = r.get("type")
    v = r.get("values") or {}

    if t == "aws_s3_bucket":
        name = v.get("bucket")
        if name: tf_s3.add(name)

    elif t == "aws_glue_job":
        name = v.get("name")
        if name: tf_glue.add(name)

    elif t == "aws_iam_role":
        name = v.get("name")
        if name: tf_iam.add(name)

    elif t == "aws_redshift_cluster":
        cid = v.get("cluster_identifier")
        if cid: tf_redshift.add(cid)

    elif t == "aws_instance":
        iid = v.get("id")
        if iid: tf_ec2.add(iid)

aws_s3       = load_lines("aws_s3_dmp.txt")
aws_glue     = load_lines("aws_glue_dmp.txt")
aws_iam      = load_lines("aws_iam_dmp.txt")
aws_redshift = load_lines("aws_redshift_dmp.txt")
aws_ec2      = load_lines("aws_ec2_dmp.txt", col=0)

def report(title, missing):
    print(f"==== {title} ====")
    if not missing:
        print("(none)")
    else:
        for x in sorted(missing):
            print(x)

report("S3 missing in TF (AWS - TF)", aws_s3 - tf_s3)
report("Glue Jobs missing in TF (AWS - TF)", aws_glue - tf_glue)
report("IAM Roles missing in TF (AWS - TF)", aws_iam - tf_iam)
report("Redshift missing in TF (AWS - TF)", aws_redshift - tf_redshift)
report("EC2 missing in TF (AWS - TF)", aws_ec2 - tf_ec2)

print("\n--- TF managed counts ---")
print("S3:", len(tf_s3))
print("Glue jobs:", len(tf_glue))
print("IAM roles:", len(tf_iam))
print("Redshift:", len(tf_redshift))
print("EC2:", len(tf_ec2))
