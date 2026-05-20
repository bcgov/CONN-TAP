# utils.py
import pandas as pd

def normalize(text):
    if pd.isna(text):
        return None
    return str(text).strip().upper()