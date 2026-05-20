# 📊 Data Validation Pipeline (Python + Pandas)

This project is a modular data validation framework built in Python using Pandas.  
It validates telecom billing data and generates an Excel report with detailed issue breakdowns and a summary sheet.

---

## Project Structure

validation-project/

├── main.py              # Entry point (runs full pipeline)
├── validation.py        # All validation logic (checks & rules)
├── mapping.py           # Business mappings & constants
├── utils.py             # Helper functions (normalization)
├── requirements.txt     # Dependencies
└── README.md

---

## Features

This pipeline performs automated data quality checks:

### Data Standardization
- Normalizes text fields (BGE, SUB_BGE, PRODUCTLINE)
- Applies business mapping rules

### Validation Checks
- Duplicate detection (full row match)
- Missing BGE values
- Missing SUB_BGE values
- SUB_BGE → BGE mapping validation
- PRODUCTLINE validation
- Pre-tax calculation validation
- Post-tax calculation validation

### Reporting
Generates an Excel report with:
- Detailed issue sheets per validation type
- Executive summary sheet (PASS / FAIL status)

---

## Output Report Structure

| Sheet Name | Description |
|------------|-------------|
| Duplicates | Fully duplicated rows |
| Missing_BGE | Records with missing BGE |
| Missing_SUB_BGE | Records with missing SUB_BGE |
| Mapping_Issues | SUB_BGE vs expected BGE mismatches |
| Productline_Issues | Invalid product line values |
| Pre_Tax_Issues | Pre-tax calculation mismatches |
| Post_Tax_Issues | Post-tax calculation mismatches |
| Summary | High-level validation results |

---

## ▶How to Run

### Install dependencies
pip install pandas openpyxl

### Run pipeline
python main.py


## Configuration

Update paths in main.py:
folder_path = r"YOUR_PATH"
input_file = "input.xlsx"
output_file = "output.xlsx"


## Summary Output Example

| Check Name | Issue Count | Status |
|------------|-------------|--------|
| Duplicates | 1240 | FAIL |
| Missing BGE | 0 | PASS |


