# validation.py

import pandas as pd
from utils import normalize
from mapping import BGE_MAP, SUB_BGE_TO_BGE, VALID_PRODUCTLINE, TOLERANCE


def prepare_data(df):
    df = df.copy()

    df["BGE"] = df["BGE"].apply(normalize)
    df["SUB_BGE"] = df["SUB_BGE"].apply(normalize)
    df["PRODUCTLINE"] = df["PRODUCTLINE"].apply(normalize)

    df["BGE_actual"] = df["BGE"].replace(BGE_MAP).fillna(df["BGE"])
    return df


def find_duplicates(df):
    df_dup = df.copy()

    for col in df_dup.columns:
        df_dup[col] = df_dup[col].astype(str).str.strip()

    grouped = (
        df_dup.groupby(list(df_dup.columns))
        .size()
        .reset_index(name="duplicate_count")
    )

    grouped = grouped[grouped["duplicate_count"] > 1]

    if grouped.empty:
        return pd.DataFrame()

    return df.merge(grouped.drop(columns=["duplicate_count"]), how="inner")


def find_missing_bge(df):
    return df[df["BGE_actual"].isna()]


def find_missing_sub_bge(df):
    return df[df["SUB_BGE"].isna()]


def find_mapping_issues(df):
    df = df.copy()
    df["expected_BGE"] = df["SUB_BGE"].map(SUB_BGE_TO_BGE)

    return df[
        df["expected_BGE"].notna()
        & (df["expected_BGE"] != df["BGE_actual"])
    ]


def find_productline_issues(df):
    df = df.copy()

    df["PRODUCTLINE"] = df["PRODUCTLINE"].replace(
        {None: "N/A", "": "N/A", "NULL": "N/A", "NAN": "N/A"}
    )

    return df[
        df["PRODUCTLINE"].isna()
        | (~df["PRODUCTLINE"].isin(VALID_PRODUCTLINE))
    ]


def find_pre_tax_issues(df):
    df = df.copy()

    for col in ["GST", "PST"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    df["calculated_pre_tax"] = (
        df["TOTALAMOUNT"] - df["GST"] - df["PST"]
    )

    return df[
        (df["calculated_pre_tax"] - df["BILLED_AMOUNT(PRE-TAX)"]).abs()
        > TOLERANCE
    ]


def find_post_tax_issues(df):
    df = df.copy()

    df["calculated_totalamount"] = (
        df["BILLED_AMOUNT(PRE-TAX)"] + df["GST"] + df["PST"]
    )

    return df[
        (df["calculated_totalamount"] - df["TOTALAMOUNT"]).abs()
        > TOLERANCE
    ]