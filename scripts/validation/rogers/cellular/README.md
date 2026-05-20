# Rogers Cellular Validation Project

## Overview

This project validates monthly Rogers NGTA cellular reports using Python.

The validation process checks data quality, mapping consistency, and total calculations before reports are used for analysis or loaded into databases.

The project is designed to be:
- Easy to maintain
- Team-friendly
- GitHub-ready
- Scalable for future PostgreSQL/database integration

---

# Project Structure

```text
rogers_cellular_autumate_validation/
│
├── main.py
├── validation.py
├── utils.py
├── mappings.py
├── README.md
│
└── Data/
    ├── input_file.xlsx
    └── validation_report.xlsx
```
---

## Validation Checks

### 1. Duplicate Records
Identifies fully duplicated rows in the dataset.

### 2. Missing BGE
Detects records where the **BGE** field is missing or null.

### 3. Missing SUB-BGE
Detects records where the **SUB-BGE** field is missing or null.

### 4. SUB-BGE to BGE Mapping Validation
Validates whether each **SUB-BGE** is correctly mapped to its corresponding **BGE**.

Example rules:
- POWERTECH → BC HYDRO  
- BC MIN HEALTH → GOV BC  

### 5. Unknown SUB-BGE Values
Flags SUB-BGE values that are not defined in the mapping dictionary.

The validation is resilient to:
- Case differences
- Extra spaces
- Special characters (e.g., dashes)
- Minor formatting inconsistencies

### 6. Total Calculation Validation

Ensures:

```

BILLED\_AMOUNT (PRE-TAX) + GST + PST + HST = BILLED\_AMOUNT (POST-TAX)
```

## Output

The validation generates an Excel report:

```
validation_report.xlsx
```

### Report Sheets

| Sheet Name        | Description                                |
|------------------|--------------------------------------------|
| Duplicates        | Fully duplicated records                   |
| Missing_BGE       | Missing BGE values                         |
| Missing_SUB-BGE   | Missing SUB-BGE values                     |
| Mapping_Issues    | Incorrect SUB-BGE → BGE mappings           |
| Mapping_Summary   | Summary of mapping issues                  |
| Unknown_SUB-BGE   | Unrecognized SUB-BGE values                |
| Total_Amount_Issues        | Total calculation discrepancies              |

---

## Mapping Management

All mapping logic is stored in:

```
mappings.py
```

Includes:
- BGE_MAP
- SUB_BGE_TO_BGE

This allows updates without modifying validation logic.

---

## Utilities

Helper functions are stored in:

```
utils.py
```

Examples:
- Text normalization
- Standardization
- Data cleaning utilities

---

## Core Validation Logic

Implemented in:

```
validation.py
```

Handles:
- Data quality checks
- Mapping validation
- Unknown SUB-BGE detection
- Ttotal Amount validation

---

## Main Entry Point

The application starts from:

```
main.py
```

Responsibilities:
- Load input Excel data
- Run validations
- Generate report
- Print summary
```
