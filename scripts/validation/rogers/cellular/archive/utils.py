# utils.py
import pandas as pd
import re


# ==============================
# NORMALIZE TEXT
# ==============================
def normalize(text):

    if pd.isna(text):
        return None

    text = str(text).upper().strip()
    # unify symbols
    text = text.replace("&", "AND")
    # Replace separators with spaces
    text = re.sub(r'[-_/]', ' ', text)

    # Remove punctuation except &
    text = re.sub(r'[^\w\s&]', '', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # collapse spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ==============================
# COMPRESS TEXT
# ==============================
def compress_text(text):

    if text is None:
        return None

    text = normalize(text)
    text = str(text).upper().strip()

    # Standardize ministry names
    text = text.replace("MINISTRY OF", "BC MIN")

    # Standardize AND/&
    text = text.replace("&", "AND")
    # Remove all non-alphanumeric
    text = re.sub(r'[^A-Z0-9]', '', text)

    return text