


# main.py

import os
import pandas as pd

from validation import run_validation


# ==============================
# PATHS
# ==============================
BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/rogers_cellular_autumate_validation"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "2026_04_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "validation_report.xlsx"
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

print(f"2) Missing BGE: {len(results['missing_bge'])}")

print(f"3) Missing SUB-BGE: {len(results['missing_subbge'])}")

print(f"4) Mapping Issues: {len(results['mapping_issues'])}")

print("\n===== Mapping Issue Breakdown =====")

print(
    results['mapping_summary']
    .head(20)
)

print(f"\n5) Unknown SUB-BGE: {len(results['unknown_subbge'])}")

print("\n===== Sample Unknown SUB-BGE =====")

print(
    results['unknown_subbge'][
        ['BGE_standardized', 'SUB-BGE']
    ]
    .drop_duplicates()
    .head(20)
)

print(f"\n6) Tax Issues: {len(results['tax_issues'])}")
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

    results['missing_bge'].to_excel(
        writer,
        sheet_name='Missing_BGE',
        index=False
    )
    results['missing_subbge'].to_excel(
        writer,
        sheet_name='Missing_SUB-BGE',
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

    results['tax_issues'].to_excel(
        writer,
        sheet_name='Tax_Issues',
        index=False
    )

print("Validation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")
=======
# main.py

import os
import pandas as pd

from validation import run_validation


# ==============================
# PATHS
# ==============================
BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/rogers_cellular_autumate_validation"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "2026_04_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "validation_report.xlsx"
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

print(f"2) Missing BGE: {len(results['missing_bge'])}")

print(f"3) Missing SUB-BGE: {len(results['missing_subbge'])}")

print(f"4) Mapping Issues: {len(results['mapping_issues'])}")

print("\n===== Mapping Issue Breakdown =====")

print(
    results['mapping_summary']
    .head(20)
)

print(f"\n5) Unknown SUB-BGE: {len(results['unknown_subbge'])}")

print("\n===== Sample Unknown SUB-BGE =====")

print(
    results['unknown_subbge'][
        ['BGE_standardized', 'SUB-BGE']
    ]
    .drop_duplicates()
    .head(20)
)

print(f"\n6) Total Amount Issues: {len(results['total_amount_issues'])}")
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

    results['missing_bge'].to_excel(
        writer,
        sheet_name='Missing_BGE',
        index=False
    )
    results['missing_subbge'].to_excel(
        writer,
        sheet_name='Missing_SUB-BGE',
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

    results['total_amount_issues'].to_excel(
        writer,
        sheet_name='Total_Amount_Issues',
        index=False
    )

print("Validation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")

=======
# main.py

import os
import pandas as pd

from validation import run_validation



# PATHS ========================

BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/rogers_cellular_autumate_validation"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "2026_04_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "validation_report.xlsx"
)



# LOAD DATA ========================

print("Loading Excel file...")


df = pd.read_excel(INPUT_FILE)

print(f"Total rows loaded: {len(df)}")



# RUN VALIDATION ====================

print("Running validations...")

results = run_validation(df)


# VALIDATION SUMMARY ==================

print("\nValidation Summary")
print("=" * 60)

print(f"1) Duplicate Rows: {len(results['duplicates'])}")

print(f"2) Missing BGE: {len(results['missing_bge'])}")

print(f"3) Missing SUB-BGE: {len(results['missing_subbge'])}")

print(f"4) Mapping Issues: {len(results['mapping_issues'])}")

print("\n===== Mapping Issue Breakdown =====")

print(
    results['mapping_summary']
    .head(20)
)

print(f"\n5) Unknown SUB-BGE: {len(results['unknown_subbge'])}")

print("\n===== Sample Unknown SUB-BGE =====")

print(
    results['unknown_subbge'][
        ['BGE_standardized', 'SUB-BGE']
    ]
    .drop_duplicates()
    .head(20)
)

print(f"\n6) Total Amount Issues: {len(results['total_amount_issues'])}")

# SAVE REPORT ===========================

print("Saving validation report...")

with pd.ExcelWriter(OUTPUT_FILE) as writer:

    results['duplicates'].to_excel(
        writer,
        sheet_name='Duplicates',
        index=False
    )

    results['missing_bge'].to_excel(
        writer,
        sheet_name='Missing_BGE',
        index=False
    )
    results['missing_subbge'].to_excel(
        writer,
        sheet_name='Missing_SUB-BGE',
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

    results['total_amount_issues'].to_excel(
        writer,
        sheet_name='Total_Amount_Issues',
        index=False
    )

print("Validation completed successfully.")
print(f"Output file: {OUTPUT_FILE
=======
# main.py

import os
import pandas as pd

from validation import run_validation



# PATHS ========================

BASE_DIR = r"C:/Users/AFATHALI/OneDrive - Government of BC/Documents/rogers_cellular_autumate_validation"

DATA_DIR = os.path.join(BASE_DIR, "Data")

INPUT_FILE = os.path.join(
    DATA_DIR,
    "2026_04_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "validation_report.xlsx"
)



# LOAD DATA ========================

print("Loading Excel file...")


df = pd.read_excel(INPUT_FILE)

print(f"Total rows loaded: {len(df)}")



# RUN VALIDATION ====================

print("Running validations...")

results = run_validation(df)


# VALIDATION SUMMARY ==================

print("\nValidation Summary")
print("=" * 60)

print(f"1) Duplicate Rows: {len(results['duplicates'])}")

print(f"2) Missing BGE: {len(results['missing_bge'])}")

print(f"3) Missing SUB-BGE: {len(results['missing_subbge'])}")

print(f"4) Mapping Issues: {len(results['mapping_issues'])}")

print("\n===== Mapping Issue Breakdown =====")

print(
    results['mapping_summary']
    .head(20)
)

print(f"\n5) Unknown SUB-BGE: {len(results['unknown_subbge'])}")

print("\n===== Sample Unknown SUB-BGE =====")

print(
    results['unknown_subbge'][
        ['BGE_report', 'SUB-BGE']
    ]
    .drop_duplicates()
    .head(20)
)

print(f"\n6) Total Amount Issues: {len(results['total_amount_issues'])}")

# SAVE REPORT ===========================

print("Saving validation report...")

with pd.ExcelWriter(OUTPUT_FILE) as writer:

    results['duplicates'].to_excel(
        writer,
        sheet_name='Duplicates',
        index=False
    )

    results['missing_bge'].to_excel(
        writer,
        sheet_name='Missing_BGE',
        index=False
    )
    results['missing_subbge'].to_excel(
        writer,
        sheet_name='Missing_SUB-BGE',
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

    results['total_amount_issues'].to_excel(
        writer,
        sheet_name='Total_Amount_Issues',
        index=False
    )

print("Validation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")
