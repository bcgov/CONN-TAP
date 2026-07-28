# main.py

import os
import pandas as pd

from validation import run_validation


# ==============================
# PATHS
# ==============================
BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/new_cellular_validation - Copy"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "2026_04_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "validation_report_June_2026.xlsx"
)


# ==============================
# LOAD DATA
# ==============================
print("Loading Excel file...")


df = pd.read_excel(INPUT_FILE)

print(f"Total rows loaded: {len(df)}")


# ==============================
# RUN VALIDATION
# ==============================
print("Running validations...")

results = run_validation(df)

# ==============================
# VALIDATION SUMMARY
# ==============================
print("\nValidation Summary")
print("=" * 60)

print(f"1) Duplicate Rows: {len(results['duplicates'])}")

print(f"2) Null BGE: {len(results['null_bge'])}")

print(f"3) Null SUB-BGE: {len(results['null_subbge'])}")

print(f"4) Mapping Issues: {len(results['mapping_issues'])}")

print("\n===== Mapping Issue Breakdown =====")

print(
    results['mapping_summary']
    .head(20)
)



print(f"\n6) Total Pre-Tax Amount Issues: {len(results['total_amount_pre_tax_issues'])}")
print(f"7) Total Post-Tax Amount Issues: {len(results['total_amount_post_tax_issues'])}")
print(f"8) Missing BGEs: {len(results['missing_bges'])}")
print(f"9) Missing SUB-BGEs: {len(results['missing_sub_bges'])}")
print(f"10) Unknown SUB-BGEs: {len(results['unknown_subbge'])}")
print(f"11) New BGEs: {len(results['new_bges'])}")
# ==============================
# SAVE REPORT
# ==============================
print("Saving validation report...")

with pd.ExcelWriter(OUTPUT_FILE) as writer:

    results['duplicates'].to_excel(
        writer,
        sheet_name='Duplicates',
        index=False
    )

    results['null_bge'].to_excel(
        writer,
        sheet_name='Null_BGE',
        index=False
    )
    results['null_subbge'].to_excel(
        writer,
        sheet_name='Null_SUB-BGE',
        index=False
    )
    results['missing_bges'].to_excel(
        writer,
        sheet_name='Missing_BGEs',
        index=False
    )

    results['missing_sub_bges'].to_excel(
        writer,
        sheet_name='Missing_SUB_BGEs',
        index=False
    )

    results['mapping_issues'].to_excel(
        writer,
        sheet_name='Mapping_Issues',
        index=False
    )

    results['mapping_summary'].to_excel(
        writer,
        sheet_name='Mapping_Summary',
        index=False
    )

    results['unknown_subbge'].to_excel(
        writer,
       sheet_name='Unknown_SUB-BGE',
       index=False
    )
    results['new_bges'].to_excel(
        writer,
       sheet_name='New_BGEs',
       index=False
    )
    results['total_amount_pre_tax_issues'].to_excel(
        writer,
        sheet_name='Total_Amount_Pre-Tax_Issues',
        index=False
    )

    results['total_amount_post_tax_issues'].to_excel(
        writer,
        sheet_name='Total_Amount_Post-Tax_Issues',
        index=False
    )

print("Validation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")