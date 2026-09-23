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

## Confirmed hardware detail descriptions

These detail descriptions are cellular hardware whatever the service id or statement
category, provided the row is wireless-sourced or `source_id` 164. Matching is on the
description's **word signature** — anything in parentheses is dropped, then every
character that is not a letter, leaving single-spaced words. Telus writes the financed
amount, the term, the expiry date and the covered date range into the label itself, so
`Easy Payment $27.50 - 2yrs (exp. Mar 2027)` and `Easy Payment $40.00 - 3 yrs (exp. Jan
2028)` both reduce to `easy payment yrs` and one entry covers them all.

| Signature | Appears as | Source |
| --- | --- | --- |
| `hardware purchase charge` | Hardware Purchase Charge | Existing methodology |
| `device discount repayment` | Device Discount Repayment | Existing methodology |
| `monthly telus easy payment` | Monthly TELUS Easy Payment | Existing methodology |
| `device discount repay canc` | Device discount repay. canc. | Existing methodology |
| `device discount repay cr` | Device discount repay. - CR | Existing methodology |
| `monthly easy payment` | Monthly Easy Payment | Existing methodology |
| `telus easy payment balance` | TELUS Easy Payment Balance | Existing methodology |
| `equipment adjustment` | Equipment Adjustment | Existing methodology |
| `gobc mos easy payment fee` | GoBC 36 Mos Easy Payment Fee (exp. XXX) | **Telus confirmation — March 2026 report validation** |
| `gobc data device pom` | GoBC Data Device PoM | **Telus confirmation — March 2026 report validation** |
| `office phone device down payment` | Office Phone - device down payment | **Telus confirmation — March 2026 report validation** |
| `smb hardware purchase` | SMB Hardware Purchase | **Telus confirmation — March 2026 report validation** |
| `easy payment yrs` | Easy Payment $XX.XX - Xyrs (exp. XXX) | **Telus confirmation — March 2026 report validation** |
| `device care complete` | Device Care Complete / Device Care Complete (XX to XX) | **Telus confirmation — March 2026 report validation** |

Amounts taken as hardware are not also counted as cellular plans: the bucket `CASE`
tests hardware first, so a row lands in `cellular_hardware` or `cellular_plans`, never
both.

### Where this list lives

- `scripts/validation/telus/helpers/telus_hardware_detail.sql` defines
  `raw_data.fn_telus_is_hardware_detail`, used by the validation report and the
  pricebook scripts.
- `scripts/sql/telus.sql` keeps its own inline copy so it stays pasteable into any
  session.
- `app/backend/dbt/seeds/telus_hardware_details.csv` is the pipeline's copy, seeded
  into the warehouse and read by `int_telus_ngta_spend`.

**Change all three together.**

The normalization itself is `reference_data.telus_detail_signature` (defined in
`app/backend/alembic/reference_data/functions.sql`), which both the pipeline and the
validation scripts call; `scripts/sql/telus.sql` inlines it for the same reason it
inlines the list.

### Effect of the March 2026 additions

Verified with `scripts/sql/telus_hardware_normalization_check.sql` before the change
shipped:

- Moving from literal matching to word signatures reclassified **nothing** — no
  description in the table changed its hardware flag.
- The six new signatures moved **$13,349.73** across 15 months (June 2025 to August
  2026), entirely `cellular_plans` → `cellular_hardware`. Data, voice and the monthly
  totals were unchanged to the cent.
- October 2025 is $9,012.24 of that total; every other month is under $700.
- Every affected row is wireless-sourced, so none were discarded by the
  wireless/`164` gate.

This restates history back to June 2025, not just March 2026 forward — reports published
before this change differ by the amounts above.
