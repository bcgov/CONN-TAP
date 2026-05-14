# utils.py

import pandas as pd
import re



# NORMALIZE TEXT ====================

def normalize(text):

    if pd.isna(text):
        return None

    text = str(text).upper().strip()

    # Replace separators with spaces
    text = re.sub(r'[-_/]', ' ', text)

    # Remove punctuation except &
    text = re.sub(r'[^\w\s&]', '', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text



# COMPRESS TEXT ==========================

def compress_text(text):

    if text is None:
        return None

    text = normalize(text)

    # Remove all non-alphanumeric
    text = re.sub(r'[^A-Z0-9]', '', text)

    return text
