## What each core ingestion script does

## 1) `telus_quantities_ingestion.py`

**Purpose**  
Ingests Telus “Quantities Reports” Excel workbooks and extracts the **Monthly Services** sheets for all entities.

**Key logic**
- Identifies sheets matching: `<entity> MONTHLY SERVICES` (case-insensitive).
- Derives `entity` as the first word of the sheet name.
- Removes repeated header rows inside sheets (rows where values equal the column headers).
- Renames ambiguous columns named `TBD`, `TBD.1`, `TBD.2`, etc. based on their values:
  - If values contain `wireless data`, `wireless voice`, `wireline data`, or `wireline voice` → rename column to `Source`
  - If values contain `SRVEQUIP` or `Monthly Local Services` → rename column to `Source System`
- Adds metadata columns: `ingestion_year`, `ingestion_month`, `ingestion_ts`
- Writes a **single Parquet** file to S3.

**Inputs**
- Trigger mode (event-driven): an S3 key is passed in via `S3_KEY`, expected layout:  
  `raw/{provider}/{report_type}/{year}/{month_name}/<file>.xlsx`
- Manual mode: `YEAR`, `MONTH_NAME`, `MONTH_NUM`

**Output**
- `s3://{BUCKET}/processed/telus/quantities_reports/{YEAR}/{MONTH_NUM}/combined_{YEAR}_{MONTH_NUM}_monthly_services.parquet`

---

## 2) `telus_spend_ingestion.py`

**Purpose**  
Ingests Telus consolidated Spend Report workbooks, combines all relevant sheets, and writes a single Parquet output.

**Key logic**
- Finds the latest matching workbook under: `raw/telus/spend_reports/{YEAR}/{MONTH_NAME}/`
- Reads all sheets and skips empty sheets
- Removes repeated header rows
- Adds `entity_name` as the sheet name per row
- Adds metadata columns: `ingestion_year`, `ingestion_month`, `ingestion_ts`
- Forces all values to string to avoid schema issues
- Writes a **single Parquet** file to S3

**Output**
- `s3://{OUTPUT_BUCKET}/processed/telus/spend_reports/{YEAR}/{MONTH_NUM}/combined_{YEAR}_{MONTH_NUM}_spend_report.parquet`

---

## 3) `rogers_spend_ingestion.py`

**Purpose**  
Ingests Rogers “Usage & Spend” workbook and writes a single Parquet output.

**Key logic**
- Finds the latest workbook under: `raw/rogers/spend_reports/{YEAR}/{MONTH_NAME}/` using filename heuristics (administrator + usage + spend + year)
- Reads the `Usage_&_Spend` sheet
- Removes repeated header rows
- Adds `entity_name="Rogers"` and ingestion metadata
- Forces all values to string
- Writes a **single Parquet** file to S3

**Output**
- `s3://{OUTPUT_BUCKET}/processed/rogers/spend_reports/{YEAR}/{MONTH_NUM}/combined_{YEAR}_{MONTH_NUM}_rogers_spend_report.parquet`

---

## Pricebook scripts (Glue Studio generated)

## 4) `load-ngta-rogers-pricebook-notebook.py`, `load-ngta-telus-pricebook-notebook.py`, `load-tsma-pricebook-notebook.py`

**Purpose**  
Glue Studio generated scripts for loading and transforming telecom pricebook CSVs. These scripts typically:
- Load multiple S3 CSV inputs (Voice/Cellular/Data)
- Apply schema mappings and transformations
- Union into a single dataset
- Perform cleaning (trim, remove invisible chars, remove blanks, drop duplicates)
- Write to a target store (historically Redshift, where configured)
- Use `preactions` / `postactions` where applicable for staging and merge patterns

**Note**  
These are generated job scripts. If standardization is needed, refactor into shared helpers and remove interactive-only statements.

---

## Triggering (event-driven ingestion)

Recommended pattern implemented for NGTA:
- An S3 `ObjectCreated` event is configured on `ngta-raw-data` for:
  - `raw/telus/spend_reports/` → `lambda-ngta-telus`
  - `raw/rogers/spend_reports/` → `lambda-ngta-rogers`
  - `raw/telus/quantities_reports/` → `lambda-ngta-telus-quantities`

Each Lambda triggers its corresponding Glue job, passing expected arguments (bucket, year/month parameters, or S3 key when used).

---

## Outputs and Athena usage

Processed outputs are written in **Parquet** under the processed zone:
- `s3://ngta-raw-data/processed/...`

These can be exposed in Athena via external tables pointing to the processed prefixes.  
Some column names contain spaces, so Athena queries should use quoted identifiers where needed.

---