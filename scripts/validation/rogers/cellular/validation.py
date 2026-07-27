# validation.py

import pandas as pd

def canonical_subbge(value):

    value = normalize(value)

    if value is None:
        return None

    return SUB_BGE_ALIASES.get(value, value)

from utils import normalize, compress_text
from mapping import (
    BGE_MAP,
    SUB_BGE_TO_BGE,
    SUB_BGE_ALIASES
)

# ==============================
# NORMALIZE MAPPINGS
# ==============================
BGE_MAP = {
    normalize(k): normalize(v)
    for k, v in BGE_MAP.items()
}

SUB_BGE_TO_BGE = {
    normalize(k): normalize(v)
    for k, v in SUB_BGE_TO_BGE.items()
}


# ==============================
# COMPRESSED MAPPINGS
# ==============================
#COMPRESSED_SUB_BGE_TO_BGE = {
#    compress_text(k): v
#    for k, v in SUB_BGE_TO_BGE.items()
#}


# ==============================
# VALID SUB-BGE FUNCTION
# ==============================
def is_valid_subbge(row):

    sub_bge = canonical_subbge(row['SUB-BGE_report'])
    bge = row['BGE_report']

    if pd.isna(sub_bge):
        return True

    # Valid SUB-BGE in controlled mapping
    if sub_bge in SUB_BGE_TO_BGE:
        return True

    # Same as BGE
    if sub_bge == bge:
        return True

    # ECC School Districts
    if sub_bge.startswith("SCHOOL DISTRICT"):
        return True

    if sub_bge.startswith("DISTRICT"):
        return True

    return False
# ==============================
# MAIN VALIDATION FUNCTION
# ==============================
def run_validation(df):

    # Normalize columns
    df['BGE'] = df['BGE'].apply(normalize)
    df["SUB-BGE_CANONICAL"] = (
    df["SUB-BGE"]
        .apply(canonical_subbge)
    )
    df['SUB-BGE'] = df['SUB-BGE'].apply(normalize)

    # Standardize BGE
    df['BGE_report'] = df['BGE'].replace(BGE_MAP)
    df['BGE_report'] = (
        df['BGE_report']
        .fillna(df['BGE'])
    )

    # Standardize SUB-BGE
    df['SUB-BGE_report'] = (
        df['SUB-BGE']
        .replace(BGE_MAP)
    )

    df['SUB-BGE_report'] = (
        df['SUB-BGE_report']
        .fillna(df['SUB-BGE'])
    )

    # Duplicate rows
    duplicates = df[df.duplicated()]
    # Null BGE
    null_bge = df[
        df['BGE_report'].isna()
    ]

    # Null SUB-BGE
    null_subbge = df[
        df['SUB-BGE'].isna()
    ]
    print(df['SUB-BGE'].isna().sum())
    
    # Expected BGEs from mapping
    expected_bges = set(BGE_MAP.values())

    # BGEs found in report
    df['BGE_NORMALIZED'] = (
       df['BGE']
       .dropna()
       .astype(str)
       .str.strip()
       .str.upper()
        .map(BGE_MAP)   # convert report values → canonical values
    ) 
    report_bges = set(df['BGE_NORMALIZED'].dropna())
    missing_bges = sorted(expected_bges - report_bges)

    missing_bges_df = pd.DataFrame({
        'Missing_BGE': missing_bges
    })

    # ==========================================
    # New / Unknown BGE Validation
    # ==========================================

    # Valid BGEs (your 13 canonical BGEs)
    valid_bges = set(BGE_MAP.values())

    # BGEs found in report after standardization
    report_bges_standardized = set(
        df['BGE_report']
        .dropna()
    )

    # New BGEs found in report but not in mapping
    new_bges = sorted(
        report_bges_standardized - valid_bges
    )

    new_bges_df = pd.DataFrame({
         'New_BGE': new_bges
    })

    # Expected SUB-BGEs from mapping (compressed)
    expected_sub_bges = set(SUB_BGE_TO_BGE.keys())

    report_sub_bges = set(
      df["SUB-BGE_CANONICAL"]
        .dropna()
    )

    # Missing SUB-BGEs (compressed comparison)
    missing_sub_bges= (
        expected_sub_bges - report_sub_bges
    )

    # Lookup compressed value -> original SUB-BGE
    lookup = {
    k: {
        "original_sub_bge": k,
        "related_bge": v
    }
    for k, v in SUB_BGE_TO_BGE.items()
    }

# Create report dataframe
    missing_sub_bges_df = pd.DataFrame([
      {
        "Related_BGE": lookup[sub_bge]["related_bge"],
        "Missing_SUB_BGE": lookup[sub_bge]["original_sub_bge"]
      }
      for sub_bge in sorted(missing_sub_bges)
    ])
    
    
    # Mapping validation
    df["expected_BGE"] = (
       df["SUB-BGE_CANONICAL"]
        .map(SUB_BGE_TO_BGE)
    )

    mapping_issues = df[
        (df['expected_BGE'].notna()) &
        (
            df['BGE_report'] !=
            df['expected_BGE']
        )
    ]
     # Mapping summary
    mapping_summary = (
        mapping_issues
        .groupby([
            'SUB-BGE',
            'BGE_report',
            'expected_BGE'
        ])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # Unknown SUB-BGE
    # Valid SUB-BGEs from mapping

    valid_sub_bges = set(SUB_BGE_TO_BGE.keys())

    # Valid BGE names and aliases
    valid_bge_names = set(BGE_MAP.keys()) | set(BGE_MAP.values())

    # SUB-BGEs found in report
    report_sub_bges = set(
      df["SUB-BGE_CANONICAL"]
        .dropna()
    )

    # New SUB-BGEs:
    # - not in SUB_BGE mapping
    # - not a valid BGE name
    new_sub_bges = sorted(
      sub_bge
       for sub_bge in report_sub_bges
       if sub_bge not in valid_sub_bges
       and sub_bge not in valid_bge_names
       and "SCHOOL DISTRICT" not in sub_bge
       and not sub_bge.startswith("DISTRICT")
    )

    unknown_subbge = pd.DataFrame({
      'Unknown_SUB_BGE': new_sub_bges
   })


   # Total amount validation
    for col in ['GST', 'PST', 'HST']:

        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['calculated_BILLED_AMOUNT(PRE-TAX)'] = (
        df['BILLED_AMOUNT(POST-TAX)'] -
        df['GST'] -
        df['PST'] -
        df['HST']
    )

    tolerance = 0.01

    total_amount_pre_tax_issues = df[
        (
            df['calculated_BILLED_AMOUNT(PRE-TAX)'] -
            df['BILLED_AMOUNT(PRE-TAX)']
        ).abs() > tolerance
    ]


    df['calculated_BILLED_AMOUNT(POST-TAX)'] = (
        df['BILLED_AMOUNT(PRE-TAX)'] +
        df['GST'] +
        df['PST'] +
        df['HST']
    )

    tolerance = 0.01

    total_amount_post_tax_issues = df[
        (
            df['calculated_BILLED_AMOUNT(POST-TAX)'] -
            df['BILLED_AMOUNT(POST-TAX)']
        ).abs() > tolerance
    ]

    return {
      'duplicates': duplicates,
      'null_bge': null_bge,
      'null_subbge': null_subbge,
      'missing_bges': missing_bges_df,
      'new_bges': new_bges_df,
      'missing_sub_bges': missing_sub_bges_df,
      'mapping_issues': mapping_issues,
      'mapping_summary': mapping_summary,
      'unknown_subbge': unknown_subbge,
      'total_amount_pre_tax_issues': total_amount_pre_tax_issues,
      'total_amount_post_tax_issues': total_amount_post_tax_issues,
   }