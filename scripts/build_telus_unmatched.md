# build_telus_unmatched.py

Generates a TELUS **"unmatched services"** workbook: every
`raw_data.raw_telus_spend` row that does **not** match any service in the TELUS
pricebook tables, written to `scripts/telus_unmatched_spend.xlsx` with **one tab
per `YYYY-MM`** (month/year) combination.

## Usage

```bash
export DATABASE_URL=postgresql://app:app@localhost:5432/app

# All month/year combinations present in the data (one tab each):
python3 scripts/build_telus_unmatched.py

# A single month/year (one tab):
python3 scripts/build_telus_unmatched.py 2025-06

# Exclude specific statement categories (compose freely):
python3 scripts/build_telus_unmatched.py 2025-06 --exclude-recurring
python3 scripts/build_telus_unmatched.py 2025-06 --exclude-other-charges
python3 scripts/build_telus_unmatched.py 2025-06 --exclude-recurring --exclude-other-charges

# Alternate database / output path:
python3 scripts/build_telus_unmatched.py --dsn postgresql://user:pw@host/db --output /tmp/out.xlsx
```

| Argument | Description |
|----------|-------------|
| `period` (positional, optional) | Month/year as `YYYY-MM`. Omit to build every month in the data. |
| `--dsn` | Postgres DSN. Defaults to the `DATABASE_URL` environment variable. |
| `--output` | Output `.xlsx` path (default: `scripts/telus_unmatched_spend.xlsx`). |
| `--exclude-recurring` | Also drop rows with `statement_category = 'Recurring Service Charges'`. |
| `--exclude-other-charges` | Also drop rows with `statement_category = 'Other Charges and Credits'`. |

Requires `DATABASE_URL` (or `--dsn`), `psycopg`, and `xlsxwriter`.

Reference logic lives in
`scripts/validation/telus/classification_exploration` (scripts 03/04/05/07),
with the normalization made case-robust here.

## Columns used

**Spend** (`raw_telus_spend`):

- `detail_description` — all matching methods.
- `source_id` / `source` / `statement_section` / `statement_category` — filtering.
- `statement_date` — determines the month tab.
- `sheet_name`, `account_number`, `service_number`, `amount` — output only.

**Pricebooks:**

- `service_id`, `service_name`, `short_service_description` — data + voice
  (`raw_telus_data_services_pricebook`, `raw_telus_voice_services_pricebook`).
- `service_id` only — the 4 cellular tables
  (`raw_telus_cellular_services_pricebook`,
  `raw_telus_cellular_catalog_and_price_list_pricebook`,
  `raw_telus_control_center_services_pricebook`,
  `raw_telus_cellular_mms_pricebook`).

## Matching — a row matches if ANY of these succeed

1. **NG code → `service_id`.** Extracts an NG code from the *start* of
   `detail_description`:
   - `ng_data` = `^(NG[0-9]{5})`, `ng_any` = `^(NG[A-Z0-9]{2,6})`, both uppercased.
   - Matches if `ng_data` or `ng_any` is a **data** `service_id`, or `ng_any` is
     a **voice** `service_id`.
2. **Exact normalized text.** Normalized `detail_description` equals a normalized
   `service_name` **or** `short_service_description` in the data or voice pricebook.
3. **Cellular plan-name mapping.** A `CASE` maps GoBC/TSMA-style plan names
   (e.g. `GoBC Data 5GB` → `XPTMHS5GB`, plus Visual Voicemail, Static IP, Network
   Priority, Vacation Disconnect, etc.) to a cellular `service_id`, checked
   against the union of the 4 cellular tables.

A row is **unmatched** when none of the above succeed. The check is implemented
with NULL-safe `EXISTS` subqueries — an earlier `IN (...)` version silently
dropped every row because some pricebook sets contained `NULL` values (in SQL,
`x IN (set containing NULL)` returns `NULL`, not `FALSE`).

## Cleanup / normalization

**Pre-filter (applied before matching):**

- Drop `statement_section = 'balance forward'`.
- Drop hardware detail lines: `hardware purchase charge`,
  `device discount repayment`, `monthly telus easy payment`,
  `device discount repay. canc.`, `device discount repay. - cr`,
  `monthly easy payment`, `telus easy payment balance`, `equipment adjustment`.
- Drop categories: `taxes`, `payment`, `payments`,
  `amount due from last bill`, `usage`.
- Optionally drop `recurring service charges` and/or
  `other charges and credits` (via the `--exclude-*` flags).

**Text normalization** (`detail_description` and pricebook names):

- `LOWER` first, then strip `*` (detail only), then remove every character
  except `a–z`, `0–9`, and space, then `TRIM`.
- Lowercasing happens *first* so mixed-case spend text matches lowercased
  pricebook text.
- `NULL`/empty entries are removed from the name and cellular-id sets.

**ID normalization:**

- `service_id` values and NG codes are `UPPER(TRIM(...))`.
- Blank/`NULL` ids are excluded from the lookup sets.

**Month bucket:**

- `date_trunc('month', statement_date)` → one tab per `YYYY-MM`.
- Undated rows (NULL `statement_date`) go to a `no-date` tab.

## Output layout

Each tab contains one detail row per unmatched spend record, with a summed
**Amount** total row at the bottom:

| Statement Date | Entity | Account Number | Service Number | Source | Source ID | Statement Category | Detail Description | NG Code | Amount |
|---|---|---|---|---|---|---|---|---|---|

Notes:

- Excel caps a worksheet at 1,048,576 rows. A month exceeding ~1,000,000
  unmatched rows is split into continuation tabs (`2026-03`, `2026-03 (2)`, …).
- The workbook is written with xlsxwriter `constant_memory` mode to keep memory
  low on very large months.
- An all-months run can produce millions of rows and a very large file;
  single-month runs are much faster when only specific periods are needed.
