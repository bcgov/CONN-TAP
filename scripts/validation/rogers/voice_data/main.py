# main.py
# This is the main script for validating the Rogers voice data.
import pandas as pd
import os

from validation import (
    prepare_data,
    find_duplicates,
    find_missing_bge,
    find_missing_sub_bge,
    find_mapping_issues,
    find_productline_issues,
    find_pre_tax_issues,
    find_post_tax_issues,
)

# ---------------- CONFIG ----------------
BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/rogers_voice_data_automate_validation"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "BC_GOV_Wireline_report_20260331_Consolidated.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "rogers_voice_data_validation_report.xlsx"
)


# ---------------- LOAD DATA ----------------
df = pd.read_excel(INPUT_FILE)

print(f"Total rows: {len(df)}")
print("=" * 60)

# ---------------- PREPARE DATA ----------------
df = prepare_data(df)

# ---------------- RUN VALIDATIONS ----------------
duplicates = find_duplicates(df)
missing_bge = find_missing_bge(df)
missing_subbge = find_missing_sub_bge(df)
mapping_issues = find_mapping_issues(df)
productline_issues = find_productline_issues(df)
pre_tax_issues = find_pre_tax_issues(df)
post_tax_issues = find_post_tax_issues(df)

# ---------------- PRINT SUMMARY ----------------
print("1) Duplicates:", len(duplicates))
print("2) Missing BGE:", len(missing_bge))
print("3) Missing SUB_BGE:", len(missing_subbge))
print("4) Mapping Issues:", len(mapping_issues))
print("5) Productline Issues:", len(productline_issues))
print("6) Pre-Tax Issues:", len(pre_tax_issues))
print("7) Post-Tax Issues:", len(post_tax_issues))

# ---------------- CREATE SUMMARY TABLE ----------------
summary_df = pd.DataFrame([
    {"Check": "Duplicates", "Issue_Count": len(duplicates)},
    {"Check": "Missing BGE", "Issue_Count": len(missing_bge)},
    {"Check": "Missing SUB_BGE", "Issue_Count": len(missing_subbge)},
    {"Check": "Mapping Issues", "Issue_Count": len(mapping_issues)},
    {"Check": "Productline Issues", "Issue_Count": len(productline_issues)},
    {"Check": "Pre-Tax Issues", "Issue_Count": len(pre_tax_issues)},
    {"Check": "Post-Tax Issues", "Issue_Count": len(post_tax_issues)},
])

# Add status column
summary_df["Status"] = summary_df["Issue_Count"].apply(
    lambda x: "PASS" if x == 0 else "FAIL"
)

# Sort for readability
summary_df = summary_df.sort_values(by="Issue_Count", ascending=False)

# ---------------- EXPORT ----------------
with pd.ExcelWriter(OUTPUT_FILE) as writer:

    # Detail sheets
    duplicates.to_excel(writer, sheet_name="Duplicates", index=False)
    missing_bge.to_excel(writer, sheet_name="Missing_BGE", index=False)
    missing_subbge.to_excel(writer, sheet_name="Missing_SUB_BGE", index=False)
    mapping_issues.to_excel(writer, sheet_name="Mapping_Issues", index=False)
    productline_issues.to_excel(writer, sheet_name="Productline_Issues", index=False)
    pre_tax_issues.to_excel(writer, sheet_name="Pre_Tax_Issues", index=False)
    post_tax_issues.to_excel(writer, sheet_name="Post_Tax_Issues", index=False)

    # ⭐ Summary sheet (NEW)
    summary_df.to_excel(writer, sheet_name="Summary", index=False)

print("Validation report saved at:", OUTPUT_FILE)