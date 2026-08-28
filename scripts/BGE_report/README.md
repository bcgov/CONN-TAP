# Telecom Spend Dashboard Generator

## Purpose

This Python script generates a telecom spend dashboard workbook from the monthly source file.

The purpose of the solution is to visualize telecom spend across all BC Government Business Group Entities (BGEs) and provide interactive dashboards for analyzing spend trends by:

- BGE
- Service Category
- Provider
- Month

The script uses the source telecom spend data and automatically creates dashboard sheets, summary tables, and charts for reporting and analysis.

---

# Input File

The script reads data from:

```text
spend_tracking_2026_07_03_0826AM.xlsx
```

The source workbook must contain:

```text
Sheet1
```

which holds the telecom spend data.

The source sheet is preserved exactly as provided, including:

- Formatting
- Colours
- Column widths
- Row heights
- Merged cells
- Filters
- Freeze panes

---

# Output File

The script generates:

```text
Telecom_Dashboard_Report.xlsx
```

---

# How to Run

## 1. Install Python

Required:

```text
Python 3.10+
```

---

## 2. Install Required Package

```bash
pip install openpyxl
```

---

## 3. Place Source File

Copy the source workbook:

```text
spend_tracking_2026_07_03_0826AM.xlsx
```

into the same folder as the script.

---

## 4. Run Script

```bash
python update_bge_category_dashboard_full_with_dropdown_fixes.py
```

---

## 5. Output

After successful execution:

```text
Telecom_Dashboard_Report.xlsx
```

will be created.

---

# Output Worksheets

The report workbook contains the following primary reporting sheets.

---

## Sheet1

### Purpose

Contains the original telecom spend source data.

---

## BGE_Dashboard

### Purpose

Provides a high-level spend view by BGE.

### Features

BGE Selector:

```text
Dropdown list of BGEs
```

Users can select a BGE and automatically update:

### Table 1

Monthly spend for selected BGE.

Columns:

```text
Month
Grand Total
Cellular
Data
Voice
```

### Chart 1

Selected BGE Monthly Spend 

Chart Type:

```text
Line Chart
```

Displays:

- Grand Total
- Cellular
- Data
- Voice

---

### Table 2

All BGEs Roll-up Summary

Columns:

```text
Month
Grand Total
Telus Total
Rogers Total
```

### Chart 2

All BGEs Monthly Spend 

Chart Type:

```text
Line Chart
```

Displays:

- Grand Total
- Telus Total
- Rogers Total

---

## BGE_Category_Dashboard

### Purpose

Provides detailed spend analysis by category and provider.

### Features

BGE Selector:

```text
Dropdown list of BGEs
```

---

### Table 1

Service Category Summary

Columns:

```text
Month
Cellular
Data
Voice
Cellular Plan
Cellular H/W
```

### Chart 1

Monthly Spend by Service Category

Chart Type:

```text
Stacked Bar Chart
```

Displays:

- Cellular
- Data
- Voice
- Cellular Plan
- Cellular H/W

for each month.

---

### Table 2

Provider Category Detail

Breaks spend into:

```text
Telus
Rogers
```

categories.

### Chart 2

Provider Category Trend

Chart Type:

```text
Line Chart
```

Displays monthly trend lines for:

```text
Cellular (Telus)
Data (Telus)
Voice (Telus)

Cellular Plan (Telus)
Cellular H/W (Telus)

Data (Rogers)
Voice (Rogers)

Cellular Plan (Rogers)
Cellular H/W (Rogers)
```

---

## GovBC_Stacked_bar_charts

### Purpose

Provides a detailed telecom spend view specifically for the:

```text
Gov BC
```

BGE.

---

### Section 1 - Cellular

Table includes:

```text
Month
Cellular (TSMA + TSMA Lite)
TELUS NGTA Cellular Plan
TELUS NGTA Cellular H/W
Rogers NGTA Cellular Plan
Rogers NGTA Cellular H/W
```

#### Chart 1

Gov BC Cellular Monthly Spend

Chart Type:

```text
Stacked Bar Chart
```

Shows:

```text
Cellular Plan
vs
Cellular H/W
```

---

#### Chart 2

Cellular Component Trend

Chart Type:

```text
Line Chart
```

Displays all cellular spend components.

---

### Section 2 - Data

Table includes:

```text
Month
Data (TSMA + TSMA Lite)
Data (TELUS NGTA)
Data (Rogers NGTA)
```

#### Chart

Chart Type:

```text
Stacked Bar Chart
```

Shows:

```text
Telus Data
vs
Rogers Data
```

---

### Section 3 - Voice

Table includes:

```text
Month
Voice (TSMA + TSMA Lite)
Voice (TELUS NGTA)
Voice (Rogers NGTA)
```

#### Chart

Chart Type:

```text
Stacked Bar Chart
```

Shows:

```text
Telus Voice
vs
Rogers Voice
```

---

# Supporting Worksheets

## BGE_List

Contains the list of available BGEs used by dashboard dropdown selections.

---

## BGE_Category_Detail_Data

Intermediate calculation sheet used by dashboard tables and charts.

This sheet should not be edited manually.

---

# Business Rules

The report follows these rules:

### Voice-IVR

```text
Voice-IVR is rolled into Voice.
```

### Provider Rollups

Telus Total:

```text
TSMA
+
TSMA Lite
+
TELUS NGTA
```

Rogers Total:

```text
Rogers NGTA
```

### Out of Scope

```text
Excluded from dashboard visualizations unless specifically reported.
```

---

# Maintenance

When a new month is added to the source workbook:

1. Update source file.
2. Save workbook.
3. Run script.
4. Generate updated dashboard report.

No dashboard modifications are required.