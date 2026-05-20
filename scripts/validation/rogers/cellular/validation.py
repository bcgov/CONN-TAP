


# validation.py

import pandas as pd

from utils import normalize, compress_text
from mappings import BGE_MAP, SUB_BGE_TO_BGE


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
COMPRESSED_SUB_BGE_TO_BGE = {
    compress_text(k): v
    for k, v in SUB_BGE_TO_BGE.items()
}


# ==============================
# VALID SUB-BGE FUNCTION
# ==============================
def is_valid_subbge(row):

    sub_bge = row['SUB-BGE_standardized']
    bge = row['BGE_standardized']

    if pd.isna(sub_bge):
        return True

    compressed_subbge = compress_text(sub_bge)
    compressed_bge = compress_text(bge)

    # Controlled mapping
    if compressed_subbge in COMPRESSED_SUB_BGE_TO_BGE:
        return True

    # Same as BGE
    if compressed_subbge == compressed_bge:
        return True

    # ECC school districts
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
    df['SUB-BGE'] = df['SUB-BGE'].apply(normalize)

    # Standardize BGE
    df['BGE_standardized'] = df['BGE'].replace(BGE_MAP)
    df['BGE_standardized'] = (
        df['BGE_standardized']
        .fillna(df['BGE'])
    )

    # Standardize SUB-BGE
    df['SUB-BGE_standardized'] = (
        df['SUB-BGE']
        .replace(BGE_MAP)
    )

    df['SUB-BGE_standardized'] = (
        df['SUB-BGE_standardized']
        .fillna(df['SUB-BGE'])
    )

    # Duplicate rows
    duplicates = df[df.duplicated()]
    # Missing BGE
    missing_bge = df[
        df['BGE_standardized'].isna()
    ]

    # Missing SUB-BGE
    missing_subbge = df[
        df['SUB-BGE'].isna()
    ]

    # Mapping validation
    df['compressed_subbge'] = (
        df['SUB-BGE']
        .apply(compress_text)
    )

    df['expected_BGE'] = (
        df['compressed_subbge']
        .map(COMPRESSED_SUB_BGE_TO_BGE)
    )

    mapping_issues = df[
        (df['expected_BGE'].notna()) &
        (
            df['BGE_standardized'] !=
            df['expected_BGE']
        )
    ]
     # Mapping summary
    mapping_summary = (
        mapping_issues
        .groupby([
            'SUB-BGE',
            'BGE_standardized',
            'expected_BGE'
        ])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # Unknown SUB-BGE
    df['valid_subbge'] = df.apply(
        is_valid_subbge,
        axis=1
    )

    unknown_subbge = df[
        (df['valid_subbge'] == False) &
        (df['SUB-BGE'].notna())
    ]
   # Tax validation
    for col in ['GST', 'PST', 'HST']:

        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['calculated_total'] = (
        df['BILLED_AMOUNT(PRE-TAX)'] +
        df['GST'] +
        df['PST'] +
        df['HST']
    )

    tolerance = 0.01

    tax_issues = df[
        (
            df['calculated_total'] -
            df['BILLED_AMOUNT(POST-TAX)']
        ).abs() > tolerance
    ]

    return {
        'duplicates': duplicates,
        'missing_bge': missing_bge,
        'missing_subbge': missing_subbge,
        'mapping_issues': mapping_issues,
        'mapping_summary': mapping_summary,
        'unknown_subbge': unknown_subbge,
        'tax_issues': tax_issues
    }
=======
# validation.py

import pandas as pd

from utils import normalize, compress_text
from mappings import BGE_MAP, SUB_BGE_TO_BGE


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
COMPRESSED_SUB_BGE_TO_BGE = {
    compress_text(k): v
    for k, v in SUB_BGE_TO_BGE.items()
}


# ==============================
# VALID SUB-BGE FUNCTION
# ==============================
def is_valid_subbge(row):

    sub_bge = row['SUB-BGE_standardized']
    bge = row['BGE_standardized']

    if pd.isna(sub_bge):
        return True

    compressed_subbge = compress_text(sub_bge)
    compressed_bge = compress_text(bge)

    # Controlled mapping
    if compressed_subbge in COMPRESSED_SUB_BGE_TO_BGE:
        return True

    # Same as BGE
    if compressed_subbge == compressed_bge:
        return True

    # ECC school districts
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
    df['SUB-BGE'] = df['SUB-BGE'].apply(normalize)

    # Standardize BGE
    df['BGE_standardized'] = df['BGE'].replace(BGE_MAP)
    df['BGE_standardized'] = (
        df['BGE_standardized']
        .fillna(df['BGE'])
    )

    # Standardize SUB-BGE
    df['SUB-BGE_standardized'] = (
        df['SUB-BGE']
        .replace(BGE_MAP)
    )

    df['SUB-BGE_standardized'] = (
        df['SUB-BGE_standardized']
        .fillna(df['SUB-BGE'])
    )

    # Duplicate rows
    duplicates = df[df.duplicated()]
    # Missing BGE
    missing_bge = df[
        df['BGE_standardized'].isna()
    ]

    # Missing SUB-BGE
    missing_subbge = df[
        df['SUB-BGE'].isna()
    ]

    # Mapping validation
    df['compressed_subbge'] = (
        df['SUB-BGE']
        .apply(compress_text)
    )

    df['expected_BGE'] = (
        df['compressed_subbge']
        .map(COMPRESSED_SUB_BGE_TO_BGE)
    )

    mapping_issues = df[
        (df['expected_BGE'].notna()) &
        (
            df['BGE_standardized'] !=
            df['expected_BGE']
        )
    ]
     # Mapping summary
    mapping_summary = (
        mapping_issues
        .groupby([
            'SUB-BGE',
            'BGE_standardized',
            'expected_BGE'
        ])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # Unknown SUB-BGE
    df['valid_subbge'] = df.apply(
        is_valid_subbge,
        axis=1
    )

    unknown_subbge = df[
        (df['valid_subbge'] == False) &
        (df['SUB-BGE'].notna())
    ]
   # Total Amount validation
    for col in ['GST', 'PST', 'HST']:

        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['calculated_total'] = (
        df['BILLED_AMOUNT(PRE-TAX)'] +
        df['GST'] +
        df['PST'] +
        df['HST']
    )

    tolerance = 0.01

    total_amount_issues = df[
        (
            df['calculated_total'] -
            df['BILLED_AMOUNT(POST-TAX)']
        ).abs() > tolerance
    ]

    return {
        'duplicates': duplicates,
        'missing_bge': missing_bge,
        'missing_subbge': missing_subbge,
        'mapping_issues': mapping_issues,
        'mapping_summary': mapping_summary,
        'unknown_subbge': unknown_subbge,
        'total_amount_issues': total_amount_issues
    }

=======
# validation.py

import pandas as pd

from utils import normalize, compress_text
from mappings import BGE_MAP, SUB_BGE_TO_BGE



# NORMALIZE MAPPINGS ===========

BGE_MAP = {
    normalize(k): normalize(v)
    for k, v in BGE_MAP.items()
}

SUB_BGE_TO_BGE = {
    normalize(k): normalize(v)
    for k, v in SUB_BGE_TO_BGE.items()
}



# COMPRESSED MAPPINGS =========

COMPRESSED_SUB_BGE_TO_BGE = {
    compress_text(k): v
    for k, v in SUB_BGE_TO_BGE.items()
}



# VALID SUB-BGE FUNCTION ===========

def is_valid_subbge(row):

    sub_bge = row['SUB-BGE_standardized']
    bge = row['BGE_standardized']

    if pd.isna(sub_bge):
        return True

    compressed_subbge = compress_text(sub_bge)
    compressed_bge = compress_text(bge)

    # Controlled mapping
    if compressed_subbge in COMPRESSED_SUB_BGE_TO_BGE:
        return True

    # Same as BGE
    if compressed_subbge == compressed_bge:
        return True

    # ECC school districts
    if sub_bge.startswith("SCHOOL DISTRICT"):
        return True

    if sub_bge.startswith("DISTRICT"):
        return True

    return False

# MAIN VALIDATION FUNCTION ================

def run_validation(df):

    # Normalize columns
    df['BGE'] = df['BGE'].apply(normalize)
    df['SUB-BGE'] = df['SUB-BGE'].apply(normalize)

    # Standardize BGE
    df['BGE_standardized'] = df['BGE'].replace(BGE_MAP)
    df['BGE_standardized'] = (
        df['BGE_standardized']
        .fillna(df['BGE'])
    )

    # Standardize SUB-BGE
    df['SUB-BGE_standardized'] = (
        df['SUB-BGE']
        .replace(BGE_MAP)
    )

    df['SUB-BGE_standardized'] = (
        df['SUB-BGE_standardized']
        .fillna(df['SUB-BGE'])
    )

    # Duplicate rows
    duplicates = df[df.duplicated()]
    # Missing BGE
    missing_bge = df[
        df['BGE_standardized'].isna()
    ]

    # Missing SUB-BGE
    missing_subbge = df[
        df['SUB-BGE'].isna()
    ]

    # Mapping validation
    df['compressed_subbge'] = (
        df['SUB-BGE']
        .apply(compress_text)
    )

    df['expected_BGE'] = (
        df['compressed_subbge']
        .map(COMPRESSED_SUB_BGE_TO_BGE)
    )

    mapping_issues = df[
        (df['expected_BGE'].notna()) &
        (
            df['BGE_standardized'] !=
            df['expected_BGE']
        )
    ]
     # Mapping summary
    mapping_summary = (
        mapping_issues
        .groupby([
            'SUB-BGE',
            'BGE_standardized',
            'expected_BGE'
        ])
        .size()
        .reset_index(name='count')
        .sort_values(by='count', ascending=False)
    )

    # Unknown SUB-BGE
    df['valid_subbge'] = df.apply(
        is_valid_subbge,
        axis=1
    )

    unknown_subbge = df[
        (df['valid_subbge'] == False) &
        (df['SUB-BGE'].notna())
    ]
   # Total Amount validation
    for col in ['GST', 'PST', 'HST']:

        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['calculated_total'] = (
        df['BILLED_AMOUNT(PRE-TAX)'] +
        df['GST'] +
        df['PST'] +
        df['HST']
    )

    tolerance = 0.01

    total_amount_issues = df[
        (
            df['calculated_total'] -
            df['BILLED_AMOUNT(POST-TAX)']
        ).abs() > tolerance
    ]

    return {
        'duplicates': duplicates,
        'missing_bge': missing_bge,
        'missing_subbge': missing_subbge,
        'mapping_issues': mapping_issues,
        'mapping_summary': mapping_summary,
        'unknown_subbge': unknown_subbge,
        'total_amount_issues': total_amount_issues
    }
=======
# validation.py

import pandas as pd

from utils import normalize, compress_text
from mappings import BGE_MAP, SUB_BGE_TO_BGE



# NORMALIZE MAPPINGS ===========

BGE_MAP = {
    normalize(k): normalize(v)
    for k, v in BGE_MAP.items()
}

SUB_BGE_TO_BGE = {
    normalize(k): normalize(v)
    for k, v in SUB_BGE_TO_BGE.items()
}



# COMPRESSED MAPPINGS =========

COMPRESSED_SUB_BGE_TO_BGE = {
    compress_text(k): v
    for k, v in SUB_BGE_TO_BGE.items()
}



# VALID SUB-BGE FUNCTION ===========

def is_valid_subbge(row):

    sub_bge = row['SUB-BGE_report']
    bge = row['BGE_report']

    if pd.isna(sub_bge):
        return True

    compressed_subbge = compress_text(sub_bge)
    compressed_bge = compress_text(bge)

    # Controlled mapping
    if compressed_subbge in COMPRESSED_SUB_BGE_TO_BGE:
        return True

    # Same as BGE
    if compressed_subbge == compressed_bge:
        return True

    # ECC school districts
    if sub_bge.startswith("SCHOOL DISTRICT"):
        return True

    if sub_bge.startswith("DISTRICT"):
        return True

    return False

# MAIN VALIDATION FUNCTION ================

def run_validation(df):

    # Normalize columns
    df['BGE'] = df['BGE'].apply(normalize)
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
    # Missing BGE
    missing_bge = df[
        df['BGE_report'].isna()
    ]

    # Missing SUB-BGE
    missing_subbge = df[
        df['SUB-BGE'].isna()
    ]

    # Mapping validation
    df['compressed_subbge'] = (
        df['SUB-BGE']
        .apply(compress_text)
    )

    df['expected_BGE'] = (
        df['compressed_subbge']
        .map(COMPRESSED_SUB_BGE_TO_BGE)
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
    df['valid_subbge'] = df.apply(
        is_valid_subbge,
        axis=1
    )

    unknown_subbge = df[
        (df['valid_subbge'] == False) &
        (df['SUB-BGE'].notna())
    ]
   # Total Amount validation
    for col in ['GST', 'PST', 'HST']:

        if col in df.columns:
            df[col] = df[col].fillna(0)

    df['calculated_total'] = (
        df['BILLED_AMOUNT(PRE-TAX)'] +
        df['GST'] +
        df['PST'] +
        df['HST']
    )

    tolerance = 0.01

    total_amount_issues = df[
        (
            df['calculated_total'] -
            df['BILLED_AMOUNT(POST-TAX)']
        ).abs() > tolerance
    ]

    return {
        'duplicates': duplicates,
        'missing_bge': missing_bge,
        'missing_subbge': missing_subbge,
        'mapping_issues': mapping_issues,
        'mapping_summary': mapping_summary,
        'unknown_subbge': unknown_subbge,
        'total_amount_issues': total_amount_issues
    }
