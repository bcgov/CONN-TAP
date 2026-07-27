# build_telus_cost_validation.py

Generates a TELUS **"pricebook cost validation"** workbook: every
`raw_data.raw_telus_spend` row that **matches** a TELUS pricebook service but
whose billed `amount` **differs** from the pricebook `monthly_fee` (higher or
lower). Output is written to `scripts/telus_cost_validation.xlsx` with **one tab
per `YYYY-MM`** (month/year) combination.

This is the cost-comparison counterpart to
[`build_telus_unmatched.py`](build_telus_unmatched.md): that script reports rows
that match **nothing**; this one reports rows that **do** match but are billed at
the wrong price.

## Usage

```bash
export DATABASE_URL=******localhost:5432/app

# All month/year combinations present in the data (one tab each):
python3 scripts/build_telus_cost_validation.py

# A single month/year (one tab):
python3 scripts/build_telus_cost_validation.py 2025-06

# Optional category exclusions (compose freely):
python3 scripts/build_telus_cost_validation.py 2025-06 --exclude-recurring
python3 scripts/build_telus_cost_validation.py 2025-06 --exclude-other-charges

# Alternate database / output path:
python3 scripts/build_telus_cost_validation.py --dsn ******host/db --output /tmp/out.xlsx
```

| Argument | Description |
|----------|-------------|
| `period` (positional, optional) | Month/year as `YYYY-MM`. Omit to build every month in the data. |
| `--dsn` | Postgres DSN. Defaults to the `DATABASE_URL` environment variable. |
| `--output` | Output `.xlsx` path (default: `scripts/telus_cost_validation.xlsx`). |
| `--exclude-recurring` | Drop rows with `statement_category = 'Recurring Service Charges'`. |
| `--exclude-other-charges` | Drop rows with `statement_category = 'Other Charges and Credits'`. |

Requires `DATABASE_URL` (or `--dsn`), `psycopg`, and `xlsxwriter`.

> **Note on the exclude flags.** In practice every cost discrepancy falls into
> exactly two categories: **Recurring Service Charges** and **Other Charges and
> Credits** (these are the only categories that carry billed service lines).
> Passing **both** flags together therefore removes **every** row and yields an
> empty report — that is expected, not a bug. Use a single flag to narrow the
> view (e.g. `--exclude-other-charges` for a recurring-only report), and run with
> no flags to see the full picture.

## Columns used

**Spend** (`raw_telus_spend`):

- `detail_description` — all matching methods.
- `amount` — the billed value compared against the pricebook cost.
- `statement_section` / `statement_category` — filtering.
- `statement_date` — determines the month tab.
- `sheet_name`, `account_number`, `service_number`, `source`, `source_id` — output only.

**Pricebooks:**

- `service_id`, `service_name`, `short_service_description`, `monthly_fee` — data +
  voice (`raw_telus_data_services_pricebook`, `raw_telus_voice_services_pricebook`).
- `service_id`, `monthly_fee` — the 4 cellular tables
  (`raw_telus_cellular_services_pricebook`,
  `raw_telus_cellular_catalog_and_price_list_pricebook`,
  `raw_telus_control_center_services_pricebook`,
  `raw_telus_cellular_mms_pricebook`).

## Matching — same logic as the unmatched report

A row is considered matched if **any** of these succeed (see
[`build_telus_unmatched.md`](build_telus_unmatched.md) for full detail):

1. **NG code → `service_id`.** `ng_data` = `^(NG[0-9]{5})`,
   `ng_any` = `^(NG[A-Z0-9]{2,6})` (both uppercased), checked against **data** and
   **voice** `service_id`s.
2. **Exact normalized text.** Normalized `detail_description` equals a normalized
   `service_name` **or** `short_service_description` in the data or voice pricebook.
3. **Cellular plan-name mapping.** A `CASE` maps GoBC/TSMA-style plan names to a
   cellular `service_id`, checked against the union of the 4 cellular tables.

Only matched rows continue to the cost comparison; unmatched rows are dropped
(they belong in the unmatched report).

## Cost comparison

Once a row is matched, the script picks the authoritative pricebook fee and
compares it to the billed `amount`.

**Choosing the pricebook fee — by precedence.** A single `detail_description`
can satisfy more than one match method, so the source is chosen in this fixed
order (first hit wins), recorded in the **Type** and **Pricebook** columns:

1. Data pricebook via NG code
2. Voice pricebook via NG code
3. Data pricebook via exact text
4. Voice pricebook via exact text
5. Cellular pricebooks via plan-name mapping

**Parsing the fee.** `monthly_fee` is stored as text (e.g. `$380.00`,
`$4,500.00`, `$ 6.49`). It is parsed by stripping whitespace, `$`, and `,`, then
requiring the result to match `^[0-9]+(\.[0-9]+)?$`. Non-numeric fees such as
`$5/SIM on all lines` or blanks parse to `NULL` and are **not comparable** — a
matched service whose fee cannot be parsed is skipped (not reported).

**Closest fee for multi-fee services.** Some services (mostly certain voice
`service_id`s) map to several distinct fees. The script compares against the fee
**closest** to the billed amount
(`min(fees, key=lambda f: abs(amount - f))`), so a legitimate alternate price is
not falsely flagged.

**Tolerance.** A row is reported only when
`|amount − pricebook_cost| >= 0.01` (one cent, `COST_TOLERANCE`). Exact matches
(and sub-cent rounding) are excluded. The sign of the difference sets the
**Discrepancy** column: `higher` when billed above cost, `lower` when below.

> **Multi-quantity lines.** A billing line covering N units of a service shows an
> `amount` of roughly N × fee and will appear as a `higher` discrepancy. This is
> inherent to line-level comparison — the report does not divide by quantity.

## Cleanup / normalization

**Pre-filter (applied before matching):**

- Drop `statement_section = 'balance forward'`.
- Drop hardware detail lines: `hardware purchase charge`,
  `device discount repayment`, `monthly telus easy payment`,
  `device discount repay. canc.`, `device discount repay. - cr`,
  `monthly easy payment`, `telus easy payment balance`, `equipment adjustment`.
- Drop categories: `taxes`, `payment`, `payments`,
  `amount due from last bill`, `usage`.
- Drop rows with a `NULL` `amount` (nothing to compare).
- Optionally drop `recurring service charges` and/or
  `other charges and credits` (via the `--exclude-*` flags).

**Text normalization** (`detail_description` and pricebook names):

- `LOWER` first, then strip `*` (detail only), then remove every character
  except `a–z`, `0–9`, and space, then `TRIM`.
- Lowercasing happens *first* so mixed-case spend text matches lowercased
  pricebook text.

**ID / fee normalization:**

- `service_id` values and NG codes are `UPPER(TRIM(...))`; blank/`NULL` ids are
  excluded from the lookup sets.
- Each pricebook lookup set aggregates its parseable fees into an array
  (`ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL)`), keeping only entries
  with at least one comparable fee.

**Month bucket:**

- `date_trunc('month', statement_date)` → one tab per `YYYY-MM`.
- Undated rows (NULL `statement_date`) go to a `no-date` tab.

## Output layout

Each tab contains one detail row per matched-but-mispriced spend record, sorted
with the largest discrepancies first, and a summed **Amount** and **Difference**
total row at the bottom:

| Statement Date | Entity | Account Number | Service Number | Source | Source ID | Statement Category | Detail Description | NG Code | Amount | Type | Pricebook | Pricebook Cost | Discrepancy | Difference |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

The five columns added over the unmatched report are:

| Column | Meaning |
|--------|---------|
| **Type** | Which pricebook family supplied the cost: `data`, `voice`, or `cellular`. |
| **Pricebook** | Specific pricebook and chosen `service_id`, e.g. `voice_services (NG001)`. |
| **Pricebook Cost** | The pricebook `monthly_fee` the amount was compared against (closest fee for multi-fee services). |
| **Discrepancy** | `higher` if billed above the pricebook cost, `lower` if below. |
| **Difference** | Signed `amount − Pricebook Cost`. |

Notes:

- Excel caps a worksheet at 1,048,576 rows. A month exceeding ~1,000,000 rows is
  split into continuation tabs (`2026-03`, `2026-03 (2)`, …).
- The workbook is written with xlsxwriter `constant_memory` mode to keep memory
  low on very large months.
- An all-months run can produce millions of rows and a very large file;
  single-month runs are much faster when only specific periods are needed.
