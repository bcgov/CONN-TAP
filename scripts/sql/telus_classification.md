## Confirmed source IDs

| source_id | Meaning | Bucket | Source |
| --- | --- | --- | --- |
| `1001` | Pure Fibre charges not billed on the monthly voice bill | **Data** | Telus: "Pure Fibre is a voice over IP product but it is defined as DATA not VOICE in the NGTA catalogue." (corrects an earlier internal note that had called it Voice) |
| `103` | Wireline data | Data | Existing NGTA reference data |
| `104` | ICE Anywhere | Voice | Telus confirmation |
| `102` | Wireline voice | Voice | Existing NGTA reference data |
| `106` | TC2 monthly charges and some professional charges | Voice | Telus confirmation |
| `164` | Cellular one-time equipment charges | **Cellular Hardware** | Telus confirmation — previously bucketed as Cellular Plans; corrected 2026-08-28 |
| `130` | Wireless / cellular plans | Cellular Plans | Existing NGTA reference data |

## Spend classification order

The spend report, month-over-month comparison, and dbt Telus model apply these
rules to normalized text and source IDs:

1. Exclude balance-forward sections, known tax descriptions, and rows without a
   statement month.
2. Exclude the categories `payment`, `payments`, `amount due from last bill`, and
   `taxes`. These exclusions also apply to hardware descriptions and source ID 164.
3. Classify source ID 164 as Cellular Hardware, regardless of description.
4. Match the description against `seeds.telus_hardware_details` using `LIKE`.
   A match with source `Wireless` is Cellular Hardware. A match with any other
   source is excluded unless its source ID is 164; `Onetime` alone is insufficient.
5. Assign each remaining row to its normal service category. The report checks
   source ID 130 or source `Wireless` for Cellular Plans, then the Data and Voice
   IDs above, and otherwise Other. dbt resolves the source ID through reference
   data, falling back to source only when the ID is missing.

Each retained row contributes to one category only. Negative credits retain
their sign and reduce the category total.

## Hardware patterns and refresh

The shared list is
[`telus_hardware_details.csv`](../../app/backend/dbt/seeds/telus_hardware_details.csv).
Entries are lowercase `LIKE` patterns: `%` matches any suffix, including an empty
suffix. The cost, unmatched-spend, and device-description validators also use this
seed, so all consumers receive the same confirmed descriptions.

- `easy payment%` covers all descriptions beginning with `Easy Payment`, including
  `Easy Payment Amt for Tax Due`, subject to the exclusion and source rules above.
- `gobc data device pom` and `gobc data device pom (%)` cover the plain and dated descriptions.
- `device care complete` and `device care complete (%)` cover the plain and dated descriptions.

After changing the CSV, load it into the database used by the reports. From the
repository root, with the appropriate `POSTGRES_*` connection settings:

```bash
dbt seed --select telus_hardware_details --project-dir app/backend/dbt --profiles-dir app/backend/dbt
dbt run --select int_telus_ngta_spend+ --project-dir app/backend/dbt --profiles-dir app/backend/dbt
```

The seed refresh updates the report allowlist; the dbt run rebuilds application
spend totals. The validation runner reloads its SQL functions by default.

Regression checks for the intermediate model and seed run with:

```bash
PYTHONPATH=app/backend python -m pytest app/backend/tests/dbt/test_telus_spend.py
```
